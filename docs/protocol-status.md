# Protocol and capability status

## Authoritative source

The **Feature Status** table in [README.md](../README.md#feature-status-v302) is the **single source of truth** for what is Beta, Experimental, or Planned in the current release.

This page explains how to read that table and how status changes are made. It does **not** duplicate the full matrix (to avoid drift).

---

## Status definitions

| Status | Meaning |
|--------|---------|
| **Beta** | Runnable with documented examples (README, smoke, or tutorials); validation reports may still be in progress |
| **Experimental** | Partial implementation or limited validation; API may change |
| **Planned** | Design, placeholder, or documentation only — not production-ready |

---

## Summary (current release)

High-level areas (see README for the full table):

| Area | Representative capabilities | Typical status |
|------|----------------------------|----------------|
| Physical QCVV | XEB, RB / IRB | Beta |
| Physical QCVV | MRB, PRB, CSB, SPB | Experimental |
| Physical QCVV | T1, T2, QV, Rabi, SPAM, … | Planned |
| Data platform | Phase 1 PostgreSQL, bi-temporal schema | Beta |
| Domain / intelligence | Version DAG, forecasting overlay | Planned |
| Logical QEC | Surface code, decoders | Planned |

---

## How status is upgraded

1. Open a **Protocol validation request** issue (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
2. Land synthetic or ground-truth validation artifacts under `docs/validation/<protocol>.md` (Horizon C).
3. Merge a PR that updates README **Feature Status** and [CHANGELOG.md](../CHANGELOG.md).
4. Maintainers review whether **Beta** is justified (uncertainty, failure modes documented).

**Status is not upgraded by roadmap items or issue comments alone.**

---

## Validation reports

| Protocol | Report | Synthetic tests |
|----------|--------|-------------------|
| XEB | [xeb-validation.md](validation/xeb-validation.md) | `pytest tests/validation/test_xeb_synthetic.py` |
| RB | [rb-validation.md](validation/rb-validation.md) | `pytest tests/validation/test_rb_synthetic.py` |

Summary: [validation/validation-summary.md](validation/validation-summary.md). IRB and other protocols: **Pending**.

See [Known Limitations](../README.md#known-limitations) for remaining statistical and hardware scope limits.
