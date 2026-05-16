# Getting started

This guide gets you from zero to a working EGM install and a minimal **XEB** run on a simulator. No real quantum hardware or PostgreSQL is required for the first path.

---

## Prerequisites

- **Python** ≥ 3.9
- **pip** (or uv/poetry if you adapt commands)

---

## Install

### From PyPI

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install errorgnomark
python -c "import egm; print(egm.__version__)"
```

### From source (development)

```bash
git clone https://github.com/BAQIS-Quantum/ErrorGnoMark.git
cd ErrorGnoMark
pip install -e ".[dev]"
python -c "import egm; print(egm.__version__)"
```

China mirror: `git clone https://gitee.com/xdchai/errorgnomark.git` (see README § Repositories).

---

## 10-minute path: XEB on a simulator

The full example lives in [README § Quick Start](../README.md#quick-start). Minimal flow:

1. Build a `ConfigSchema` with an XEB `ProtocolBundle`.
2. `PlanBuilder.build_plan_from_config(config)`.
3. Run with `DummyBackendXEB` and `run_plan`.
4. Analyze with `analyze_task_execution_result`.

After install, copy the README Quick Start block into a file `demo_xeb.py` and run:

```bash
python demo_xeb.py
```

---

## Smoke scripts (no notebook required)

Pre-made demos under [../scripts/smoke/](../scripts/smoke/):

| Script | Purpose |
|--------|---------|
| `workflow_observation_e2e_smoke.py` | In-memory observation workflow |
| `workflow_observation_e2e_pg_smoke.py` | PostgreSQL end-to-end (needs DSN) |

Run from repo root:

```bash
python scripts/smoke/workflow_observation_e2e_smoke.py
```

---

## Optional: PostgreSQL (Phase 1)

1. Start PostgreSQL 15+ locally.
2. Set `EGM_PG_DSN`, e.g. `postgresql://user:pass@localhost:5432/egm_phase1`.
3. Follow [../scripts/postgres/README.md](../scripts/postgres/README.md) to apply `db/phase1/` schema and seed.
4. Try notebooks under `scripts/postgres/` or `scripts/smoke/workflow_observation_e2e_pg_smoke.ipynb`.

---

## Tutorials

- [xeb.ipynb](tutorials/xeb.ipynb)
- [rb.ipynb](tutorials/rb.ipynb)

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|----------------|--------|
| `ModuleNotFoundError: egm` | Wrong venv / not installed | `pip install -e ".[dev]"` or `pip install errorgnomark` |
| Postgres smoke fails | `EGM_PG_DSN` unset or DB down | Export DSN; run `scripts/postgres/apply_phase1.sh` |
| Cloud backend errors | Missing API keys / quota | Use `DummyBackend*` or simulators for local dev |
| Version mismatch vs docs | Old PyPI install | `pip install -U errorgnomark` or match git tag |

---

## Next steps

- Read [protocol-status.md](protocol-status.md) and [README Feature Status](../README.md#feature-status-v302).
- See [ROADMAP.md](../ROADMAP.md) for planned validation and CI work.
- To contribute, read [CONTRIBUTING.md](../CONTRIBUTING.md).
