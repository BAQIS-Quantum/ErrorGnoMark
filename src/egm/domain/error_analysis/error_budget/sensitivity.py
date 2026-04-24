"""
Sensitivity Analysis Module
===========================

Purpose
-------
Quantify how sensitive total logical error is
to changes in individual error parameters.

Mathematical Concept
--------------------
Approximate partial derivatives:

    dF / dp_i

Where:
    F = total logical error
    p_i = individual physical error rate

Why This Matters
----------------
Sensitivity analysis enables:

    - Hardware optimization prioritization
    - Resource allocation decisions
    - QEC threshold studies
    - Bottleneck identification

Design Constraints
------------------
- Must remain independent of specific noise models.
- Should operate on abstract propagation results.
- Should not modify hardware state.

Future QEC Use
--------------
Critical for:

    - Logical threshold estimation
    - Decoder robustness analysis
    - Cycle-level optimization
"""