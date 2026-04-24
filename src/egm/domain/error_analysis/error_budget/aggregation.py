"""
Aggregation Utilities
=====================

Purpose
-------
Provide reusable grouping and aggregation utilities
for error contributions.

Why Separate?
-------------
We isolate aggregation logic to prevent:

    - Analyzer class bloat
    - Tight coupling between analysis and reporting
    - Repetition of grouping code

Responsibilities
----------------
- Group contributions by error type
- Group contributions by source
- Compute aggregated sums

Non-Responsibilities
--------------------
- No propagation
- No error modeling
- No sensitivity computation
- No hardware interaction

Future Extensions
-----------------
May support:

    - Multi-dimensional aggregation
    - Hierarchical grouping (physical → logical)
    - Graph-based clustering
"""