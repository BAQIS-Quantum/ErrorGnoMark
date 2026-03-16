"""
EGM Intelligence Layer
======================

This package contains system-level cognitive extensions
built on top of the deterministic semantic core (v3).

Current Capabilities
--------------------
- Forecasting (Predictive Semantic Layer)

Future Extensions May Include
-----------------------------
- Adaptive policy engines
- Online anomaly detection
- Resource scheduling intelligence
- Self-optimization modules

Architectural Principle
-----------------------
Intelligence layer:
    - Reads from deterministic semantic layer (egm.system)
    - Produces high-level semantic augmentation
    - Never mutates core Version or HardwareState

This separation preserves semantic purity
while enabling higher-level reasoning capabilities.
"""

from .forecasting import (
    TimeSeriesExtractor,
    TransitionModel,
    RiskModel,
    Prediction,
    PredictiveContext,
    PredictiveSnapshot,
)

__all__ = [
    "TimeSeriesExtractor",
    "TransitionModel",
    "RiskModel",
    "Prediction",
    "PredictiveContext",
    "PredictiveSnapshot",
]