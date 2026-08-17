import math
from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.models import Sales, Prediction, Product
from backend.app.schemas.schemas import (
    ForecastEvaluationSummary,
    ForecastEvaluationPoint,
    ProductForecastEvaluation
)

def evaluate_forecasts(
    db: Session,
    business_id: int,
    product_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> ForecastEvaluationSummary:
    """
    Evaluates persisted Prediction records against historical observed Sales records.
    Strictly scoped by business_id.
    
    Rules:
    - Target terminology: "Observed Units Sold" (never "True Demand" or "Actual Demand").
    - Evaluates ONLY forecasts for target dates where historical sales observations exist (sale_date <= MAX(sale_date)).
    - absolute_error = abs(observed - predicted)
    - squared_error = (observed - predicted) ** 2
    - percentage_error = abs(observed - predicted) / observed ONLY when observed > 0.
    - Zero observed sales are excluded from MAPE calculation to prevent division by zero.
    - Separately counts confirmed stockout observations (is_stockout == True) and zero EOD stock observations (stock_available == 0).
    - If evaluated_count == 0, returns status='INSUFFICIENT_EVALUATION_DATA' with null metrics.
    """
    # 1. Total persisted prediction count for tenant
    total_query = db.query(Prediction).filter(Prediction.business_id == business_id)
    if product_id is not None:
        total_query = total_query.filter(Prediction.product_id == product_id)
    if start_date:
        total_query = total_query.filter(Prediction.forecast_date >= start_date)
    if end_date:
        total_query = total_query.filter(Prediction.forecast_date <= end_date)
        
    total_forecast_count = total_query.count()

    # 2. Join Prediction with Sales for matching business_id, product_id, and forecast_date == sale_date
    query = db.query(Prediction, Sales).join(
        Sales,
        (Prediction.business_id == Sales.business_id) &
        (Prediction.product_id == Sales.product_id) &
        (Prediction.forecast_date == Sales.sale_date)
    ).filter(Prediction.business_id == business_id)

    if product_id is not None:
        query = query.filter(Prediction.product_id == product_id)
    if start_date:
        query = query.filter(Prediction.forecast_date >= start_date)
    if end_date:
        query = query.filter(Prediction.forecast_date <= end_date)

    pairs = query.all()
    evaluated_count = len(pairs)

    if evaluated_count == 0:
        return ForecastEvaluationSummary(
            business_id=business_id,
            model_name="XGBoost",
            model_version="xgb-v1",
            eligible_forecast_count=total_forecast_count,
            evaluated_count=0,
            evaluation_coverage=0.0,
            mae=None,
            rmse=None,
            mape=None,
            confirmed_stockout_count=0,
            zero_eod_stock_count=0,
            status="INSUFFICIENT_EVALUATION_DATA",
            message="No historical observed sales records match the forecast target dates yet."
        )

    abs_errors: List[float] = []
    sq_errors: List[float] = []
    pct_errors: List[float] = []

    confirmed_stockouts = 0
    zero_eod_stock_days = 0

    first_pred = pairs[0][0]
    model_name = first_pred.model_name
    model_version = first_pred.model_version
    training_cutoff = first_pred.training_cutoff_date

    for pred, sale in pairs:
        obs = float(sale.quantity)
        pred_val = float(pred.predicted_units)

        abs_err = abs(obs - pred_val)
        sq_err = (obs - pred_val) ** 2

        abs_errors.append(abs_err)
        sq_errors.append(sq_err)

        if obs > 0:
            pct_errors.append(abs_err / obs)

        if sale.is_stockout is True:
            confirmed_stockouts += 1
        if sale.stock_available == 0:
            zero_eod_stock_days += 1

    mae = sum(abs_errors) / evaluated_count
    rmse = math.sqrt(sum(sq_errors) / evaluated_count)
    mape = (sum(pct_errors) / len(pct_errors) * 100.0) if pct_errors else None

    coverage = evaluated_count / total_forecast_count if total_forecast_count > 0 else 1.0

    eval_status = "EVALUATED"
    if coverage < 0.20:
        eval_status = "LOW_EVALUATION_COVERAGE"

    return ForecastEvaluationSummary(
        business_id=business_id,
        model_name=model_name,
        model_version=model_version,
        eligible_forecast_count=total_forecast_count,
        evaluated_count=evaluated_count,
        evaluation_coverage=round(coverage, 4),
        mae=round(mae, 2),
        rmse=round(rmse, 2),
        mape=round(mape, 2) if mape is not None else None,
        confirmed_stockout_count=confirmed_stockouts,
        zero_eod_stock_count=zero_eod_stock_days,
        status=eval_status,
        start_date=min(p[0].forecast_date for p in pairs),
        end_date=max(p[0].forecast_date for p in pairs),
        training_cutoff_date=training_cutoff
    )


def evaluate_forecast_trend(
    db: Session,
    business_id: int,
    product_id: Optional[int] = None
) -> List[ForecastEvaluationPoint]:
    """
    Returns time-series evaluation metrics grouped by forecast_date.
    Only evaluates dates with matching historical Sales observations.
    """
    query = db.query(Prediction, Sales).join(
        Sales,
        (Prediction.business_id == Sales.business_id) &
        (Prediction.product_id == Sales.product_id) &
        (Prediction.forecast_date == Sales.sale_date)
    ).filter(Prediction.business_id == business_id)

    if product_id is not None:
        query = query.filter(Prediction.product_id == product_id)

    pairs = query.order_by(Prediction.forecast_date.asc()).all()

    if not pairs:
        return []

    grouped: Dict[date, List[tuple]] = {}
    for pred, sale in pairs:
        d = pred.forecast_date
        if d not in grouped:
            grouped[d] = []
        grouped[d].append((pred, sale))

    points: List[ForecastEvaluationPoint] = []
    for d in sorted(grouped.keys()):
        day_pairs = grouped[d]
        abs_errs = []
        sq_errs = []
        pct_errs = []

        for p, s in day_pairs:
            obs = float(s.quantity)
            pred_v = float(p.predicted_units)
            ae = abs(obs - pred_v)
            abs_errs.append(ae)
            sq_errs.append(ae ** 2)
            if obs > 0:
                pct_errs.append(ae / obs)

        day_mae = sum(abs_errs) / len(abs_errs)
        day_rmse = math.sqrt(sum(sq_errs) / len(sq_errs))
        day_mape = (sum(pct_errs) / len(pct_errs) * 100.0) if pct_errs else None

        points.append(ForecastEvaluationPoint(
            evaluation_date=d,
            mae=round(day_mae, 2),
            rmse=round(day_rmse, 2),
            mape=round(day_mape, 2) if day_mape is not None else None,
            evaluated_count=len(day_pairs)
        ))

    return points


def evaluate_product_forecast(
    db: Session,
    business_id: int,
    product_id: int
) -> ProductForecastEvaluation:
    """
    Evaluates forecast accuracy for a single product.
    Returns 404 if product does not belong to tenant.
    """
    prod = db.query(Product).filter(Product.id == product_id, Product.business_id == business_id).first()
    if not prod:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found in store catalog."
        )

    summary = evaluate_forecasts(db, business_id=business_id, product_id=product_id)
    trend_points = evaluate_forecast_trend(db, business_id=business_id, product_id=product_id)

    # Load 7-day prediction vs observed point array
    query = db.query(Prediction, Sales).join(
        Sales,
        (Prediction.business_id == Sales.business_id) &
        (Prediction.product_id == Sales.product_id) &
        (Prediction.forecast_date == Sales.sale_date)
    ).filter(Prediction.business_id == business_id, Prediction.product_id == product_id).order_by(Prediction.forecast_date.asc())

    pairs = query.all()
    points_detail = [
        {
            "forecast_date": p.forecast_date,
            "predicted_units": float(p.predicted_units),
            "observed_units": float(s.quantity),
            "absolute_error": round(abs(float(s.quantity) - float(p.predicted_units)), 2),
            "is_stockout": s.is_stockout
        }
        for p, s in pairs
    ]

    return ProductForecastEvaluation(
        product_id=prod.id,
        sku=prod.sku,
        product_name=prod.name,
        category=prod.category,
        model_name=summary.model_name,
        model_version=summary.model_version,
        summary=summary,
        trend=trend_points,
        points=points_detail
    )
