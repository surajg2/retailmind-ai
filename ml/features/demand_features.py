import pandas as pd
import numpy as np
from typing import List, Tuple

TARGET_COLUMN = "observed_units_sold"

FEATURE_COLUMNS = [
    "day_of_week",
    "day_of_month",
    "month",
    "week_of_year",
    "is_weekend",
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_28",
    "rolling_std_7",
    "rolling_std_14",
    "rolling_std_28",
    "selling_price",
    "promotion",
    "holiday",
    "has_festival",
    "stock_available",
    "is_stockout_feature",
    "category_code",
    "product_id_code"
]


def build_demand_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], str]:
    """
    Leakage-safe Feature Engineering Pipeline for RetailMind AI Demand Forecasting.
    
    Rules enforced:
    1. Chronological sorting by (business_id, product_id, sale_date).
    2. Target definition: y = observed_units_sold.
    3. Lags (lag_1, lag_7, lag_14, lag_28) use strictly historical observations t-h.
    4. Rolling features (mean/std 7, 14, 28) shift by 1 FIRST before applying rolling window
       to guarantee the target day t observation is NEVER included.
    5. No forward-filling of target values or future-information leakage.
    6. Drops rows where lag history does not exist (e.g., initial 28 days per product).
    """
    if df.empty:
        empty_df = pd.DataFrame(columns=["sale_date", "business_id", "product_id"] + FEATURE_COLUMNS + [TARGET_COLUMN])
        return empty_df, FEATURE_COLUMNS, TARGET_COLUMN

    df = df.copy()

    # Column name normalization aliases
    if "date" in df.columns and "sale_date" not in df.columns:
        df["sale_date"] = df["date"]

    if "quantity" in df.columns and "units_sold" not in df.columns:
        df["units_sold"] = df["quantity"]

    if "sku" in df.columns and "product_id" not in df.columns:
        df["product_id"] = df["sku"]

    if "business_id" not in df.columns:
        df["business_id"] = 1

    # Ensure sale_date is datetime type and sort chronologically
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values(by=["business_id", "product_id", "sale_date"]).reset_index(drop=True)

    # Set Target Column
    df[TARGET_COLUMN] = df["units_sold"].astype(float)

    # 1. Calendar Features
    df["day_of_week"] = df["sale_date"].dt.dayofweek.astype(int)
    df["day_of_month"] = df["sale_date"].dt.day.astype(int)
    df["month"] = df["sale_date"].dt.month.astype(int)
    df["week_of_year"] = df["sale_date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Grouping key for product-level series
    group_cols = ["business_id", "product_id"]

    # 2. Lag Features (t-1, t-7, t-14, t-28)
    for lag in [1, 7, 14, 28]:
        df[f"lag_{lag}"] = df.groupby(group_cols)["units_sold"].shift(lag)

    # 3. Rolling Features (Shift by 1 FIRST to prevent target day leakage)
    units_shifted = df.groupby(group_cols)["units_sold"].shift(1)

    for w in [7, 14, 28]:
        df[f"rolling_mean_{w}"] = (
            units_shifted.groupby([df["business_id"], df["product_id"]])
            .rolling(w, min_periods=w)
            .mean()
            .reset_index(level=[0, 1], drop=True)
        )
        df[f"rolling_std_{w}"] = (
            units_shifted.groupby([df["business_id"], df["product_id"]])
            .rolling(w, min_periods=w)
            .std()
            .reset_index(level=[0, 1], drop=True)
        )

    # 4. Business & Exogenous Variables
    df["selling_price"] = df["selling_price"].astype(float)
    df["promotion"] = df["promotion"].astype(int) if "promotion" in df.columns else 0
    df["holiday"] = df["holiday"].astype(int) if "holiday" in df.columns else 0

    if "festival" in df.columns:
        df["has_festival"] = df["festival"].apply(
            lambda x: 1 if pd.notna(x) and str(x).strip() != "" and str(x).strip().lower() != "none" else 0
        )
    else:
        df["has_festival"] = 0

    df["stock_available"] = df["stock_available"].astype(float) if "stock_available" in df.columns else 0.0

    if "is_stockout" in df.columns:
        df["is_stockout_feature"] = df["is_stockout"].apply(
            lambda x: 1 if (pd.notna(x) and bool(x) is True) else 0
        )
    else:
        df["is_stockout_feature"] = (df["stock_available"] == 0).astype(int)

    # 5. Product Identifiers & Category Encoding
    if "category" in df.columns:
        df["category_code"] = pd.Categorical(df["category"].fillna("General")).codes
    else:
        df["category_code"] = 0

    df["product_id_code"] = pd.Categorical(df["product_id"]).codes

    # 6. Drop rows with NaN lag history (first 28 days for each product series)
    required_feature_cols = [f"lag_{l}" for l in [1, 7, 14, 28]] + [f"rolling_mean_{w}" for w in [7, 14, 28]]
    df_clean = df.dropna(subset=required_feature_cols).reset_index(drop=True)

    return df_clean, FEATURE_COLUMNS, TARGET_COLUMN
