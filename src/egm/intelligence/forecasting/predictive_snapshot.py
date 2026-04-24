"""
Predictive Snapshot Wrapper
===========================

Purpose
-------
Combines a deterministic HardwareSnapshot with a PredictiveContext
to provide a unified view for system-level consumers.

Architectural Role
------------------
This is a composition layer, not an inheritance extension.
It preserves strict separation between:

    Deterministic Semantic Layer (v3)
and
    Probabilistic Predictive Layer.

Design Principles
-----------------
- Must NOT modify the underlying HardwareSnapshot.
- Must NOT alter Version graph.
- Must remain read-only.
- Must allow consumers to ignore predictive layer if desired.

System Usage
------------
Consumers such as:
    - Compiler
    - Calibration System
    - Scheduling Layer

can consume PredictiveSnapshot to make risk-aware decisions,
while still being anchored to a specific deterministic Version.

Conceptual Model
----------------
HardwareSnapshot:
    "The world is X."

PredictiveSnapshot:
    "The world is X, and may evolve toward Y with probability P."

This layer upgrades EGM from a static world model
to a dynamic, uncertainty-aware semantic platform.
"""