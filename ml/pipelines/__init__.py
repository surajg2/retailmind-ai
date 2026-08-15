"""
Pipelines Module for RetailMind AI Demand Forecasting
"""

from .train import run_training_pipeline
from .predict import generate_7day_forecast

__all__ = ["run_training_pipeline", "generate_7day_forecast"]
