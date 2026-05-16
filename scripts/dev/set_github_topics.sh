#!/usr/bin/env bash
# Set GitHub repository topics for BAQIS-Quantum/ErrorGnoMark (requires gh CLI + auth).
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-BAQIS-Quantum/ErrorGnoMark}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: https://cli.github.com/" >&2
  echo "Or set topics manually: docs/engineering/github-repository.md" >&2
  exit 1
fi

TOPICS=(
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
)

args=()
for t in "${TOPICS[@]}"; do
  args+=(--add-topic "$t")
done

echo "Setting topics on $REPO ..."
gh repo edit "$REPO" "${args[@]}"
echo "Done. Verify at: https://github.com/$REPO"
