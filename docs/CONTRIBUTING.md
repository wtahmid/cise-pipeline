# Contributing

This is a reference pipeline. Adding a stage or swapping a tool is the best way
to learn how composable GitHub Actions work.

## Local dev (no Docker)

```bash
cd demo-app
pip install -e ".[dev]"
scripts/run_pipeline.sh
```

This verifies `bandit`, `pip-audit`, the CycloneDX SBOM, and `trivy fs` (SARIF)
without Docker.

## Container stages

Trivy (image CVE scan) + Syft (image SBOM) run on GitHub-hosted Ubuntu runners
via `.github/workflows/reuse-container-scan.yml`. They also run as the
`Container Scan` job in the PR gate.

## Adding a stage

1. Add a reusable workflow under `.github/workflows/reuse-<name>.yml`. Export your
   inputs via `with:` keys and declare a `defaults:` block.
2. Reference it from `ci.yml` under a new job, and add the job name to the
   `needs:` list in the `gate` job.
3. Choose **hard-fail** (blocks merges) or **soft-fail** (reports only) per
   `docs/quality-gates.md` — never both for the same stage.
4. Reuse `./.github/actions/setup-python-cached/action.yml` for Python setup so
   the pip cache is keyed to `pyproject.toml`.

## Repository layout

```
.github/
├── actions/
│   └── setup-python-cached/action.yml
└── workflows/
    ├── ci.yml                  # orchestrator + gate job
    ├── reuse-secrets-scan.yml
    ├── reuse-sast-sca.yml
    ├── reuse-sbom.yml
    └── reuse-container-scan.yml
demo-app/                       # real app everything is scanned against
docs/
├── quality-gates.md            # pass/fail model
├── security.md                 # reporting policy
└── contributing.md             # this file
scripts/
├── run_pipeline.sh             # local (non-container) harness
└── parse_trivy_to_sarif.py     # SARIF writer for tools without it
```

## Notes

- Keep the demo app stdlib-only: it is the cleanest possible SBOM baseline.
- Do not chase `.trivyignore` to green a container CVE run; base-image CVEs are
  reported and documented instead (see `docs/quality-gates.md`).
