"""
Predictive Context Definition
=============================

Purpose
-------
Defines the core data structures for representing probabilistic
future-state annotations tied to a deterministic Version.

Architectural Role
------------------
This module introduces the Predictive Semantic Layer,
which extends the v3 deterministic world model without
modifying it.

Key Concepts
------------
- Prediction: A probabilistic statement about future metric behavior.
- PredictiveContext: A collection of predictions anchored to a base Version.

Critical Design Constraint
--------------------------
PredictiveContext MUST:
- Reference a base_version_id.
- NEVER create new Version nodes.
- NEVER alter HardwareState.

Semantic Distinction
--------------------
v3:
    Deterministic, historical, immutable world model.

PredictiveContext:
    Probabilistic, future-oriented, disposable overlay.

It is an annotation layer, not part of the Version DAG.
"""