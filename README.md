# ErrorGnoMark (EGM) v3.0.2

> A modular, full-stack platform for quantum hardware benchmarking, characterization, and lifecycle management.

[![PyPI Version](https://img.shields.io/pypi/v/errorgnomark.svg?style=flat-square)](https://pypi.org/project/errorgnomark/)
[![Python Version](https://img.shields.io/pypi/pyversions/errorgnomark.svg?style=flat-square)](https://pypi.org/project/errorgnomark/)
[![License](https://img.shields.io/github/license/BAQIS-Quantum/ErrorGnoMark.svg?style=flat-square)](LICENSE)

---

## What is EGM?

**ErrorGnoMark** combines *error* + *gno* (to know/diagnose) + *mark* (to benchmark). It is a comprehensive toolkit that covers the entire quantum characterization workflow — from circuit generation and execution, through protocol-specific analysis, to structured data persistence and temporal querying.

### Key Capabilities

- **20+ benchmark protocols** — XEB, RB, IRB, MRB, PRB, CSB, QV, SPB, T1/T2, Rabi, SPAM, process/state tomography, and more
- **Unified analysis dispatch** — One entry point routes to protocol-specific analyzers; adding a new protocol requires zero changes to upstream/downstream code
- **Backend-agnostic execution** — Run on simulators, cloud QPUs (Quafu, Quark), or direct hardware
- **Bi-temporal data layer** — Every observation carries both *effective time* (when it was true) and *ingestion time* (when the system learned it), enabling temporal replay and audit
- **Versioned hardware state** — Event-sourced state evolution with a DAG structure, supporting branching calibration strategies and rollback
- **Predictive intelligence** — Probabilistic future-state overlay for risk-aware compilation and scheduling
- **FTQC-oriented error abstractions** — Physical-layer error models structured so a future logical/QEC layer can plug in; **logical QEC benchmarks are not shipped** in this release (see Feature Status)

> **Scope honesty:** The table below is the authoritative status for the current release. Capabilities marked **Planned** or **Experimental** are not production-ready.

---

## Feature Status (v3.0.2)

| Area | Capability | Status | Notes |
|------|------------|--------|-------|
| Physical QCVV | XEB | **Beta** | Simulator smoke + analysis dispatch; synthetic validation [report](docs/validation/xeb-validation.md) |
| Physical QCVV | RB / IRB | **Beta** | RB: [validation report](docs/validation/rb-validation.md); IRB: validation pending |
| Physical QCVV | MRB, PRB, CSB, SPB | **Experimental** | Implementation present; full validation reports pending |
| Physical QCVV | T1, T2, QV, Rabi, SPAM, Leakage RB, CLOPS | **Planned** | Placeholder modules; not yet implemented |
| Data platform | Phase 1 PostgreSQL + static queries | **Beta** | Requires `EGM_PG_DSN`; see `db/phase1/`, `sql/queries/` |
| Data platform | Bi-temporal schema + lineage (DB) | **Beta** | Schema in `db/phase1/001_schema.sql` |
| Domain | Version DAG, event-sourced hardware state (`domain/system/`) | **Planned** | Architecture documented; runtime implementation incomplete |
| Intelligence | Predictive overlay (`intelligence/forecasting/`) | **Planned** | Design docs; not production-ready |
| Logical QEC | Surface code / decoder benchmarks | **Planned** | Design direction only; no Stim/PyMatching workflow or logical MVP in this release |
| Algorithmic | Grover, QPE, VQE, etc. | **Experimental** | Lower priority than physical QCVV |

**Status definitions:** **Beta** = runnable with documented examples; **Experimental** = partial code, limited validation; **Planned** = design or placeholder only.

---

## Known Limitations

- **Logical QEC benchmarks** are not production-ready in this release (no surface-code memory experiments, decoder integration, or logical error-rate pipeline).
- **「QEC-ready」/ FTQC-oriented** wording means extensible error and data design toward fault-tolerant computing — **not** a delivered logical-QEC product.
- XEB/RB have **synthetic** validation reports ([summary](docs/validation/validation-summary.md)); other protocols and full hardware certification are still limited.
- Task-level analysis payloads may not yet expose all fields in [analyzer-output-spec.md](docs/validation/analyzer-output-spec.md).
- **Predictive intelligence** and **versioned hardware state** modules may exist as design documentation without complete runtime code paths.
- **PostgreSQL** at web-scale is out of scope; lab-scale numbers are in [postgres-benchmark-v0.1.md](docs/performance/postgres-benchmark-v0.1.md).
- **Cloud/hardware backends** depend on third-party APIs, quotas, and credentials; availability is not guaranteed by this repository.
- License metadata was corrected in **v3.0.1**; see [LICENSE-AUDIT.md](LICENSE-AUDIT.md) if you relied on pre-3.0.1 PyPI classifiers.

---

## Use Cases

**Good fit**

- Research prototypes for quantum hardware characterization (QCVV)
- Teaching and reproducible demos with simulators (`scripts/smoke/`)
- Persisting calibration and benchmark observations in PostgreSQL (Phase 1)
- Building on a unified analysis entry point for new protocols

**Not a good fit (today)**

- Sole reliance for safety-critical or certified production control loops
- Expecting turnkey logical QEC benchmark + decoder integration
- Assuming every protocol listed in marketing copy is validated and stable

---

## Installation

```bash
pip install errorgnomark
```

Or install from source for development:

```bash
git clone https://gitee.com/xdchai/errorgnomark.git
cd errorgnomark
pip install -e ".[dev]"
```

Verify:

```python
import egm
print(egm.__version__)  # 3.0.2
```

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
│   └── logical/       #   QEC benchmarks (planned)
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
│   └── system/            # Version DAG, events, lifecycle
├── intelligence/      # Predictive forecasting, risk models, transition models
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

```python
from egm.datastore.postgres_observation_store import PostgresObservationStore

store = PostgresObservationStore("postgresql://user@localhost:5432/egm_phase1")
obs_id = store.save_observation(payload)
```

---

## Supported Protocols

### Physical Layer

| Protocol | Description |
|----------|-------------|
| **XEB** | Cross-Entropy Benchmarking (with simultaneous SPB) |
| **RB** | Standard Randomized Benchmarking |
| **IRB** | Interleaved RB (per-gate error extraction) |
| **MRB** | Mirror RB |
| **PRB** | Pauli RB |
| **CSB** | Correlated Spectral Benchmarking |
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

EGM includes a PostgreSQL-based data layer with:

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
├── LICENSE             # MIT
├── LICENSE-AUDIT.md    # License history & compliance
├── SECURITY.md         # Vulnerability reporting
├── CHANGELOG.md        # Release notes
└── README.md
```

---

## Documentation & Roadmap

- [Documentation hub](docs/index.md)
- [Getting started](docs/getting-started.md)
- [Protocol status](docs/protocol-status.md) (authoritative table: [Feature Status](#feature-status-v302) above)
- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Public API](docs/engineering/public-api.md)
- [CI / testing](docs/engineering/ci.md)

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

[MIT License](LICENSE). See [LICENSE-AUDIT.md](LICENSE-AUDIT.md) for license metadata history (v3.0.1 trust patch).

---

## Links

- **Gitee**: https://gitee.com/xdchai/errorgnomark
- **GitHub**: https://github.com/BAQIS-Quantum/ErrorGnoMark
- **PyPI**: https://pypi.org/project/errorgnomark/

---

## Citation

If you use EGM in your research, please cite:

```bibtex
@software{egm2026,
  title  = {ErrorGnoMark: A Modular Platform for Quantum Hardware Benchmarking and Characterization},
  author = {Chai, Xudan},
  year   = {2026},
  url    = {https://gitee.com/xdchai/errorgnomark},
}
```
