#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json"
errors = []
try:
    doc = json.loads(TRACE.read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"Traceability parse failed: {exc}")
requirements = doc.get("requirements", [])
ids = [item.get("id") for item in requirements]
expected = [f"REQ-{number:03d}" for number in range(1, 34)]
if ids != expected:
    errors.append(f"Requirement IDs must be ordered REQ-001..REQ-033, got {ids}")
for item in requirements:
    rid = item.get("id", "UNKNOWN")
    for field in ("origin", "decisionStatus", "designEvidence", "implementationEvidence", "automatedTests", "bundleModuleKeys", "coverage", "migrationDisposition", "openFindings"):
        if field not in item:
            errors.append(f"{rid}: missing {field}")
    for field in ("designEvidence", "implementationEvidence", "automatedTests"):
        refs = item.get(field) or []
        if not refs:
            errors.append(f"{rid}: empty {field}")
        for ref in refs:
            if not (ROOT / ref).exists():
                errors.append(f"{rid}: missing referenced file {ref}")
    coverage = item.get("coverage") or {}
    for dimension in ("design", "implementation", "automatedTest", "bundle", "realGitE2E", "crossHost"):
        if dimension not in coverage:
            errors.append(f"{rid}: missing coverage.{dimension}")
if errors:
    print("SAFOR traceability validation: FAIL")
    for error in errors:
        print("-", error)
    raise SystemExit(1)
print("SAFOR traceability validation: PASS (33/33 records structurally evidenced; E2E statuses remain explicit)")
