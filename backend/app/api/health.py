from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.db.session import get_db
from backend.app.schemas.schemas import HealthCheck

router = APIRouter()

@router.get("/health", response_model=HealthCheck, status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    db_status = "unconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": db_status}
        )

    return HealthCheck(
        status="ok",
        database=db_status,
        timestamp=datetime.now(timezone.utc)
    )
