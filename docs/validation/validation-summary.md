# Validation summary

Last updated: **2026-05-16** · EGM version tested: **3.0.2** (see `egm.__version__`)

| Protocol | README status | Synthetic tests | Report | Synthetic status |
|----------|---------------|-----------------|--------|------------------|
| **XEB** | Beta | [test_xeb_synthetic.py](../../tests/validation/test_xeb_synthetic.py) | [xeb-validation.md](./xeb-validation.md) | **Passed** (v1) |
| **RB** | Beta | [test_rb_synthetic.py](../../tests/validation/test_rb_synthetic.py) | [rb-validation.md](./rb-validation.md) | **Passed** (v1) |
| IRB | Beta | — | — | Pending |
| MRB, PRB, CSB, SPB | Experimental | — | — | Pending |
| T1, T2, QV, … | Planned | — | — | N/A |

**Legend**

- **Passed (v1)** — synthetic scenarios in report match green `pytest tests/validation` for that protocol.
- **Pending** — not yet in scope for Horizon C batch 1.

Maintainer sign-off for external "statistically certified" wording: pending formal review; README Notes link reports for transparency.
