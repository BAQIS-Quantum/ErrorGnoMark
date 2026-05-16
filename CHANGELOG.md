# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.2] - 2026-05-16

### Added (Horizon B — Documentation & Community)

- `ROADMAP.md` with completed milestones and 0–3 / 3–6 / 6–12 month plans.
- `CONTRIBUTING.md` and GitHub issue templates (bug report, protocol validation) plus PR template.
- Documentation hub: `docs/index.md`, `docs/getting-started.md`, `docs/protocol-status.md`.
- `docs/roadmap/README.md` pointing readers to the public root roadmap.

### Added (Horizon C — Validation Program v1)

- `docs/validation/` — XEB and RB synthetic validation reports, summary, analyzer output spec.
- `tests/validation/` — synthetic ground-truth tests for XEB and RB (`pytest`).

### Added (Horizon D — Engineering quality v1)

- `.github/workflows/ci.yml` — `ruff`, `pytest` (unit/integration/validation/smoke), wheel build.
- Test layout: `tests/unit/`, `tests/integration/`, `tests/smoke/`, `tests/fixtures/`.
- `docs/engineering/public-api.md`, `docs/engineering/ci.md`.
- `[tool.ruff]` and `[tool.coverage]` configuration in `pyproject.toml`.

### Added (Horizon E — Data layer hardening)

- `docs/data-layer/` — Observation / Inference / Forecast semantics and `observation_record` field dictionary.
- `db/migrations/` — `0001` registry, `0002` `record_kind` + forecast metadata (`phase1_v1.1`).
- `db/MIGRATION.md`, `scripts/postgres/apply_migrations.py`; `apply_phase1.sh` applies migrations.
- `docs/performance/` — PostgreSQL benchmark v0.1 report and reproduction guide.
- `scripts/benchmark/` — bulk insert and query latency harnesses.
- `sql/queries/README.md` — schema version mapping for P0 templates.

### Changed

- README: Feature Status, Known Limitations, FTQC-oriented wording; logical QEC remains **Planned**.
- README links to validation reports for XEB/RB and data-layer / performance docs.
- CONTRIBUTING and PR template require CI checks locally.
- `PostgresObservationStore` writes `record_kind` (default `observation`) and forecast columns when set.
- `verify_seed_counts.py` aligned with Phase 1 seed 050 (Baihua bootstrap).
- Removed internal-only path references from public docs and smoke notebook.

### Notes

- Logical QEC implementation is **not** included; see README Feature Status.
- Prefer running `pytest tests/validation` and `phase1_acceptance --strict` before release tagging.

## [3.0.1] - 2026-05-16

### Fixed (Trust & Compliance — Horizon A)

- Align license metadata to **MIT** across `LICENSE`, `README.md`, and `pyproject.toml` (Scheme M).
- Correct misleading Apache 2.0 references in README and PyPI classifiers.

### Added

- `LICENSE-AUDIT.md` — license history and resolution record.
- `SECURITY.md` — vulnerability reporting process.
- `CHANGELOG.md` — version history (this file).
- README sections: **Feature Status**, **Known Limitations**, **Use cases**.

### Notes

- **No intentional functional or API changes** in this release; documentation and compliance only.
- See [LICENSE-AUDIT.md](LICENSE-AUDIT.md) for details on prior license metadata inconsistency.

## [3.0.0] - 2026-05

### Added

- EGM v3 public release: modular architecture (circuits, protocols, execution, analysis, datastore, domain, intelligence, suites, reporting).
- Phase 1 PostgreSQL schema, observation store, and static query templates.
- Unified analysis dispatch (`analyze_task_execution_result`).
- Physical-layer protocols including XEB, RB, and related analyzers; smoke demos under `scripts/smoke/`.

[3.0.2]: https://github.com/BAQIS-Quantum/ErrorGnoMark/compare/v3.0.1...v3.0.2
[3.0.1]: https://github.com/BAQIS-Quantum/ErrorGnoMark/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/BAQIS-Quantum/ErrorGnoMark/releases/tag/v3.0.0
