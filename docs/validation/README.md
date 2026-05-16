# Validation Program (Horizon C)

This directory contains **scientific validation** artifacts for ErrorGnoMark benchmark protocols. Engineering smoke tests under `scripts/smoke/` prove workflows run; validation here proves analyzers match **known synthetic ground truth** within published tolerances.

## Principles

1. **README [Feature Status](../../README.md#feature-status-v302) is authoritative** for Beta / Experimental / Planned labels.
2. A protocol is **validation-backed Beta** only when:
   - A report exists in this directory;
   - `tests/validation/test_<protocol>_synthetic.py` passes;
   - A maintainer PR links the report from README Notes.
3. **At most 2–3 protocol status upgrades per quarter** (project roadmap policy).

## Workflow

1. Open a **Protocol validation request** issue (see [CONTRIBUTING.md](../../CONTRIBUTING.md)).
2. Implement or extend `tests/validation/`.
3. Write `docs/validation/<protocol>-validation.md`.
4. Update [validation-summary.md](./validation-summary.md) and README Notes.
5. Maintainer review (Athena) before claiming statistical certification.

## Contents

| Document | Description |
|----------|-------------|
| [validation-summary.md](./validation-summary.md) | One-page status table |
| [analyzer-output-spec.md](./analyzer-output-spec.md) | Required uncertainty fields |
| [xeb-validation.md](./xeb-validation.md) | XEB synthetic validation (v1) |
| [rb-validation.md](./rb-validation.md) | RB synthetic validation (v1) |

## Reproduce tests

```bash
pip install -e ".[dev]"
pytest tests/validation -q
```

Tolerances are defined in `tests/validation/conftest.py`.

## Scope limits

- Reports v1 cover **simulator/synthetic** ground truth only unless an appendix says otherwise.
- Real hardware (e.g. cloud QPUs) may appear as **appendix** evidence, not as formal ground truth.
