"""
Forecasting Package
===================

This package implements the Semantic Predictive Layer of EGM.

It extends the deterministic v3 world model with
probabilistic future-state estimation capabilities.

Layer Position
--------------
Deterministic Semantic Layer (v3):
    egm.system.*

Predictive Semantic Layer:
    egm.intelligence.forecasting.*

Application Consumers:
    egm.compiler.*
    egm.suites.calibration.*
    (future scheduler / health monitoring modules)

Design Guarantees
-----------------
- Forecasting NEVER modifies Version graph.
- Forecasting NEVER creates Event.
- Forecasting NEVER mutates HardwareState.
- Forecasting is strictly read-only and overlay-based.

Core Components
---------------
- TimeSeriesExtractor: historical metric retrieval
- TransitionModel: state evolution modeling
- RiskModel: risk evaluation
- PredictiveContext: probabilistic annotation container
- PredictiveSnapshot: combined deterministic + predictive view

This layer upgrades EGM from:
    Static World Model
to:
    Dynamic, Uncertainty-Aware World Model.
"""

from .time_series import TimeSeriesExtractor
from .transition_model import TransitionModel
from .risk_model import RiskModel
from .predictive_context import Prediction, PredictiveContext
from .predictive_snapshot import PredictiveSnapshot

__all__ = [
    "TimeSeriesExtractor",
    "TransitionModel",
    "RiskModel",
    "Prediction",
    "PredictiveContext",
    "PredictiveSnapshot",
]