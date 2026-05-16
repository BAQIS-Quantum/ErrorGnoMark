# ErrorGnoMark Documentation

Welcome to the EGM documentation hub. For the **authoritative protocol capability table**, see [README § Feature Status](../README.md#feature-status-v302).

---

## Start here

| Document | Description |
|----------|-------------|
| [Getting started](getting-started.md) | Install, verify, and run your first XEB demo |
| [Protocol status](protocol-status.md) | Status definitions and how capabilities are upgraded |
| [README](../README.md) | Project overview, architecture, Quick Start |

---

## Tutorials

| Notebook | Topic |
|----------|--------|
| [tutorials/xeb.ipynb](tutorials/xeb.ipynb) | Cross-entropy benchmarking |
| [tutorials/rb.ipynb](tutorials/rb.ipynb) | Randomized benchmarking |
| [tutorials/foundamental_elements.ipynb](tutorials/foundamental_elements.ipynb) | Fundamental elements |

---

## Architecture

Design and module boundaries (v3):

| Document | Topic |
|----------|--------|
| [architecture/system_overview.md](architecture/system_overview.md) | System overview |
| [architecture/core_design_principles.md](architecture/core_design_principles.md) | Core design principles |
| [architecture/module_dependency_rules.md](architecture/module_dependency_rules.md) | Module dependencies |
| [architecture/interface_stability_policy.md](architecture/interface_stability_policy.md) | Interface stability |
| [architecture/naming-and-boundaries.md](architecture/naming-and-boundaries.md) | Naming and boundaries |
| [architecture/experiment_event_version_model.md](architecture/experiment_event_version_model.md) | Experiment / version model |
| [architecture/development_model.md](architecture/development_model.md) | Development model |

---

## Data & operations

| Resource | Description |
|----------|-------------|
| [data-layer/README.md](data-layer/README.md) | Observation / Inference / Forecast semantics |
| [performance/README.md](performance/README.md) | PostgreSQL benchmark reports |
| [../scripts/postgres/README.md](../scripts/postgres/README.md) | PostgreSQL Phase 1 setup |
| [../db/phase1/](../db/phase1/) | Schema and seed SQL |
| [../db/MIGRATION.md](../db/MIGRATION.md) | Schema migration policy |
| [../scripts/smoke/](../scripts/smoke/) | Smoke tests and demos |

---

## Project

| Document | Description |
|----------|-------------|
| [../ROADMAP.md](../ROADMAP.md) | 3 / 6 / 12 month public roadmap |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | How to contribute |
| [engineering/public-api.md](engineering/public-api.md) | Python public API |
| [engineering/ci.md](engineering/ci.md) | CI workflows and local checks |
| [../CHANGELOG.md](../CHANGELOG.md) | Release history |
| [../SECURITY.md](../SECURITY.md) | Security reporting |
| [../LICENSE-AUDIT.md](../LICENSE-AUDIT.md) | License history |

---

## Validation

| Document | Description |
|----------|-------------|
| [validation/README.md](validation/README.md) | Validation Program charter |
| [validation/validation-summary.md](validation/validation-summary.md) | Protocol validation status |
| [validation/xeb-validation.md](validation/xeb-validation.md) | XEB synthetic validation (v1) |
| [validation/rb-validation.md](validation/rb-validation.md) | RB synthetic validation (v1) |

Run checks: `pytest tests/validation -q`
