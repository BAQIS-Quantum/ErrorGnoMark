# GitHub repository setup (topics & badges)

Canonical repo: **https://github.com/BAQIS-Quantum/ErrorGnoMark**

---

## 1. Badges (README)

Badges are defined at the top of [README.md](../../README.md). They are **static images** from [shields.io](https://shields.io) or **GitHub Actions**; no extra service is required except:

| Badge | Source | Notes |
|-------|--------|--------|
| PyPI version | `img.shields.io/pypi/v/errorgnomark` | Updates when you publish to PyPI |
| Python versions | `img.shields.io/pypi/pyversions/errorgnomark` | From `pyproject.toml` classifiers |
| License | Static Apache-2.0 label | Must match [LICENSE](../../LICENSE) |
| CI | GitHub Actions workflow badge | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) |
| Tests | Same workflow, `label=tests` | Pytest runs inside CI job |
| Coverage | Static “CI term report” | Full **Codecov/Coveralls** badge needs extra setup (see below) |
| Docs | Link to [docs/index.md](../index.md) | Replace with Read the Docs URL if you add RTD later |

### Optional: live coverage badge (Codecov)

1. Sign in at [codecov.io](https://about.codecov.io/) with GitHub.
2. Add repository `BAQIS-Quantum/ErrorGnoMark`.
3. In CI, after pytest, upload:

```yaml
- uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage.xml
```

4. Generate `coverage.xml` in the pytest step: `--cov-report=xml`.
5. Replace the Coverage line in README with:

```markdown
[![Coverage](https://codecov.io/gh/BAQIS-Quantum/ErrorGnoMark/branch/main/graph/badge.svg)](https://codecov.io/gh/BAQIS-Quantum/ErrorGnoMark)
```

Until then, the grey “CI term report” badge is intentional (honest).

---

## 2. GitHub Topics

Topics improve **discoverability** on GitHub search. They are **repository metadata**, not files in the repo.

### Recommended topics

```
quantum-computing
quantum-benchmarking
quantum-error-characterization
randomized-benchmarking
cross-entropy-benchmarking
quantum-hardware
qec
calibration
qcvv
python
postgresql
```

### Method A — Web UI (no tools)

1. Open https://github.com/BAQIS-Quantum/ErrorGnoMark  
2. Click the **⚙️ gear** next to “About” (right sidebar on repo home).  
3. Under **Topics**, paste or add each topic (GitHub suggests normalized forms).  
4. Save.

### Method B — GitHub CLI (`gh`)

```bash
# Install: https://cli.github.com/  then: gh auth login
cd /path/to/errorgnomark
./scripts/dev/set_github_topics.sh
```

Or manually:

```bash
gh repo edit BAQIS-Quantum/ErrorGnoMark \
  --add-topic quantum-computing \
  --add-topic quantum-benchmarking \
  --add-topic quantum-error-characterization \
  --add-topic randomized-benchmarking \
  --add-topic cross-entropy-benchmarking \
  --add-topic quantum-hardware \
  --add-topic qec \
  --add-topic calibration \
  --add-topic qcvv \
  --add-topic python \
  --add-topic postgresql
```

### Method C — GitHub API

```bash
export GITHUB_TOKEN=ghp_...   # fine-grained or classic PAT with repo scope
curl -X PUT \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/BAQIS-Quantum/ErrorGnoMark/topics \
  -d '{"names":["quantum-computing","quantum-benchmarking","quantum-error-characterization","randomized-benchmarking","cross-entropy-benchmarking","quantum-hardware","qec","calibration","qcvv","python","postgresql"]}'
```

`PUT` **replaces** the full topic list; include every topic you want each time.

### Gitee

Gitee has a separate “标签/分类” UI on the project settings page. Mirror the same keywords there if you care about Gitee search (optional).

---

## 3. Repository “About” blurb (optional)

On the same About panel, set:

- **Description:** Modular quantum hardware benchmarking, QCVV, and Phase 1 data platform  
- **Website:** PyPI or docs link if you have one  
- **License:** Apache-2.0 (should match after you select license in Settings)

---

## 4. Checklist after setup

- [ ] Topics visible on repo home  
- [ ] README badges render (CI green on `main`)  
- [ ] PyPI badge shows `3.0.3+` after `twine upload`  
- [ ] License badge + GitHub license field = Apache-2.0  
