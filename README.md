# CISE — CI/CD Security & SBOM Pipeline

A composable, GitHub-Actions–driven security gate for every pull request.
It runs four security stages per build and blocks the merge if anything
critical is found:

| Stage | Tool | What it catches |
|---|---|---|
| Secrets | [Gitleaks](https://github.com/gitleaks/gitleaks) | Accidentally committed tokens, API keys, passwords (full git history) |
| SAST + SCA | [bandit](https://bandit.readthedocs.io) + [pip-audit](https://pypi.org/project/pip-audit) | Python code flaws + vulnerable dependencies |
| SBOM | [CycloneDX](https://cyclonedx.org) (`cyclonedx-py`) | A machine-readable bill of materials — "what's *actually* in this environment?" |
|| Container | [Trivy](https://trivy.dev) + [Syft](https://github.com/aquasecurity/syft) | OS-package & dependency CVEs in the built image, plus an image SBOM. Container CVE is **soft-fail** by default (see docs) — findings still upload as SARIF to code scanning. |

**Design principles** (sourced from leading public DevSecOps repos):

1. **Reusable & composable.** Nine small reusable workflows + one orchestrator
   is a common, hard-to-maintain pattern; this project uses **four small
   reusable workflows + one orchestrator**, so each stage is independently
   testable and consumers can toggle stages on/off.
2. **SBOM never gates the build.** An SBOM is evidence to keep, not a
   pass/fail signal — generate it and archive it every time.
3. **Hard-fail where it matters** (secrets, SAST, CVE HIGH+), **soft-fail
   where it doesn't** (base-image OS CVEs with no fix upstream) — see
   `docs/quality-gates.md`.
4. **SARIF everywhere.** Every scan that supports it uploads SARIF to
   GitHub's code-scanning UI so findings live in the repo instead of burying
   job logs.
5. **A real, minimal demo app** (`demo-app/`) is bundled so every stage runs
   against something genuine, not a placeholder.

---

![CI/CD Security & SBOM Gate](https://github.com/wtahmid/cise-pipeline/actions/workflow/ci.yml/badge?branch=main&event=pull_request)

## Quick start — add it to your repo

```bash
# In your service repo, copy the pipeline in (customise working-directory)
mkdir -p .github/workflows
cp -r cise/.github/workflows .github/
# add the required demo-app dir (see below) or point dockerfile-directory at yours
```

A consuming repo's `ci.yml` (one file, ~20 lines):

```yaml
name: Security Gate

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  secrets-scan:
    uses: ./.github/workflows/reuse-secrets-scan.yml

  sast-sca:
    uses: ./.github/workflows/reuse-sast-sca.yml
    with:
      working-directory: ./demo-app
      python-version: "3.11"

  sbom:
    uses: ./.github/workflows/reuse-sbom.yml
    with:
      working-directory: ./demo-app
      python-version: "3.11"

  container-scan:
    uses: ./.github/workflows/reuse-container-scan.yml
    with:
      dockerfile-directory: ./demo-app
      image-tag: demo-app:${{ github.sha }}
      fail-on-severity: "CRITICAL,HIGH"
    permissions:
      contents: read
      security-events: write

  gate:
    name: Security Gate
    runs-on: ubuntu-latest
    needs: [secrets-scan, sast-sca, sbom, container-scan]
    if: always()
    steps:
      - name: Fail on any stage failure
        run: |
          if [[ "${{ contains(needs.*.result, 'failure') }}" == "true" ]]; then
            echo "One or more security stages failed."
            exit 1
          fi
          echo "All CISE stages passed."
```

---

## Local development

The CI stages that do not require Docker are verified locally (see
`scripts/run_pipeline.sh`):

```bash
cd demo-app
pip install -e ".[dev]"
scripts/run_pipeline.sh       # bandit, pip-audit, cyclonedx SBOM, trivy fs (SARIF)
```

The container stages (Trivy image + Syft SBOM) run on GitHub-hosted
ubuntu-latest runners in `.github/workflows/reuse-container-scan.yml`. To run
the whole gate locally you need Docker + act, or push to GitHub and watch the
Actions run.

---

## Repository layout

```
cise/
├── .github/
│   ├── actions/
│   │   └── setup-python-cached/action.yml        # composite: python + pip cache
│   └── workflows/
│       ├── ci.yml                                # orchestrator + gate job
│       ├── reuse-secrets-scan.yml                # Gitleaks
│       ├── reuse-sast-sca.yml                    # bandit + pip-audit
│       ├── reuse-sbom.yml                        # CycloneDX SBOM (env)
│       └── reuse-container-scan.yml              # Trivy + Syft
├── demo-app/                                     # the real app everything is scanned against
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/demo_app/
├── docs/quality-gates.md                         # what blocks vs soft-fails
└── scripts/
    ├── run_pipeline.sh                           # local harness
    └── parse_trivy_to_sarif.py                   # SARIF writer for tools without it
```

---

## Contributing

No Docker is needed for the code stages — `scripts/run_pipeline.sh` verifies
`bandit`, `pip-audit`, the CycloneDX SBOM, and `trivy fs` (SARIF) locally. The
container stages (Trivy image + Syft SBOM) run on GitHub-hosted runners.

1. Add a stage as a reusable workflow under `.github/workflows/reuse-<name>.yml`.
2. Wire it into the `ci.yml` orchestrator (add the new job name to `needs:`).
3. Keep the demo app stdlib-only — the cleanest possible SBOM baseline.
4. See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md),
   [`docs/SECURITY.md`](docs/SECURITY.md), and
   [`docs/quality-gates.md`](docs/quality-gates.md) for the full policy.

## What this repo is / is not

- **It is** a reusable security gate you can drop into any Python service repo.
- **It is** a learning/reference project: its own `ci.yml` is the same call a
  consumer makes (dogfooding), so the whole pipeline is continuously verified.
- **It is not** a production-grade policy framework, a secrets manager, or a
  runtime WAF. Those belong to the workload's own infrastructure.
