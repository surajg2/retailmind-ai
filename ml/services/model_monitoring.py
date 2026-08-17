import math
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.schemas.schemas import ModelMonitoring
from ml.services.forecast_evaluation_service import evaluate_forecast_trend

# Configurable Threshold Constants (Documented)
STABLE_THRESHOLD = 1.15 # Degradation ratio < 1.15 is STABLE
WATCH_THRESHOLD = 1.35  # Degradation ratio 1.15 - 1.35 is WATCH; > 1.35 is DEGRADED
RECENT_WINDOW_DAYS = 7  # Recent window uses 7 most recent evaluated dates


def monitor_model_performance(
    db: Session,
    business_id: int,
    product_id: Optional[int] = None
) -> ModelMonitoring:
    """
    Evaluates forecast model error drift over time.
    Compares recent MAE (last 7 evaluated dates) against historical baseline MAE (preceding evaluation dates).
    
    Status Rules:
    - ratio < 1.15 -> STABLE
    - 1.15 <= ratio <= 1.35 -> WATCH
    - ratio > 1.35 -> DEGRADED
    - If historical_mae == 0:
        - recent_mae == 0 -> STABLE
        - recent_mae > 0 -> DEGRADED
    - If evaluated dates count < 7 -> INSUFFICIENT_MONITORING_DATA
    """
    trend = evaluate_forecast_trend(db, business_id=business_id, product_id=product_id)

    if not trend or len(trend) < RECENT_WINDOW_DAYS:
        return ModelMonitoring(
            business_id=business_id,
            model_name="XGBoost",
            model_version="xgb-v1",
            status="INSUFFICIENT_MONITORING_DATA",
            recent_mae=None,
            historical_mae=None,
            degradation_ratio=None,
            evaluated_days=len(trend),
            explanation=f"Insufficient historical evaluation days (requires at least {RECENT_WINDOW_DAYS} evaluated dates, found {len(trend)}).",
            thresholds={"stable": STABLE_THRESHOLD, "watch": WATCH_THRESHOLD, "window": RECENT_WINDOW_DAYS}
        )

    # Sort trend points by date ascending
    sorted_trend = sorted(trend, key=lambda p: p.evaluation_date)

    recent_points = sorted_trend[-RECENT_WINDOW_DAYS:]
    historical_points = sorted_trend[:-RECENT_WINDOW_DAYS]

    recent_mae = sum(p.mae for p in recent_points) / len(recent_points)

    if historical_points:
        historical_mae = sum(p.mae for p in historical_points) / len(historical_points)
    else:
        # If all available dates fit in recent window, use recent as historical baseline
        historical_mae = recent_mae

    recent_mae = round(recent_mae, 2)
    historical_mae = round(historical_mae, 2)

    # Calculate degradation ratio and status
    if historical_mae == 0:
        if recent_mae == 0:
            ratio = 1.0
            status = "STABLE"
            explanation = "Model error is 0.0 across recent and historical evaluation periods (STABLE)."
        else:
            ratio = float('inf')
            status = "DEGRADED"
            explanation = f"Recent MAE increased to {recent_mae} from historical baseline of 0.0 (DEGRADED)."
    else:
        ratio = round(recent_mae / historical_mae, 2)
        if ratio < STABLE_THRESHOLD:
            status = "STABLE"
            explanation = f"Recent MAE ({recent_mae}) is within 15% of historical baseline MAE ({historical_mae}). Model performance is STABLE."
        elif ratio <= WATCH_THRESHOLD:
            status = "WATCH"
            explanation = f"Recent MAE ({recent_mae}) is {int((ratio - 1.0)*100)}% higher than historical baseline MAE ({historical_mae}). Model performance is under WATCH."
        else:
            status = "DEGRADED"
            explanation = f"Recent MAE ({recent_mae}) is {int((ratio - 1.0)*100)}% higher than historical baseline MAE ({historical_mae}). Model performance is DEGRADED."

    return ModelMonitoring(
        business_id=business_id,
        model_name="XGBoost",
        model_version="xgb-v1",
        status=status,
        recent_mae=recent_mae,
        historical_mae=historical_mae,
        degradation_ratio=ratio if not math.isinf(ratio) else 99.99,
        evaluated_days=len(sorted_trend),
        explanation=explanation,
        thresholds={"stable": STABLE_THRESHOLD, "watch": WATCH_THRESHOLD, "window": RECENT_WINDOW_DAYS}
    )
