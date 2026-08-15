import os
import datetime
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.session import SessionLocal
from backend.app.models.models import Sales, Product, Business
from ml.features.demand_features import build_demand_features, FEATURE_COLUMNS, TARGET_COLUMN
from ml.baselines.naive import predict_naive, predict_seasonal_naive
from ml.models.xgboost_model import DemandXGBoostModel
from ml.evaluation.metrics import calculate_mae, calculate_rmse, evaluate_models


def load_business_sales_dataframe(db: Session, business_id: int) -> pd.DataFrame:
    """
    Loads historical sales and product data for a specific business_id from PostgreSQL.
    Strictly tenant-scoped.
    """
    query = db.query(
        Sales.sale_date,
        Sales.business_id,
        Sales.product_id,
        Sales.quantity.label("units_sold"),
        Sales.selling_price,
        Sales.promotion,
        Sales.holiday,
        Sales.festival,
        Sales.stock_available,
        Sales.is_stockout,
        Product.category,
        Product.sku,
        Product.name.label("product_name")
    ).join(Product, Product.id == Sales.product_id).filter(
        Sales.business_id == business_id
    ).order_by(Sales.sale_date.asc())

    records = [dict(row._mapping) for row in query.all()]
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    return df


def split_chronologically(
    df: pd.DataFrame, train_ratio: float = 0.70, val_ratio: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits feature DataFrame chronologically per unique date into 70% Train, 15% Validation, 15% Test.
    Ensures Train dates < Validation dates < Test dates.
    """
    unique_dates = sorted(df["sale_date"].unique())
    n_dates = len(unique_dates)

    if n_dates < 5:
        # Too few dates to split effectively
        return df, pd.DataFrame(), pd.DataFrame()

    n_train = int(n_dates * train_ratio)
    n_val = int(n_dates * val_ratio)

    train_dates = set(unique_dates[:n_train])
    val_dates = set(unique_dates[n_train:n_train + n_val])
    test_dates = set(unique_dates[n_train + n_val:])

    train_df = df[df["sale_date"].isin(train_dates)].reset_index(drop=True)
    val_df = df[df["sale_date"].isin(val_dates)].reset_index(drop=True)
    test_df = df[df["sale_date"].isin(test_dates)].reset_index(drop=True)

    return train_df, val_df, test_df


def run_training_pipeline(db: Session, business_id: Optional[int] = None) -> dict:
    """
    Runs full ML demand forecasting pipeline:
    1. Loads PostgreSQL sales data for authenticated business.
    2. Builds leakage-safe features.
    3. Chronologically splits data (70% Train, 15% Val, 15% Test).
    4. Evaluates Naive & Seasonal Naive baselines on TEST set.
    5. Trains XGBoost and evaluates on TEST set.
    6. Verifies Model Acceptance Rule (XGBoost must beat best baseline).
    7. Saves model binary and metadata JSON artifact.
    """
    if business_id is None:
        # Pick business with the most sales records
        b_id = db.query(Sales.business_id, func.count(Sales.id)).group_by(Sales.business_id).order_by(func.count(Sales.id).desc()).first()
        if not b_id:
            print("No sales data found in database for any business.")
            return {}
        business_id = b_id[0]

    b_obj = db.query(Business).filter(Business.id == business_id).first()
    business_name = b_obj.name if b_obj else f"Business {business_id}"

    print(f"==================================================")
    print(f"RUNNING DEMAND FORECASTING PIPELINE FOR: {business_name} (ID: {business_id})")
    print(f"==================================================")

    # 1. Load Data
    raw_df = load_business_sales_dataframe(db, business_id)
    if raw_df.empty:
        print(f"No historical sales records found for business_id {business_id}.")
        return {}

    total_raw_rows = len(raw_df)
    min_sale_date = raw_df["sale_date"].min()
    max_sale_date = raw_df["sale_date"].max()
    num_products = raw_df["product_id"].nunique()

    # Stockout statistics
    if "is_stockout" in raw_df.columns:
        confirmed_stockouts = (raw_df["is_stockout"] == True).sum()
    else:
        confirmed_stockouts = (raw_df["stock_available"] == 0).sum()
    
    stockout_percentage = round((float(confirmed_stockouts) / float(total_raw_rows)) * 100.0, 2)

    print(f"Raw Dataset Info:")
    print(f"  - Products: {num_products}")
    print(f"  - Date Range: {min_sale_date} to {max_sale_date}")
    print(f"  - Total Historical Records: {total_raw_rows}")
    print(f"  - Confirmed Stockout Records: {confirmed_stockouts} ({stockout_percentage}% of target observations)")

    # 2. Build Leakage-Safe Features
    df_features, feat_cols, target_col = build_demand_features(raw_df)
    total_usable_rows = len(df_features)

    print(f"Usable Features Dataset Info (after 28-day lag history drop):")
    print(f"  - Usable Feature Rows: {total_usable_rows}")
    print(f"  - Feature Count: {len(feat_cols)}")

    # 3. Chronological Split (70% Train, 15% Val, 15% Test)
    train_df, val_df, test_df = split_chronologically(df_features, train_ratio=0.70, val_ratio=0.15)

    if test_df.empty or train_df.empty:
        print("Insufficient history to perform chronological split.")
        return {}

    train_dates_range = f"{train_df['sale_date'].min().strftime('%Y-%m-%d')} to {train_df['sale_date'].max().strftime('%Y-%m-%d')}"
    val_dates_range = f"{val_df['sale_date'].min().strftime('%Y-%m-%d')} to {val_df['sale_date'].max().strftime('%Y-%m-%d')}" if not val_df.empty else "N/A"
    test_dates_range = f"{test_df['sale_date'].min().strftime('%Y-%m-%d')} to {test_df['sale_date'].max().strftime('%Y-%m-%d')}"

    print(f"\nChronological Dataset Splits:")
    print(f"  - Train Set:      {len(train_df)} rows ({train_dates_range})")
    print(f"  - Validation Set: {len(val_df)} rows ({val_dates_range})")
    print(f"  - Test Set:       {len(test_df)} rows ({test_dates_range})")

    # 4. Evaluate Baselines on Held-Out TEST Set
    y_test = test_df[TARGET_COLUMN].values
    
    pred_naive = predict_naive(test_df)
    pred_snaive = predict_seasonal_naive(test_df)

    mae_naive = calculate_mae(y_test, pred_naive)
    rmse_naive = calculate_rmse(y_test, pred_naive)

    mae_snaive = calculate_mae(y_test, pred_snaive)
    rmse_snaive = calculate_rmse(y_test, pred_snaive)

    # 5. Train XGBoost Model
    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN]
    X_val, y_val = (val_df[FEATURE_COLUMNS], val_df[TARGET_COLUMN]) if not val_df.empty else (None, None)

    xgb_model = DemandXGBoostModel()
    xgb_model.fit(X_train, y_train, X_val, y_val)

    pred_xgb = xgb_model.predict(test_df)
    mae_xgb = calculate_mae(y_test, pred_xgb)
    rmse_xgb = calculate_rmse(y_test, pred_xgb)

    # 6. Evaluation Framework Comparison
    predictions_map = {
        "Naive (y_t-1)": pred_naive,
        "Seasonal Naive (y_t-7)": pred_snaive,
        "XGBoost Regressor": pred_xgb
    }
    eval_df = evaluate_models(y_test, predictions_map)

    print(f"\n==================================================")
    print(f"HELD-OUT TEST SET EVALUATION RESULTS:")
    print(f"==================================================")
    print(eval_df.to_string(index=False))

    # 7. Model Acceptance Rule
    best_baseline_mae = min(mae_naive, mae_snaive)
    xgb_beats_baseline = mae_xgb < best_baseline_mae

    if xgb_beats_baseline:
        status_msg = f"SUCCESS: XGBoost outperformed the baseline (MAE {mae_xgb:.2f} vs Best Baseline MAE {best_baseline_mae:.2f})."
        preferred_model = "XGBoost Regressor"
    else:
        status_msg = "XGBoost did not outperform the baseline."
        preferred_model = "Seasonal Naive (y_t-7)" if mae_snaive <= mae_naive else "Naive (y_t-1)"

    print(f"\nModel Acceptance Status: {status_msg}")

    # 8. Save Model Artifact & Metadata JSON
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    model_path = os.path.join(artifacts_dir, "xgboost_demand_model.joblib")

    metadata = {
        "model_name": "RetailMind_Demand_XGBoost",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "business_id": business_id,
        "business_name": business_name,
        "features": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
        "training_period": train_dates_range,
        "validation_period": val_dates_range,
        "test_period": test_dates_range,
        "raw_record_count": total_raw_rows,
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "confirmed_stockout_count": int(confirmed_stockouts),
        "stockout_percentage": stockout_percentage,
        "test_metrics": {
            "Naive": {"MAE": round(mae_naive, 2), "RMSE": round(rmse_naive, 2)},
            "Seasonal_Naive": {"MAE": round(mae_snaive, 2), "RMSE": round(rmse_snaive, 2)},
            "XGBoost": {"MAE": round(mae_xgb, 2), "RMSE": round(rmse_xgb, 2)}
        },
        "xgb_beats_baseline": xgb_beats_baseline,
        "preferred_model": preferred_model,
        "acceptance_status": status_msg
    }

    xgb_model.save(model_path, metadata)
    print(f"Saved model artifact at: {model_path}")

    return {
        "business_id": business_id,
        "business_name": business_name,
        "num_products": num_products,
        "min_sale_date": str(min_sale_date),
        "max_sale_date": str(max_sale_date),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "confirmed_stockouts": int(confirmed_stockouts),
        "stockout_percentage": stockout_percentage,
        "mae_naive": mae_naive,
        "rmse_naive": rmse_naive,
        "mae_snaive": mae_snaive,
        "rmse_snaive": rmse_snaive,
        "mae_xgb": mae_xgb,
        "rmse_xgb": rmse_xgb,
        "xgb_beats_baseline": xgb_beats_baseline,
        "status_message": status_msg,
        "eval_df": eval_df
    }


if __name__ == "__main__":
    db = SessionLocal()
    try:
        run_training_pipeline(db)
    finally:
        db.close()
