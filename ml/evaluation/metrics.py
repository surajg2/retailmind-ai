import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculates Mean Absolute Error (MAE).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if len(y_true) == 0:
        return 0.0
    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculates Root Mean Squared Error (RMSE).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if len(y_true) == 0:
        return 0.0
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> Optional[float]:
    """
    Calculates Mean Absolute Percentage Error (MAPE).
    Handles zero actual values explicitly by evaluating only on positive actuals.
    Returns None if no positive actuals exist.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = y_true > 0
    if not np.any(mask):
        return None
    
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def evaluate_models(
    y_true: np.ndarray,
    predictions: Dict[str, np.ndarray]
) -> pd.DataFrame:
    """
    Evaluates multiple forecasting models on the held-out TEST set.
    """
    rows = []
    for model_name, y_pred in predictions.items():
        mae = calculate_mae(y_true, y_pred)
        rmse = calculate_rmse(y_true, y_pred)
        mape = calculate_mape(y_true, y_pred)
        
        rows.append({
            "Model": model_name,
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "MAPE (%)": round(mape, 2) if mape is not None else "N/A"
        })

    res_df = pd.DataFrame(rows)
    return res_df
