from datetime import date, timedelta
from decimal import Decimal
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.models import Product, Sales, User
from backend.app.schemas.schemas import (
    AnalyticsSummary,
    CategoryBreakdown,
    DataQualityReport,
    ProductPerformancePoint,
    SalesTrendPoint,
    TopProductItem,
)

router = APIRouter()

def resolve_date_bounds(
    db: Session,
    business_id: int,
    range_preset: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date]
) -> tuple[Optional[date], Optional[date]]:
    """
    Resolves date range bounds based on presets (7d, 30d, 90d, 1y, all) or custom inputs.
    ALL preset dynamically calculates min(sale_date) to max(sale_date) for the business.
    """
    if range_preset:
        preset = range_preset.lower()
        if preset == "all":
            min_max = db.query(
                func.min(Sales.sale_date),
                func.max(Sales.sale_date)
            ).filter(Sales.business_id == business_id).first()
            if min_max and min_max[0] and min_max[1]:
                return min_max[0], min_max[1]
            return None, None
        
        today = date.today()
        if preset == "7d":
            return today - timedelta(days=7), today
        elif preset == "30d":
            return today - timedelta(days=30), today
        elif preset == "90d":
            return today - timedelta(days=90), today
        elif preset == "1y":
            return today - timedelta(days=365), today

    return start_date, end_date


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    range_preset: Optional[str] = Query("all", alias="range", description="Preset range: 7d, 30d, 90d, 1y, all"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id
    s_date, e_date = resolve_date_bounds(db, b_id, range_preset, start_date, end_date)

    query = db.query(Sales).filter(Sales.business_id == b_id)
    if category:
        query = query.join(Product).filter(Product.category.ilike(f"%{category}%"))
    if s_date:
        query = query.filter(Sales.sale_date >= s_date)
    if e_date:
        query = query.filter(Sales.sale_date <= e_date)

    # 1. Total Revenue & Observed Units Sold
    sums = query.with_entities(
        func.coalesce(func.sum(Sales.total_amount), 0),
        func.coalesce(func.sum(Sales.quantity), 0),
        func.count(func.distinct(Sales.sale_date))
    ).first()

    total_revenue = Decimal(str(sums[0]))
    observed_units_sold = int(sums[1])
    recorded_days_count = int(sums[2])

    # Average Revenue / Recorded Day (Using distinct recorded sale dates)
    avg_rev_per_recorded_day = Decimal("0.00")
    if recorded_days_count > 0:
        avg_rev_per_recorded_day = round(total_revenue / Decimal(recorded_days_count), 2)

    # Active Catalog Size
    active_catalog_size = db.query(func.count(Product.id)).filter(
        Product.business_id == b_id,
        Product.is_active == True
    ).scalar() or 0

    # Confirmed Stockout Days (strictly is_stockout = TRUE)
    confirmed_stockout_query = query.filter(Sales.is_stockout == True)
    confirmed_stockout_days = confirmed_stockout_query.with_entities(
        func.count(func.distinct(Sales.sale_date))
    ).scalar() or 0

    # Zero EOD Inventory Days (strictly stock_available = 0)
    zero_eod_query = query.filter(Sales.stock_available == 0)
    zero_eod_stock_days = zero_eod_query.with_entities(
        func.count(func.distinct(Sales.sale_date))
    ).scalar() or 0

    return AnalyticsSummary(
        total_revenue=total_revenue,
        observed_units_sold=observed_units_sold,
        avg_revenue_per_recorded_day=avg_rev_per_recorded_day,
        active_catalog_size=active_catalog_size,
        confirmed_stockout_days=confirmed_stockout_days,
        zero_eod_stock_days=zero_eod_stock_days,
        start_date=s_date,
        end_date=e_date
    )


@router.get("/sales-trend", response_model=List[SalesTrendPoint])
def get_sales_trend(
    range_preset: Optional[str] = Query("all", alias="range"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id
    s_date, e_date = resolve_date_bounds(db, b_id, range_preset, start_date, end_date)

    query = db.query(
        Sales.sale_date,
        func.coalesce(func.sum(Sales.total_amount), 0).label("revenue"),
        func.coalesce(func.sum(Sales.quantity), 0).label("units_sold"),
        func.bool_or(Sales.promotion).label("promo_active")
    ).filter(Sales.business_id == b_id)

    if category:
        query = query.join(Product).filter(Product.category.ilike(f"%{category}%"))
    if s_date:
        query = query.filter(Sales.sale_date >= s_date)
    if e_date:
        query = query.filter(Sales.sale_date <= e_date)

    trend_data = query.group_by(Sales.sale_date).order_by(Sales.sale_date.asc()).all()

    return [
        SalesTrendPoint(
            sale_date=row.sale_date,
            revenue=round(Decimal(str(row.revenue)), 2),
            units_sold=int(row.units_sold),
            promo_active=bool(row.promo_active)
        )
        for row in trend_data
    ]


@router.get("/category-breakdown", response_model=List[CategoryBreakdown])
def get_category_breakdown(
    range_preset: Optional[str] = Query("all", alias="range"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id
    s_date, e_date = resolve_date_bounds(db, b_id, range_preset, start_date, end_date)

    query = db.query(
        func.coalesce(Product.category, "Uncategorized").label("category"),
        func.coalesce(func.sum(Sales.total_amount), 0).label("revenue"),
        func.coalesce(func.sum(Sales.quantity), 0).label("units_sold")
    ).join(Sales, Sales.product_id == Product.id).filter(Sales.business_id == b_id)

    if s_date:
        query = query.filter(Sales.sale_date >= s_date)
    if e_date:
        query = query.filter(Sales.sale_date <= e_date)

    breakdown = query.group_by(Product.category).all()
    total_rev = sum(Decimal(str(r.revenue)) for r in breakdown) or Decimal("1.00")

    result = []
    for r in breakdown:
        rev = Decimal(str(r.revenue))
        pct = float((rev / total_rev) * 100) if total_rev > 0 else 0.0
        result.append(CategoryBreakdown(
            category=r.category,
            revenue=round(rev, 2),
            units_sold=int(r.units_sold),
            percentage_share=round(pct, 2)
        ))

    result.sort(key=lambda x: x.revenue, reverse=True)
    return result


@router.get("/top-products", response_model=List[TopProductItem])
def get_top_products(
    limit: int = Query(5, ge=1, le=50),
    range_preset: Optional[str] = Query("all", alias="range"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id
    s_date, e_date = resolve_date_bounds(db, b_id, range_preset, start_date, end_date)

    query = db.query(
        Product.id.label("product_id"),
        Product.sku,
        Product.name,
        Product.category,
        func.coalesce(func.sum(Sales.total_amount), 0).label("total_revenue"),
        func.coalesce(func.sum(Sales.quantity), 0).label("total_units_sold")
    ).join(Sales, Sales.product_id == Product.id).filter(Sales.business_id == b_id)

    if s_date:
        query = query.filter(Sales.sale_date >= s_date)
    if e_date:
        query = query.filter(Sales.sale_date <= e_date)

    top_items = query.group_by(Product.id).order_by(func.sum(Sales.total_amount).desc()).limit(limit).all()

    return [
        TopProductItem(
            product_id=row.product_id,
            sku=row.sku,
            name=row.name,
            category=row.category,
            total_revenue=round(Decimal(str(row.total_revenue)), 2),
            total_units_sold=int(row.total_units_sold)
        )
        for row in top_items
    ]


@router.get("/product-performance/{product_id}", response_model=List[ProductPerformancePoint])
def get_product_performance(
    product_id: int,
    range_preset: Optional[str] = Query("all", alias="range"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Product Performance Timeline Endpoint.
    Strictly tenant-scoped: verifies product_id belongs to current_user.business_id (returns 404 if cross-business).
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id

    # Verify tenant ownership
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == b_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found in your store catalog."
        )

    s_date, e_date = resolve_date_bounds(db, b_id, range_preset, start_date, end_date)

    query = db.query(Sales).filter(
        Sales.business_id == b_id,
        Sales.product_id == product_id
    )

    if s_date:
        query = query.filter(Sales.sale_date >= s_date)
    if e_date:
        query = query.filter(Sales.sale_date <= e_date)

    history = query.order_by(Sales.sale_date.asc()).all()

    return [
        ProductPerformancePoint(
            sale_date=row.sale_date,
            units_sold=row.quantity,
            selling_price=row.selling_price,
            stock_available=row.stock_available,
            is_stockout=row.is_stockout
        )
        for row in history
    ]


@router.get("/data-quality", response_model=DataQualityReport)
def get_data_quality_report(
    range_preset: Optional[str] = Query("all", alias="range"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Data Quality Score Engine:
    Evaluates data completeness, date coverage continuity, and integrity anomalies.
    Stockouts are operational events and are NOT penalized in the Data Quality Score.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    b_id = current_user.business_id
    s_date, e_date = resolve_date_bounds(db, b_id, range_preset, start_date, end_date)

    query = db.query(Sales).filter(Sales.business_id == b_id)
    if s_date:
        query = query.filter(Sales.sale_date >= s_date)
    if e_date:
        query = query.filter(Sales.sale_date <= e_date)

    total_records = query.count()
    if total_records == 0:
        return DataQualityReport(
            quality_score=0.0,
            total_recorded_days=0,
            expected_days=0,
            date_coverage_ratio=0.0,
            date_gaps_count=0,
            anomalies_count=0,
            stockout_censored_ratio=0.0,
            status="No Data"
        )

    # Date coverage
    min_date = s_date or query.with_entities(func.min(Sales.sale_date)).scalar()
    max_date = e_date or query.with_entities(func.max(Sales.sale_date)).scalar()
    
    recorded_days = query.with_entities(func.count(func.distinct(Sales.sale_date))).scalar() or 0
    expected_days = (max_date - min_date).days + 1 if min_date and max_date else recorded_days

    coverage_ratio = min(1.0, max(0.0, float(recorded_days) / float(expected_days))) if expected_days > 0 else 1.0
    date_gaps = max(0, expected_days - recorded_days)

    # Data anomalies (negative values, missing required fields)
    anomalies_count = query.filter(Sales.quantity < 0).count()
    anomalies_ratio = float(anomalies_count) / float(total_records) if total_records > 0 else 0.0

    # Quality Score = DateCoverageRatio * 70% + (1 - AnomaliesRatio) * 30%
    score = round(min(100.0, max(0.0, (coverage_ratio * 70.0) + ((1.0 - anomalies_ratio) * 30.0))), 1)

    # Operational Stockout Ratio (Separate Business Indicator)
    confirmed_stockouts = query.filter(Sales.is_stockout == True).count()
    stockout_ratio = round(float(confirmed_stockouts) / float(total_records), 3) if total_records > 0 else 0.0

    status_str = "Excellent" if score >= 90.0 else ("Good" if score >= 75.0 else ("Warning" if score >= 50.0 else "Poor"))

    return DataQualityReport(
        quality_score=score,
        total_recorded_days=recorded_days,
        expected_days=expected_days,
        date_coverage_ratio=round(coverage_ratio, 3),
        date_gaps_count=date_gaps,
        anomalies_count=anomalies_count,
        stockout_censored_ratio=stockout_ratio,
        status=status_str
    )
