# ErrorGnoMark (EGM) v3.0.3

> A modular platform for quantum hardware **characterization (QCVV), benchmark execution, and auditable observation storage** — not a quantum cloud operator or a production logical-QEC benchmark suite.

[![PyPI version](https://img.shields.io/pypi/v/errorgnomark.svg?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/errorgnomark/)
[![Python versions](https://img.shields.io/pypi/pyversions/errorgnomark.svg?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/errorgnomark/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square)](LICENSE)
[![CI](https://github.com/BAQIS-Quantum/ErrorGnoMark/actions/workflows/ci.yml/badge.svg)](https://github.com/BAQIS-Quantum/ErrorGnoMark/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/BAQIS-Quantum/ErrorGnoMark/ci.yml?label=tests&style=flat-square)](https://github.com/BAQIS-Quantum/ErrorGnoMark/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-CI%20term%20report-lightgrey?style=flat-square)](docs/engineering/ci.md)
[![Docs](https://img.shields.io/badge/docs-hub-1f6feb?style=flat-square)](docs/index.md)

---

## Start here

| If you want to… | Go to |
|-----------------|--------|
| **See what actually works in this release** | [Feature Status (v3.0.3)](#feature-status-v303) below — **authoritative** |
| **Run something in 10 minutes** | [Getting started](docs/getting-started.md) or [Quick Start](#quick-start) (Python API) |
| **Understand limits before you rely on EGM** | [Known Limitations](#known-limitations) |
| **Validate XEB / RB (synthetic)** | [validation summary](docs/validation/validation-summary.md) · [XEB](docs/validation/xeb-validation.md) · [RB](docs/validation/rb-validation.md) |

---

## What is EGM?

**ErrorGnoMark** combines *error* + *gno* (to know/diagnose) + *mark* (to benchmark). It connects protocol execution, unified analysis, and a **bi-temporal PostgreSQL observation layer** so benchmark results can be stored, queried, and audited over time.

**EGM exists because** most toolchains separate “run a benchmark script” from “keep calibration and benchmark facts in a comparable, time-aware store with lineage” — EGM targets that **reproducible, auditable lifecycle** for lab and platform integration work.

> **Scope honesty:** Only capabilities marked **Beta** or **Experimental** in [Feature Status](#feature-status-v303) are in scope for this release. **Planned** items are design or placeholders only.

---

## What ships in v3.0.3 (summary)

| Area | Shipped focus |
|------|----------------|
| **Protocols** | **XEB**, **RB** runnable on simulators with synthetic validation reports |
| **Data** | **PostgreSQL Phase 1** — bi-temporal observations, lineage, **31** static SQL templates (`phase1_acceptance --strict` in CI) |
| **Analysis** | Unified `analyze_task_execution_result()` dispatch |
| **Not in this release** | Logical QEC benchmarks, predictive runtime, Version DAG runtime, most extra protocols (T1/T2, QV, …) |

---

## Key Capabilities (framework vs this release)

The codebase is organized for many protocol **directions**; **this release** emphasizes the rows in [Feature Status](#feature-status-v303).

- **XEB & RB (Beta)** — End-to-end on simulators; see validation links in the status table  
- **Unified analysis dispatch** — One entry point routes to protocol-specific analyzers  
- **Backend-agnostic execution** — Simulators and cloud QPUs (Quafu, Quark); **hardware certification not claimed**  
- **Bi-temporal data layer (Beta)** — `effective_time` + `ingested_at`, lineage, Phase 1 SQL catalog  
- **Protocol framework** — Additional protocols (IRB, MRB, CSB, SPB, …) exist as **Experimental** or **Planned**; not implied as production-ready  

**Roadmap only (not shipped):** versioned hardware-state runtime, predictive overlay, logical QEC benchmark pipelines — see [Known Limitations](#known-limitations) and [ROADMAP.md](ROADMAP.md).

---

## Feature Status (v3.0.3)

| Area | Capability | Status | Notes |
|------|------------|--------|-------|
| Physical QCVV | XEB | **Beta** | Simulator smoke + analysis dispatch; [synthetic validation](docs/validation/xeb-validation.md) |
| Physical QCVV | RB | **Beta** | [synthetic validation](docs/validation/rb-validation.md); hardware validation pending |
| Physical QCVV | IRB | **Experimental** | Implementation present; **not** Beta — validation & limitations pending |
| Physical QCVV | MRB, PRB, CSB, SPB | **Experimental** | Implementation present; full validation reports pending |
| Physical QCVV | T1, T2, QV, Rabi, SPAM, Leakage RB, CLOPS | **Planned** | Placeholder modules; not yet implemented |
| Data platform | Phase 1 PostgreSQL + static queries | **Beta** | Requires `EGM_PG_DSN`; see `db/phase1/`, `sql/queries/` |
| Data platform | Bi-temporal schema + lineage (DB) | **Beta** | Schema in `db/phase1/001_schema.sql` |
| Domain | Version DAG, event-sourced hardware state (`domain/system/`) | **Planned** | Architecture documented; runtime implementation incomplete |
| Intelligence | Predictive overlay (`intelligence/forecasting/`) | **Planned** | Design docs; not production-ready |
| Logical QEC | Surface code / decoder benchmarks | **Planned** | FTQC-oriented **data hooks** only — no Stim/PyMatching workflow in this release |
| Algorithmic | Grover, QPE, VQE, etc. | **Experimental** | Lower priority than physical QCVV |

**Status definitions:** **Beta** = runnable with documented examples; **Experimental** = partial code, limited validation; **Planned** = design or placeholder only.  
**How status changes:** [docs/protocol-status.md](docs/protocol-status.md)

---

## Known Limitations

Read this before treating EGM as a production QCVV or QEC platform.

- **Logical QEC benchmarks** are not production-ready (no surface-code memory experiments, decoder integration, or logical error-rate pipeline).
- **FTQC-oriented** means **data abstractions and error-model hooks** in the datastore/schema — **not** turnkey logical-QEC benchmarks or decoders.
- **XEB/RB** validation is primarily **synthetic** ([summary](docs/validation/validation-summary.md)); **public hardware case studies are pending**.
- **Uncertainty / confidence intervals** on analysis outputs are **not yet guaranteed** on all code paths ([analyzer-output-spec](docs/validation/analyzer-output-spec.md)).
- **Reproducibility:** full one-command replay from a single `observation_id` is **roadmap** (v3.2 target); raw-count and circuit provenance are being extended.
- **Predictive intelligence** and **versioned hardware state** exist as design documentation without complete runtime paths.
- **PostgreSQL** is validated at **lab scale** ([postgres-benchmark-v0.1.md](docs/performance/postgres-benchmark-v0.1.md)), not web-scale.
- **Cloud/hardware backends** depend on third-party APIs, quotas, and credentials.
- License is **Apache-2.0** ([LICENSE](LICENSE)); history in [LICENSE-AUDIT.md](LICENSE-AUDIT.md).

---

## Use Cases

**Good fit**

- Research prototypes for quantum hardware characterization (QCVV)
- Teaching and reproducible demos with simulators ([`scripts/smoke/`](scripts/smoke/))
- Persisting calibration and benchmark observations in PostgreSQL (Phase 1)
- Building on a unified analysis entry point for new protocols

**Not a good fit (today)**

- Sole reliance for safety-critical or certified production control loops
- Expecting turnkey logical QEC benchmark + decoder integration
- Assuming every protocol name in the [Supported Protocols](#supported-protocols) list is validated and stable

---

## Installation

```bash
pip install errorgnomark
```

Or install from source for development (canonical repository):

```bash
git clone https://github.com/BAQIS-Quantum/ErrorGnoMark.git
cd ErrorGnoMark
pip install -e ".[dev]"
```

**China mirror** (read-only sync; tags should match GitHub):

```bash
git clone https://gitee.com/xdchai/errorgnomark.git
```

Verify:

```python
import egm
print(egm.__version__)  # 3.0.3
```

---

## Repositories

| Role | URL | Notes |
|------|-----|--------|
| **Canonical (official)** | https://github.com/BAQIS-Quantum/ErrorGnoMark | Primary development, issues, pull requests, and CI |
| **China mirror** | https://gitee.com/xdchai/errorgnomark | Mirror for faster clone in China; **BAQIS-Quantum** on GitHub is the official maintainer org |

Release tags and changelog on **GitHub** are authoritative. If versions differ between hosts, prefer GitHub.

**Requirements:** Python >= 3.9

---

## Architecture

EGM v3 is organized into 12 cohesive subsystems:

```
src/egm/
├── circuits/          # Backend-agnostic circuit IR, gate definitions, decomposition
├── protocols/         # Protocol implementations (physical / algorithmic / logical)
│   ├── physical/      #   XEB, RB, IRB, MRB, CSB, QV, T1/T2, SPAM, tomography, ...
│   ├── algorithmic/   #   Grover, QPE, VQE, QAOA, simulation benchmarks
│   └── logical/       #   Logical QEC protocols (Planned; not shipped)
├── backends/          # Hardware abstraction layer
│   ├── simulators/    #   Statevector, density matrix, dummy backends
│   ├── cloud/         #   Quafu Cloud, Quark Cloud
│   └── direct/        #   Direct hardware access
├── execution/         # Plan building, executor, job scheduling
├── analysis/          # Protocol-agnostic analysis dispatch + per-protocol analyzers
├── schemas/           # Type-safe Pydantic models (configs, plans, results)
├── datastore/         # Observation persistence (memory, SQLite, file, PostgreSQL)
├── domain/            # Error modeling, inference, propagation, state management
│   ├── error_analysis/    # Error budget decomposition & sensitivity
│   ├── error_modeling/    # Physical & logical noise models
│   ├── error_inference/   # RB/T1-based error inference
│   ├── error_propagation/ # Physical & logical error propagation
│   ├── state/             # Hardware state & snapshot
│   └── system/            # Version DAG, events, lifecycle (Planned runtime)
├── intelligence/      # Predictive forecasting (Planned)
├── services/          # Planning, query, serialization (application glue)
├── suites/            # High-level workflow orchestration
│   ├── calibration/   #   Auto-calibration, drift-triggered recalibration
│   ├── compiler/      #   Hardware-aware compilation, dynamic recompilation
│   └── system_profiling/  # Full-chip health scan, noise mapping
└── reporting/         # Dashboard generation, visualizers, formatters
```

### Data Flow

```
ConfigSchema ─── PlanBuilder ──→ PlanSchema (CircuitTasks)
                                      │
                              Executor + Backend
                                      │
                              TaskExecutionResult
                                      │
                          analyze_task_execution_result()
                                      │
                              TaskAnalysisResult
                                      │
                          ObservationStore.save_observation()
                                      │
                              PostgreSQL / SQLite / Memory
                                      │
                           SQL queries (31 templates) + API
```

---

## Quick Start

For a shorter path, see **[docs/getting-started.md](docs/getting-started.md)**. End-to-end smoke scripts: [`scripts/smoke/`](scripts/smoke/).

### Run XEB on a simulator

```python
from egm.schemas.configs import ConfigSchema, ConfigBase, HardwareConfig, ProtocolConfig, ProtocolBundle
from egm.services.planning.plan_builder import PlanBuilder
from egm.execution.plan_runner import run_plan
from egm.backends.dummy_backend_xeb import DummyBackendXEB
from egm.analysis import analyze_task_execution_result

config = ConfigSchema(
    base=ConfigBase(plan_id="demo-001", backend_name="DummyBackendXEB"),
    hardware=HardwareConfig(chip_name="Demo", available_qubits=[0, 1]),
    protocol=ProtocolConfig(bundles=[
        ProtocolBundle(
            protocol="XEB",
            qubits=[[0, 1]],
            depths=[3, 5, 8],
            number_of_circuits=10,
            shots=2048,
        )
    ]),
)

plan = PlanBuilder.build_plan_from_config(config)
backend = DummyBackendXEB(num_qubits=2)
exec_results = run_plan(plan, backend)

for task, exec_result in zip(plan.tasks, exec_results.task_results):
    analysis = analyze_task_execution_result(task, exec_result)
    print(f"Protocol: {task.protocol}, Fidelity: {analysis.analysis_payload}")
```

### Persist to PostgreSQL

Requires PostgreSQL and `EGM_PG_DSN`; see [scripts/postgres/README.md](scripts/postgres/README.md).

```python
from egm.datastore.postgres_observation_store import PostgresObservationStore

store = PostgresObservationStore("postgresql://user@localhost:5432/egm_phase1")
obs_id = store.save_observation(payload)
```

---

## Supported Protocols

Naming reference for the **protocol framework**. **Status** is only defined in [Feature Status](#feature-status-v303).

### Physical Layer

| Protocol | Description |
|----------|-------------|
| **XEB** | Cross-Entropy Benchmarking (with simultaneous SPB) |
| **RB** | Standard Randomized Benchmarking |
| **IRB** | Interleaved RB (per-gate error extraction) |
| **MRB** | Mirror RB |
| **PRB** | Pauli RB |
| **CSB** | Channel Spectrum Benchmarking |
| **QV** | Quantum Volume |
| **SPB** | Speckle Purity Benchmarking |
| **T1/T2** | Coherence time measurement (Ramsey, Echo) |
| **Rabi** | Drive amplitude calibration |
| **SPAM** | State Preparation And Measurement errors |
| **Tomography** | State and process tomography |
| **Leakage RB** | Leakage detection via RB |
| **CLOPS** | Circuit Layer Operations Per Second |

### Algorithmic Layer

Grover, QPE, Shor, VQE, QAOA, QML, Digital Simulation

### Execution Modes

Each protocol supports three modes for flexible characterization:

- **standard** — Single qubit group
- **respectively** — Independent per-group (control variable isolation)
- **simultaneously** — Merged circuits across groups (crosstalk characterization)

---

## Database & Querying (Phase 1)

### Why PostgreSQL?

EGM uses PostgreSQL as the **reference store** for multi-entity calibration/benchmark facts, **bi-temporal** queries (`as_of` / `known-at`), and **lineage** between runs — not as a generic file dump. Lab-scale performance is documented in [postgres-benchmark-v0.1.md](docs/performance/postgres-benchmark-v0.1.md). SQLite/memory remain available for local tests.

EGM includes:

- **Bi-temporal schema** — Every fact has `effective_time` + `ingested_at`
- **Record kinds (v1.1)** — `observation` / `inference` / `forecast` on `observation_record` ([semantics](docs/data-layer/observation-inference-forecast.md))
- **Lineage tracking** — DAG tracing from derived artifacts to raw sources
- **31 SQL query templates** covering entity lookup, calibration facts, benchmark results, system state, and lineage traversal
- **Schema migrations** — `db/migrations/` ([policy](db/MIGRATION.md))
- **Idempotent ETL** for external calibration data (Quafu)

```
db/phase1/              # DDL + seed scripts
db/migrations/          # Forward schema migrations
docs/data-layer/        # Semantics and field dictionary
docs/performance/       # Benchmark reports
sql/queries/p0/         # 31 SQL templates (q01–q26)
scripts/ingest/         # ETL pipeline for Quafu calibration data
scripts/postgres/       # Database admin & demo notebooks
scripts/benchmark/      # Insert/query throughput harness
```

---

## Project Structure

```
errorgnomark/
├── src/egm/            # Core library (211 Python modules)
├── db/phase1/          # PostgreSQL schema & seed data
├── sql/queries/        # SQL query templates
├── scripts/
│   ├── ingest/         # ETL scripts
│   ├── postgres/       # Database utilities & demos
│   └── smoke/          # End-to-end smoke tests & demos
├── docs/               # Documentation hub (see docs/index.md)
├── .github/            # Workflows, issue/PR templates
├── pyproject.toml      # PEP 621 metadata
├── ROADMAP.md          # Public 3/6/12 month roadmap
├── CONTRIBUTING.md     # Contribution guide
├── LICENSE             # Apache-2.0
├── LICENSE-AUDIT.md    # License history & compliance
├── SECURITY.md         # Vulnerability reporting
├── CHANGELOG.md        # Release notes
└── README.md
```

---

## Documentation & Roadmap

- [Documentation hub](docs/index.md)
- [Getting started](docs/getting-started.md)
- [Protocol status](docs/protocol-status.md) (how to read [Feature Status](#feature-status-v303))
- [Validation summary](docs/validation/validation-summary.md)
- [Data layer](docs/data-layer/README.md)
- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Public API](docs/engineering/public-api.md)
- [CI / testing](docs/engineering/ci.md)
- [Open-source licenses explained](docs/legal/open-source-licenses.md)

---

## Contributing

Contributions are welcome. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, branching, and PR expectations.

Quick rules:

1. Code follows existing patterns (type hints, docstrings, Pydantic schemas)
2. New protocols implement the three-layer architecture (kernel → wrapper → orchestration)
3. Analysis modules register with `_TASK_ANALYZERS` in `analysis/__init__.py`
4. Run `ruff check src/egm/analysis src/egm/schemas tests` and `pytest tests/unit tests/integration tests/validation tests/smoke -q` before submitting (see [CI](docs/engineering/ci.md))

---

## License

[Apache License 2.0](LICENSE). See [LICENSE-AUDIT.md](LICENSE-AUDIT.md) for license metadata history.

---

## Links

- **GitHub (canonical)**: https://github.com/BAQIS-Quantum/ErrorGnoMark
- **Gitee (mirror)**: https://gitee.com/xdchai/errorgnomark
- **PyPI**: https://pypi.org/project/errorgnomark/

---

## Citation

If you use EGM in your research, please cite:

```bibtex
@software{egm2026,
  title  = {ErrorGnoMark: A Modular Platform for Quantum Hardware Benchmarking and Characterization},
  author = {Chai, Xudan},
  year   = {2026},
  url    = {https://github.com/BAQIS-Quantum/ErrorGnoMark},
}
```
