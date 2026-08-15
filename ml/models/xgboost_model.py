import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import xgboost as xgb

from ml.features.demand_features import FEATURE_COLUMNS, TARGET_COLUMN

class DemandXGBoostModel:
    """
    XGBoost Regression Model for RetailMind AI Observed Demand Forecasting.
    Formulation: y(t) = f(X(t))
    Uses engineered tabular features anchored strictly before target date t.
    """
    def __init__(self, n_estimators: int = 100, max_depth: int = 4, learning_rate: float = 0.05, random_state: int = 42):
        self.feature_columns = FEATURE_COLUMNS
        self.target_column = TARGET_COLUMN
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            objective="reg:squarederror",
            n_jobs=-1
        )
        self.is_trained = False

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: Optional[pd.DataFrame] = None, y_val: Optional[pd.Series] = None):
        """
        Trains the XGBoost regressor on feature matrix X_train and target y_train.
        """
        X_tr = X_train[self.feature_columns]
        
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_val[self.feature_columns], y_val)]

        self.model.fit(
            X_tr,
            y_train,
            eval_set=eval_set,
            verbose=False
        )
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predicts observed units sold for feature matrix X.
        Clips predictions to non-negative values (units sold cannot be < 0).
        """
        if not self.is_trained:
            raise RuntimeError("Cannot predict: DemandXGBoostModel is not trained yet.")
        
        X_feats = X[self.feature_columns]
        preds = self.model.predict(X_feats)
        return np.maximum(0.0, preds)

    def save(self, filepath_model: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Saves local model binary and metadata JSON.
        Does NOT store passwords, DB URLs, or secrets.
        """
        os.makedirs(os.path.dirname(filepath_model), exist_ok=True)
        joblib.dump(self.model, filepath_model)

        if metadata:
            meta_path = filepath_model.replace(".joblib", "_metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)

    def load(self, filepath_model: str):
        """
        Loads local model binary.
        """
        self.model = joblib.load(filepath_model)
        self.is_trained = True
