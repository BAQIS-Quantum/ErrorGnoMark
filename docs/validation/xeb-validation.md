# XEB validation report (v1)

**Status:** Synthetic validation **Passed** (2026-05-16)  
**Code:** `src/egm/analysis/xeb.py`  
**Tests:** `tests/validation/test_xeb_synthetic.py`

## Summary

Normalized cross-entropy benchmarking (XEB) fidelity in EGM matches closed-form expectations on constructed distributions and recovers exponential decay parameter `p` within tolerance on synthetic depth sweeps. This v1 report does **not** certify all backends or hardware paths.

## Theory (abbreviated)

- **Estimator:** \(F_{\mathrm{XEB}} = (\sum_x p_{\mathrm{ideal}}(x) p_{\mathrm{exp}}(x) - 2^{-n}) / (\sum_x p_{\mathrm{ideal}}(x)^2 - 2^{-n})\) implemented as `analyze_xeb_fidelity`.
- **Decay fit:** \(f(x) = A p^x + B\) via `fit_xeb_data` (RB-schema fields including `epc` derived from `p`).
- **Assumptions:** Ideal distribution known; sufficient shots; depth axis has ≥3 points for fit.
- **Failure modes:** `denom <= 0` → 0 fidelity; `<3` depths → fit unsuccessful; extreme noise breaks `curve_fit`.

## Test environment

| Item | Value |
|------|--------|
| Python | ≥3.9 |
| Package | `errorgnomark` editable / 3.0.3 |
| RNG seed | 42 (`tests/validation/conftest.py`) |

## Synthetic experiments

| Case | Description | Tolerance | Result |
|------|-------------|-----------|--------|
| **S1** | 1-qubit depolarizing mix; compare to hand-derived \(F\) | \|ΔF\| < 1e-3 | Pass |
| **S1b** | 2-qubit noiseless copy of ideal | F ≈ 1 | Pass |
| **S2** | Depth sweep A·p^m+B + Gaussian jitter; recover `p` | \|p_fit−p_true\| < 0.02 | Pass |
| **S3** | Multiple circuits per depth; SEM > 0 | SEM > 0 | Pass |
| **Fail** | Only 2 depths | fit unsuccessful | Pass (expected) |

Constants: `Fidelity_ABS_TOL`, `RB_P_ABS_TOL` in `tests/validation/conftest.py`.

## Known gaps

- No full Executor + `DummyBackendXEB` E2E in validation suite yet (smoke scripts separate).
- Bootstrap error bars not exhaustively regression-tested.
- Real hardware not used as ground truth.

## Reproduction

```bash
pip install -e ".[dev]"
pytest tests/validation/test_xeb_synthetic.py -v
```

## Appendix

- Tutorial: [docs/tutorials/xeb.ipynb](../tutorials/xeb.ipynb)
- Smoke: `scripts/smoke/` (engineering only)
