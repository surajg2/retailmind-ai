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
