"""
Abstractions for Error Sources
==============================

Purpose
-------
Define abstract interfaces representing error sources.

Why This Exists
---------------
We must not assume that all errors come from physical gates.

Future QEC scenarios may include:
    - Stabilizer cycles
    - Syndrome measurement rounds
    - Decoder misclassification
    - Feedback control errors

Therefore, we abstract error sources instead of binding to gate objects.

Design Constraints
------------------
- This file defines interface-level concepts only.
- No implementation logic.
- No propagation logic.
- No hardware coupling.
- No physical gate assumptions.

Extension Policy
----------------
Future implementations may include:
    - PhysicalGateErrorSource
    - LogicalCycleErrorSource
    - DecoderErrorSource
    - LeakageEventSource

This abstraction prevents technical debt when extending to QEC.
"""