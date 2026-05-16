# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[3.0.1]: https://github.com/BAQIS-Quantum/ErrorGnoMark/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/BAQIS-Quantum/ErrorGnoMark/releases/tag/v3.0.0
