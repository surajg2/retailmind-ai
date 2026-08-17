import statistics
from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.models import Sales, Product
from backend.app.schemas.schemas import AnomalyItem, AnomalyListResponse


def calculate_median(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(values))


def calculate_mad(values: List[float], median_val: float) -> float:
    if not values:
        return 0.0
    devs = [abs(x - median_val) for x in values]
    return float(statistics.median(devs))


def detect_sales_anomalies(
    db: Session,
    business_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    severity_filter: Optional[str] = None,
    anomaly_type_filter: Optional[str] = None
) -> AnomalyListResponse:
    """
    Detects historical sales anomalies dynamically from Sales data using 21-day rolling median & MAD.
    Strictly scoped by business_id.
    
    Rules:
    - Current observation t is EXCLUDED from its own baseline [t-21 ... t-1] (leakage-safe).
    - Stockout days (is_stockout == True) are NOT classified as low customer demand anomalies.
    - Zero sales are only flagged as ZERO_SALES if statistically unusual relative to baseline.
    """
    prod_query = db.query(Product).filter(Product.business_id == business_id)
    if product_id is not None:
        prod_query = prod_query.filter(Product.id == product_id)
    if category:
        prod_query = prod_query.filter(Product.category == category)

    products = prod_query.all()
    if not products:
        return AnomalyListResponse(
            business_id=business_id,
            total_count=0,
            critical_count=0,
            warning_count=0,
            anomalies=[]
        )

    anomalies: List[AnomalyItem] = []

    for prod in products:
        sales_records = db.query(Sales).filter(
            Sales.business_id == business_id,
            Sales.product_id == prod.id
        ).order_by(Sales.sale_date.asc()).all()

        if len(sales_records) < 7:
            # Insufficient history to establish rolling baseline
            continue

        prev_price: Optional[float] = None

        for i, curr in enumerate(sales_records):
            s_date = curr.sale_date

            # Date range filtering
            if start_date and s_date < start_date:
                prev_price = float(curr.selling_price)
                continue
            if end_date and s_date > end_date:
                prev_price = float(curr.selling_price)
                continue

            curr_units = float(curr.quantity)
            curr_price = float(curr.selling_price)

            # Price Change Detection
            price_change_pct: Optional[float] = None
            price_anomaly = False
            if prev_price is not None and prev_price > 0:
                p_diff = abs(curr_price - prev_price)
                if p_diff / prev_price >= 0.05:
                    price_change_pct = round(((curr_price - prev_price) / prev_price) * 100.0, 2)
                    price_anomaly = True

            # Extract prior 21 days window (excluding current day i)
            window_start = max(0, i - 21)
            prior_records = sales_records[window_start:i]

            if len(prior_records) < 5:
                # Use current price as prev_price for next iteration
                prev_price = curr_price
                continue

            prior_units = [float(r.quantity) for r in prior_records]
            baseline_median = calculate_median(prior_units)
            mad = calculate_mad(prior_units, baseline_median)

            # Modified Z-Score calculation
            if mad > 0:
                z_score = 0.6745 * (curr_units - baseline_median) / mad
            else:
                # Fallback ratio deviation if MAD is 0
                diff = curr_units - baseline_median
                z_score = (diff / (baseline_median + 1.0)) * 3.0

            deviation = round(curr_units - baseline_median, 2)
            z_score = round(z_score, 2)

            detected_type: Optional[str] = None
            severity: str = "INFO"

            # Check Anomaly Rules
            if curr.promotion and z_score > 2.5:
                detected_type = "PROMOTION_SPIKE"
                severity = "WARNING" if z_score <= 4.0 else "CRITICAL"

            elif price_anomaly:
                detected_type = "PRICE_CHANGE"
                severity = "WARNING" if (price_change_pct and abs(price_change_pct) >= 15.0) else "INFO"

            elif z_score > 3.0:
                detected_type = "HIGH_SALES"
                severity = "CRITICAL" if z_score > 4.5 else "WARNING"

            elif z_score < -3.0:
                if curr.is_stockout:
                    # Stockout censoring: DO NOT classify as customer demand drop
                    detected_type = None
                elif curr_units == 0:
                    detected_type = "ZERO_SALES"
                    severity = "CRITICAL" if z_score < -4.5 else "WARNING"
                else:
                    detected_type = "LOW_SALES"
                    severity = "CRITICAL" if z_score < -4.5 else "WARNING"

            if detected_type is not None:
                # Filter check
                if anomaly_type_filter and detected_type != anomaly_type_filter:
                    prev_price = curr_price
                    continue
                if severity_filter and severity != severity_filter:
                    prev_price = curr_price
                    continue

                anomalies.append(AnomalyItem(
                    product_id=prod.id,
                    sku=prod.sku,
                    product_name=prod.name,
                    category=prod.category,
                    date=s_date,
                    anomaly_type=detected_type,
                    severity=severity,
                    observed_units=int(curr_units),
                    baseline_units=round(baseline_median, 2),
                    deviation=deviation,
                    deviation_score=z_score,
                    is_stockout=bool(curr.is_stockout),
                    promotion=bool(curr.promotion),
                    holiday=bool(curr.holiday),
                    festival=curr.festival,
                    selling_price=curr_price,
                    previous_price=prev_price,
                    price_change_percentage=price_change_pct
                ))

            prev_price = curr_price

    # Sort anomalies by date descending
    anomalies.sort(key=lambda a: a.date, reverse=True)

    critical_c = sum(1 for a in anomalies if a.severity == "CRITICAL")
    warning_c = sum(1 for a in anomalies if a.severity == "WARNING")

    return AnomalyListResponse(
        business_id=business_id,
        total_count=len(anomalies),
        critical_count=critical_c,
        warning_count=warning_c,
        anomalies=anomalies
    )
