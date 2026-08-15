import pandas as pd
import numpy as np
from datetime import date, timedelta
import pytest

from backend.app.db.session import SessionLocal
from ml.features.demand_features import build_demand_features, FEATURE_COLUMNS, TARGET_COLUMN
from ml.pipelines.train import split_chronologically, load_business_sales_dataframe

def test_1_lag_features_do_not_contain_future_information():
    """
    Test 1: Proves lag_1, lag_7, lag_14, lag_28 use strictly historical observations t-h.
    """
    start_date = date(2025, 1, 1)
    records = []
    for i in range(40):
        d = start_date + timedelta(days=i)
        records.append({
            "business_id": 1,
            "product_id": 101,
            "sale_date": d,
            "units_sold": (i + 1) * 10, # 10, 20, 30, ...
            "selling_price": 50.0,
            "stock_available": 100
        })
    df_raw = pd.DataFrame(records)
    df_feat, _, _ = build_demand_features(df_raw)

    # For day index i (say day 30, units_sold = 310):
    # lag_1 for day 30 must equal units_sold of day 29 (300)
    # lag_7 for day 30 must equal units_sold of day 23 (240)
    row_30 = df_feat[df_feat["sale_date"] == "2025-01-31"].iloc[0]
    row_29 = df_raw[df_raw["sale_date"] == date(2025, 1, 30)].iloc[0]
    row_24 = df_raw[df_raw["sale_date"] == date(2025, 1, 24)].iloc[0]

    assert row_30["lag_1"] == row_29["units_sold"]
    assert row_30["lag_7"] == row_24["units_sold"]


def test_2_rolling_features_exclude_target_day_value():
    """
    Test 2: Proves rolling_mean_7 excludes target day t's value.
    If target day t has a huge anomaly (e.g., 9999), rolling_mean_7 on target day t must NOT reflect 9999.
    """
    start_date = date(2025, 1, 1)
    records = []
    for i in range(35):
        d = start_date + timedelta(days=i)
        val = 9999 if i == 34 else 10 # Anomaly on target day
        records.append({
            "business_id": 1,
            "product_id": 101,
            "sale_date": d,
            "units_sold": val,
            "selling_price": 50.0,
            "stock_available": 100
        })
    df_raw = pd.DataFrame(records)
    df_feat, _, _ = build_demand_features(df_raw)

    target_day_row = df_feat[df_feat["sale_date"] == "2025-02-04"].iloc[0]
    # rolling_mean_7 on 2025-02-04 must be average of previous 7 days (all 10s) = 10.0, NOT including 9999
    assert target_day_row["rolling_mean_7"] == 10.0


def test_3_and_4_train_val_test_dates_are_strictly_chronological():
    """
    Test 3 & 4: Proves Train dates < Validation dates < Test dates.
    """
    start_date = date(2025, 1, 1)
    records = []
    for i in range(100):
        d = start_date + timedelta(days=i)
        records.append({
            "business_id": 1,
            "product_id": 101,
            "sale_date": d,
            "units_sold": 15,
            "selling_price": 50.0,
            "stock_available": 100
        })
    df_raw = pd.DataFrame(records)
    df_feat, _, _ = build_demand_features(df_raw)

    train_df, val_df, test_df = split_chronologically(df_feat, train_ratio=0.70, val_ratio=0.15)

    max_train_date = train_df["sale_date"].max()
    min_val_date = val_df["sale_date"].min()
    max_val_date = val_df["sale_date"].max()
    min_test_date = test_df["sale_date"].min()

    assert max_train_date < min_val_date
    assert max_val_date < min_test_date


def test_5_no_cross_business_training_data_leakage():
    """
    Test 5: Proves tenant isolation — load_business_sales_dataframe returns ONLY business's records.
    """
    db = SessionLocal()
    try:
        b1_df = load_business_sales_dataframe(db, business_id=1)
        if not b1_df.empty:
            assert (b1_df["business_id"] == 1).all()
    finally:
        db.close()


def test_11_stockout_observations_explicitly_identified():
    """
    Test 11: Proves stockout observations (is_stockout = True or stock_available = 0) are correctly flagged.
    """
    start_date = date(2025, 1, 1)
    records = [
        {
            "business_id": 1,
            "product_id": 101,
            "sale_date": start_date + timedelta(days=i),
            "units_sold": 10,
            "selling_price": 20.0,
            "stock_available": 0 if i == 30 else 50,
            "is_stockout": True if i == 30 else False
        }
        for i in range(35)
    ]
    df_raw = pd.DataFrame(records)
    df_feat, _, _ = build_demand_features(df_raw)

    stockout_row = df_feat[df_feat["sale_date"] == "2025-01-31"].iloc[0]
    assert stockout_row["is_stockout_feature"] == 1


def test_12_empty_or_insufficient_history_handled_without_crashing():
    """
    Test 12: Proves empty DataFrame or < 28 days history returns empty without raising exceptions.
    """
    empty_df = pd.DataFrame()
    df_feat, feat_cols, target_col = build_demand_features(empty_df)
    assert df_feat.empty
    assert target_col == TARGET_COLUMN

    # Insufficient history (< 28 days)
    start_date = date(2025, 1, 1)
    short_records = [
        {
            "business_id": 1,
            "product_id": 101,
            "sale_date": start_date + timedelta(days=i),
            "units_sold": 10,
            "selling_price": 20.0,
            "stock_available": 50
        }
        for i in range(15)
    ]
    df_short_feat, _, _ = build_demand_features(pd.DataFrame(short_records))
    assert df_short_feat.empty # 15 days is insufficient to compute lag_28 / rolling_mean_28, correctly dropped


def test_13_synthetic_dataset_passes_through_feature_pipeline():
    """
    Test 13: Proves synthetic dataset passes through feature pipeline successfully.
    """
    from data.generate_synthetic_data import generate_dataset
    from pathlib import Path
    
    out_file = Path(__file__).resolve().parent / "temp_synth.csv"
    generate_dataset(out_file)
    
    df_synth = pd.read_csv(out_file, comment="#")
    # Clean up file
    if out_file.exists():
        out_file.unlink()

    df_feat, feat_cols, target_col = build_demand_features(df_synth)
    assert not df_feat.empty
    assert target_col in df_feat.columns
    for c in FEATURE_COLUMNS:
        assert c in df_feat.columns
