# Security policy

This repo is a **reference / development project**, not a production system.
Treat the findings from `ci.yml` as the source of truth for what your own
security posture should look like, and validate them against your own workload.

## Reporting a vulnerability

1. Open a **private security advisory** (GitHub `Security > Advisories > New draft
   advisory`) with the affected ref (`main`, a tag, or a commit SHA), the command
   you ran, and the full job log from the gated run.
2. Do **not** open a public issue for credential leaks, CVEs in base images, or
   accidental commits — the repo's `secrets-scan` stage already flags those.

## What the pipeline catches

| Stage | Tool | Result |
|---|---|---|
| Secrets | Gitleaks | hard-fail |
| SAST | bandit | hard-fail |
| SCA | pip-audit | hard-fail |
| Container CVE | Trivy | soft-fail by default (reported, not blocking) |
| SBOM | CycloneDX | evidence only |

## Supported & last scanned

- CI: Ubuntu 24.04 runners, Python 3.11 (3.12 supported via `python-version`).
- Local: `python -m venv` + `pip install -e ".[dev]"` + `pytest`.

See [`docs/quality-gates.md`](docs/quality-gates.md) for the pass/fail model.
