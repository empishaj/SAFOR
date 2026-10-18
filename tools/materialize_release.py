#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def current_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def artifact_paths(version: str) -> list[str]:
    return [
        "SAFOR-FRAMEWORK.json",
        f"SAFOR-FRAMEWORK-v{version}.json",
        "SAFOR-FRAMEWORK-WEBSITE.json",
        "SAFOR-FRAMEWORK-SAAS.json",
        "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        "SAFOR-TEST-ACCESS-SAAS.json",
        "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
    ]


def evidence_path(version: str) -> str:
    return f"RELEASE-EVIDENCE-{version}.json"


def notes_path(version: str) -> str:
    return f"RELEASE-NOTES-{version}.md"


def checksum_path(version: str) -> str:
    return f"SHA256SUMS-{version}.txt"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: str, value) -> None:
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def artifact_records(version: str):
    records = []
    for path in artifact_paths(version):
        raw = (ROOT / path).read_bytes()
        records.append({
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        })
    return records


def write_checksums(records, version: str) -> None:
    lines = [f'{item["sha256"]}  {item["path"]}' for item in records]
    (ROOT / checksum_path(version)).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_release_notes(version: str) -> None:
    text = f"""# SAFOR {version} Release Notes

## Purpose

This release candidate makes the MASTER-to-subagent communication path operationally match the intended SAFOR model: MASTER writes the job into the assigned agent's personal Git INBOX and the initialized agent pulls that job after explicit HUMAN `GO`.

## Agent orchestration correction

- MASTER dispatches an immutable Agent Job to `agents/{{agentId}}/inbox/{{jobId}}.json` and updates `agents/{{agentId}}/inbox/index.json`.
- The job itself is never transported in the HUMAN `GO` message.
- After `GO`, the agent reads its pinned ACTIVE identity, its personal INBOX index, the selected authoritative Job JSON, MASTER job state and only the job-pinned inputs.
- Execution identity is proven from project, agentId, identityRevision, personal INBOX binding, Job assignment and dispatchRevision.
- Host-side `sessionId` or `chatBindingId` attestation is not required.
- Foreign INBOX, stale identityRevision, foreign Job assignment or stale dispatchRevision fail closed before claim.
- Git pushes, polling, inbox creation, automation, scheduler activity and background host events still never activate a normal chat agent.
- Provider compare-and-swap and exact provider readback remain mandatory for authoritative claim confirmation.
- Substantive Agent-to-MASTER communication remains typed and persisted in the Agent OUTBOX.

## Distribution files

- `SAFOR-FRAMEWORK-v{version}.json`
- `SAFOR-FRAMEWORK.json`
- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- `SAFOR-TEST-ACCESS-SAAS.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json`

## Evidence boundary

Automated source, schema, reproducibility and regression PASS proves the Framework contracts and reference runtime agree. It does not prove behavior of every external LLM host, provider permission, commercial production readiness, empirical cognitive-load impact or General Availability.
"""
    (ROOT / notes_path(version)).write_text(text, encoding="utf-8")


def prepare(run_id: str, source_sha: str) -> None:
    version = current_version()
    if not re.fullmatch(r"0\.14\.0-rc\.\d+", version):
        raise SystemExit(f"Unsupported release version: {version}")

    run("python", "tools/build_bundle.py")
    for profile in ("WEBSITE", "SAAS", "BOOK_CREATION"):
        run("python", "tools/build_domain_framework.py", "--profile", profile)

    current_versioned = f"SAFOR-FRAMEWORK-v{version}.json"
    for old_versioned in ROOT.glob("SAFOR-FRAMEWORK-v*.json"):
        if old_versioned.name != current_versioned:
            old_versioned.unlink()

    records = artifact_records(version)
    write_checksums(records, version)
    write_release_notes(version)

    evidence = {
        "format": "SAFOR_RELEASE_EVIDENCE",
        "schemaVersion": "0.14.0",
        "product": "SAFOR",
        "version": version,
        "status": "MATERIALIZED_VALIDATION_PENDING",
        "createdAt": now(),
        "sourceCommitBeforeMaterialization": source_sha,
        "integrationBranch": os.environ.get("GITHUB_REF_NAME", "LOCAL"),
        "workflow": {
            "repository": "empishaj/SAFOR",
            "runId": str(run_id),
            "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
        },
        "validatedCommands": [],
        "artifacts": records,
        "truthBoundary": [
            "Automated PASS is not proof of behavior on every external LLM host.",
            "Normal chat agents still require explicit HUMAN GO before pulling and claiming an INBOX job.",
            "Host sessionId/chatBindingId attestation is intentionally not required for normal chat-agent execution identity.",
            "Provider claim authority still requires actual compare-and-swap and exact provider readback.",
            "JSON does not create provider permissions or expand authority.",
        ],
        "materializedAt": now(),
        "artifactCount": len(records),
        "checksumFile": checksum_path(version),
        "automatedValidationCompletedAt": None,
    }
    write_json(evidence_path(version), evidence)


def finalize(run_id: str, source_sha: str) -> None:
    version = current_version()
    facts = load("RELEASE-FACTS.json")
    manifest = load("RELEASE-MANIFEST.json")
    trace = load("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
    evidence = load(evidence_path(version))
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
        "releaseTarget": version,
        "repository": "empishaj/SAFOR",
        "workflowRunId": str(run_id),
        "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
        "sourceCommitBeforeMaterialization": source_sha,
        "status": "PASS_FOR_AUTOMATED_AND_BUNDLE_VALIDATION_ON_MATERIALIZED_WORKTREE",
    }

    final_line = (
        "Materialization state: **MATERIALIZED + AUTOMATED VALIDATION PASS**. "
        f"The {version} Framework distributions and checksums are reproducible and automated validation is green."
    )
    readiness = re.sub(
        r"Materialization state: \*\*[^\n]+",
        final_line,
        readiness,
        count=1,
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
        f"sha256sum --check {checksum_path(version)}",
    ]
    evidence["automatedValidationCompletedAt"] = now()

    write_json("RELEASE-FACTS.json", facts)
    write_json("RELEASE-MANIFEST.json", manifest)
    write_json("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json", trace)
    write_json(evidence_path(version), evidence)
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
