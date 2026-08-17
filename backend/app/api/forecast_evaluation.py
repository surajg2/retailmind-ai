from datetime import date
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import (
    ForecastEvaluationSummary,
    ForecastEvaluationPoint,
    ProductForecastEvaluation,
    ModelMonitoring
)
from ml.services.forecast_evaluation_service import (
    evaluate_forecasts,
    evaluate_forecast_trend,
    evaluate_product_forecast
)
from ml.services.model_monitoring import monitor_model_performance

router = APIRouter()

@router.get("/summary", response_model=ForecastEvaluationSummary)
def get_evaluation_summary(
    product_id: Optional[int] = Query(None, description="Filter by Product ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve store forecast vs actual evaluation metrics (MAE, RMSE, Zero-Safe MAPE, coverage, stockouts).
    Enforces strict tenant isolation.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date cannot be after end_date.")

    return evaluate_forecasts(
        db=db,
        business_id=current_user.business_id,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/trend", response_model=List[ForecastEvaluationPoint])
def get_evaluation_trend(
    product_id: Optional[int] = Query(None, description="Filter by Product ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve historical forecast evaluation performance time-series over time.
    Enforces strict tenant isolation.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    return evaluate_forecast_trend(
        db=db,
        business_id=current_user.business_id,
        product_id=product_id
    )


@router.get("/product/{product_id}", response_model=ProductForecastEvaluation)
def get_product_evaluation(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve 7-day forecast evaluation and accuracy metrics for a specific product.
    Returns 404 if product does not belong to current user's business.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    return evaluate_product_forecast(
        db=db,
        business_id=current_user.business_id,
        product_id=product_id
    )


@router.get("/models", response_model=ModelMonitoring)
def get_model_monitoring(
    product_id: Optional[int] = Query(None, description="Filter by Product ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve model error drift and performance status (STABLE, WATCH, DEGRADED, INSUFFICIENT_MONITORING_DATA).
    Compares recent MAE (last 7 evaluated dates) against historical baseline MAE.
    Enforces strict tenant isolation.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    return monitor_model_performance(
        db=db,
        business_id=current_user.business_id,
        product_id=product_id
    )
