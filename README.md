# ErrorGnoMark (EGM) v3

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
- **QEC-ready error budget** — Error source abstractions decoupled from physical gates, designed for fault-tolerant era

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
print(egm.__version__)  # 3.0.0
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
- **Lineage tracking** — DAG tracing from derived artifacts to raw sources
- **31 SQL query templates** covering entity lookup, calibration facts, benchmark results, system state, and lineage traversal
- **Idempotent ETL** for external calibration data (Quafu)

```
db/phase1/              # DDL + seed scripts
sql/queries/p0/         # 31 SQL templates (q01–q26)
scripts/ingest/         # ETL pipeline for Quafu calibration data
scripts/postgres/       # Database admin & demo notebooks
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
├── docs/               # Documentation
├── .github/workflows/  # CI/CD
├── pyproject.toml      # PEP 621 metadata
├── LICENSE             # Apache 2.0
└── README.md
```

---

## Contributing

Contributions are welcome. Please ensure:

1. Code follows existing patterns (type hints, docstrings, Pydantic schemas)
2. New protocols implement the three-layer architecture (kernel → wrapper → orchestration)
3. Analysis modules register with `_TASK_ANALYZERS` in `analysis/__init__.py`
4. Run `ruff check src/` and `black src/` before submitting

---

## License

[Apache License 2.0](LICENSE)

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
