"""
Error Budget Subsystem
======================

Purpose
-------
Provide structured decomposition of circuit-level or logical-level
error into interpretable contributions.

This subsystem answers:

    - What contributes most to total logical error?
    - How much does each gate / component contribute?
    - Which error types dominate (1Q / 2Q / readout / decoder)?
    - What is the sensitivity of total error to individual sources?

Layer Position
--------------
This module belongs to the Domain Layer.

It depends on:
    - error_modeling (for noise model definitions)
    - error_propagation (for propagation results)

It must NOT depend on:
    - compiler
    - execution
    - hardware_state mutation
    - datastore

Design Philosophy
-----------------
- Pure analysis layer.
- No state mutation.
- No decision-making logic.
- No routing logic.
- No calibration logic.

Future Extension
----------------
Designed to support:
    - Physical circuit error budget
    - Logical error budget (QEC)
    - Multi-round syndrome analysis
    - Decoder-induced logical error attribution
"""