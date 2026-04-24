"""
Error Budget Analyzer
=====================

Purpose
-------
Main entry point for decomposing logical error
into structured contributions.

High-Level Workflow
-------------------
1. Accept propagation result.
2. Query impact per error source.
3. Construct contribution objects.
4. Aggregate and produce report.

Architectural Position
----------------------
Domain Layer - Analysis Component.

Dependencies
------------
Allowed:
    - Propagation result interface
    - Abstract error source interface
    - Aggregation utilities

Not Allowed:
    - Compiler
    - Execution backend
    - Hardware state mutation
    - Calibration logic
    - Routing heuristics

Key Design Decision
-------------------
The analyzer does NOT recompute propagation.
It interprets propagation results.

This ensures:
    - Separation of physics simulation and analysis
    - Pluggable propagation engines
    - Future logical-level extensibility

QEC Compatibility
-----------------
Must support:

    - Multi-cycle error attribution
    - Decoder-induced logical error sources
    - Feedback-based correction loops
    - Correlated error clusters

The analyzer must remain agnostic to:

    - Circuit type
    - Abstraction level (physical vs logical)
    - Noise model complexity
"""