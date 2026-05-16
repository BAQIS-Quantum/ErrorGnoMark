# Phase 1 database (PostgreSQL 14+)

## 和仓库根目录下的 `db/` vs `scripts/postgres/`（易混说明）

| 路径 | 放什么 | 是否重复 |
|------|--------|----------|
| **`db/phase1/`**（本 README 所在目录） | **只放 SQL**：建表 DDL、seed 数据。 | 与下面**不是**同一类东西。 |
| **`scripts/postgres/`** | **放脚本/笔记本**：`apply_phase1.sh`（调用上面的 SQL）、`verify_seed_counts.py`、`run_p0_queries.py`、`phase1_database_checks.ipynb`（验收）、`phase1_live_demo.ipynb`（现场演示：apply + 样例查询表格 + 验收）等。 | 同上。 |

**两个都要保留**：`db/` =「库里该长什么样、演示行是什么」；`scripts/postgres/` =「怎么 apply、怎么验收」。`apply_phase1.sh` 里写的是 `-f "$ROOT/db/phase1/..."`，依赖根目录下的 `db/`。

## Contents

| Path | Role |
|------|------|
| `001_schema.sql` | DDL from `p1-step1` draft (extensions, enums, core tables, indexes, views). |
| `seed/010_minimal_demo.sql` | Minimal `chip-alpha` / `chip-beta` + qubits, couplers, scopes, `source`, `metric_definition` for workflow smoke + P0 queries. |
| `seed/020_structure_snapshots_and_events.sql` | `structure_snapshot` (superseded + latest) and `structure_event` rows for **chip-alpha**; supports **p1-step2** API-05/06 (Q5–Q7) SQL under `sql/queries/p0/`. |
| `seed/030_calibration_benchmark_observation_system.sql` | `calibration_run` / `calibration_artifact`, **two** `benchmark_run`, `observation_record` (×2), `calibration_snapshot`, `system_state` for **chip-alpha**; supports API-07..13 (Q8–Q18), API-10 **Q12** (list + optional filters/paging), API-11 **Q13–Q14**. |
| `seed/040_lineage_for_system_state.sql` | **Lineage** for current `system_state` (API-14 / Q19–Q21): one `lineage` row + two `lineage_edge` rows. |

Stable UUIDs for the seed are mirrored in `src/egm/datastore/phase1_pg_constants.py`.

**已落地表清单**（与 `001_schema.sql` 对齐）：见 [`TABLES_LANDED.md`](TABLES_LANDED.md)。

## Apply

Requires `psql` and a reachable database.

```bash
export EGM_PG_DSN='postgresql://USER:PASS@HOST:5432/DBNAME'
./scripts/postgres/apply_phase1.sh
```

Re-apply on a **non-empty** database may fail on duplicate keys; for development, drop/recreate the database or schema first.

**Migrations (Horizon E):** `apply_phase1.sh` also runs `db/migrations/*.sql` (target `db/schema_version.txt`). Upgrade-only: `python scripts/postgres/apply_migrations.py`. See [../MIGRATION.md](../MIGRATION.md).

## Verify

```bash
pip install 'psycopg[binary]>=3.2'   # if not already installed
python scripts/postgres/verify_seed_counts.py
PYTHONPATH=src python scripts/postgres/run_p0_queries.py
```

**验收入口（推荐）**：在已 apply+seed 的库上，一次跑完「行数校验 + P0 SQL」，与上两行等价；CI 使用 ``--strict``（无 DSN 或缺 psycopg 则失败，避免静默 skip）。

```bash
PYTHONPATH=src python -m egm.datastore.phase1_acceptance --strict
```

实现见 ``src/egm/datastore/phase1_acceptance.py``。

`run_p0_queries.py` runs **Q1–Q23** templates in `sql/queries/p0/` (through API-16), including **API-06 Q7** filtered/paged (`q07_structure_events_filtered.sql`), **API-07 Q8** filtered/paged (`q08_calibration_runs_filtered.sql`), **API-10 Q12** filtered/paged (`q12_benchmark_runs_filtered.sql`), **API-11 Q14** paging (`q14_metric_history_paged.sql`), and filtered API-15/16 variants.

## Alignment

- DDL source: `001_schema.sql` in this directory (executable Phase 1 minimum table set).
- Workflow store: `PostgresObservationStore` (`src/egm/datastore/postgres_observation_store.py`).
