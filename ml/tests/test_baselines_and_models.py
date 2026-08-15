import pandas as pd
import numpy as np
from datetime import date, timedelta
import pytest

from ml.baselines.naive import predict_naive, predict_seasonal_naive
from ml.evaluation.metrics import calculate_mae, calculate_rmse, calculate_mape
from ml.models.xgboost_model import DemandXGBoostModel
from ml.features.demand_features import build_demand_features, FEATURE_COLUMNS, TARGET_COLUMN


def test_6_naive_baseline_calculation():
    """
    Test 6: Proves Naive baseline predicts y(t-1) using lag_1.
    """
    df = pd.DataFrame({
        "lag_1": [10.0, 20.0, 30.0],
        "units_sold": [15.0, 25.0, 35.0]
    })
    preds = predict_naive(df)
    np.testing.assert_array_equal(preds, np.array([10.0, 20.0, 30.0]))


def test_7_seasonal_naive_baseline_calculation():
    """
    Test 7: Proves Seasonal Naive baseline predicts y(t-7) using lag_7.
    """
    df = pd.DataFrame({
        "lag_7": [14.0, 24.0, 34.0],
        "units_sold": [15.0, 25.0, 35.0]
    })
    preds = predict_seasonal_naive(df)
    np.testing.assert_array_equal(preds, np.array([14.0, 24.0, 34.0]))


def test_8_mae_calculation_correctness():
    """
    Test 8: Proves MAE calculation is mathematically exact.
    """
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0]) # errors: |2|, |2|, |3| -> mean = 7/3 = 2.3333...
    mae = calculate_mae(y_true, y_pred)
    assert pytest.approx(mae, 0.001) == 2.333333


def test_9_rmse_calculation_correctness():
    """
    Test 9: Proves RMSE calculation is mathematically exact.
    """
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([10.0, 20.0, 36.0]) # errors sq: 0, 0, 36 -> mean sq = 12 -> sqrt = 3.4641
    rmse = calculate_rmse(y_true, y_pred)
    assert pytest.approx(rmse, 0.001) == 3.4641016


def test_10_xgboost_receives_only_permitted_historical_features():
    """
    Test 10: Proves XGBoost model trains and predicts strictly using FEATURE_COLUMNS.
    """
    start_date = date(2025, 1, 1)
    records = []
    for i in range(40):
        d = start_date + timedelta(days=i)
        records.append({
            "business_id": 1,
            "product_id": 101,
            "sale_date": d,
            "units_sold": 10 + (i % 5),
            "selling_price": 50.0,
            "stock_available": 100
        })
    df_raw = pd.DataFrame(records)
    df_feat, feat_cols, target_col = build_demand_features(df_raw)

    xgb = DemandXGBoostModel(n_estimators=10, max_depth=2)
    xgb.fit(df_feat, df_feat[target_col])

    # Ensure model feature names match FEATURE_COLUMNS
    assert list(xgb.feature_columns) == list(FEATURE_COLUMNS)

    preds = xgb.predict(df_feat)
    assert len(preds) == len(df_feat)
    assert (preds >= 0).all() # Predictions clipped at 0
