# What blocks a merge, and what doesn't (and why)

This repo uses a small set of rules. The orchestrator `ci.yml` assembles four
reusable stages. Each stage is **hard-fail** or **soft-fail**; the `gate` job
blocks a merge only when a **hard-fail** stage fails.

## Hard-fail (blocks merge)

| Stage | Tool | Reason |
|---|---|---|
| Secrets | Gitleaks (full history) | A leaked credential is an active exploit path. Deleted later ≠ gone. |
| SAST | bandit `medium+` | Code flaws (pickle, YAML load, shell injection, hardcoded creds) are reproducible in prod. |
| SCA | pip-audit `medium+` | Vulnerable dependencies can be exploited today. |
| CVE | Trivy image, `CRITICAL,HIGH` | High/Critical OS or dependency CVEs in the built image are a public-facing risk. |

## Soft-fail (reported, does NOT block merge)

| Stage | Tool | Reason |
|---|---|---|
| Container CVE | Trivy image, everything else | Base-image OS-package CVEs (e.g. Debian `trixie`'s gzip, libacl1, ncurses, sqlite3, perl-base cluster) get new CVEs daily and often have **no fix published upstream**. Producing a clean run by chasing a `.trivyignore` is worse than documenting the accepted risk. Set `soft-fail: false` in `ci.yml` to make these hard-fail. |

## SBOM — evidence only

`reuse-sbom.yml` generates a CycloneDX SBOM from the real environment and
archives it as a 30-day artifact. **It does not gate anything.** The SBOM is
the record you consult next time a Log4Shell-scale advisory lands: "are we
affected?" you check the SBOM, not re-scan the world.

## SARIF — where findings live

Every stage that can emit SARIF uploads it to GitHub's code-scanning UI.
Findings are therefore:
- visible in the PR's "Files changed" security tab,
- aggregated across runs,
- not lost in job logs on a re-run.

## Local note

- `reuse-container-scan.yml` needs Docker + a GitHub-hosted runner (no Docker
  build is performed locally). Run the non-container stages locally via
  `scripts/run_pipeline.sh`.
- The demo app is stdlib-only (no third-party deps), so locally
  `bandit`/`pip-audit` are clean by design and the SBOM is empty-of-deps —
  a plain, honest baseline you can grow.
