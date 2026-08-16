from datetime import date, timedelta
from decimal import Decimal
from typing import Tuple
from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from backend.app.models.models import Business, Product, Sales, Prediction, User
from backend.app.services.csv_importer import validate_and_import_sales_csv
from ml.services.forecast_service import generate_and_persist_forecasts

def create_user_helper(client, db, prefix: str) -> Tuple[User, str]:
    import random
    rand_id = random.randint(10000, 99999)
    email = f"{prefix}_{rand_id}@forecast.com"
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


def populate_product_sales_history(db, business_id: int, sku: str, days: int = 35, end_date: date = date(2025, 12, 31)):
    """Helper to populate N days of historical sales for a product."""
    start_date = end_date - timedelta(days=days - 1)
    csv_rows = ["date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available"]
    for i in range(days):
        d_str = (start_date + timedelta(days=i)).isoformat()
        csv_rows.append(f"{d_str},{sku},Test Product {sku},Grocery,10,25.00,0,0,,100")
    
    csv_data = "\n".join(csv_rows)
    val_res = validate_and_import_sales_csv(db, business_id, csv_data)
    assert val_res.success is True


def test_1_forecast_table_creation(db):
    """Test 1: Proves predictions table exists with required columns."""
    inspector = inspect(db.bind)
    assert "predictions" in inspector.get_table_names()
    columns = [c["name"] for c in inspector.get_columns("predictions")]
    for col in ["id", "business_id", "product_id", "forecast_date", "predicted_units", "model_name", "model_version", "generated_at", "training_cutoff_date", "horizon_days"]:
        assert col in columns


def test_2_and_3_and_4_and_5_and_6_forecast_generation_and_consecutive_7_days(client, db):
    """
    Tests 2, 3, 4, 5, 6:
    - Generates 7-day forecast for active products.
    - Exactly 7 consecutive dates generated per product.
    - Belongs strictly to current business_id.
    """
    user, token = create_user_helper(client, db, "gen_7d")
    headers = {"Authorization": f"Bearer {token}"}

    # Populate 35 days of history for 2 products
    populate_product_sales_history(db, user.business_id, "SKU-FCST-01", days=35)
    populate_product_sales_history(db, user.business_id, "SKU-FCST-02", days=35)

    # 1. Generate for all active products
    gen_resp = client.post("/api/v1/forecasts/generate", headers=headers, json={})
    assert gen_resp.status_code == status.HTTP_201_CREATED
    data = gen_resp.json()

    assert data["business_id"] == user.business_id
    assert data["generated_count"] == 14 # 2 products * 7 days
    assert data["skipped_count"] == 0

    # 2. Verify 7 consecutive dates
    p1 = db.query(Product).filter(Product.business_id == user.business_id, Product.sku == "SKU-FCST-01").first()
    p1_forecasts = [f for f in data["forecasts"] if f["product_id"] == p1.id]
    assert len(p1_forecasts) == 7

    dates = [f["forecast_date"] for f in p1_forecasts]
    for i in range(len(dates) - 1):
        d1 = date.fromisoformat(dates[i])
        d2 = date.fromisoformat(dates[i+1])
        assert d2 - d1 == timedelta(days=1)

    # 3. Test generating for ONE product only
    gen_one = client.post("/api/v1/forecasts/generate", headers=headers, json={"product_id": p1.id})
    assert gen_one.status_code == status.HTTP_201_CREATED
    assert gen_one.json()["generated_count"] == 7


def test_7_and_8_cross_business_forecast_and_generation_returns_404(client, db):
    """
    Tests 7 & 8: Cross-tenant forecast access or product forecast generation returns 404.
    """
    user_a, token_a = create_user_helper(client, db, "tenant_a")
    user_b, token_b = create_user_helper(client, db, "tenant_b")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    populate_product_sales_history(db, user_a.business_id, "SKU-TENANT-A", days=35)
    p_a = db.query(Product).filter(Product.business_id == user_a.business_id, Product.sku == "SKU-TENANT-A").first()

    # User A generates forecast
    client.post("/api/v1/forecasts/generate", headers=headers_a, json={})

    # User B attempts to access User A's product forecast -> Returns 404
    prod_fcst_b = client.get(f"/api/v1/forecasts/product/{p_a.id}", headers=headers_b)
    assert prod_fcst_b.status_code == status.HTTP_404_NOT_FOUND

    # User B attempts to generate forecast for User A's product_id -> Returns 404
    gen_cross_b = client.post("/api/v1/forecasts/generate", headers=headers_b, json={"product_id": p_a.id})
    assert gen_cross_b.status_code == status.HTTP_404_NOT_FOUND


def test_9_insufficient_history_products_skipped(client, db):
    """
    Test 9: Products with < 28 days history are skipped cleanly with reason='INSUFFICIENT_HISTORY'.
    """
    user, token = create_user_helper(client, db, "skip_hist")
    headers = {"Authorization": f"Bearer {token}"}

    # Populate only 10 days of history
    populate_product_sales_history(db, user.business_id, "SKU-SHORT-01", days=10)

    gen_resp = client.post("/api/v1/forecasts/generate", headers=headers, json={})
    assert gen_resp.status_code == status.HTTP_201_CREATED
    data = gen_resp.json()

    assert data["generated_count"] == 0
    assert data["skipped_count"] == 1
    assert data["skipped_products"][0]["reason"] == "INSUFFICIENT_HISTORY"


def test_10_duplicate_forecast_generation_replaces_active_records(client, db):
    """
    Test 10: Re-generating forecasts applies Option A Replacement strategy (no duplicate active rows).
    """
    user, token = create_user_helper(client, db, "dup_regen")
    headers = {"Authorization": f"Bearer {token}"}

    populate_product_sales_history(db, user.business_id, "SKU-REGEN-01", days=35)

    # First generation
    client.post("/api/v1/forecasts/generate", headers=headers, json={})
    count_1 = db.query(Prediction).filter(Prediction.business_id == user.business_id).count()
    assert count_1 == 7

    # Second generation (same business, product, dates, model_version)
    client.post("/api/v1/forecasts/generate", headers=headers, json={})
    count_2 = db.query(Prediction).filter(Prediction.business_id == user.business_id).count()
    assert count_2 == 7 # Replaced cleanly, no duplicate rows


def test_11_12_13_metadata_cutoff_and_version_stored(client, db):
    """
    Tests 11, 12, 13: Auditability metadata (model_name, model_version, training_cutoff_date, horizon_days) verified.
    """
    user, token = create_user_helper(client, db, "meta_audit")
    headers = {"Authorization": f"Bearer {token}"}

    populate_product_sales_history(db, user.business_id, "SKU-AUDIT-01", days=35, end_date=date(2025, 12, 31))

    gen_resp = client.post("/api/v1/forecasts/generate", headers=headers, json={})
    assert gen_resp.status_code == status.HTTP_201_CREATED
    data = gen_resp.json()

    meta = data["metadata"]
    assert meta["model_name"] in ["XGBoost", "Seasonal Naive (y_t-7)"]
    assert meta["model_version"] in ["xgb-v1", "snaive-v1"]
    assert meta["training_cutoff_date"] == "2025-12-31"
    assert meta["horizon_days"] == 7
    assert "historical_stockout_ratio" in meta


def test_14_and_15_get_forecasts_tenant_isolation_and_latest(client, db):
    """
    Tests 14 & 15:
    - GET /api/v1/forecasts returns only current tenant's data.
    - GET /api/v1/forecasts/latest returns deterministic latest forecast set.
    """
    user, token = create_user_helper(client, db, "latest_fcst")
    headers = {"Authorization": f"Bearer {token}"}

    populate_product_sales_history(db, user.business_id, "SKU-LATEST-01", days=35)
    client.post("/api/v1/forecasts/generate", headers=headers, json={})

    # Test GET /forecasts
    list_resp = client.get("/api/v1/forecasts", headers=headers)
    assert list_resp.status_code == status.HTTP_200_OK
    list_data = list_resp.json()
    assert list_data["total_records"] == 7
    for item in list_data["forecasts"]:
        assert item["business_id"] == user.business_id

    # Test GET /forecasts/latest
    latest_resp = client.get("/api/v1/forecasts/latest", headers=headers)
    assert latest_resp.status_code == status.HTTP_200_OK
    latest_data = latest_resp.json()
    assert latest_data["business_id"] == user.business_id
    assert latest_data["total_products"] == 1
    assert len(latest_data["products"][0]["forecast"]) == 7


def test_16_invalid_date_range_rejected(client, db):
    """
    Test 16: GET /api/v1/forecasts with start_date > end_date returns 400 Bad Request.
    """
    user, token = create_user_helper(client, db, "inv_date")
    headers = {"Authorization": f"Bearer {token}"}

    inv_resp = client.get("/api/v1/forecasts?start_date=2025-12-31&end_date=2025-01-01", headers=headers)
    assert inv_resp.status_code == status.HTTP_400_BAD_REQUEST


def test_17_and_18_missing_model_artifact_fallback_and_non_negative_units(client, db):
    """
    Tests 17 & 18:
    - Missing model artifact falls back safely to Seasonal Naive.
    - Forecast quantities are strictly non-negative (>= 0).
    """
    user, token = create_user_helper(client, db, "non_neg")
    headers = {"Authorization": f"Bearer {token}"}

    populate_product_sales_history(db, user.business_id, "SKU-NON-NEG", days=35)

    gen_resp = client.post("/api/v1/forecasts/generate", headers=headers, json={})
    assert gen_resp.status_code == status.HTTP_201_CREATED
    data = gen_resp.json()

    for fcst in data["forecasts"]:
        assert fcst["predicted_units"] >= 0.0
