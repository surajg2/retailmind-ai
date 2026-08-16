from datetime import date, timedelta, datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.models import User, Product, Sales, Prediction, Business
from backend.app.schemas.schemas import (
    ForecastGenerateRequest,
    ForecastGenerationResponse,
    ForecastListResponse,
    ProductForecastResponse,
    LatestForecastResponse,
    ForecastItem,
    ForecastProductInfo,
    ForecastMetadata,
    ForecastPoint,
    LatestForecastProductGroup
)
from ml.services.forecast_service import generate_and_persist_forecasts, get_forecast_model

router = APIRouter()

@router.post("/generate", response_model=ForecastGenerationResponse, status_code=status.HTTP_201_CREATED)
def generate_forecasts(
    payload: ForecastGenerateRequest = ForecastGenerateRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate and persist 7-day demand forecasts for the authenticated business.
    - If product_id is supplied: generates forecast for that product only.
    - If product_id is omitted: generates forecasts for all eligible active products.
    - Replaces existing forecast records for the same (business, product, forecast_date, model_version).
    - Products with < 28 recorded sales dates are skipped cleanly.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    return generate_and_persist_forecasts(
        db=db,
        business_id=current_user.business_id,
        target_product_id=payload.product_id
    )


@router.get("", response_model=ForecastListResponse)
def get_forecasts(
    product_id: Optional[int] = Query(None, description="Filter by Product ID"),
    start_date: Optional[date] = Query(None, description="Filter start date"),
    end_date: Optional[date] = Query(None, description="Filter end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve persisted demand forecasts for the authenticated business.
    Strictly tenant-scoped.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id

    # If product_id supplied, verify tenant ownership
    if product_id is not None:
        prod = db.query(Product).filter(Product.id == product_id, Product.business_id == b_id).first()
        if not prod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product ID {product_id} not found in your store catalog."
            )

    # Validate date range parameters
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date."
        )

    query = db.query(Prediction).filter(Prediction.business_id == b_id)

    if product_id is not None:
        query = query.filter(Prediction.product_id == product_id)

    if start_date:
        query = query.filter(Prediction.forecast_date >= start_date)
    if end_date:
        query = query.filter(Prediction.forecast_date <= end_date)

    # Default to next 7 forecast days relative to max forecast_date if no dates provided
    if not start_date and not end_date:
        max_fdate = db.query(func.max(Prediction.forecast_date)).filter(Prediction.business_id == b_id).scalar()
        if max_fdate:
            min_fdate = max_fdate - timedelta(days=6)
            query = query.filter(Prediction.forecast_date >= min_fdate, Prediction.forecast_date <= max_fdate)

    predictions = query.order_by(Prediction.forecast_date.asc(), Prediction.product_id.asc()).all()

    # Build Metadata
    cutoff_res = db.query(func.max(Sales.sale_date)).filter(Sales.business_id == b_id).scalar()
    cutoff_date = cutoff_res if cutoff_res else date.today()
    now_utc = datetime.now(timezone.utc)

    meta = ForecastMetadata(
        model_name="XGBoost",
        model_version="xgb-v1",
        training_cutoff_date=cutoff_date,
        generated_at=now_utc,
        horizon_days=7,
        disclaimer="Forecasts estimate future observed units sold based on historical observations."
    )

    items = [
        ForecastItem(
            id=p.id,
            business_id=p.business_id,
            product_id=p.product_id,
            forecast_date=p.forecast_date,
            predicted_units=float(p.predicted_units),
            model_name=p.model_name,
            model_version=p.model_version,
            training_cutoff_date=p.training_cutoff_date,
            horizon_days=p.horizon_days,
            generated_at=p.generated_at,
            actual_units=float(p.actual_units) if p.actual_units is not None else None,
            product=ForecastProductInfo(
                id=p.product.id,
                sku=p.product.sku,
                name=p.product.name,
                category=p.product.category
            ) if p.product else None
        )
        for p in predictions
    ]

    return ForecastListResponse(
        total_records=len(items),
        metadata=meta,
        forecasts=items
    )


@router.get("/product/{product_id}", response_model=ProductForecastResponse)
def get_product_forecast(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve 7-day demand forecast for a specific product.
    Returns 404 if product does not belong to the authenticated business.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id

    # Verify tenant ownership
    prod = db.query(Product).filter(Product.id == product_id, Product.business_id == b_id).first()
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found in your store catalog."
        )

    predictions = db.query(Prediction).filter(
        Prediction.business_id == b_id,
        Prediction.product_id == product_id
    ).order_by(Prediction.forecast_date.asc()).all()

    # Get latest 7 forecast points
    if len(predictions) > 7:
        predictions = predictions[-7:]

    cutoff_res = db.query(func.max(Sales.sale_date)).filter(
        Sales.business_id == b_id,
        Sales.product_id == product_id
    ).scalar()
    cutoff_date = cutoff_res if cutoff_res else date.today()
    now_utc = datetime.now(timezone.utc)

    meta = ForecastMetadata(
        model_name=predictions[0].model_name if predictions else "XGBoost",
        model_version=predictions[0].model_version if predictions else "xgb-v1",
        training_cutoff_date=predictions[0].training_cutoff_date if predictions else cutoff_date,
        generated_at=predictions[0].generated_at if predictions else now_utc,
        horizon_days=7,
        disclaimer="Forecasts estimate future observed units sold based on historical observations."
    )

    points = [
        ForecastPoint(
            forecast_date=p.forecast_date,
            predicted_units=float(p.predicted_units),
            actual_units=float(p.actual_units) if p.actual_units is not None else None
        )
        for p in predictions
    ]

    return ProductForecastResponse(
        product=ForecastProductInfo(
            id=prod.id,
            sku=prod.sku,
            name=prod.name,
            category=prod.category
        ),
        metadata=meta,
        forecast=points
    )


@router.get("/latest", response_model=LatestForecastResponse)
def get_latest_forecasts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve deterministic latest 7-day forecast set for the authenticated business.
    Groups predictions by product for the most recent generated batch.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id

    # Find latest generated_at timestamp for business predictions
    latest_gen = db.query(func.max(Prediction.generated_at)).filter(Prediction.business_id == b_id).scalar()

    if not latest_gen:
        now_utc = datetime.now(timezone.utc)
        return LatestForecastResponse(
            business_id=b_id,
            generated_at=now_utc,
            model_version="xgb-v1",
            training_cutoff_date=date.today(),
            horizon_days=7,
            total_products=0,
            products=[]
        )

    # Query all predictions belonging to latest_gen timestamp (or latest predictions per product)
    latest_preds = db.query(Prediction).filter(
        Prediction.business_id == b_id,
        Prediction.generated_at == latest_gen
    ).order_by(Prediction.product_id.asc(), Prediction.forecast_date.asc()).all()

    # Group by product
    prod_map: Dict[int, Tuple[Product, List[ForecastPoint]]] = {}
    for p in latest_preds:
        pid = p.product_id
        if pid not in prod_map:
            prod_map[pid] = (p.product, [])
        prod_map[pid][1].append(ForecastPoint(
            forecast_date=p.forecast_date,
            predicted_units=float(p.predicted_units),
            actual_units=float(p.actual_units) if p.actual_units is not None else None
        ))

    product_groups = [
        LatestForecastProductGroup(
            product=ForecastProductInfo(
                id=prod.id,
                sku=prod.sku,
                name=prod.name,
                category=prod.category
            ),
            forecast=points
        )
        for pid, (prod, points) in prod_map.items()
    ]

    first_pred = latest_preds[0] if latest_preds else None

    return LatestForecastResponse(
        business_id=b_id,
        generated_at=latest_gen,
        model_version=first_pred.model_version if first_pred else "xgb-v1",
        training_cutoff_date=first_pred.training_cutoff_date if first_pred else date.today(),
        horizon_days=7,
        total_products=len(product_groups),
        products=product_groups
    )
