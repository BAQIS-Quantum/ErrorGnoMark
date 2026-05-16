# License Audit — ErrorGnoMark

## Current effective license (since 2026-05-16 / v3.0.1)

| Field | Value |
|-------|--------|
| **SPDX** | `MIT` |
| **File** | [`LICENSE`](LICENSE) (repository root) |
| **Copyright** | Copyright (c) 2025-2026 Xudan Chai |

All project metadata (README, `pyproject.toml` classifiers, GitHub license detection) are aligned to **MIT** as of tag **v3.0.1**.

## Historical inconsistency (resolved in v3.0.1)

| Period | Issue |
|--------|--------|
| Through v3.0.0 | Root `LICENSE` contained **MIT** text, while `README.md` stated **Apache License 2.0** and `pyproject.toml` used the **Apache Software License** classifier. |
| Resolution | **Scheme M**: retain MIT in `LICENSE`; update README, `pyproject.toml`, and documentation to MIT. No relicensing of code was required because the authoritative file was already MIT. |

## PyPI / release artifacts

| Version | Notes |
|---------|--------|
| ≤ 3.0.0 | PyPI metadata may have listed Apache classifier while `LICENSE` was MIT; users should treat **v3.0.1+** as the corrected metadata baseline. |
| 3.0.1 | Trust & compliance release: license metadata alignment only (no functional API changes intended). |

## Third-party dependencies

Runtime dependencies are listed in [`pyproject.toml`](pyproject.toml). This audit does not replace a full SBOM or legal review of transitive licenses. For enterprise adoption, run your standard dependency license scan on the installed environment.

## Contact

License questions: project maintainers via repository issues or the email listed in `pyproject.toml` authors.
