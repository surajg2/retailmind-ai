import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.models.models import User, Business, Product, Sales, Prediction
from backend.app.core.security import create_access_token
from ml.services.forecast_evaluation_service import evaluate_forecasts, evaluate_forecast_trend
from ml.services.model_monitoring import monitor_model_performance
from ml.services.anomaly_service import detect_sales_anomalies

client = TestClient(app)

import uuid

@pytest.fixture
def test_setup(client: TestClient, db: Session):
    uid = uuid.uuid4().hex[:8]
    email1 = f"t1_{uid}@test.com"
    email2 = f"t2_{uid}@test.com"
    pwd = "Password123!"

    client.post("/api/v1/auth/register", json={
        "email": email1,
        "password": pwd,
        "full_name": "Tenant 1 User",
        "business_name": f"Tenant 1 Store {uid}"
    })
    token1 = client.post("/api/v1/auth/login", json={"email": email1, "password": pwd}).json()["access_token"]

    client.post("/api/v1/auth/register", json={
        "email": email2,
        "password": pwd,
        "full_name": "Tenant 2 User",
        "business_name": f"Tenant 2 Store {uid}"
    })
    token2 = client.post("/api/v1/auth/login", json={"email": email2, "password": pwd}).json()["access_token"]

    u1 = db.query(User).filter(User.email == email1).first()
    u2 = db.query(User).filter(User.email == email2).first()

    b1_id = u1.business_id
    b2_id = u2.business_id

    p1 = Product(business_id=b1_id, sku=f"P1-{uid}", name="Product 1 Tenant 1", selling_price=100.0, cost_price=60.0)
    p2 = Product(business_id=b2_id, sku=f"P2-{uid}", name="Product 1 Tenant 2", selling_price=200.0, cost_price=120.0)
    db.add_all([p1, p2])
    db.commit()

    return {
        "b1": u1.business, "b2": u2.business,
        "u1": u1, "u2": u2,
        "p1": p1, "p2": p2,
        "headers1": {"Authorization": f"Bearer {token1}"},
        "headers2": {"Authorization": f"Bearer {token2}"}
    }


def test_forecast_evaluation_mae_rmse_mape_correctness(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id

    base_date = date(2026, 1, 1)
    # Seed 5 days of actual sales and predictions
    # Day 1: actual=10, pred=12 (abs_err=2, sq_err=4, pct_err=0.2)
    # Day 2: actual=20, pred=15 (abs_err=5, sq_err=25, pct_err=0.25)
    # Day 3: actual=30, pred=30 (abs_err=0, sq_err=0, pct_err=0.0)
    # Day 4: actual=40, pred=36 (abs_err=4, sq_err=16, pct_err=0.1)
    # Day 5: actual=50, pred=55 (abs_err=5, sq_err=25, pct_err=0.1)
    actuals = [10, 20, 30, 40, 50]
    preds = [12, 15, 30, 36, 55]

    for idx in range(5):
        dt = base_date + timedelta(days=idx)
        db.add(Sales(
            business_id=b1_id, product_id=p1_id, sale_date=dt,
            quantity=actuals[idx], selling_price=100.0, stock_available=50, is_stockout=False
        ))
        db.add(Prediction(
            business_id=b1_id, product_id=p1_id, forecast_date=dt,
            predicted_units=preds[idx], model_name="XGBoost", model_version="xgb-v1",
            training_cutoff_date=base_date
        ))
    db.commit()

    summary = evaluate_forecasts(db, business_id=b1_id)
    
    # Expected MAE = (2 + 5 + 0 + 4 + 5) / 5 = 16 / 5 = 3.2
    # Expected RMSE = sqrt((4 + 25 + 0 + 16 + 25) / 5) = sqrt(70 / 5) = sqrt(14) = 3.74
    # Expected MAPE = (0.2 + 0.25 + 0.0 + 0.1 + 0.1) / 5 * 100 = 0.65 / 5 * 100 = 13.0%
    assert summary.status == "EVALUATED"
    assert summary.evaluated_count == 5
    assert summary.mae == 3.2
    assert summary.rmse == 3.74
    assert summary.mape == 13.0


def test_forecast_evaluation_zero_sales_mape_safe(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id
    dt = date(2026, 2, 1)

    # Actual = 0 (zero sales date), Prediction = 5
    db.add(Sales(
        business_id=b1_id, product_id=p1_id, sale_date=dt,
        quantity=0, selling_price=100.0, stock_available=0, is_stockout=False
    ))
    db.add(Prediction(
        business_id=b1_id, product_id=p1_id, forecast_date=dt,
        predicted_units=5.0, model_name="XGBoost", model_version="xgb-v1",
        training_cutoff_date=dt - timedelta(days=7)
    ))
    db.commit()

    summary = evaluate_forecasts(db, business_id=b1_id)
    assert summary.evaluated_count == 1
    assert summary.mae == 5.0
    assert summary.mape is None # Zero observed sales excluded from MAPE, no crash!


def test_forecast_evaluation_insufficient_data(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id

    # Seed future prediction without matching historical sales
    future_dt = date(2030, 1, 1)
    db.add(Prediction(
        business_id=b1_id, product_id=p1_id, forecast_date=future_dt,
        predicted_units=20.0, model_name="XGBoost", model_version="xgb-v1",
        training_cutoff_date=date(2025, 12, 31)
    ))
    db.commit()

    summary = evaluate_forecasts(db, business_id=b1_id)
    assert summary.status == "INSUFFICIENT_EVALUATION_DATA"
    assert summary.evaluated_count == 0
    assert summary.mae is None
    assert summary.rmse is None
    assert summary.mape is None


def test_forecast_evaluation_stockout_and_zero_eod_distinction(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id

    dt1 = date(2026, 3, 1)
    dt2 = date(2026, 3, 2)

    # dt1: Confirmed stockout (is_stockout = True)
    db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=dt1, quantity=15, selling_price=100.0, stock_available=0, is_stockout=True))
    db.add(Prediction(business_id=b1_id, product_id=p1_id, forecast_date=dt1, predicted_units=18.0, training_cutoff_date=dt1))

    # dt2: Zero EOD stock only (is_stockout = False, stock_available = 0)
    db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=dt2, quantity=20, selling_price=100.0, stock_available=0, is_stockout=False))
    db.add(Prediction(business_id=b1_id, product_id=p1_id, forecast_date=dt2, predicted_units=22.0, training_cutoff_date=dt2))
    db.commit()

    summary = evaluate_forecasts(db, business_id=b1_id)
    assert summary.confirmed_stockout_count == 1
    assert summary.zero_eod_stock_count == 2


def test_model_monitoring_stable_watch_degraded(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id

    # Seed 14 evaluated dates: first 7 dates MAE = 10, recent 7 dates MAE = 10 -> ratio = 1.0 (STABLE)
    start_d = date(2026, 4, 1)
    for i in range(14):
        dt = start_d + timedelta(days=i)
        db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=dt, quantity=50, selling_price=100.0, stock_available=50))
        db.add(Prediction(business_id=b1_id, product_id=p1_id, forecast_date=dt, predicted_units=40.0, training_cutoff_date=start_d))
    db.commit()

    mon = monitor_model_performance(db, business_id=b1_id)
    assert mon.status == "STABLE"
    assert mon.degradation_ratio == 1.0


def test_model_monitoring_historical_mae_zero_edge_case(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id

    start_d = date(2026, 5, 1)
    # 7 historical dates with 0 error
    for i in range(7):
        dt = start_d + timedelta(days=i)
        db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=dt, quantity=30, selling_price=100.0, stock_available=50))
        db.add(Prediction(business_id=b1_id, product_id=p1_id, forecast_date=dt, predicted_units=30.0, training_cutoff_date=start_d))

    # 7 recent dates with non-zero error (actual=30, pred=40 -> error=10)
    for i in range(7, 14):
        dt = start_d + timedelta(days=i)
        db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=dt, quantity=30, selling_price=100.0, stock_available=50))
        db.add(Prediction(business_id=b1_id, product_id=p1_id, forecast_date=dt, predicted_units=40.0, training_cutoff_date=start_d))

    db.commit()

    mon = monitor_model_performance(db, business_id=b1_id)
    assert mon.status == "DEGRADED"


def test_anomaly_detection_high_sales_and_stockout_exclusion(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id

    start_d = date(2026, 6, 1)
    # Seed 20 baseline days of 10 units
    for i in range(20):
        dt = start_d + timedelta(days=i)
        db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=dt, quantity=10, selling_price=100.0, stock_available=50))

    # Day 21: High sales spike = 100 units
    spike_dt = start_d + timedelta(days=20)
    db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=spike_dt, quantity=100, selling_price=100.0, stock_available=50))

    # Day 22: Confirmed stockout day with 0 units sold (MUST NOT be classified as LOW_SALES demand drop)
    stockout_dt = start_d + timedelta(days=21)
    db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=stockout_dt, quantity=0, selling_price=100.0, stock_available=0, is_stockout=True))

    db.commit()

    anomalies_res = detect_sales_anomalies(db, business_id=b1_id)
    anom_list = anomalies_res.anomalies

    # High sales spike should be detected
    spike_anom = [a for a in anom_list if a.date == spike_dt]
    assert len(spike_anom) == 1
    assert spike_anom[0].anomaly_type == "HIGH_SALES"

    # Confirmed stockout day should NOT be emitted as LOW_SALES
    stockout_anom = [a for a in anom_list if a.date == stockout_dt]
    assert len(stockout_anom) == 0


def test_anomaly_detection_price_change(db: Session, test_setup):
    b1_id = test_setup["b1"].id
    p1_id = test_setup["p1"].id

    start_d = date(2026, 7, 1)
    # 10 days at 100.0 price
    for i in range(10):
        dt = start_d + timedelta(days=i)
        db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=dt, quantity=10, selling_price=100.0, stock_available=50))

    # Day 11: Price change to 130.0 (+30%)
    p_change_dt = start_d + timedelta(days=10)
    db.add(Sales(business_id=b1_id, product_id=p1_id, sale_date=p_change_dt, quantity=10, selling_price=130.0, stock_available=50))
    db.commit()

    anomalies_res = detect_sales_anomalies(db, business_id=b1_id)
    price_anom = [a for a in anomalies_res.anomalies if a.anomaly_type == "PRICE_CHANGE"]

    assert len(price_anom) >= 1
    assert price_anom[0].previous_price == 100.0
    assert price_anom[0].selling_price == 130.0
    assert price_anom[0].price_change_percentage == 30.0


def test_api_tenant_isolation_forecast_evaluation_and_anomalies(db: Session, test_setup):
    # Verify Tenant 1 cannot view Tenant 2's evaluation or anomalies
    res1 = client.get("/api/v1/forecast-evaluation/summary", headers=test_setup["headers1"])
    assert res1.status_code == 200
    assert res1.json()["business_id"] == test_setup["b1"].id

    res2 = client.get("/api/v1/forecast-evaluation/summary", headers=test_setup["headers2"])
    assert res2.status_code == 200
    assert res2.json()["business_id"] == test_setup["b2"].id

    # Verify cross-tenant product evaluation returns 404
    cross_res = client.get(f"/api/v1/forecast-evaluation/product/{test_setup['p2'].id}", headers=test_setup["headers1"])
    assert cross_res.status_code == 404
