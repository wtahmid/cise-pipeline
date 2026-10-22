#!/usr/bin/env bash
# CISE — local dev harness for the non-container pipeline stages.
# Run from the repo root:
#   ./scripts/run_pipeline.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

APP="${1:-demo-app}"

echo "==> CISE local harness for: $APP"
echo "   (container stages skipped: need Docker / GitHub runner)"

# Tooling for the local stages
for t in bandit pip-audit cyclonedx-bom; do
  if ! command -v "$t" >/dev/null 2>&1; then
    echo "   installing $t ..."
    pip install "$t"
  fi
done

cd "$APP"

echo
echo "==> 1) bandit (SAST) — medium+"
bandit -r src --severity-level medium -f json -o bandit-report.json
bandit -r src --severity-level medium

echo
echo "==> 2) pip-audit (SCA)"
pip install -e ".[dev]" -q
pytest
pip-audit --skip-editable

echo
echo "==> 3) CycloneDX SBOM (environment)"
pip install cyclonedx-bom -q
cyclonedx-py environment --output-format json --output-file sbom.json
ls -1 sbom.json && echo "    SBOM written ($(wc -c < sbom.json) bytes)"

echo
echo "==> 4) Trivy filesystem (SARIF route 1: human-readable)"
# trivy fs is always a readable log here; SARIF is dumped below
trivy fs --format table --severity HIGH,CRITICAL .

echo
echo "==> 5) Trivy filesystem -> SARIF (for code-scanning UI)"
trivy fs --format sarif --output trivy-results.sarif --severity HIGH,CRITICAL .
echo "    SARIF written: trivy-results.sarif"

echo
echo "==> local stages complete"
