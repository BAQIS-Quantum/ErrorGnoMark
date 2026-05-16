# `observation_record` schema (Phase 1)

The table `observation_record` is the **metric fact table** for Phase 1. Despite the name, it holds observations, inferences, and forecasts (v1.1+ via `record_kind`).

DDL source: [db/phase1/001_schema.sql](../../db/phase1/001_schema.sql).  
Extensions: [db/migrations/0002_record_kind.sql](../../db/migrations/0002_record_kind.sql).

Bi-temporal fields align with EGM’s **effective time** (when a fact is true in the world) vs **ingested time** (when EGM learned it). See architecture notes on experiment/version models.

## Columns

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `observation_record_id` | UUID | PK | Surrogate key |
| `chip_id` | UUID | yes | FK → `chip` |
| `subject_type` | enum | yes | e.g. `chip`, `qubit` |
| `subject_id` | UUID | yes | Entity measured |
| `scope_id` | UUID | no | Optional scope FK |
| `metric_definition_id` | UUID | yes | FK → `metric_definition` |
| `producer_type` | enum | yes | e.g. `benchmark_run`, `calibration_artifact` |
| `producer_id` | UUID | yes | Run or artifact that produced the row |
| `value_numeric` | float | one of value_* | Scalar metric |
| `value_text` | text | one of value_* | Text metric |
| `value_json` | jsonb | one of value_* | Structured payload (workflow store uses this) |
| `unit` | text | no | SI or convention string |
| `quality_flag` | enum | yes | Default `raw` |
| `observation_time` | timestamptz | yes | **Valid time** anchor for the measurement |
| `effective_from` | timestamptz | no | Start of fact validity (bi-temporal) |
| `effective_to` | timestamptz | no | End of validity (NULL = open) |
| `published_at` | timestamptz | no | External publication time |
| `ingested_at` | timestamptz | yes | **Transaction time** — when stored in EGM |
| `source_id` | UUID | yes | FK → `source` |
| `created_at` | timestamptz | yes | Row creation |
| `record_kind` | enum | yes (v1.1) | `observation` \| `inference` \| `forecast` |
| `forecast_model_version` | text | if forecast | Model id/version |
| `forecast_horizon_seconds` | int | recommended | Seconds into future |
| `forecast_metadata_json` | jsonb | no | CI, training window, backtest stats |

## Logical fields (fix-suggestion / roadmap)

The following are represented **inside** `value_json` for workflow observations or via related tables in later phases:

| Logical field | Phase 1 location |
|---------------|------------------|
| `protocol` | `value_json` (`PostgresObservationStore`) |
| `lineage` | `lineage` / `lineage_edge` tables |
| `hardware_snapshot_id` | `structure_snapshot` / `system_state` |
| `software_version` | `value_json` or future column |
| `analysis_version` | `value_json` |
| `config_hash` | `value_json` |
| `raw_result_ref` | `benchmark_run.result_ref` or `value_json` |

## Python mapping (`PostgresObservationStore`)

| `ObservationPersistenceDict` key | DB column / note |
|----------------------------------|------------------|
| `chip_name` | Resolved → `chip_id` |
| `observation_time` | `observation_time` |
| `protocol`, `task_id`, … | Full dict → `value_json` |
| `record_kind` | `record_kind` (default `observation`) |
| `forecast_model_version` | `forecast_model_version` |
| `forecast_horizon_seconds` | `forecast_horizon_seconds` |

Keys are defined in `egm.datastore.observation_store.ObservationKeys` (`KEYS`).

## Indexes (representative)

- `(chip_id, metric_definition_id, observation_time DESC)`
- `(chip_id, record_kind, observation_time DESC)` — v1.1

See DDL for full index list.
