from datetime import date
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import AnomalyListResponse
from ml.services.anomaly_service import detect_sales_anomalies

router = APIRouter()

@router.get("", response_model=AnomalyListResponse)
def get_anomalies(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    product_id: Optional[int] = Query(None, description="Filter by Product ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, WARNING, INFO)"),
    anomaly_type: Optional[str] = Query(None, description="Filter by type (HIGH_SALES, LOW_SALES, ZERO_SALES, PROMOTION_SPIKE, PRICE_CHANGE)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve historical sales anomalies detected via 21-day rolling median & MAD.
    Strictly scoped by business_id. Enforces tenant isolation.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date cannot be after end_date.")

    return detect_sales_anomalies(
        db=db,
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date,
        product_id=product_id,
        category=category,
        severity_filter=severity,
        anomaly_type_filter=anomaly_type
    )
