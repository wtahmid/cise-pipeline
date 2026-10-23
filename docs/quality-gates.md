# CISE — pipeline gate policy

This repo uses four reusable stages composed by the orchestrator `ci.yml`.
The `gate` job blocks a merge **only** when a **hard-fail** stage fails.

## Hard-fail (blocks merge)

| Stage | Tool | Reason |
|---|---|---|
| Secrets | Gitleaks (full git history) | A leaked credential is an active exploit path. Deleted later ≠ gone. |
| SAST | bandit `medium+` | Code flaws (pickle, YAML load, shell injection, hardcoded creds) are reproducible in prod. |
| SCA | pip-audit `medium+` | Vulnerable dependencies can be exploited today. |

## Soft-fail (reported, does NOT block merge)

| Stage | Tool | Reason |
|---|---|---|
| Container CVE | Trivy image, `CRITICAL,HIGH` | Base-image OS packages (Debian `bookworm`) accumulate CVEs daily and often have **no upstream fix published**. Blocking a merge on an unfixable base CVE is worse than documenting the accepted risk — and the same CVE shows up in *every* consumer's image. Findings are still surfaced in GitHub code scanning (SARIF). Set `soft-fail: false` in `ci.yml` to force these hard-fail. |

## SBOM — evidence only

`reuse-sbom.yml` generates a CycloneDX SBOM from the real environment and archives it as a 30-day artifact. **It does not gate anything.** The SBOM is the record you consult next time a Log4Shell-scale advisory lands: "are we affected?" you check the SBOM, not re-scan the world.

## SARIF — where findings live

Every stage that can emit SARIF uploads it to GitHub's code-scanning UI. Findings are therefore:
- visible in the PR's "Files changed" security tab,
- aggregated across runs,
- not lost in job logs on a re-run.

## First-run observation (real CVEs caught)

On the initial PR run, the container CVE stage found **63 vulnerabilities in the demo image** (61 HIGH + 2 CRITICAL). These are distro-packaged OS libraries in `python:3.11-slim-bookworm`, not code in the demo app:

| CVE | Library | Severity | Fixed version |
|---|---|---|---|
| CVE-2026-53613 | bsdutils (util-linux) | HIGH | 2.38.1-5+deb12u4 |
| CVE-2026-78410 | libsqlite3-0 | HIGH | 3.40.1-2+deb12u3 |
| CVE-2025-7458 | libsqlite3-0 | CRITICAL | 3.40.1-2+deb12u3 |

The full list is reported in the PR's code-scanning SARIF tab. This is the pipeline working — see the SBOM artifact and the local harness.

## Local note

- `reuse-container-scan.yml` needs Docker + a GitHub-hosted runner (no Docker build is performed locally). Run the non-container stages locally via `scripts/run_pipeline.sh`.
- The demo app is stdlib-only (no third-party deps), so locally `bandit`/`pip-audit` are clean by design and the SBOM is empty-of-deps — a plain, honest baseline you can grow.
