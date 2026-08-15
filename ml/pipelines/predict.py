import pandas as pd
import numpy as np
from datetime import timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import Sales, Product
from ml.features.demand_features import build_demand_features, FEATURE_COLUMNS, TARGET_COLUMN
from ml.models.xgboost_model import DemandXGBoostModel

def generate_7day_forecast(
    db: Session,
    business_id: int,
    model: Optional[DemandXGBoostModel] = None
) -> pd.DataFrame:
    """
    Generates a 7-day observed units sold forecast per product for the authenticated business.
    Calculated relative to the latest available sale_date in PostgreSQL for the business.
    Enforces leakage-safe tabular feature evaluation.
    """
    # 1. Load historical sales
    query = db.query(
        Sales.sale_date,
        Sales.business_id,
        Sales.product_id,
        Sales.quantity.label("units_sold"),
        Sales.selling_price,
        Sales.promotion,
        Sales.holiday,
        Sales.festival,
        Sales.stock_available,
        Sales.is_stockout,
        Product.category,
        Product.sku,
        Product.name.label("product_name")
    ).join(Product, Product.id == Sales.product_id).filter(
        Sales.business_id == business_id
    ).order_by(Sales.sale_date.asc())

    records = [dict(row._mapping) for row in query.all()]
    if not records:
        return pd.DataFrame()

    df_raw = pd.DataFrame(records)
    
    # 2. Build leakage-safe features for historical series
    df_feat, feat_cols, target_col = build_demand_features(df_raw)
    if df_feat.empty:
        return pd.DataFrame()

    # Get latest date per product
    latest_date = df_feat["sale_date"].max()
    
    # Filter latest feature vector per product (t = max_date)
    latest_features = df_feat[df_feat["sale_date"] == latest_date].copy()

    forecast_rows = []
    for idx, row in latest_features.iterrows():
        pid = row["product_id"]
        sku = row["sku"]
        pname = row["product_name"]
        cat = row["category"]

        # Base prediction from model or lag_7 seasonal fallback
        if model and model.is_trained:
            pred_base = model.predict(pd.DataFrame([row]))[0]
        else:
            pred_base = float(row["lag_7"]) if pd.notna(row["lag_7"]) else float(row["lag_1"])

        # Generate 7-day horizon projection (days t+1 to t+7)
        for h in range(1, 8):
            target_date = latest_date + timedelta(days=h)
            # Add small random variation or promo effect if needed, clip at 0
            day_pred = max(0.0, float(pred_base))
            
            forecast_rows.append({
                "business_id": business_id,
                "product_id": pid,
                "sku": sku,
                "product_name": pname,
                "category": cat,
                "forecast_date": target_date.strftime("%Y-%m-%d"),
                "horizon_day": h,
                "predicted_observed_units": round(day_pred, 2)
            })

    return pd.DataFrame(forecast_rows)
