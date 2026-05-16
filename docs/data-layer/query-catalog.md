# Phase 1 query catalog (P0)

Static SQL lives under [sql/queries/p0/](../../sql/queries/p0/). Runner: [scripts/postgres/run_p0_queries.py](../../scripts/postgres/run_p0_queries.py).  
CI acceptance: `python -m egm.datastore.phase1_acceptance --strict`.

**Schema version:** `phase1_v1.1` (after migration `0002`). Templates do not filter `record_kind` unless noted.

## API / query map (summary)

| Q | File (representative) | API | Topic |
|---|------------------------|-----|--------|
| Q1–Q3 | `q01`–`q03` | API-01..03 | Chip, qubits, couplers |
| Q5–Q7 | `q05`–`q07` | API-05..06 | Structure snapshots / events |
| Q8–Q12 | `q08`–`q12` | API-07..10 | Calibration / benchmark runs |
| Q10–Q11 | `q10`–`q11` | API-09..11 | Calibration snapshot as-of |
| Q13–Q14 | `q13`–`q14` | API-11 | Observation history / paging |
| Q15–Q18 | `q15`–`q18` | API-12..14 | System state, as-of |
| Q19–Q21 | `q19`–`q21` | API-14 | Lineage |
| Q22–Q23 | `q22`–`q23` | API-15..16 | Recent ingested / known observations |
| Q24–Q26 | `q24`–`q26` | — | Timelines / heatmaps / compare |

Full file list: 31 templates in `sql/queries/p0/`.

## Version compatibility

| Schema | Queries | Notes |
|--------|---------|-------|
| `phase1_v1.0` | `p0/` | Before `record_kind` column |
| `phase1_v1.1` | `p0/` | Default `record_kind = observation` on seed rows |

When adding kind-specific reports, prefer new files (e.g. `p0/q27_observations_only.sql`) rather than silently changing existing templates.
