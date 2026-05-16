# Public API (Python package)

Last updated: **2026-05-16** · Horizon D v1

This document lists the **intended integration surface** for `errorgnomark`. Internal modules (`protocols.*.kernel`, private backend helpers) are not listed.

For domain/interface governance (L0/L1/L2), see [interface_stability_policy.md](../architecture/interface_stability_policy.md).

## Stability levels

| Level | Promise |
|-------|---------|
| **Stable** | Compatible across patch/minor releases unless documented |
| **Beta** | Runnable; signatures or semantics may evolve |
| **Experimental** | May change without notice |
| **Internal** | No compatibility promise |

Capability maturity for protocols is in [README Feature Status](../../README.md#feature-status-v302).

## Public API table

| Symbol | Module | Stability | Notes |
|--------|--------|-----------|-------|
| `analyze_task_execution_result` | `egm.analysis` | **Stable** | Unified per-task analysis entry |
| `CircuitTask`, `PlanSchema` | `egm.schemas.plan` | **Beta** | Planning dataclasses |
| `TaskExecutionResult`, `PlanExecutionResult` | `egm.schemas.results.execution` | **Beta** | Execution contracts |
| `TaskAnalysisResult` | `egm.schemas.results.analysis` | **Beta** | Analysis output wrapper |
| `ConfigSchema`, `PlanBuilder` | `egm.schemas.configs`, `egm.services.planning` | **Beta** | Config → plan |
| `run_plan` | `egm.execution.plan_runner` | **Beta** | Execute plan on backend |
| `PostgresObservationStore` | `egm.datastore.postgres_observation_store` | **Beta** | Requires `EGM_PG_DSN` |
| `XEBAnalysisResult`, `RBAnalysisResult` | `egm.schemas.results.xeb`, `.rb` | **Beta** | Batch/schema-level results |
| Physical protocol classes | `egm.protocols.physical.*` | **Beta / Experimental** | Per README |
| `analyze_xeb_fidelity`, `fit_rb_data` | `egm.analysis.xeb`, `.rb` | **Beta** | Lower-level; prefer dispatch |

## Errors and logging (current)

- Task-level failures return `TaskAnalysisResult` with `status="analysis_error"` and `error` message.
- A unified `EGMError` hierarchy is **planned** (Horizon D phase 2).
- Prefer logging `plan_id`, `task_id`, and `protocol` in custom integrations.

## Validation vs coverage

- **Scientific correctness**: `docs/validation/` + `tests/validation/`.
- **Regression**: CI `pytest` + coverage report (targets in [ci.md](./ci.md)).
- High coverage does not imply all protocols are validated.
