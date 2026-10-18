#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = [
    "SAFOR-FRAMEWORK.json",
    "SAFOR-FRAMEWORK-v0.14.0-rc.4.json",
    "SAFOR-FRAMEWORK-WEBSITE.json",
    "SAFOR-FRAMEWORK-SAAS.json",
    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
    "SAFOR-TEST-ACCESS-SAAS.json",
    "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: str, value) -> None:
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def artifact_records():
    records = []
    for path in ARTIFACTS:
        raw = (ROOT / path).read_bytes()
        records.append({
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        })
    return records


def write_checksums(records) -> None:
    lines = [f'{item["sha256"]}  {item["path"]}' for item in records]
    (ROOT / "SHA256SUMS-0.14.0-rc.4.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_release_notes() -> None:
    text = """# SAFOR 0.14.0-rc.4 Release Notes

## Purpose

This release candidate integrates the rc.3 review remediation and produces a reproducible rc.4 distribution without changing SAFOR's chat-first product boundary.

## Corrected contracts

- Legacy conformance assertions are explicitly superseded and active rules are scope-aware.
- REMOTE_GIT and LOCAL_GIT initialization are mutually exclusive; LOCAL_GIT does not require remote safor-memory.
- HUMAN response menus are derived from the platform response class; informational notices are menu-free.
- HUMAN-GO claim authority requires exact full-state provider readback, canonical digest equality and bound identity/job/chat/dispatch fields.
- BLOCKED agent output enforces a strict persistence XOR: persisted details reference or persistence-failure object, never both.
- VERSION, release facts, manifest, readiness and 33-requirement traceability are synchronized to rc.4.
- The historical safomwebsite migration remains legacy evidence; rc.4 candidate migration remains NOT_STARTED until isolated real-Git E2E passes.

## Distribution files

- `SAFOR-FRAMEWORK-v0.14.0-rc.4.json`
- `SAFOR-FRAMEWORK.json`
- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- `SAFOR-TEST-ACCESS-SAAS.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json`

## Evidence boundary

Automated source, schema, reproducibility and regression PASS does not constitute fresh-chat real-Git E2E, cross-host equivalence, rc.4 safomwebsite migration acceptance, empirical cognitive-load evidence, commercial GA or General Availability.
"""
    (ROOT / "RELEASE-NOTES-0.14.0-rc.4.md").write_text(text, encoding="utf-8")


def prepare(run_id: str, source_sha: str) -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if version != "0.14.0-rc.4":
        raise SystemExit(f"Expected 0.14.0-rc.4, got {version}")

    run("python", "tools/build_bundle.py")
    for profile in ("WEBSITE", "SAAS", "BOOK_CREATION"):
        run("python", "tools/build_domain_framework.py", "--profile", profile)

    current_versioned = f"SAFOR-FRAMEWORK-v{version}.json"
    for old_versioned in ROOT.glob("SAFOR-FRAMEWORK-v*.json"):
        if old_versioned.name != current_versioned:
            old_versioned.unlink()

    records = artifact_records()
    write_checksums(records)
    write_release_notes()

    evidence = {
        "format": "SAFOR_RELEASE_EVIDENCE",
        "schemaVersion": "0.14.0",
        "product": "SAFOR",
        "version": version,
        "status": "MATERIALIZED_VALIDATION_PENDING",
        "createdAt": now(),
        "sourceCommitBeforeMaterialization": source_sha,
        "integrationBranch": "safor/review-remediation-0.14.0-rc.4",
        "workflow": {
            "repository": "empishaj/SAFOR",
            "runId": str(run_id),
            "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
        },
        "validatedCommands": [],
        "artifacts": records,
        "truthBoundary": [
            "Automated PASS is not a fresh-chat real-Git E2E PASS.",
            "Provider claim semantics require actual host/provider CAS and full committed-state readback.",
            "JSON does not create provider permissions or force a non-conforming host.",
            "The rc.4 reference-project migration remains NOT_STARTED until isolated real-Git E2E passes.",
            "Cognitive-load reduction remains an empirical product claim requiring measurement.",
        ],
        "materializedAt": now(),
        "artifactCount": len(records),
        "checksumFile": "SHA256SUMS-0.14.0-rc.4.txt",
        "automatedValidationCompletedAt": None,
    }
    write_json("RELEASE-EVIDENCE-0.14.0-rc.4.json", evidence)


def finalize(run_id: str, source_sha: str) -> None:
    facts = load("RELEASE-FACTS.json")
    manifest = load("RELEASE-MANIFEST.json")
    trace = load("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
    evidence = load("RELEASE-EVIDENCE-0.14.0-rc.4.json")
    readiness_path = ROOT / "PRODUCT-READINESS.md"
    readiness = readiness_path.read_text(encoding="utf-8")

    facts["status"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    facts["releaseArtifacts"]["state"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    facts["releaseArtifacts"]["workflowRunId"] = str(run_id)
    facts["traceability"]["automatedTest"] = "PASS"
    facts["traceability"]["bundle"] = "PASS"
    manifest["releaseArtifactsState"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"

    for item in trace["requirements"]:
        item["coverage"]["automatedTest"] = "PASS"
        item["coverage"]["bundle"] = "PASS"
    trace["summary"]["automatedTestPendingUntilCI"] = 0
    trace["summary"]["bundlePendingUntilMaterialization"] = 0
    trace["summary"]["automatedTestPass"] = 33
    trace["summary"]["bundlePass"] = 33
    trace["ciEvidence"]["currentCandidate"] = {
        "releaseTarget": "0.14.0-rc.4",
        "repository": "empishaj/SAFOR",
        "workflowRunId": str(run_id),
        "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
        "sourceCommitBeforeMaterialization": source_sha,
        "status": "PASS_FOR_AUTOMATED_AND_BUNDLE_VALIDATION_ON_MATERIALIZED_WORKTREE",
    }

    pending_line = (
        "Materialization state: **PENDING WP-A7**. Source-contract remediation is validated, "
        "but rc.4 Framework artifacts, checksums and full release CI are not release evidence until WP-A7 completes."
    )
    final_line = (
        "Materialization state: **MATERIALIZED + AUTOMATED VALIDATION PASS**. "
        "The rc.4 Framework distributions and checksums are reproducible and automated validation is green; "
        "real-Git E2E, cross-host and migration acceptance remain separate open gates."
    )
    if pending_line in readiness:
        readiness = readiness.replace(pending_line, final_line)
    elif final_line not in readiness:
        readiness = readiness.replace(
            "Current target: **v0.14.0-rc.4**",
            "Current target: **v0.14.0-rc.4**\n\n" + final_line,
        )

    evidence["status"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    evidence["workflow"]["runId"] = str(run_id)
    evidence["sourceCommitBeforeMaterialization"] = source_sha
    evidence["validatedCommands"] = [
        "python tools/build_bundle.py --check",
        "python tools/build_domain_framework.py --check",
        "python tools/validate_safor.py",
        "python tools/validate_audit_remediation.py",
        "python tools/validate_release_facts.py",
        "python tools/validate_traceability.py",
        "python -m unittest discover -s tests -v",
        "sha256sum --check SHA256SUMS-0.14.0-rc.4.txt",
    ]
    evidence["automatedValidationCompletedAt"] = now()

    write_json("RELEASE-FACTS.json", facts)
    write_json("RELEASE-MANIFEST.json", manifest)
    write_json("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json", trace)
    write_json("RELEASE-EVIDENCE-0.14.0-rc.4.json", evidence)
    readiness_path.write_text(readiness, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    phase = parser.add_mutually_exclusive_group(required=True)
    phase.add_argument("--prepare", action="store_true")
    phase.add_argument("--finalize", action="store_true")
    parser.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID", "LOCAL"))
    parser.add_argument("--source-sha", default=os.environ.get("GITHUB_SHA", "LOCAL"))
    args = parser.parse_args()

    if args.prepare:
        prepare(args.workflow_run_id, args.source_sha)
    else:
        finalize(args.workflow_run_id, args.source_sha)


if __name__ == "__main__":
    main()
