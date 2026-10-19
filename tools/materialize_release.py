#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from release_provenance import (
    ReleaseProvenanceError,
    artifact_set_digest,
    sha256_bytes,
    sha256_file,
    validate_release_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "empishaj/SAFOR"
CONTRACT_REF = "docs/releases/RELEASE-EVIDENCE-CONTRACT-v1.json"


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
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: str, value) -> None:
    (ROOT / path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run(*args: str) -> None:
    subprocess.run(list(args), cwd=ROOT, check=True)


def git_value(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
    ).strip()


def resolve_source_identity(source_sha: str | None) -> tuple[str, str, str]:
    local_head = git_value("rev-parse", "HEAD")
    local_tree = git_value("rev-parse", "HEAD^{tree}")
    requested = (source_sha or os.environ.get("GITHUB_SHA") or local_head).strip()
    workflow_head = (os.environ.get("SAFOR_WORKFLOW_HEAD_SHA") or os.environ.get("GITHUB_SHA") or requested).strip()

    if requested != local_head:
        raise SystemExit(
            "RELEASE_SOURCE_HEAD_DRIFT: --source-sha/GITHUB_SHA must equal checked-out HEAD"
        )
    if workflow_head != requested:
        raise SystemExit(
            "RELEASE_WORKFLOW_HEAD_SOURCE_DRIFT: GITHUB_SHA differs from release source SHA"
        )
    return requested, local_tree, workflow_head


def artifact_records(version: str, source_sha: str):
    records = []
    for path in artifact_paths(version):
        raw = (ROOT / path).read_bytes()
        records.append(
            {
                "path": path,
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
                "generatedFromSourceCommit": source_sha,
            }
        )
    return records


def write_checksums(records, version: str) -> None:
    lines = [f'{item["sha256"]}  {item["path"]}' for item in records]
    (ROOT / checksum_path(version)).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_release_notes(version: str) -> None:
    text = f"""# SAFOR {version} Release Notes

## Purpose

This release candidate is the Operational Readiness candidate for the frozen
HUMAN → MASTER → Git INBOX → HUMAN GO → subagent operating model.

## Operating target

- The HUMAN uploads one applicable Domain Framework JSON into the MASTER chat.
- MASTER remains the only normal domain-facing HUMAN interface.
- Each normal subagent receives one identity/bootstrap initialization prompt.
- Later Agent Jobs are transported only through the Agent's personal Git INBOX.
- HUMAN `GO` is the exclusive normal activation signal and carries no Job payload.
- The Agent claims only through provider-confirmed CAS/readback of its own
  `agents/{{agentId}}/state.json`.
- `master/jobs/{{jobId}}.json` remains MASTER-owned and read-only to the Agent.
- Substantive Agent-to-MASTER communication uses typed Git responses.

## Release-integrity correction

- Release Evidence is bound to one exact source commit and source tree.
- The workflow head SHA must equal the release source SHA during materialization.
- Every distributable records its generating source commit.
- One canonical artifact-set digest binds all distributables.
- The checksum file is itself SHA-256 bound in Release Evidence.
- Final PASS requires a second exact-artifact verification after all automated
  checks complete.
- A prior workflow run, stale source SHA, changed artifact, changed checksum file,
  or mismatched validation run fails closed.

## Distribution files

- `SAFOR-FRAMEWORK-v{version}.json`
- `SAFOR-FRAMEWORK.json`
- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- `SAFOR-TEST-ACCESS-SAAS.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json`

## Evidence boundary

Automated source, schema, reproducibility and regression PASS proves only the
validated exact source/artifact set. It does not prove every external LLM host,
provider permission, commercial production readiness, empirical cognitive-load
impact or General Availability.
"""
    (ROOT / notes_path(version)).write_text(text, encoding="utf-8")


def prepare(run_id: str, source_sha: str | None) -> None:
    version = current_version()
    if not re.fullmatch(r"0\.14\.0-rc\.\d+", version):
        raise SystemExit(f"Unsupported release version: {version}")

    source_sha, source_tree_sha, workflow_head_sha = resolve_source_identity(source_sha)

    run("python", "tools/build_bundle.py")
    for profile in ("WEBSITE", "SAAS", "BOOK_CREATION"):
        run("python", "tools/build_domain_framework.py", "--profile", profile)

    current_versioned = f"SAFOR-FRAMEWORK-v{version}.json"
    for old_versioned in ROOT.glob("SAFOR-FRAMEWORK-v*.json"):
        if old_versioned.name != current_versioned:
            old_versioned.unlink()

    current_release_metadata = {
        evidence_path(version),
        notes_path(version),
        checksum_path(version),
    }
    for pattern in (
        "RELEASE-EVIDENCE-*.json",
        "RELEASE-NOTES-*.md",
        "SHA256SUMS-*.txt",
    ):
        for old_release_file in ROOT.glob(pattern):
            if old_release_file.name not in current_release_metadata:
                old_release_file.unlink()

    records = artifact_records(version, source_sha)
    write_checksums(records, version)
    write_release_notes(version)

    checksum_digest = sha256_file(ROOT / checksum_path(version))
    set_digest = artifact_set_digest(records)
    workflow_run_id = str(run_id or os.environ.get("GITHUB_RUN_ID") or "LOCAL")
    workflow_attempt = str(os.environ.get("GITHUB_RUN_ATTEMPT", "1"))

    evidence = {
        "format": "SAFOR_RELEASE_EVIDENCE",
        "schemaVersion": "0.14.0",
        "contractVersion": "1.0",
        "contractRef": CONTRACT_REF,
        "product": "SAFOR",
        "version": version,
        "status": "MATERIALIZED_VALIDATION_PENDING",
        "createdAt": now(),
        "provenance": {
            "repository": REPOSITORY,
            "sourceCommitSha": source_sha,
            "sourceTreeSha": source_tree_sha,
            "workflowHeadSha": workflow_head_sha,
            "workflowRunId": workflow_run_id,
            "workflowRunAttempt": workflow_attempt,
            "integrationRef": os.environ.get("GITHUB_REF_NAME", "LOCAL"),
            "exactHeadRequired": True,
        },
        "validatedCommands": [],
        "artifacts": records,
        "artifactSetDigest": set_digest,
        "truthBoundary": [
            "Automated PASS is not proof of behavior on every external LLM host.",
            "Normal chat agents still require explicit HUMAN GO before pulling and claiming an INBOX job.",
            "Provider claim authority still requires actual compare-and-swap and exact provider readback.",
            "JSON does not create provider permissions or expand authority.",
            "Release PASS is valid only for the exact source commit and artifact set bound here.",
        ],
        "materializedAt": now(),
        "artifactCount": len(records),
        "checksumFile": checksum_path(version),
        "checksumFileSha256": checksum_digest,
        "validation": {
            "status": "PENDING",
            "validationSourceCommitSha": None,
            "validationWorkflowHeadSha": None,
            "validationWorkflowRunId": None,
            "validatedArtifactSetDigest": None,
            "validatedChecksumFileSha256": None,
            "validatedAt": None,
        },
    }
    write_json(evidence_path(version), evidence)


def finalize(run_id: str, source_sha: str | None) -> None:
    version = current_version()
    source_sha, _source_tree_sha, workflow_head_sha = resolve_source_identity(source_sha)
    workflow_run_id = str(run_id or os.environ.get("GITHUB_RUN_ID") or "LOCAL")
    if workflow_run_id == "LOCAL":
        raise SystemExit("RELEASE_PASS_REQUIRES_NON_LOCAL_WORKFLOW_RUN")

    facts = load("RELEASE-FACTS.json")
    manifest = load("RELEASE-MANIFEST.json")
    trace = load(
        "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json"
    )
    evidence = load(evidence_path(version))
    readiness_path = ROOT / "PRODUCT-READINESS.md"
    readiness = readiness_path.read_text(encoding="utf-8")

    provenance = evidence.get("provenance", {})
    if provenance.get("sourceCommitSha") != source_sha:
        raise SystemExit("RELEASE_FINALIZE_SOURCE_COMMIT_DRIFT")
    if provenance.get("workflowHeadSha") != workflow_head_sha:
        raise SystemExit("RELEASE_FINALIZE_WORKFLOW_HEAD_DRIFT")
    if provenance.get("workflowRunId") != workflow_run_id:
        raise SystemExit("RELEASE_FINALIZE_WORKFLOW_RUN_DRIFT")

    records = artifact_records(version, source_sha)
    if records != evidence.get("artifacts"):
        raise SystemExit("RELEASE_ARTIFACTS_CHANGED_AFTER_PREPARE")
    set_digest = artifact_set_digest(records)
    if evidence.get("artifactSetDigest") != set_digest:
        raise SystemExit("RELEASE_ARTIFACT_SET_CHANGED_AFTER_PREPARE")
    checksum_digest = sha256_file(ROOT / checksum_path(version))
    if evidence.get("checksumFileSha256") != checksum_digest:
        raise SystemExit("RELEASE_CHECKSUM_FILE_CHANGED_AFTER_PREPARE")

    evidence["status"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    evidence["validatedCommands"] = [
        "python tools/build_bundle.py --check",
        "python tools/build_domain_framework.py --check",
        "python tools/validate_safor.py",
        "python tools/validate_audit_remediation.py",
        "python tools/validate_release_facts.py",
        "python tools/validate_traceability.py",
        "python tools/validate_content_consistency.py",
        "python -m unittest discover -s tests -v",
        f"sha256sum --check {checksum_path(version)}",
    ]
    evidence["validation"] = {
        "status": "PASS",
        "validationSourceCommitSha": source_sha,
        "validationWorkflowHeadSha": workflow_head_sha,
        "validationWorkflowRunId": workflow_run_id,
        "validatedArtifactSetDigest": set_digest,
        "validatedChecksumFileSha256": checksum_digest,
        "validatedAt": now(),
    }

    try:
        validate_release_evidence(
            root=ROOT,
            evidence=evidence,
            expected_version=version,
            expected_source_sha=source_sha,
            expected_workflow_run_id=workflow_run_id,
            require_pass=True,
        )
    except ReleaseProvenanceError as exc:
        raise SystemExit(f"RELEASE_FINALIZE_PROVENANCE_INVALID:{exc}") from exc

    facts["status"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    facts["releaseArtifacts"]["state"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    facts["releaseArtifacts"]["workflowRunId"] = workflow_run_id
    facts["releaseArtifacts"]["sourceCommitSha"] = source_sha
    facts["releaseArtifacts"]["artifactSetDigest"] = set_digest
    facts["releaseArtifacts"]["checksumFileSha256"] = checksum_digest
    facts["traceability"]["automatedTest"] = "PASS"
    facts["traceability"]["bundle"] = "PASS"
    manifest["releaseArtifactsState"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    trace["status"] = "RC6_MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS_EXACT_HEAD"

    for item in trace["requirements"]:
        item["coverage"]["automatedTest"] = "PASS"
        item["coverage"]["bundle"] = "PASS"
    trace["summary"]["automatedTestPendingUntilCI"] = 0
    trace["summary"]["bundlePendingUntilMaterialization"] = 0
    trace["summary"]["automatedTestPass"] = 33
    trace["summary"]["bundlePass"] = 33
    trace["ciEvidence"]["currentCandidate"] = {
        "releaseTarget": version,
        "repository": REPOSITORY,
        "workflowRunId": workflow_run_id,
        "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
        "sourceCommitSha": source_sha,
        "sourceTreeSha": provenance["sourceTreeSha"],
        "workflowHeadSha": workflow_head_sha,
        "artifactSetDigest": set_digest,
        "checksumFileSha256": checksum_digest,
        "status": "PASS_EXACT_HEAD_AND_ARTIFACT_SET_VALIDATION",
    }

    final_line = (
        "Materialization state: **MATERIALIZED + AUTOMATED VALIDATION PASS**. "
        f"The {version} Framework distributions are bound to exact source "
        f"{source_sha}, exact artifact-set digest {set_digest} and exact checksum "
        "file evidence."
    )
    readiness = re.sub(
        r"Materialization state: \*\*[^\n]+",
        final_line,
        readiness,
        count=1,
    )

    write_json("RELEASE-FACTS.json", facts)
    write_json("RELEASE-MANIFEST.json", manifest)
    write_json(
        "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json",
        trace,
    )
    write_json(evidence_path(version), evidence)
    readiness_path.write_text(readiness, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    phase = parser.add_mutually_exclusive_group(required=True)
    phase.add_argument("--prepare", action="store_true")
    phase.add_argument("--finalize", action="store_true")
    parser.add_argument(
        "--workflow-run-id",
        default=os.environ.get("GITHUB_RUN_ID", "LOCAL"),
    )
    parser.add_argument(
        "--source-sha",
        default=os.environ.get("GITHUB_SHA"),
    )
    args = parser.parse_args()

    if args.prepare:
        prepare(args.workflow_run_id, args.source_sha)
    else:
        finalize(args.workflow_run_id, args.source_sha)


if __name__ == "__main__":
    main()
