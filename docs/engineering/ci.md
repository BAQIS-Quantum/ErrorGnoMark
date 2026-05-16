# Continuous integration

## Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| **CI** | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) | `ruff`, `pytest` (unit/integration/validation/smoke), wheel build |
| **Phase 1 Postgres** | [`.github/workflows/phase1-postgres.yml`](../../.github/workflows/phase1-postgres.yml) | DDL, seed, P0 SQL acceptance |

Pull requests should pass **both** when touching data layer or PostgreSQL paths.

## Local commands

```bash
pip install -e ".[dev]"
ruff check src/egm/analysis src/egm/schemas tests
pytest tests/unit tests/integration tests/validation tests/smoke -q
pytest tests/ --cov=egm --cov-report=html
```

Postgres-marked tests (`pytest -m postgres`) are excluded from default runs; use when `EGM_PG_DSN` is set.
