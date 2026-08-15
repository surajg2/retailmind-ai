from datetime import date, timedelta
from decimal import Decimal
from typing import Tuple
from fastapi import status
from sqlalchemy.orm import Session

from backend.app.models.models import Business, Product, Sales, User
from backend.app.services.csv_importer import validate_and_import_sales_csv

def create_user_helper(client, db, prefix: str) -> Tuple[User, str]:
    import random
    rand_id = random.randint(10000, 99999)
    email = f"{prefix}_{rand_id}@analytics.com"
    pwd = "Password123!"
    
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": f"{prefix} User",
        "business_name": f"{prefix} Store",
        "business_type": "Grocery"
    })
    
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login_resp.json()["access_token"]
    user = db.query(User).filter(User.email == email).first()
    return user, token


def test_cross_business_product_and_analytics_access(client, db):
    user_a, token_a = create_user_helper(client, db, "user_a")
    user_b, token_b = create_user_helper(client, db, "user_b")
    
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A creates a product
    p_resp = client.post("/api/v1/products", headers=headers_a, json={
        "sku": "SKU-ISOLATE-001",
        "name": "User A Item",
        "category": "Snacks",
        "unit": "pcs",
        "cost_price": "10.00",
        "selling_price": "15.00",
        "min_stock_level": 5
    })
    assert p_resp.status_code == status.HTTP_201_CREATED
    product_a_id = p_resp.json()["id"]

    # 2. User B attempts to access User A's product -> Returns 404 Not Found
    get_resp_b = client.get(f"/api/v1/products/{product_a_id}", headers=headers_b)
    assert get_resp_b.status_code == status.HTTP_404_NOT_FOUND

    # 3. User B attempts to update User A's product -> Returns 404 Not Found
    put_resp_b = client.put(f"/api/v1/products/{product_a_id}", headers=headers_b, json={"name": "Hacked Name"})
    assert put_resp_b.status_code == status.HTTP_404_NOT_FOUND

    # 4. User B attempts to access User A's product performance analytics -> Returns 404 Not Found
    perf_resp_b = client.get(f"/api/v1/analytics/product-performance/{product_a_id}", headers=headers_b)
    assert perf_resp_b.status_code == status.HTTP_404_NOT_FOUND


def test_product_deactivation_preserving_historical_sales(client, db):
    user, token = create_user_helper(client, db, "soft_delete")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload CSV data for product
    csv_data = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-01-01,SKU-DEACT-001,Deactivation Item,General,10,25.00,0,0,,100
2025-01-02,SKU-DEACT-001,Deactivation Item,General,15,25.00,0,0,,85
"""
    result = validate_and_import_sales_csv(db, user.business_id, csv_data)
    assert result.success is True

    product = db.query(Product).filter(Product.business_id == user.business_id, Product.sku == "SKU-DEACT-001").first()
    assert product is not None
    assert product.is_active is True

    # 2. Soft-deactivate product via DELETE endpoint
    del_resp = client.delete(f"/api/v1/products/{product.id}", headers=headers)
    assert del_resp.status_code == status.HTTP_200_OK
    assert del_resp.json()["is_active"] is False

    # 3. Verify Product disappears from active catalog by default
    cat_resp = client.get("/api/v1/products", headers=headers)
    active_skus = [p["sku"] for p in cat_resp.json()]
    assert "SKU-DEACT-001" not in active_skus

    # 4. Verify product appears when include_inactive=true
    all_cat_resp = client.get("/api/v1/products?include_inactive=true", headers=headers)
    all_skus = [p["sku"] for p in all_cat_resp.json()]
    assert "SKU-DEACT-001" in all_skus

    # 5. Verify historical Sales records remain 100% intact in database
    sales_count = db.query(Sales).filter(Sales.business_id == user.business_id, Sales.product_id == product.id).count()
    assert sales_count == 2


def test_confirmed_stockout_counting_and_eod_zero_inventory(client, db):
    user, token = create_user_helper(client, db, "stk_count")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload CSV with EOD stock 0 (is_stockout = None for CSV)
    csv_data = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-02-01,SKU-STK-CNT,Stk Item,Dairy,5,50.00,0,0,,0
2025-02-02,SKU-STK-CNT,Stk Item,Dairy,0,50.00,0,0,,0
"""
    validate_and_import_sales_csv(db, user.business_id, csv_data)

    # Manually mark 1 record as explicit confirmed stockout (is_stockout = True)
    sales = db.query(Sales).filter(Sales.business_id == user.business_id).all()
    sales[0].is_stockout = True
    sales[1].is_stockout = False # EOD stock 0 but is_stockout = False
    db.commit()

    summary_resp = client.get("/api/v1/analytics/summary?range=all", headers=headers)
    assert summary_resp.status_code == status.HTTP_200_OK
    summary = summary_resp.json()

    # Confirmed stockout count must strictly count is_stockout = TRUE (which is 1 day)
    assert summary["confirmed_stockout_days"] == 1
    # Zero EOD stock days must count stock_available = 0 (which is 2 days)
    assert summary["zero_eod_stock_days"] == 2


def test_missing_date_quality_calculation_and_all_range(client, db):
    user, token = create_user_helper(client, db, "dq_all")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload data covering 3 distinct days across a 10-day span (7 missing date gaps)
    csv_data = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-03-01,SKU-DQ-001,DQ Item,Snacks,10,20.00,0,0,,50
2025-03-05,SKU-DQ-001,DQ Item,Snacks,12,20.00,0,0,,40
2025-03-10,SKU-DQ-001,DQ Item,Snacks,15,20.00,0,0,,30
"""
    validate_and_import_sales_csv(db, user.business_id, csv_data)

    # 1. Test ALL date range bounds calculation
    summary_resp = client.get("/api/v1/analytics/summary?range=all", headers=headers)
    assert summary_resp.status_code == status.HTTP_200_OK
    summary = summary_resp.json()
    assert summary["start_date"] == "2025-03-01"
    assert summary["end_date"] == "2025-03-10"
    assert summary["total_revenue"] == "740.00" # (10+12+15) * 20 = 37 * 20 = 740.00
    assert summary["observed_units_sold"] == 37
    # Average revenue / recorded day = 740.00 / 3 recorded days = 246.67
    assert summary["avg_revenue_per_recorded_day"] == "246.67"

    # 2. Test Data Quality Report calculation
    dq_resp = client.get("/api/v1/analytics/data-quality?range=all", headers=headers)
    assert dq_resp.status_code == status.HTTP_200_OK
    dq = dq_resp.json()
    assert dq["total_recorded_days"] == 3
    assert dq["expected_days"] == 10
    assert dq["date_gaps_count"] == 7
    assert dq["date_coverage_ratio"] == 0.3 # 3 / 10 = 0.3
    # Score = 0.3 * 70 + (1 - 0) * 30 = 21 + 30 = 51.0
    assert dq["quality_score"] == 51.0


def test_dynamic_relative_date_preset_anchoring(client, db):
    # 1. Test Empty Database does not crash (returns None for date bounds, 0 for metrics)
    user_empty, token_empty = create_user_helper(client, db, "empty_preset")
    headers_empty = {"Authorization": f"Bearer {token_empty}"}

    summary_empty = client.get("/api/v1/analytics/summary?range=7d", headers=headers_empty)
    assert summary_empty.status_code == status.HTTP_200_OK
    assert Decimal(summary_empty.json()["total_revenue"]) == Decimal("0.00")
    assert summary_empty.json()["start_date"] is None
    assert summary_empty.json()["end_date"] is None

    # 2. Populate dataset with sale dates ending on 2026-08-14
    user, token = create_user_helper(client, db, "date_preset_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate sales ending on 2026-08-14 (from 2026-05-07 to 2026-08-14 = 100 days)
    # Plus an older record on 2025-08-15 (1 year boundary)
    csv_rows = ["date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available"]
    csv_rows.append("2025-08-15,SKU-RANGE-01,Range Item,Grocery,10,10.00,0,0,,50")
    
    start_d = date(2026, 5, 7)
    for i in range(100):
        d_str = (start_d + timedelta(days=i)).isoformat()
        csv_rows.append(f"{d_str},SKU-RANGE-01,Range Item,Grocery,5,10.00,0,0,,50")

    csv_data = "\n".join(csv_rows)
    val_res = validate_and_import_sales_csv(db, user.business_id, csv_data)
    assert val_res.success is True

    # MAX(sale_date) is 2026-08-14.
    # 7d:  2026-08-08 to 2026-08-14 (7 days * 5 pcs * 10.00 = 350.00 revenue)
    # 30d: 2026-07-16 to 2026-08-14 (30 days * 5 pcs * 10.00 = 1500.00 revenue)
    # 90d: 2026-05-17 to 2026-08-14 (90 days * 5 pcs * 10.00 = 4500.00 revenue)
    # 1y:  2025-08-15 to 2026-08-14 (100 days * 50 + 10 = 510 pcs -> 5100.00 revenue)
    # ALL: 2025-08-15 to 2026-08-14

    # Test 7D Preset
    s_7d = client.get("/api/v1/analytics/summary?range=7d", headers=headers).json()
    assert s_7d["start_date"] == "2026-08-08"
    assert s_7d["end_date"] == "2026-08-14"
    assert s_7d["observed_units_sold"] == 35 # 7 days * 5 pcs
    assert s_7d["total_revenue"] == "350.00"

    # Test 30D Preset
    s_30d = client.get("/api/v1/analytics/summary?range=30d", headers=headers).json()
    assert s_30d["start_date"] == "2026-07-16"
    assert s_30d["end_date"] == "2026-08-14"
    assert s_30d["observed_units_sold"] == 150 # 30 days * 5 pcs
    assert s_30d["total_revenue"] == "1500.00"

    # Test 90D Preset
    s_90d = client.get("/api/v1/analytics/summary?range=90d", headers=headers).json()
    assert s_90d["start_date"] == "2026-05-17"
    assert s_90d["end_date"] == "2026-08-14"
    assert s_90d["observed_units_sold"] == 450 # 90 days * 5 pcs
    assert s_90d["total_revenue"] == "4500.00"

    # Test 1Y Preset
    s_1y = client.get("/api/v1/analytics/summary?range=1y", headers=headers).json()
    assert s_1y["start_date"] == "2025-08-15"
    assert s_1y["end_date"] == "2026-08-14"
    assert s_1y["observed_units_sold"] == 510 # 100 days * 5 + 10 = 510 pcs
    assert s_1y["total_revenue"] == "5100.00"

    # Test ALL Preset
    s_all = client.get("/api/v1/analytics/summary?range=all", headers=headers).json()
    assert s_all["start_date"] == "2025-08-15"
    assert s_all["end_date"] == "2026-08-14"
    assert s_all["observed_units_sold"] == 510

    # Verify that all 5 analytics endpoints receive consistent range bounds
    t_7d = client.get("/api/v1/analytics/sales-trend?range=7d", headers=headers).json()
    assert len(t_7d) == 7

    cat_7d = client.get("/api/v1/analytics/category-breakdown?range=7d", headers=headers).json()
    assert len(cat_7d) == 1
    assert cat_7d[0]["units_sold"] == 35

    top_7d = client.get("/api/v1/analytics/top-products?range=7d", headers=headers).json()
    assert len(top_7d) == 1
    assert top_7d[0]["total_units_sold"] == 35

    dq_7d = client.get("/api/v1/analytics/data-quality?range=7d", headers=headers).json()
    assert dq_7d["total_recorded_days"] == 7

