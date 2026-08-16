import os
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from datetime import date, timedelta, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from backend.app.models.models import Product, Sales, Prediction, Business
from backend.app.schemas.schemas import (
    ForecastGenerationResponse,
    ForecastMetadata,
    SkippedProductInfo,
    ForecastItem,
    ForecastProductInfo,
    ForecastPoint,
    ProductForecastResponse,
    LatestForecastResponse,
    LatestForecastProductGroup,
    ForecastListResponse
)
from ml.features.demand_features import build_demand_features
from ml.models.xgboost_model import DemandXGBoostModel

def get_forecast_model() -> Optional[DemandXGBoostModel]:
    """
    Attempts to load local trained XGBoost model artifact if available.
    Returns None if artifact is not present.
    """
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
    model_path = os.path.join(artifacts_dir, "xgboost_demand_model.joblib")
    
    if os.path.exists(model_path):
        try:
            model = DemandXGBoostModel()
            model.load(model_path)
            return model
        except Exception as e:
            print(f"Warning: Failed to load XGBoost model artifact: {e}")
            return None
    return None


def generate_and_persist_forecasts(
    db: Session,
    business_id: int,
    target_product_id: Optional[int] = None
) -> ForecastGenerationResponse:
    """
    Core Forecast Generation Service (Phase 4B).
    
    Rules:
    1. Scoped strictly by business_id (returns 404 for cross-tenant target_product_id).
    2. Checks product eligibility (requires >= 28 distinct historical sales dates).
    3. Products with < 28 days of history are skipped with reason='INSUFFICIENT_HISTORY'.
    4. Generates exactly 7 consecutive calendar days relative to MAX(sale_date).
    5. Applies Option A Replacement Strategy (replaces existing forecasts for same business/product/date/version).
    6. Returns structured response with auditability metadata.
    """
    # 1. Verify tenant & load products
    product_query = db.query(Product).filter(
        Product.business_id == business_id,
        Product.is_active == True
    )

    if target_product_id is not None:
        target_prod = db.query(Product).filter(
            Product.id == target_product_id,
            Product.business_id == business_id
        ).first()

        if not target_prod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product ID {target_product_id} not found in your store catalog."
            )
        products_to_process = [target_prod]
    else:
        products_to_process = product_query.all()

    if not products_to_process:
        now_utc = datetime.now(timezone.utc)
        return ForecastGenerationResponse(
            business_id=business_id,
            generated_count=0,
            skipped_count=0,
            skipped_products=[],
            metadata=ForecastMetadata(
                model_name="XGBoost",
                model_version="xgb-v1",
                training_cutoff_date=date.today(),
                generated_at=now_utc,
                horizon_days=7
            ),
            forecasts=[]
        )

    # 2. Determine business training_cutoff_date
    cutoff_res = db.query(func.max(Sales.sale_date)).filter(Sales.business_id == business_id).scalar()
    training_cutoff_date = cutoff_res if cutoff_res else date.today()

    # Calculate historical stockout ratio
    total_sales_count = db.query(Sales).filter(Sales.business_id == business_id).count()
    confirmed_stockouts = db.query(Sales).filter(Sales.business_id == business_id, Sales.is_stockout == True).count()
    hist_stockout_ratio = round(float(confirmed_stockouts) / float(total_sales_count), 4) if total_sales_count > 0 else 0.0

    model = get_forecast_model()
    model_name = "XGBoost" if (model and model.is_trained) else "Seasonal Naive (y_t-7)"
    model_version = "xgb-v1" if (model and model.is_trained) else "snaive-v1"
    now_utc = datetime.now(timezone.utc)

    generated_items: List[Prediction] = []
    skipped_products: List[SkippedProductInfo] = []

    for product in products_to_process:
        # 3. Check historical eligibility (at least 28 recorded sale dates)
        recorded_days_count = db.query(func.count(func.distinct(Sales.sale_date))).filter(
            Sales.business_id == business_id,
            Sales.product_id == product.id
        ).scalar() or 0

        if recorded_days_count < 28:
            skipped_products.append(SkippedProductInfo(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                reason="INSUFFICIENT_HISTORY"
            ))
            continue

        # Load raw sales data for product
        sales_query = db.query(Sales).filter(
            Sales.business_id == business_id,
            Sales.product_id == product.id
        ).order_by(Sales.sale_date.asc())
        
        sales_list = sales_query.all()
        raw_records = [
            {
                "sale_date": s.sale_date,
                "business_id": business_id,
                "product_id": product.id,
                "units_sold": s.quantity,
                "selling_price": float(s.selling_price),
                "promotion": 1 if s.promotion else 0,
                "holiday": 1 if s.holiday else 0,
                "festival": s.festival,
                "stock_available": s.stock_available,
                "is_stockout": s.is_stockout,
                "category": product.category or "General"
            }
            for s in sales_list
        ]
        import pandas as pd
        raw_df = pd.DataFrame(raw_records)

        df_feat, feat_cols, target_col = build_demand_features(raw_df)
        if df_feat.empty:
            skipped_products.append(SkippedProductInfo(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                reason="INSUFFICIENT_HISTORY"
            ))
            continue

        # Get latest feature row
        latest_row = df_feat.iloc[-1:]

        # Compute base 1-day prediction
        if model and model.is_trained:
            base_pred = float(model.predict(latest_row)[0])
        else:
            # Fallback Seasonal Naive (t-7) or Naive (t-1)
            base_pred = float(latest_row["lag_7"].iloc[0]) if pd.notna(latest_row["lag_7"].iloc[0]) else float(latest_row["lag_1"].iloc[0])

        prod_cutoff_date = pd.to_datetime(latest_row["sale_date"].iloc[0]).date()

        # 4. Generate 7 consecutive calendar days & apply Option A Replacement Strategy
        for h in range(1, 8):
            f_date = prod_cutoff_date + timedelta(days=h)
            predicted_qty = max(0.0, round(float(base_pred), 2))

            # Delete any existing prediction record for same (business_id, product_id, forecast_date, model_version)
            db.query(Prediction).filter(
                Prediction.business_id == business_id,
                Prediction.product_id == product.id,
                Prediction.forecast_date == f_date,
                Prediction.model_version == model_version
            ).delete(synchronize_session=False)

            pred_record = Prediction(
                business_id=business_id,
                product_id=product.id,
                forecast_date=f_date,
                predicted_units=Decimal(str(predicted_qty)),
                model_name=model_name,
                model_version=model_version,
                generated_at=now_utc,
                training_cutoff_date=prod_cutoff_date,
                horizon_days=7
            )
            db.add(pred_record)
            generated_items.append(pred_record)

    db.commit()

    # Refresh items to get assigned IDs
    for item in generated_items:
        db.refresh(item)

    meta = ForecastMetadata(
        model_name=model_name,
        model_version=model_version,
        training_cutoff_date=training_cutoff_date,
        generated_at=now_utc,
        horizon_days=7,
        disclaimer="Forecasts estimate future observed units sold based on historical observations.",
        historical_stockout_ratio=hist_stockout_ratio
    )

    forecast_items = [
        ForecastItem(
            id=item.id,
            business_id=item.business_id,
            product_id=item.product_id,
            forecast_date=item.forecast_date,
            predicted_units=float(item.predicted_units),
            model_name=item.model_name,
            model_version=item.model_version,
            training_cutoff_date=item.training_cutoff_date,
            horizon_days=item.horizon_days,
            generated_at=item.generated_at,
            actual_units=float(item.actual_units) if item.actual_units is not None else None,
            product=ForecastProductInfo(
                id=item.product.id,
                sku=item.product.sku,
                name=item.product.name,
                category=item.product.category
            ) if item.product else None
        )
        for item in generated_items
    ]

    return ForecastGenerationResponse(
        business_id=business_id,
        generated_count=len(generated_items),
        skipped_count=len(skipped_products),
        skipped_products=skipped_products,
        metadata=meta,
        forecasts=forecast_items
    )
