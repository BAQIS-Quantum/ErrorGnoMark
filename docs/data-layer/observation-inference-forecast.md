# Observation, Inference, and Forecast

EGM stores **three kinds of metric facts**. They share the physical table `observation_record` (Phase 1 v1.1+) but must be distinguished by `record_kind` and metadata. **Do not mix semantics** in `value_json` alone.

## Definitions

| Kind | Meaning | Example | Typical writer |
|------|---------|---------|----------------|
| **Observation** | Direct experimental or execution measurement | RB survival probability, XEB fidelity, fitted T1 | Protocol run → analysis → `PostgresObservationStore` |
| **Inference** | Quantity **derived** from observations (with uncertainty) | EPC from RB, tomography inversion | Analyzer extension / batch job |
| **Forecast** | **Future** state prediction (model-backed) | Drift probability in 2 hours | `intelligence/forecasting` (**Planned** runtime) |

## Write rules

### Observation (`record_kind = observation`)

- Default for workflow persistence via `PostgresObservationStore`.
- `observation_time` = when the measurement applies.
- Use `effective_from` / `effective_to` when the fact has a validity window (bi-temporal).
- `ingested_at` = when EGM recorded the row (system time).

### Inference (`record_kind = inference`)

- Must reference provenance (e.g. source observation IDs in `value_json` or future `provenance_json`).
- Do **not** store raw shot histograms or circuit outcomes as inference.
- `observation_time` = time the inference is anchored to (often same as source observation window).

### Forecast (`record_kind = forecast`)

**Required columns** (enforced by DB check constraint):

- `forecast_model_version` — non-empty string (e.g. `egm-forecast-v0.0.0-draft`)
- `forecast_horizon_seconds` — recommended (seconds into the future)

**Recommended in** `forecast_metadata_json`:

- `confidence_interval`
- `training_data_window`
- `backtest_performance` (when available)

Forecast rows may exist before the forecasting **runtime** ships; they must still carry model metadata.

## Anti-patterns

| Do not | Why |
|--------|-----|
| Store forecasts without `forecast_model_version` | Breaks audit and reproducibility |
| Label raw execution payloads as `inference` | Inference is derived, not measured |
| Use `observation` for predicted future metrics | Use `forecast` + horizon |
| Rely only on `value_json` for kind | Use `record_kind` for queries and constraints |

## Querying

Filter by kind when listing facts:

```sql
SELECT *
FROM observation_record
WHERE chip_id = $1
  AND record_kind = 'observation'
  AND observation_time <= $2
ORDER BY observation_time DESC;
```

Existing P0 templates (Q13, Q22, Q23) return all kinds unless filtered; add `record_kind` filters in application code or new templates as needed.

## Evolution

- **v1.1 (current):** single table + `record_kind_enum`.
- **Future:** optional split into `inference_record` / `forecast_record` if volume or constraints require it (Horizon F+ RFC).
