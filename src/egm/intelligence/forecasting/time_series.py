"""
Time Series Extraction Layer
=============================

Purpose
-------
Provides a standardized interface for extracting historical metric
time series from the Version graph / datastore layer.

Architectural Role
------------------
This module is part of the Semantic Predictive Layer (Forecast Layer).
It does NOT modify system state and does NOT generate new Version nodes.
It strictly reads historical data from the deterministic world model.

Key Responsibilities
--------------------
- Query historical metric trajectories (e.g., T1, T2, gate fidelity).
- Provide time-windowed metric series for predictive models.
- Abstract away datastore implementation details.

Non-Responsibilities
--------------------
- Does NOT perform prediction.
- Does NOT perform risk evaluation.
- Does NOT alter HardwareState or Snapshot.
- Does NOT create Events or Versions.

Design Principle
----------------
This module is a read-only bridge between:
    Deterministic Semantic Layer (v3)
and
    Predictive Modeling Components.

It must remain infrastructure-level and model-agnostic.
"""