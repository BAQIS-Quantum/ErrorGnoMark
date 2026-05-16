# RB validation report (v1)

**Status:** Synthetic validation **Passed** (2026-05-16)  
**Code:** `src/egm/analysis/rb.py`  
**Tests:** `tests/validation/test_rb_synthetic.py`

## Summary

Standard Clifford RB analysis (`analyze_rb_standard` / `fit_rb_data`) recovers depolarizing survival parameter `p` and error-per-Clifford (EPC) within tolerance on synthetic decay curves. Interleaved RB (IRB) is **out of scope** for this v1 report.

## Theory (abbreviated)

- **Model:** \(P(m) = A p^m + B\) survival vs Clifford length `m`.
- **EPC:** \( \mathrm{EPC} = \frac{d-1}{d}(1-p) \) with \(d = 2^n\).
- **SPAM:** Absorbed in `A`, `B`; not separately identified in v1 tests.
- **Failure modes:** <3 depths; non-finite weights (e.g. zero std with single shot per depth); poor initial guess.

## Test environment

Same as [xeb-validation.md](./xeb-validation.md#test-environment).

## Synthetic experiments

| Case | Description | Tolerance | Result |
|------|-------------|-----------|--------|
| **R1** | Known A,p,B curve → `fit_rb_data` | \|p_fit−p_true\| < 0.02; EPC rel < 5% | Pass |
| **R1b** | Replicates per depth → `analyze_rb_standard` | p within tol; std_error > 0 | Pass |
| **R2** | 2-qubit `00` ground string + replicates | p within 0.03 | Pass |
| **Fail** | 2 depths only | fit unsuccessful | Pass (expected) |

## Known gaps

- `DummyBackend` depolarizing E2E not automated in `tests/validation` (future R2 extension).
- IRB / simultaneous RB not covered.
- Pulse-level errors not modeled.

## Reproduction

```bash
pip install -e ".[dev]"
pytest tests/validation/test_rb_synthetic.py -v
```

## Appendix

- Tutorial: [docs/tutorials/rb.ipynb](../tutorials/rb.ipynb)
- Smoke: `scripts/smoke/workflow_observation_e2e_smoke.py`
