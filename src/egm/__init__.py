"""
ErrorGnoMark (EGM) — Quantum Hardware Benchmarking & Characterization Platform
===============================================================================

EGM provides a modular, full-stack toolkit for evaluating quantum computing
systems: from physical-layer characterization (T1/T2, RB, XEB) to
application-level performance profiling, with a unified data layer that
supports bi-temporal queries, lineage tracking, and predictive analytics.

Quick start::

    pip install errorgnomark          # or: pip install -e .
    python -c "import egm; print(egm.__version__)"

Subpackages
-----------
circuits     Backend-agnostic quantum circuit IR
protocols    Benchmark protocol implementations (XEB, RB, IRB, MRB, ...)
backends     Hardware abstraction (simulators, cloud QPUs)
execution    Plan building, running, and orchestration
analysis     Protocol-agnostic analysis dispatch
schemas      Type-safe Pydantic models (configs, plans, results)
datastore    Observation persistence (memory, SQLite, PostgreSQL)
domain       Error modeling, inference, propagation, state management
intelligence Predictive forecasting, risk models
services     Application-layer glue (planning, queries, serialization)
suites       High-level workflow orchestration (calibration, profiling)
reporting    Dashboard generation and visualization
"""

from __future__ import annotations

__version__ = "3.0.2"
__all__ = ["__version__"]
