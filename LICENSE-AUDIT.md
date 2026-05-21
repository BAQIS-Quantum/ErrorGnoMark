# License Audit — ErrorGnoMark

## Current effective license (since 2026-05-16 / v3.0.3)

| Field | Value |
|-------|--------|
| **SPDX** | `Apache-2.0` |
| **File** | [`LICENSE`](LICENSE) (repository root, Apache License 2.0 full text) |
| **Copyright** | Copyright 2025-2026 Xudan Chai |

All project metadata (README, `pyproject.toml` classifiers, license badge) are aligned to **Apache-2.0** as of tag **v3.0.3**.

**Rationale:** Apache-2.0 is commonly used for academic and enterprise adoption (explicit patent grant, NOTICE handling). Prior releases through v3.0.2 were distributed under **MIT** per [`LICENSE`](LICENSE) history below; v3.0.3 relicenses the project under Apache-2.0 with maintainer approval.

## Historical timeline

| Version | License | Issue / resolution |
|---------|---------|-------------------|
| ≤ 3.0.0 | `LICENSE` = MIT; README / PyPI said **Apache** | Metadata mismatch (trust risk). |
| 3.0.1 | **MIT** everywhere | Scheme M: align metadata to existing MIT `LICENSE` file. |
| 3.0.2 | **MIT** | Horizons B–E release; metadata consistent. |
| **3.0.3** | **Apache-2.0** | Replace `LICENSE` text; align README, `pyproject.toml`, CONTRIBUTING. |

## Checklist (must stay in sync)

| Location | Expected |
|----------|----------|
| `LICENSE` | Apache License 2.0 full text |
| `pyproject.toml` | `license = { file = "LICENSE" }`; classifier `Apache Software License` |
| `README.md` | Apache-2.0 badge, License section, project tree `LICENSE # Apache-2.0` |
| GitHub | Repository license field = Apache-2.0 (set on GitHub when publishing) |

## PyPI / release artifacts

| Version | Notes |
|---------|--------|
| ≤ 3.0.0 | May show Apache classifier while `LICENSE` was MIT — do not rely on metadata. |
| 3.0.1 – 3.0.2 | **MIT** on PyPI and in `LICENSE`. |
| **3.0.3+** | **Apache-2.0** baseline. |

## Third-party dependencies

Runtime dependencies are listed in [`pyproject.toml`](pyproject.toml). This audit does not replace a full SBOM or legal review of transitive licenses.

## Plain-language guide

For a non-legal overview of MIT vs Apache-2.0 vs GPL and why EGM uses Apache-2.0, see [docs/legal/open-source-licenses.md](docs/legal/open-source-licenses.md) (Chinese).

## Contact

License questions: project maintainers via GitHub issues or the email listed in `pyproject.toml` authors.
