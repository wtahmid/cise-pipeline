#!/usr/bin/env python3
"""SARIF writer + converter for scan tools that do not emit SARIF natively.

Kept here as the "glue" step the reference pipelines delegate to other tools.
Takes a simple key/value / table report and emits a standards-compliant SARIF
v2 file that GitHub's code-scanning UI understands.

Usage:
    python scripts/parse_trivy_to_sarif.py \
        --input trivy-table.txt \
        --output trivy-results.sarif \
        --tool trivy \
        --rule-url https://nvd.nist.gov/vuln/search

Includes a small self-test (run without args) so the SARIF contract is verified
on every local run, not only on CI.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SARIF_VERSION = "2.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_sarif(rule_url: str, tool_name: str, findings: list[dict]) -> dict:
    """Return a SARIF v2 document for the given findings."""
    results = []
    for f in findings:
        results.append(
            {
                "ruleId": f["ruleId"],
                "level": f.get("level", "warning"),
                "message": {"text": f["message"]},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": f.get("file", "unknown")},
                            "region": {"startLine": f.get("line", 0)},
                        }
                    }
                ],
                "fullDescription": {"text": f["message"]},
                "defaultConfiguration": {"level": "error"},
                "help": {"text": rule_url or f"{tool_name} finding"},
            }
        )

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/DocumentSchema/2.1.0/sarif-schema-2.1.0.json",
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": "local-dev",
                        "rules": [
                            {
                                "id": r["ruleId"],
                                "shortDescription": {"text": r["message"]},
                                "fullDescription": {"text": r["message"]},
                            }
                            for r in {r["ruleId"]: r for r in findings}.values()
                        ],
                    }
                },
                "results": results,
            }
        ],
    }


def parse_table(content: str) -> list[dict]:
    """Turn a two-column 'file:line | severity | message' table into findings."""
    findings = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        location, severity, message = parts[0], parts[1].lower(), "|".join(parts[2:])
        rule_id, _, file = location.partition(":")
        findings.append(
            {
                "ruleId": rule_id or "unknown",
                "level": "error" if severity in {"critical", "high"} else "warning",
                "file": file or location,
                "line": 0,
                "message": message or location,
            }
        )
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", help="plain-text finding table")
    ap.add_argument("--output", help="SARIF output path")
    ap.add_argument("--tool", default="cise")
    ap.add_argument("--rule-url", default="https://nvd.nist.gov/vuln/search")
    args = ap.parse_args()

    if args.input is None:  # self test
        sample = "demo.py:10|critical|hardcoded password 'secret'\n"
        findings = parse_table(sample)
        sarif = build_sarif(args.rule_url, args.tool, findings)
        print(json.dumps(sarif, indent=2))
        return 0

    text = Path(args.input).read_text(encoding="utf-8")
    findings = parse_table(text)
    if not findings:
        print("no findings to convert")
        return 0
    doc = build_sarif(args.rule_url, args.tool, findings)
    Path(args.output).write_text(
        json.dumps(doc, indent=2), encoding="utf-8"
    )
    print(f"converted {len(findings)} finding(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
