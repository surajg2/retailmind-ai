import numpy as np
import pandas as pd
from typing import Union

def predict_naive(df: pd.DataFrame) -> np.ndarray:
    """
    Naive Baseline 1:
    y_hat(t) = y(t-1)
    Uses lag_1 feature.
    """
    if "lag_1" in df.columns:
        return df["lag_1"].values.astype(float)
    elif "units_sold" in df.columns:
        return df.groupby(["business_id", "product_id"])["units_sold"].shift(1).values.astype(float)
    else:
        raise ValueError("Cannot compute Naive forecast: missing lag_1 or units_sold column.")


def predict_seasonal_naive(df: pd.DataFrame) -> np.ndarray:
    """
    Seasonal Naive Baseline 2:
    y_hat(t) = y(t-7)
    Uses lag_7 feature.
    """
    if "lag_7" in df.columns:
        return df["lag_7"].values.astype(float)
    elif "units_sold" in df.columns:
        return df.groupby(["business_id", "product_id"])["units_sold"].shift(7).values.astype(float)
    else:
        raise ValueError("Cannot compute Seasonal Naive forecast: missing lag_7 or units_sold column.")
