# Analyzer output specification (Horizon C v1)

Beta protocols must expose **point estimates and uncertainty** where fitting applies. Task-level JSON may lag schemas; this document is the target contract.

## XEB (`XEBAnalysisResult` — `src/egm/schemas/results/xeb.py`)

| Field | Required for Beta | Description |
|-------|-------------------|-------------|
| `mean_fidelity[]` | Yes | Per-depth mean normalized XEB fidelity |
| `error_bar[]` | Yes | SEM (or documented mode) per depth |
| `fit.params` (`A`, `p`, `B`) | Yes | Exponential decay fit |
| `fit.success` | Yes | Must be inspectable when false |
| `axis_mode` | Yes | `depth` or `gate_count` |

Low-level fidelity: `analyze_xeb_fidelity()` in `src/egm/analysis/xeb.py` (Google normalized XEB).

## RB (`RBAnalysisResult` — `src/egm/schemas/results/rb.py`)

| Field | Required for Beta | Description |
|-------|-------------------|-------------|
| `sequence_data[].survival_probability` | Yes | Aggregated survival at each m |
| `sequence_data[].std_error` | Yes | SEM across sequences |
| `fit.params` (`A`, `p`, `B`) | Yes | RB decay model |
| Derived EPC | Yes | From `p` and qubit count d |

Low-level fit: `fit_rb_data()` / `analyze_rb_standard()` in `src/egm/analysis/rb.py`.

## Anti-patterns

Do not document or publish benchmark results as:

```json
{"fidelity": 0.992}
```

without uncertainty, fit quality, or scope notes.

## Task-level payload

`TaskAnalysisResult.analysis_payload` should converge to schema-serializable objects. Known gap: some paths still return nested dicts; track in validation PRs.
