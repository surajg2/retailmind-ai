"""
Baseline Forecasting Models for RetailMind AI
"""

from .naive import predict_naive, predict_seasonal_naive

__all__ = ["predict_naive", "predict_seasonal_naive"]
