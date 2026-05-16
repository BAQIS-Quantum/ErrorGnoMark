# Contributing to ErrorGnoMark

Thank you for your interest in EGM. This guide helps you set up a development environment, open issues, and submit pull requests.

**Before you start:** read [README.md](README.md) § **Feature Status** and **Known Limitations** so you know what is Beta, Experimental, or Planned.

---

## Development setup

### Clone

```bash
# Canonical repository (GitHub)
git clone https://github.com/BAQIS-Quantum/ErrorGnoMark.git
cd ErrorGnoMark

# China mirror (optional)
# git clone https://gitee.com/xdchai/errorgnomark.git
```

### Install (editable)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Requirements:** Python ≥ 3.9 (see [pyproject.toml](pyproject.toml)).

### Verify

```bash
python -c "import egm; print(egm.__version__)"
ruff check src/
```

### Required checks (Horizon D)

Pull requests must pass GitHub Actions **CI** (`.github/workflows/ci.yml`):

```bash
pip install -e ".[dev]"
ruff check src/egm/analysis src/egm/schemas tests
pytest tests/unit tests/integration tests/validation tests/smoke -q
```

Optional local coverage report:

```bash
pytest tests/ --cov=egm --cov-report=html
```

PostgreSQL workflows (`phase1-postgres.yml`) run separately; touch `db/phase1/` or datastore when relevant.

See [docs/engineering/ci.md](docs/engineering/ci.md).

---

## Repository layout

| Path | Purpose |
|------|---------|
| `src/egm/` | Library code (protocols, analysis, datastore, …) |
| `docs/` | Documentation hub — start at [docs/index.md](docs/index.md) |
| `scripts/smoke/` | End-to-end smoke demos (no real hardware required) |
| `scripts/postgres/` | Phase 1 PostgreSQL utilities |
| `db/phase1/` | Phase 1 DDL and seed |
| `sql/queries/` | Static query templates |

New protocols should follow the **three-layer** pattern (kernel → wrapper → orchestration) and register analyzers in `src/egm/analysis/__init__.py` (`_TASK_ANALYZERS`).

---

## Branching

- **`main`** — stable line; merge via reviewed PRs.
- **`develop`** / **`feature/*`** / **`exp/*`** — integration and experiments (when present).

Keep PRs **small and focused**. Prefer documentation-only PRs separate from behavior changes.

---

## Before you open a PR

1. **Style:** `ruff check src/` and `black src/` (if you format).
2. **Scope:** Do not change license metadata without updating [LICENSE-AUDIT.md](LICENSE-AUDIT.md).
3. **Protocols:** If capability changes, update README **Feature Status** or state explicitly in the PR why the table is unchanged.
4. **CHANGELOG:** For user-visible releases, add an entry under `[Unreleased]` or the target version in [CHANGELOG.md](CHANGELOG.md).
5. **Tests:** Add or update tests when changing behavior; note **N/A** in the PR template if docs-only.
6. **Security:** Do not file public issues for unpatched vulnerabilities — see [SECURITY.md](SECURITY.md).

---

## Pull request checklist

Use the [pull request template](.github/pull_request_template.md). At minimum:

- [ ] Summary and type of change
- [ ] `ruff check src/` passes (if code changed)
- [ ] CHANGELOG updated (if user-visible)
- [ ] README Feature Status updated (if protocol capability changed)
- [ ] No license/metadata conflict introduced

---

## Types of contributions

### Bug reports

Use the **Bug report** issue template. Include Python version, `egm.__version__`, steps to reproduce, and expected vs actual behavior.

### Protocol validation

Use the **Protocol validation request** template when asking for synthetic/ground-truth validation or reporting that a protocol should (not) be promoted to Beta. Status upgrades require merged validation artifacts (Horizon C), not issue comments alone.

### New protocols or backends

1. Open an issue describing scope, backends, and validation plan.
2. Implement with smoke/demo that runs **without** real hardware when possible (`DummyBackend*`, simulators).
3. Register analysis dispatch and document status in README.

### Data layer / PostgreSQL

- Set `EGM_PG_DSN` for local Postgres; see [scripts/postgres/README.md](scripts/postgres/README.md).
- Semantics: [docs/data-layer/](docs/data-layer/) (Observation / Inference / Forecast).
- Schema changes: add `db/migrations/NNNN_*.sql`, bump [db/schema_version.txt](db/schema_version.txt), document in [db/MIGRATION.md](db/MIGRATION.md).
- Performance baselines: [docs/performance/](docs/performance/).

---

## Documentation

- **Hub:** [docs/index.md](docs/index.md)
- **Getting started:** [docs/getting-started.md](docs/getting-started.md)
- **Protocol status:** [docs/protocol-status.md](docs/protocol-status.md) (links README authoritative table)
- **Roadmap:** [ROADMAP.md](ROADMAP.md)

---

## Releases and versioning

- **Semantic versioning** for the Python package (`pyproject.toml`, `src/egm/__init__.py`).
- **Trust/docs-only patches** (e.g. v3.0.1, v3.0.2): no intentional API changes; noted in CHANGELOG.
- Maintainers tag releases and push to Gitee/GitHub; PyPI publish is a separate maintainer step.

---

## License

By contributing, you agree that your contributions are licensed under the project’s [Apache License 2.0](LICENSE), consistent with [LICENSE-AUDIT.md](LICENSE-AUDIT.md).

---

## Communication

- Prefer **issues** for bugs and validation requests.
- For security issues, follow [SECURITY.md](SECURITY.md).
