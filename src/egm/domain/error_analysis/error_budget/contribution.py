"""
Error Contribution Data Model
=============================

Purpose
-------
Represent the quantified impact of a single error source
on total logical error.

Conceptual Model
----------------
Each contribution consists of:

    - A unique source identifier
    - A categorized error type
    - The raw physical error rate
    - The propagated impact on final logical error
    - A normalized weight in the total error budget

Design Principles
-----------------
- Immutable data structure.
- Pure data container.
- No computational logic.
- No dependency on propagation engine internals.

Why Separation Matters
----------------------
We separate contribution objects from analysis logic to:

    - Allow flexible aggregation
    - Support structured reporting
    - Enable future serialization
    - Avoid coupling to specific circuit models

Future QEC Support
------------------
Logical error contributions may include:

    - Syndrome round failures
    - Decoder decisions
    - Leakage accumulation
    - Correlated error clusters
"""