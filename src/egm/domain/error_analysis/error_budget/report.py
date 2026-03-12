"""
Error Budget Report Structure
=============================

Purpose
-------
Provide a structured and serializable output of
error budget analysis.

Responsibilities
----------------
The report aggregates:

    - Total logical error
    - List of individual contributions
    - Aggregated statistics by type
    - Aggregated statistics by source
    - Metadata about abstraction level

What This Is NOT
----------------
- Not a visualization layer.
- Not a datastore adapter.
- Not responsible for formatting.
- Not responsible for propagation.

Design Goal
-----------
Keep this structure stable over time to avoid breaking
downstream analysis or storage pipelines.

Future Extension
----------------
May include:

    - Confidence intervals
    - Correlation matrices
    - Time-resolved error decomposition
    - Multi-level logical hierarchy
"""