#!/usr/bin/env bash
# Apply Phase 1 DDL + minimal seed. Requires: psql, EGM_PG_DSN.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [[ -z "${EGM_PG_DSN:-}" ]]; then
  echo "EGM_PG_DSN is not set (e.g. postgresql://user:pass@localhost:5432/egm_phase1)" >&2
  exit 1
fi
psql "$EGM_PG_DSN" -v ON_ERROR_STOP=1 -f "$ROOT/db/phase1/001_schema.sql"
psql "$EGM_PG_DSN" -v ON_ERROR_STOP=1 -f "$ROOT/db/phase1/seed/010_minimal_demo.sql"
psql "$EGM_PG_DSN" -v ON_ERROR_STOP=1 -f "$ROOT/db/phase1/seed/020_structure_snapshots_and_events.sql"
psql "$EGM_PG_DSN" -v ON_ERROR_STOP=1 -f "$ROOT/db/phase1/seed/030_calibration_benchmark_observation_system.sql"
psql "$EGM_PG_DSN" -v ON_ERROR_STOP=1 -f "$ROOT/db/phase1/seed/040_lineage_for_system_state.sql"
psql "$EGM_PG_DSN" -v ON_ERROR_STOP=1 -f "$ROOT/db/phase1/seed/050_quafu_baihua_bootstrap.sql"
echo "Phase 1 schema + seed applied."
