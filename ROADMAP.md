# ErrorGnoMark Roadmap

> Living document. Last updated: 2026-05-16. For issue-level tracking, use GitHub or Gitee issues.

## Vision

ErrorGnoMark (EGM) is a **physical-layer QCVV and data-platform** toolkit today: unified analysis dispatch, structured observations, and Phase 1 PostgreSQL workflows. **Logical QEC** benchmarks and production-grade predictive overlays are **planned**, not current core deliverables. See [README.md](README.md) § Feature Status for the authoritative capability table.

---

## Completed

- **v3.0.1 (2026-05-16)** — Trust & compliance (Horizon A): MIT license alignment across `LICENSE`, README, and PyPI metadata; Feature Status; Known Limitations; `LICENSE-AUDIT.md`; `SECURITY.md`. No intentional functional API changes.
- **v3.0.2 (2026-05-16)** — Project hygiene (Horizon B): this roadmap, [CONTRIBUTING.md](CONTRIBUTING.md), documentation hub under `docs/`, GitHub issue/PR templates. Documentation and community files only.

---

## Now (0–3 months)

- [x] Project hygiene: `CONTRIBUTING.md`, issue/PR templates, `docs/index.md` hub (Horizon B)
- [x] Validation program (XEB, RB) v1: `docs/validation/` reports + `tests/validation/` (Horizon C batch 1)
- [ ] Validation program v2: IRB, hardware appendix (Horizon C)
- [x] Engineering baseline v1: `ci.yml` with `ruff` + `pytest` (Horizon D-v1)
- [ ] Engineering v2: coverage `fail_under` 50%, Python version matrix (Horizon D-v2)

---

## Next (3–6 months)

- [ ] Protocol status upgrades **only** with merged validation reports and PR updates to README Feature Status
- [ ] Phase 1 schema migrations and performance baseline documentation (Horizon E)
- [ ] Public API stability table for analysis dispatch and core datastore entry points

---

## Later (6–12 months)

- [ ] Logical QEC: RFC and data model before implementation (Horizon F)
- [ ] Decoder workflow adapters (e.g. Stim / PyMatching-oriented workflows), not an in-house decoder core
- [ ] Community governance, extended CI matrix, and ecosystem hardening (Horizon G)

---

## Non-goals (current release)

- A turnkey **logical QEC production platform** in the near term
- Claiming every protocol listed in marketing copy is **statistically validated**
- Pulse-level or cycle-level QEC execution guarantees on all backends
- Mass protocol promotion without validation reports (at most **2–3 protocol status upgrades per quarter**)

---

## How to propose changes

- **Roadmap feedback**: open a documentation issue or discuss via [CONTRIBUTING.md](CONTRIBUTING.md).
- **Protocol validation**: use the **Protocol validation request** issue template.
- **New features**: align with [ROADMAP.md](ROADMAP.md) non-goals before large PRs; prefer small, reviewable changes.

---

## Internal planning

Engineering horizons (A–G) are tracked in the project’s internal technical planning notes. This public roadmap is a **summary** for external readers and may lag internal drafts by one revision cycle.
