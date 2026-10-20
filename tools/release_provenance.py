#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_TOP_LEVEL_FIELDS = (
    "format",
    "schemaVersion",
    "contractVersion",
    "contractRef",
    "product",
    "version",
    "status",
    "createdAt",
    "provenance",
    "artifacts",
    "artifactSetDigest",
    "artifactCount",
    "checksumFile",
    "checksumFileSha256",
    "validation",
    "validatedCommands",
    "truthBoundary",
    "materializedAt",
)
REQUIRED_PROVENANCE_FIELDS = (
    "repository",
    "sourceCommitSha",
    "sourceTreeSha",
    "workflowHeadSha",
    "workflowRunId",
    "workflowRunAttempt",
    "integrationRef",
    "exactHeadRequired",
)
REQUIRED_ARTIFACT_FIELDS = (
    "path",
    "sha256",
    "bytes",
    "generatedFromSourceCommit",
)
REQUIRED_VALIDATION_FIELDS = (
    "status",
    "validationSourceCommitSha",
    "validationWorkflowHeadSha",
    "validationWorkflowRunId",
    "validatedArtifactSetDigest",
    "validatedChecksumFileSha256",
    "validatedAt",
)


def canonical_artifact_paths(version: str) -> list[str]:
    """Return the only distributable artifact paths valid for one release."""
    return [
        "SAFOR-FRAMEWORK.json",
        f"SAFOR-FRAMEWORK-v{version}.json",
        "SAFOR-FRAMEWORK-WEBSITE.json",
        "SAFOR-FRAMEWORK-SAAS.json",
        "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        "SAFOR-TEST-ACCESS-SAAS.json",
        "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
    ]


class ReleaseProvenanceError(ValueError):
    """Raised when release provenance or artifact identity is inconsistent."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(raw)


def artifact_set_digest(records: list[Mapping[str, Any]]) -> str:
    normalized = [
        {
            "path": item["path"],
            "sha256": item["sha256"],
            "bytes": item["bytes"],
            "generatedFromSourceCommit": item["generatedFromSourceCommit"],
        }
        for item in sorted(records, key=lambda item: item["path"])
    ]
    return canonical_json_sha256(normalized)


def parse_checksum_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ReleaseProvenanceError(f"CHECKSUM_LINE_INVALID:{lineno}")
        digest, file_name = parts
        file_name = file_name.lstrip("*")
        if not SHA256_RE.fullmatch(digest):
            raise ReleaseProvenanceError(f"CHECKSUM_DIGEST_INVALID:{lineno}")
        if file_name in values:
            raise ReleaseProvenanceError(f"CHECKSUM_DUPLICATE_PATH:{file_name}")
        values[file_name] = digest
    return values


def _require_mapping(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReleaseProvenanceError(code)
    return value


def _require_nonempty(value: Any, code: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ReleaseProvenanceError(code)
    return text


def _require_sha1(value: Any, code: str) -> str:
    text = _require_nonempty(value, code)
    if not SHA1_RE.fullmatch(text):
        raise ReleaseProvenanceError(code)
    return text


def _require_fields(
    value: Mapping[str, Any], fields: tuple[str, ...], code: str
) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ReleaseProvenanceError(f"{code}:{','.join(missing)}")


def _require_utc_timestamp(value: Any, code: str) -> datetime:
    text = _require_nonempty(value, code)
    if not text.endswith("Z"):
        raise ReleaseProvenanceError(code)
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError:
        raise ReleaseProvenanceError(code) from None
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ReleaseProvenanceError(code)
    return parsed


def _require_string_list(
    value: Any, code: str, *, allow_empty: bool = False
) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ReleaseProvenanceError(code)
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ReleaseProvenanceError(code)
        normalized.append(item.strip())
    return normalized


def _resolve_repo_file(root: Path, rel: str, *, kind: str) -> Path:
    """Resolve a canonical release file without permitting path or symlink escape."""
    if "\x00" in rel or "\\" in rel:
        raise ReleaseProvenanceError(f"{kind}_PATH_INVALID:{rel}")

    relative = Path(rel)
    if (
        relative.is_absolute()
        or relative.as_posix() != rel
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ReleaseProvenanceError(f"{kind}_PATH_INVALID:{rel}")

    root_resolved = root.resolve()
    cursor = root_resolved
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ReleaseProvenanceError(f"{kind}_SYMLINK_FORBIDDEN:{rel}")

    candidate = root_resolved.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        raise ReleaseProvenanceError(f"{kind}_NOT_FOUND:{rel}") from None

    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        raise ReleaseProvenanceError(f"{kind}_OUTSIDE_ROOT:{rel}") from None

    if not resolved.is_file():
        raise ReleaseProvenanceError(f"{kind}_NOT_FILE:{rel}")
    return resolved


def validate_release_evidence(
    *,
    root: Path,
    evidence: Mapping[str, Any],
    expected_version: str,
    expected_source_sha: str | None = None,
    expected_source_tree_sha: str | None = None,
    expected_workflow_run_id: str | None = None,
    expected_workflow_run_attempt: str | None = None,
    expected_integration_ref: str | None = None,
    require_pass: bool = True,
) -> None:
    evidence = _require_mapping(evidence, "RELEASE_EVIDENCE_NOT_OBJECT")
    _require_fields(
        evidence, REQUIRED_TOP_LEVEL_FIELDS, "RELEASE_EVIDENCE_REQUIRED_FIELD_MISSING"
    )
    if evidence.get("format") != "SAFOR_RELEASE_EVIDENCE":
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_FORMAT_INVALID")
    if evidence.get("schemaVersion") != "0.14.0":
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_SCHEMA_INVALID")
    if evidence.get("contractVersion") != "1.0":
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_CONTRACT_VERSION_INVALID")
    if evidence.get("product") != "SAFOR":
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_PRODUCT_INVALID")
    if evidence.get("version") != expected_version:
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_VERSION_MISMATCH")
    if evidence.get("contractRef") != "docs/releases/RELEASE-EVIDENCE-CONTRACT-v1.json":
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_CONTRACT_REF_INVALID")

    status = evidence.get("status")
    if require_pass and status != "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS":
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_PASS_REQUIRED")
    if status not in {
        "MATERIALIZED_VALIDATION_PENDING",
        "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS",
    }:
        raise ReleaseProvenanceError("RELEASE_EVIDENCE_STATUS_INVALID")

    created_at = _require_utc_timestamp(
        evidence.get("createdAt"), "RELEASE_CREATED_AT_INVALID"
    )
    materialized_at = _require_utc_timestamp(
        evidence.get("materializedAt"), "RELEASE_MATERIALIZED_AT_INVALID"
    )
    if materialized_at < created_at:
        raise ReleaseProvenanceError("RELEASE_MATERIALIZED_BEFORE_CREATED")

    _require_string_list(evidence.get("truthBoundary"), "RELEASE_TRUTH_BOUNDARY_INVALID")
    validated_commands = _require_string_list(
        evidence.get("validatedCommands"),
        "RELEASE_VALIDATED_COMMANDS_INVALID",
        allow_empty=status == "MATERIALIZED_VALIDATION_PENDING",
    )
    if status == "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS" and not validated_commands:
        raise ReleaseProvenanceError("RELEASE_PASS_VALIDATED_COMMANDS_REQUIRED")

    provenance = _require_mapping(evidence.get("provenance"), "RELEASE_PROVENANCE_MISSING")
    _require_fields(
        provenance,
        REQUIRED_PROVENANCE_FIELDS,
        "RELEASE_PROVENANCE_REQUIRED_FIELD_MISSING",
    )
    source_sha = _require_sha1(
        provenance.get("sourceCommitSha"), "RELEASE_SOURCE_COMMIT_INVALID"
    )
    source_tree_sha = _require_sha1(
        provenance.get("sourceTreeSha"), "RELEASE_SOURCE_TREE_INVALID"
    )
    workflow_head = _require_sha1(
        provenance.get("workflowHeadSha"), "RELEASE_WORKFLOW_HEAD_INVALID"
    )
    if workflow_head != source_sha:
        raise ReleaseProvenanceError("RELEASE_WORKFLOW_HEAD_SOURCE_DRIFT")
    if provenance.get("exactHeadRequired") is not True:
        raise ReleaseProvenanceError("RELEASE_EXACT_HEAD_NOT_REQUIRED")
    if provenance.get("repository") != "empishaj/SAFOR":
        raise ReleaseProvenanceError("RELEASE_REPOSITORY_IDENTITY_INVALID")
    run_id = _require_nonempty(
        provenance.get("workflowRunId"), "RELEASE_WORKFLOW_RUN_ID_MISSING"
    )
    run_attempt = _require_nonempty(
        provenance.get("workflowRunAttempt"), "RELEASE_WORKFLOW_RUN_ATTEMPT_MISSING"
    )
    if not re.fullmatch(r"[1-9][0-9]*", run_attempt):
        raise ReleaseProvenanceError("RELEASE_WORKFLOW_RUN_ATTEMPT_INVALID")
    integration_ref = _require_nonempty(
        provenance.get("integrationRef"), "RELEASE_INTEGRATION_REF_MISSING"
    )
    if run_id != "LOCAL" and not re.fullmatch(r"[1-9][0-9]*", run_id):
        raise ReleaseProvenanceError("RELEASE_WORKFLOW_RUN_ID_INVALID")
    if run_id == "LOCAL" and require_pass:
        raise ReleaseProvenanceError("RELEASE_PASS_CANNOT_USE_LOCAL_RUN")
    if expected_source_sha and source_sha != expected_source_sha:
        raise ReleaseProvenanceError("RELEASE_EXPECTED_SOURCE_SHA_MISMATCH")
    if expected_source_tree_sha and source_tree_sha != expected_source_tree_sha:
        raise ReleaseProvenanceError("RELEASE_EXPECTED_SOURCE_TREE_MISMATCH")
    if expected_workflow_run_id and run_id != str(expected_workflow_run_id):
        raise ReleaseProvenanceError("RELEASE_EXPECTED_WORKFLOW_RUN_MISMATCH")
    if (
        expected_workflow_run_attempt
        and run_attempt != str(expected_workflow_run_attempt)
    ):
        raise ReleaseProvenanceError("RELEASE_EXPECTED_WORKFLOW_RUN_ATTEMPT_MISMATCH")
    if expected_integration_ref and integration_ref != expected_integration_ref:
        raise ReleaseProvenanceError("RELEASE_EXPECTED_INTEGRATION_REF_MISMATCH")

    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ReleaseProvenanceError("RELEASE_ARTIFACTS_MISSING")
    if evidence.get("artifactCount") != len(artifacts):
        raise ReleaseProvenanceError("RELEASE_ARTIFACT_COUNT_MISMATCH")

    seen: set[str] = set()
    normalized_artifacts: list[tuple[Mapping[str, Any], str]] = []
    for item in artifacts:
        item = _require_mapping(item, "RELEASE_ARTIFACT_RECORD_INVALID")
        _require_fields(
            item, REQUIRED_ARTIFACT_FIELDS, "RELEASE_ARTIFACT_REQUIRED_FIELD_MISSING"
        )
        rel = _require_nonempty(item.get("path"), "RELEASE_ARTIFACT_PATH_MISSING")
        if rel in seen:
            raise ReleaseProvenanceError(f"RELEASE_ARTIFACT_DUPLICATE:{rel}")
        seen.add(rel)
        normalized_artifacts.append((item, rel))

    expected_paths = set(canonical_artifact_paths(expected_version))
    if seen != expected_paths:
        raise ReleaseProvenanceError("RELEASE_ARTIFACT_PATH_SET_INVALID")

    for item, rel in normalized_artifacts:
        if item.get("generatedFromSourceCommit") != source_sha:
            raise ReleaseProvenanceError(
                f"RELEASE_ARTIFACT_SOURCE_COMMIT_MISMATCH:{rel}"
            )
        declared = _require_nonempty(
            item.get("sha256"), f"RELEASE_ARTIFACT_DIGEST_MISSING:{rel}"
        )
        if not SHA256_RE.fullmatch(declared):
            raise ReleaseProvenanceError(f"RELEASE_ARTIFACT_DIGEST_INVALID:{rel}")
        declared_bytes = item.get("bytes")
        if (
            isinstance(declared_bytes, bool)
            or not isinstance(declared_bytes, int)
            or declared_bytes < 0
        ):
            raise ReleaseProvenanceError(f"RELEASE_ARTIFACT_SIZE_INVALID:{rel}")
        path = _resolve_repo_file(root, rel, kind="RELEASE_ARTIFACT")
        raw = path.read_bytes()
        if len(raw) != declared_bytes:
            raise ReleaseProvenanceError(f"RELEASE_ARTIFACT_SIZE_DRIFT:{rel}")
        if sha256_bytes(raw) != declared:
            raise ReleaseProvenanceError(f"RELEASE_ARTIFACT_DIGEST_DRIFT:{rel}")

    expected_set_digest = artifact_set_digest(artifacts)
    if evidence.get("artifactSetDigest") != expected_set_digest:
        raise ReleaseProvenanceError("RELEASE_ARTIFACT_SET_DIGEST_DRIFT")

    checksum_file = _require_nonempty(
        evidence.get("checksumFile"), "RELEASE_CHECKSUM_FILE_MISSING"
    )
    expected_checksum_file = f"SHA256SUMS-{expected_version}.txt"
    if checksum_file != expected_checksum_file:
        raise ReleaseProvenanceError("RELEASE_CHECKSUM_FILE_NAME_INVALID")
    checksum_path = _resolve_repo_file(
        root, checksum_file, kind="RELEASE_CHECKSUM_FILE"
    )
    checksums = parse_checksum_file(checksum_path)
    artifact_paths = {item["path"] for item in artifacts}
    if set(checksums) != artifact_paths:
        raise ReleaseProvenanceError("RELEASE_CHECKSUM_PATH_SET_DRIFT")
    for item in artifacts:
        if checksums[item["path"]] != item["sha256"]:
            raise ReleaseProvenanceError(
                f"RELEASE_CHECKSUM_ARTIFACT_DRIFT:{item['path']}"
            )
    checksum_digest = sha256_file(checksum_path)
    if evidence.get("checksumFileSha256") != checksum_digest:
        raise ReleaseProvenanceError("RELEASE_CHECKSUM_FILE_DIGEST_DRIFT")

    validation = _require_mapping(
        evidence.get("validation"), "RELEASE_VALIDATION_BLOCK_MISSING"
    )
    _require_fields(
        validation,
        REQUIRED_VALIDATION_FIELDS,
        "RELEASE_VALIDATION_REQUIRED_FIELD_MISSING",
    )
    if status == "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS":
        if validation.get("status") != "PASS":
            raise ReleaseProvenanceError("RELEASE_VALIDATION_PASS_MISSING")
        if validation.get("validationSourceCommitSha") != source_sha:
            raise ReleaseProvenanceError("RELEASE_VALIDATION_SOURCE_DRIFT")
        if validation.get("validationWorkflowHeadSha") != source_sha:
            raise ReleaseProvenanceError("RELEASE_VALIDATION_HEAD_DRIFT")
        if validation.get("validationWorkflowRunId") != run_id:
            raise ReleaseProvenanceError("RELEASE_VALIDATION_RUN_DRIFT")
        if validation.get("validatedArtifactSetDigest") != expected_set_digest:
            raise ReleaseProvenanceError("RELEASE_VALIDATED_ARTIFACT_SET_DRIFT")
        if validation.get("validatedChecksumFileSha256") != checksum_digest:
            raise ReleaseProvenanceError("RELEASE_VALIDATED_CHECKSUM_DRIFT")
        validated_at = _require_utc_timestamp(
            validation.get("validatedAt"), "RELEASE_VALIDATED_AT_INVALID"
        )
        if validated_at < materialized_at:
            raise ReleaseProvenanceError("RELEASE_VALIDATED_BEFORE_MATERIALIZED")


def collect_validation_errors(**kwargs: Any) -> list[str]:
    try:
        validate_release_evidence(**kwargs)
    except ReleaseProvenanceError as exc:
        return [str(exc)]
    return []
