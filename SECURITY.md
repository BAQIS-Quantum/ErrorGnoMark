# Security Policy

## Supported versions

Security fixes are applied to the **latest release on the default branch** (`main`). Older tags may not receive backports unless explicitly announced.

| Version | Supported |
|---------|-----------|
| 3.0.1+  | Yes       |
| < 3.0.1 | No (upgrade recommended for license-metadata clarity; see [LICENSE-AUDIT.md](LICENSE-AUDIT.md)) |

## Reporting a vulnerability

If you believe you have found a security issue in ErrorGnoMark:

1. **Do not** open a public GitHub/Gitee issue with exploit details.
2. Email the maintainers at **chaixd@baqis.ac.cn** with:
   - A description of the issue and impact
   - Steps to reproduce (if applicable)
   - Affected version(s)
   - Your contact information (optional)

We will acknowledge receipt within a reasonable time and work with you on verification and remediation. We do not guarantee a fixed SLA.

## Scope

This policy covers the **errorgnomark** Python package and repository tooling. It does **not** cover third-party quantum cloud providers (e.g. Quafu, Quark) or user-managed PostgreSQL deployments—report those to the respective vendors/operators.
