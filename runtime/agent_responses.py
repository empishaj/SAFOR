from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


class AgentResponseValidationError(ValueError):
    """Raised when a SAFOR agent response violates the v0.14 contract."""


_RESPONSE_RULES = {
    "JOB_RESULT": {
        "status": "SUBMITTED",
        "chatStatus": "SUBMITTED",
        "templatePath": "v0.14.0/templates/responses/job-result.template.json",
        "blocking": False,
    },
    "JOB_ERROR": {
        "status": "FAILED",
        "chatStatus": "BLOCKED",
        "templatePath": "v0.14.0/templates/responses/job-error.template.json",
        "blocking": True,
    },
    "CLARIFICATION_REQUEST": {
        "status": "BLOCKED",
        "chatStatus": "BLOCKED",
        "templatePath": "v0.14.0/templates/responses/clarification-request.template.json",
        "blocking": True,
    },
    "CAPABILITY_MISMATCH": {
        "status": "BLOCKED",
        "chatStatus": "BLOCKED",
        "templatePath": "v0.14.0/templates/responses/capability-mismatch.template.json",
        "blocking": True,
    },
    "IMPROVEMENT_PROPOSAL": {
        "status": "ADVISORY",
        "chatStatus": "NONE",
        "templatePath": "v0.14.0/templates/responses/improvement-proposal.template.json",
        "blocking": False,
    },
}

_CONFLICT_FIELDS = {
    "conflictId",
    "conflictType",
    "severity",
    "description",
    "blockedStep",
    "affectedRefs",
    "suggestedResolution",
    "status",
    "responseTemplateVersion",
}

_CAPABILITY_SET_FIELDS = {
    "roleIds",
    "skillIds",
    "domainIds",
    "technologyIds",
}


_RESPONSE_FIELDS = {
    "format", "schemaVersion", "responseId", "responseType", "projectId",
    "jobId", "packageId", "workItemId", "agentId", "identityRevision",
    "jobContractRef", "observedJobContractBlobSha", "responseContractRef",
    "targetMasterRef", "createdAt", "status", "summary", "executionControl",
    "chatStatus", "evidenceRefs", "providerMutationRefs", "payload", "immutable",
}
_POINTER_FIELDS = {"repository", "ref", "path", "blobSha"}
_ARTIFACT_REF_FIELDS = {"ref", "expectedType"}
_GIT_TRACE_FIELDS = {
    "repository", "branch", "baseCommitSha", "headCommitSha", "commitShas",
    "changedPaths", "changeRequestRef", "providerReadbackRef",
}
_CHECK_FIELDS = {"checkId", "commandOrMethod", "status", "evidenceRef"}


def _canonical_response_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentResponseValidationError(f"{name} must be a mapping")
    return value


def _nonempty(value: Any, code: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AgentResponseValidationError(code)
    return text


def _validate_pointer(value: Any, name: str) -> Mapping[str, Any]:
    pointer = _mapping(value, name)
    if set(pointer) != _POINTER_FIELDS:
        raise AgentResponseValidationError(f"{name.upper()}_FIELDS_INVALID")
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(pointer.get(field), f"{name.upper()}_{field.upper()}_MISSING")
    if len(str(pointer["blobSha"])) < 7:
        raise AgentResponseValidationError(f"{name.upper()}_BLOB_SHA_INVALID")
    return pointer


def _validate_execution_control(
    response_type: str, value: Any
) -> Mapping[str, Any]:
    control = _mapping(value, "executionControl")
    required = {
        "controlsJobLifecycle",
        "executionStopped",
        "furtherProductMutationAllowed",
        "scopeExpansionAllowed",
        "agentMayAskHumanDomainQuestions",
    }
    if set(control) != required:
        raise AgentResponseValidationError("EXECUTION_CONTROL_FIELDS_INVALID")
    if control["scopeExpansionAllowed"] is not False:
        raise AgentResponseValidationError("RESPONSE_MUST_NOT_EXPAND_SCOPE")
    if control["agentMayAskHumanDomainQuestions"] is not False:
        raise AgentResponseValidationError("AGENT_HUMAN_DOMAIN_DIALOG_FORBIDDEN")
    if control["furtherProductMutationAllowed"] is not False:
        raise AgentResponseValidationError("RESPONSE_CANNOT_AUTHORIZE_PRODUCT_MUTATION")

    if response_type == "IMPROVEMENT_PROPOSAL":
        if control["controlsJobLifecycle"] is not False:
            raise AgentResponseValidationError(
                "IMPROVEMENT_PROPOSAL_MUST_NOT_CONTROL_JOB"
            )
        if control["executionStopped"] is not False:
            raise AgentResponseValidationError(
                "IMPROVEMENT_PROPOSAL_MUST_BE_NON_BLOCKING"
            )
    else:
        if control["controlsJobLifecycle"] is not True:
            raise AgentResponseValidationError("LIFECYCLE_RESPONSE_REQUIRED")
        if control["executionStopped"] is not True:
            raise AgentResponseValidationError(
                "RESULT_OR_BLOCKER_MUST_END_CURRENT_EXECUTION"
            )
    return control


def _validate_conflict(value: Any) -> Mapping[str, Any]:
    conflict = _mapping(value, "conflict")
    missing = sorted(_CONFLICT_FIELDS - set(conflict))
    unknown = sorted(set(conflict) - _CONFLICT_FIELDS)
    if missing or unknown:
        raise AgentResponseValidationError(
            f"CONFLICT_FIELDS_INVALID: missing={missing}, unknown={unknown}"
        )
    for field in (
        "conflictId",
        "conflictType",
        "severity",
        "description",
        "blockedStep",
        "suggestedResolution",
        "responseTemplateVersion",
    ):
        _nonempty(conflict.get(field), f"CONFLICT_{field.upper()}_MISSING")
    if conflict.get("status") != "OPEN":
        raise AgentResponseValidationError("NEW_CONFLICT_MUST_BE_OPEN")
    if conflict.get("responseTemplateVersion") != "1.0.0":
        raise AgentResponseValidationError("CONFLICT_TEMPLATE_VERSION_INVALID")
    if not isinstance(conflict.get("affectedRefs"), list):
        raise AgentResponseValidationError("CONFLICT_AFFECTED_REFS_INVALID")
    return conflict


def _validate_capability_set(value: Any, name: str) -> Mapping[str, Any]:
    capset = _mapping(value, name)
    if set(capset) != _CAPABILITY_SET_FIELDS:
        raise AgentResponseValidationError(
            f"{name.upper()}_CAPABILITY_FIELDS_INVALID"
        )
    for field in _CAPABILITY_SET_FIELDS:
        if not isinstance(capset[field], list):
            raise AgentResponseValidationError(
                f"{name.upper()}_{field.upper()}_INVALID"
            )
    return capset


def validate_agent_response(
    response: Mapping[str, Any],
    *,
    expected_job: Mapping[str, Any] | None = None,
) -> None:
    """Reference validator; normative rules remain embedded in SAFOR JSON."""

    response = _mapping(response, "response")
    missing = sorted(_RESPONSE_FIELDS - set(response))
    unknown = sorted(set(response) - _RESPONSE_FIELDS)
    if missing or unknown:
        raise AgentResponseValidationError(
            f"RESPONSE_FIELDS_INVALID:missing={missing},unknown={unknown}"
        )
    if response.get("format") != "SAFOR_AGENT_RESPONSE":
        raise AgentResponseValidationError("RESPONSE_FORMAT_INVALID")
    if response.get("schemaVersion") != "0.14.0":
        raise AgentResponseValidationError("RESPONSE_SCHEMA_VERSION_INVALID")
    response_type = str(response.get("responseType", ""))
    if response_type not in _RESPONSE_RULES:
        raise AgentResponseValidationError("UNKNOWN_RESPONSE_TYPE")
    rule = _RESPONSE_RULES[response_type]

    for field in (
        "responseId",
        "projectId",
        "jobId",
        "packageId",
        "workItemId",
        "agentId",
        "observedJobContractBlobSha",
        "targetMasterRef",
        "createdAt",
        "summary",
    ):
        _nonempty(response.get(field), f"RESPONSE_{field.upper()}_MISSING")
    if not isinstance(response.get("identityRevision"), int) or response[
        "identityRevision"
    ] < 1:
        raise AgentResponseValidationError("RESPONSE_IDENTITY_REVISION_INVALID")
    if response.get("immutable") is not True:
        raise AgentResponseValidationError("RESPONSE_MUST_BE_IMMUTABLE")

    job_ref = _validate_pointer(response.get("jobContractRef"), "jobContractRef")
    response_ref = _validate_pointer(
        response.get("responseContractRef"), "responseContractRef"
    )
    if response_ref.get("path") != rule["templatePath"]:
        raise AgentResponseValidationError("RESPONSE_TEMPLATE_PATH_MISMATCH")
    if response.get("status") != rule["status"]:
        raise AgentResponseValidationError("RESPONSE_STATUS_MISMATCH")
    if response.get("chatStatus") != rule["chatStatus"]:
        raise AgentResponseValidationError("RESPONSE_CHAT_STATUS_MISMATCH")
    _validate_execution_control(response_type, response.get("executionControl"))

    if not isinstance(response.get("evidenceRefs"), list):
        raise AgentResponseValidationError("EVIDENCE_REFS_INVALID")
    if not isinstance(response.get("providerMutationRefs"), list):
        raise AgentResponseValidationError("PROVIDER_MUTATION_REFS_INVALID")
    payload = _mapping(response.get("payload"), "payload")

    if expected_job is not None:
        expected_job = _mapping(expected_job, "expectedJob")
        expected = {
            "projectId": expected_job.get("projectId"),
            "jobId": expected_job.get("jobId"),
            "packageId": expected_job.get("packageId"),
            "workItemId": expected_job.get("workItemId"),
            "agentId": expected_job.get("agentId"),
            "identityRevision": expected_job.get("identityRevision"),
            "observedJobContractBlobSha": expected_job.get("jobContractBlobSha"),
        }
        for field, value in expected.items():
            if response.get(field) != value:
                raise AgentResponseValidationError(
                    f"RESPONSE_JOB_BINDING_MISMATCH:{field}"
                )
        if job_ref.get("path") != expected_job.get("jobContractPath"):
            raise AgentResponseValidationError(
                "RESPONSE_JOB_CONTRACT_PATH_MISMATCH"
            )

    if response_type == "JOB_RESULT":
        required = {"completionStatus", "outputs", "gitTrace", "checks", "openItems"}
        if set(payload) != required:
            raise AgentResponseValidationError("JOB_RESULT_PAYLOAD_FIELDS_INVALID")
        if payload["completionStatus"] != "COMPLETED":
            raise AgentResponseValidationError("JOB_RESULT_NOT_COMPLETED")
        if not isinstance(payload["outputs"], list) or not payload["outputs"]:
            raise AgentResponseValidationError("JOB_RESULT_OUTPUTS_REQUIRED")
        for output in payload["outputs"]:
            output = _mapping(output, "artifactRef")
            if set(output) != _ARTIFACT_REF_FIELDS:
                raise AgentResponseValidationError("JOB_RESULT_ARTIFACT_REF_FIELDS_INVALID")
            _nonempty(output.get("ref"), "JOB_RESULT_ARTIFACT_REF_MISSING")
            expected_type = output.get("expectedType")
            if expected_type is not None and not isinstance(expected_type, str):
                raise AgentResponseValidationError("JOB_RESULT_ARTIFACT_TYPE_INVALID")
        for field in ("gitTrace", "checks", "openItems"):
            if not isinstance(payload[field], list):
                raise AgentResponseValidationError(
                    f"JOB_RESULT_{field.upper()}_INVALID"
                )
        for trace in payload["gitTrace"]:
            trace = _mapping(trace, "gitTrace")
            if set(trace) != _GIT_TRACE_FIELDS:
                raise AgentResponseValidationError("JOB_RESULT_GIT_TRACE_FIELDS_INVALID")
            for field in (
                "repository", "branch", "baseCommitSha", "headCommitSha",
                "providerReadbackRef",
            ):
                _nonempty(trace.get(field), f"JOB_RESULT_GIT_TRACE_{field.upper()}_MISSING")
            if not isinstance(trace.get("commitShas"), list) or not trace["commitShas"]:
                raise AgentResponseValidationError("JOB_RESULT_COMMIT_SHAS_REQUIRED")
            if not isinstance(trace.get("changedPaths"), list):
                raise AgentResponseValidationError("JOB_RESULT_CHANGED_PATHS_INVALID")
            if trace.get("changeRequestRef") is not None and not isinstance(
                trace.get("changeRequestRef"), str
            ):
                raise AgentResponseValidationError("JOB_RESULT_CHANGE_REQUEST_REF_INVALID")
        for check in payload["checks"]:
            check = _mapping(check, "check")
            if set(check) != _CHECK_FIELDS:
                raise AgentResponseValidationError("JOB_RESULT_CHECK_FIELDS_INVALID")
            _nonempty(check.get("checkId"), "JOB_RESULT_CHECK_ID_MISSING")
            _nonempty(
                check.get("commandOrMethod"),
                "JOB_RESULT_CHECK_COMMAND_OR_METHOD_MISSING",
            )
            if check.get("status") not in {"PASS", "FAIL", "NOT_RUN"}:
                raise AgentResponseValidationError("JOB_RESULT_CHECK_STATUS_INVALID")
            if check.get("evidenceRef") is not None and not isinstance(
                check.get("evidenceRef"), str
            ):
                raise AgentResponseValidationError("JOB_RESULT_CHECK_EVIDENCE_REF_INVALID")
        if not all(isinstance(item, str) for item in payload["openItems"]):
            raise AgentResponseValidationError("JOB_RESULT_OPEN_ITEMS_INVALID")

    elif response_type == "JOB_ERROR":
        required = {
            "errorClass", "failedStep", "reproducibleFinding", "retryable",
            "safeState", "blockedArtifacts", "conflict",
        }
        if set(payload) != required:
            raise AgentResponseValidationError("JOB_ERROR_PAYLOAD_FIELDS_INVALID")
        for field in ("errorClass", "failedStep", "reproducibleFinding", "safeState"):
            _nonempty(payload.get(field), f"JOB_ERROR_{field.upper()}_MISSING")
        if not isinstance(payload.get("retryable"), bool):
            raise AgentResponseValidationError("JOB_ERROR_RETRYABLE_INVALID")
        _validate_conflict(payload.get("conflict"))

    elif response_type == "CLARIFICATION_REQUEST":
        required = {"question", "affectedJobFields", "options", "recommendedOption", "conflict"}
        if set(payload) != required:
            raise AgentResponseValidationError("CLARIFICATION_PAYLOAD_FIELDS_INVALID")
        _nonempty(payload.get("question"), "CLARIFICATION_QUESTION_MISSING")
        if not isinstance(payload.get("affectedJobFields"), list) or not payload["affectedJobFields"]:
            raise AgentResponseValidationError("CLARIFICATION_AFFECTED_FIELDS_REQUIRED")
        if not isinstance(payload.get("options"), list) or not payload["options"]:
            raise AgentResponseValidationError("CLARIFICATION_OPTIONS_REQUIRED")
        _validate_conflict(payload.get("conflict"))

    elif response_type == "CAPABILITY_MISMATCH":
        required = {"expected", "available", "risk", "affectedScope", "conflict"}
        if set(payload) != required:
            raise AgentResponseValidationError("CAPABILITY_MISMATCH_PAYLOAD_FIELDS_INVALID")
        _validate_capability_set(payload.get("expected"), "expected")
        _validate_capability_set(payload.get("available"), "available")
        _nonempty(payload.get("risk"), "CAPABILITY_MISMATCH_RISK_MISSING")
        if not isinstance(payload.get("affectedScope"), list) or not payload["affectedScope"]:
            raise AgentResponseValidationError("CAPABILITY_MISMATCH_SCOPE_REQUIRED")
        _validate_conflict(payload.get("conflict"))

    elif response_type == "IMPROVEMENT_PROPOSAL":
        required = {
            "proposalId", "problem", "suggestion", "expectedBenefit", "risk",
            "affectedProcess", "blocking", "requiresSeparateDecision", "jobScopeChanged",
        }
        if set(payload) != required:
            raise AgentResponseValidationError("IMPROVEMENT_PROPOSAL_PAYLOAD_FIELDS_INVALID")
        for field in ("proposalId", "problem", "suggestion", "expectedBenefit", "risk", "affectedProcess"):
            _nonempty(payload.get(field), f"IMPROVEMENT_PROPOSAL_{field.upper()}_MISSING")
        if payload.get("blocking") is not False:
            raise AgentResponseValidationError("IMPROVEMENT_PROPOSAL_MUST_NOT_BLOCK")
        if payload.get("requiresSeparateDecision") is not True:
            raise AgentResponseValidationError("IMPROVEMENT_PROPOSAL_REQUIRES_SEPARATE_DECISION")
        if payload.get("jobScopeChanged") is not False:
            raise AgentResponseValidationError("IMPROVEMENT_PROPOSAL_CANNOT_CHANGE_JOB_SCOPE")


def prepare_agent_response(
    *,
    job: Mapping[str, Any],
    response_type: str,
    response_id: str,
    created_at: str,
    summary: str,
    payload: Mapping[str, Any],
    job_contract_ref: Mapping[str, Any],
    target_master_ref: str,
    evidence_refs: list[str] | None = None,
    provider_mutation_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Build an exact v0.14 response envelope from the active Job binding."""

    job = _mapping(job, "job")
    identity = _mapping(job.get("identity"), "job.identity")
    lineage = _mapping(job.get("lineage"), "job.lineage")
    assignment = _mapping(job.get("assignment"), "job.assignment")
    responses = _mapping(job.get("responseContracts"), "job.responseContracts")
    if response_type not in _RESPONSE_RULES:
        raise AgentResponseValidationError("UNKNOWN_RESPONSE_TYPE")
    binding = _mapping(responses.get(response_type), f"responseContracts.{response_type}")
    if binding.get("responseType") != response_type:
        raise AgentResponseValidationError("RESPONSE_JOB_BINDING_TYPE_MISMATCH")
    if binding.get("preWriteSchemaValidationRequired") is not True:
        raise AgentResponseValidationError("RESPONSE_PRE_WRITE_VALIDATION_NOT_BOUND")
    if binding.get("providerReadbackRequired") is not True:
        raise AgentResponseValidationError("RESPONSE_PROVIDER_READBACK_NOT_BOUND")
    if binding.get("postReadbackSchemaValidationRequired") is not True:
        raise AgentResponseValidationError("RESPONSE_POST_READBACK_VALIDATION_NOT_BOUND")
    template_ref = _validate_pointer(binding.get("templateRef"), "responseTemplateRef")
    schema_ref = _validate_pointer(binding.get("schemaRef"), "responseSchemaRef")
    if template_ref.get("path") != _RESPONSE_RULES[response_type]["templatePath"]:
        raise AgentResponseValidationError("RESPONSE_TEMPLATE_PATH_MISMATCH")
    if schema_ref.get("path") != "v0.14.0/schemas/agent-response.schema.json":
        raise AgentResponseValidationError("RESPONSE_SCHEMA_PATH_MISMATCH")
    job_contract_ref = _validate_pointer(job_contract_ref, "jobContractRef")

    controls_lifecycle = response_type != "IMPROVEMENT_PROPOSAL"
    response = {
        "format": "SAFOR_AGENT_RESPONSE",
        "schemaVersion": "0.14.0",
        "responseId": _nonempty(response_id, "RESPONSE_ID_MISSING"),
        "responseType": response_type,
        "projectId": lineage.get("projectId"),
        "jobId": identity.get("jobId"),
        "packageId": lineage.get("packageId"),
        "workItemId": lineage.get("workItemId"),
        "agentId": assignment.get("agentId"),
        "identityRevision": assignment.get("identityRevision"),
        "jobContractRef": dict(job_contract_ref),
        "observedJobContractBlobSha": job_contract_ref.get("blobSha"),
        "responseContractRef": dict(template_ref),
        "targetMasterRef": _nonempty(target_master_ref, "TARGET_MASTER_REF_MISSING"),
        "createdAt": _nonempty(created_at, "RESPONSE_CREATED_AT_MISSING"),
        "status": _RESPONSE_RULES[response_type]["status"],
        "summary": _nonempty(summary, "RESPONSE_SUMMARY_MISSING"),
        "executionControl": {
            "controlsJobLifecycle": controls_lifecycle,
            "executionStopped": controls_lifecycle,
            "furtherProductMutationAllowed": False,
            "scopeExpansionAllowed": False,
            "agentMayAskHumanDomainQuestions": False,
        },
        "chatStatus": _RESPONSE_RULES[response_type]["chatStatus"],
        "evidenceRefs": list(evidence_refs or []),
        "providerMutationRefs": list(provider_mutation_refs or []),
        "payload": deepcopy(dict(_mapping(payload, "payload"))),
        "immutable": True,
    }
    expected_job = {
        "projectId": lineage.get("projectId"),
        "jobId": identity.get("jobId"),
        "packageId": lineage.get("packageId"),
        "workItemId": lineage.get("workItemId"),
        "agentId": assignment.get("agentId"),
        "identityRevision": assignment.get("identityRevision"),
        "jobContractBlobSha": job_contract_ref.get("blobSha"),
        "jobContractPath": job_contract_ref.get("path"),
    }
    validate_agent_response(response, expected_job=expected_job)
    return response


def confirm_agent_response_after_provider_readback(
    *,
    proposed_response: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
    expected_job: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Confirm a typed response only after exact provider readback and revalidation."""

    proposed = deepcopy(dict(_mapping(proposed_response, "proposedResponse")))
    validate_agent_response(proposed, expected_job=expected_job)
    readback = _mapping(provider_readback, "providerReadback")
    if readback.get("writeSucceeded") is not True:
        raise AgentResponseValidationError("RESPONSE_PROVIDER_WRITE_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise AgentResponseValidationError("RESPONSE_PROVIDER_READBACK_UNVERIFIED")
    observed = deepcopy(dict(_mapping(readback.get("observedResponse"), "observedResponse")))
    validate_agent_response(observed, expected_job=expected_job)
    if observed != proposed:
        raise AgentResponseValidationError("RESPONSE_PROVIDER_READBACK_MISMATCH")
    observed_digest = _canonical_response_digest(observed)
    declared_digest = _nonempty(
        readback.get("observedResponseDigest"),
        "RESPONSE_PROVIDER_READBACK_DIGEST_MISSING",
    )
    if declared_digest != observed_digest:
        raise AgentResponseValidationError("RESPONSE_PROVIDER_READBACK_DIGEST_INVALID")
    readback_ref = _nonempty(
        readback.get("readbackRef"), "RESPONSE_PROVIDER_READBACK_REF_MISSING"
    )
    observed_blob_sha = _nonempty(
        readback.get("observedBlobSha"), "RESPONSE_PROVIDER_BLOB_SHA_MISSING"
    )
    return {
        "format": "SAFOR_CONFIRMED_AGENT_RESPONSE",
        "schemaVersion": "0.14.0",
        "authoritativePersistence": True,
        "responseId": observed["responseId"],
        "responseType": observed["responseType"],
        "responseDigest": observed_digest,
        "providerReadbackRef": readback_ref,
        "providerBlobSha": observed_blob_sha,
        "response": observed,
    }


def validate_response_resolution(
    resolution: Mapping[str, Any], *, response: Mapping[str, Any]
) -> None:
    resolution = _mapping(resolution, "resolution")
    response = _mapping(response, "response")
    if resolution.get("format") != "SAFOR_AGENT_RESPONSE_RESOLUTION":
        raise AgentResponseValidationError("RESOLUTION_FORMAT_INVALID")
    if resolution.get("schemaVersion") != "0.14.0":
        raise AgentResponseValidationError("RESOLUTION_SCHEMA_VERSION_INVALID")
    if resolution.get("immutable") is not True:
        raise AgentResponseValidationError("RESOLUTION_MUST_BE_IMMUTABLE")
    if resolution.get("responseId") != response.get("responseId"):
        raise AgentResponseValidationError("RESOLUTION_RESPONSE_ID_MISMATCH")
    if resolution.get("jobId") != response.get("jobId"):
        raise AgentResponseValidationError("RESOLUTION_JOB_ID_MISMATCH")
    _validate_pointer(resolution.get("responseRef"), "responseRef")
    _validate_pointer(resolution.get("decisionRef"), "decisionRef")
    status = resolution.get("resolutionStatus")
    if status == "SUPERSEDED_BY_JOB":
        _nonempty(resolution.get("supersedingJobId"), "SUPERSEDING_JOB_ID_REQUIRED")
    elif resolution.get("supersedingJobId") is not None:
        raise AgentResponseValidationError(
            "SUPERSEDING_JOB_ONLY_ALLOWED_FOR_SUPERSEDED_RESOLUTION"
        )



_LEGACY_OUTBOX_INDEX_FIELDS = {
    "format", "schemaVersion", "projectId", "agentId", "identityRevision",
    "revision", "entries", "updatedAt",
}
_LEGACY_OUTBOX_ENTRY_FIELDS = {
    "responseId", "responseType", "jobId", "responseRef", "status", "createdAt",
}


def prepare_legacy_response_index_recovery(
    *,
    legacy_index: Mapping[str, Any],
    expected_project_id: str,
    expected_agent_id: str,
    expected_identity_revision: int,
    expected_blob_sha: str,
    recovered_at: str,
) -> dict[str, Any]:
    """Prepare an AGENT-owned migration of the known legacy outbox index shape.

    This recovery is intentionally narrow. It preserves historical response
    pointers exactly and does not infer response acceptance or resolution.
    """

    legacy = deepcopy(dict(_mapping(legacy_index, "legacyResponseIndex")))
    if set(legacy) != _LEGACY_OUTBOX_INDEX_FIELDS:
        raise AgentResponseValidationError("LEGACY_RESPONSE_INDEX_FIELDS_INVALID")
    if legacy.get("format") != "SAFOR_AGENT_OUTBOX_INDEX":
        raise AgentResponseValidationError("LEGACY_RESPONSE_INDEX_FORMAT_INVALID")
    if legacy.get("schemaVersion") != "0.14.0":
        raise AgentResponseValidationError("LEGACY_RESPONSE_INDEX_SCHEMA_INVALID")
    if legacy.get("projectId") != expected_project_id:
        raise AgentResponseValidationError("LEGACY_RESPONSE_INDEX_PROJECT_MISMATCH")
    if legacy.get("agentId") != expected_agent_id:
        raise AgentResponseValidationError("LEGACY_RESPONSE_INDEX_AGENT_MISMATCH")
    if legacy.get("identityRevision") != expected_identity_revision:
        raise AgentResponseValidationError(
            "LEGACY_RESPONSE_INDEX_IDENTITY_REVISION_MISMATCH"
        )
    if not isinstance(legacy.get("revision"), int) or legacy["revision"] < 1:
        raise AgentResponseValidationError("LEGACY_RESPONSE_INDEX_REVISION_INVALID")
    _nonempty(expected_blob_sha, "LEGACY_RESPONSE_INDEX_EXPECTED_BLOB_MISSING")
    _nonempty(recovered_at, "LEGACY_RESPONSE_INDEX_RECOVERED_AT_MISSING")
    entries = legacy.get("entries")
    if not isinstance(entries, list):
        raise AgentResponseValidationError("LEGACY_RESPONSE_INDEX_ENTRIES_INVALID")

    migrated_entries = []
    for raw in entries:
        entry = _mapping(raw, "legacyResponseIndexEntry")
        if set(entry) != _LEGACY_OUTBOX_ENTRY_FIELDS:
            raise AgentResponseValidationError(
                "LEGACY_RESPONSE_INDEX_ENTRY_FIELDS_INVALID"
            )
        response_id = _nonempty(
            entry.get("responseId"), "LEGACY_RESPONSE_INDEX_RESPONSE_ID_MISSING"
        )
        response_type = entry.get("responseType")
        if response_type not in _RESPONSE_RULES:
            raise AgentResponseValidationError(
                "LEGACY_RESPONSE_INDEX_RESPONSE_TYPE_INVALID"
            )
        job_id = _nonempty(
            entry.get("jobId"), "LEGACY_RESPONSE_INDEX_JOB_ID_MISSING"
        )
        response_ref = dict(
            _validate_pointer(entry.get("responseRef"), "legacyResponseRef")
        )
        created_at = _nonempty(
            entry.get("createdAt"), "LEGACY_RESPONSE_INDEX_CREATED_AT_MISSING"
        )
        if entry.get("status") not in {
            "SUBMITTED", "FAILED", "BLOCKED", "ADVISORY", "ACKNOWLEDGED",
            "RESOLVED", "CLOSED", "SUPERSEDED",
        }:
            raise AgentResponseValidationError(
                "LEGACY_RESPONSE_INDEX_STATUS_INVALID"
            )
        migrated_entries.append(
            {
                "responseId": response_id,
                "responseType": response_type,
                "jobId": job_id,
                "responseRef": response_ref,
                "createdAt": created_at,
                "responseState": "SUPERSEDED",
                "resolutionRef": None,
            }
        )

    proposed = {
        "format": "SAFOR_AGENT_RESPONSE_INDEX",
        "schemaVersion": "0.14.0",
        "projectId": expected_project_id,
        "agentId": expected_agent_id,
        "identityRevision": expected_identity_revision,
        "revision": legacy["revision"] + 1,
        "authoritativeAcceptance": False,
        "entries": migrated_entries,
        "updatedAt": recovered_at,
    }
    validate_agent_response_index(
        proposed,
        expected_project_id=expected_project_id,
        expected_agent_id=expected_agent_id,
        expected_identity_revision=expected_identity_revision,
    )
    return {
        "format": "SAFOR_AGENT_RESPONSE_INDEX_RECOVERY_INTENT",
        "schemaVersion": "0.14.0",
        "authoritative": False,
        "stateOwner": "AGENT",
        "legacyFormat": "SAFOR_AGENT_OUTBOX_INDEX",
        "expectedBlobSha": expected_blob_sha,
        "priorRevision": legacy["revision"],
        "proposedRevision": proposed["revision"],
        "preservesHistoricalResponseRefs": True,
        "authoritativeAcceptance": False,
        "proposedIndex": proposed,
    }


def confirm_legacy_response_index_recovery_after_provider_readback(
    *,
    recovery_intent: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
) -> dict[str, Any]:
    """Confirm legacy response-index recovery only after exact CAS/readback."""

    intent = _mapping(recovery_intent, "responseIndexRecoveryIntent")
    if (
        intent.get("format") != "SAFOR_AGENT_RESPONSE_INDEX_RECOVERY_INTENT"
        or intent.get("authoritative") is not False
    ):
        raise AgentResponseValidationError("RESPONSE_INDEX_RECOVERY_INTENT_INVALID")
    if intent.get("stateOwner") != "AGENT":
        raise AgentResponseValidationError("RESPONSE_INDEX_RECOVERY_OWNER_INVALID")
    if intent.get("legacyFormat") != "SAFOR_AGENT_OUTBOX_INDEX":
        raise AgentResponseValidationError(
            "RESPONSE_INDEX_RECOVERY_LEGACY_FORMAT_INVALID"
        )
    if intent.get("preservesHistoricalResponseRefs") is not True:
        raise AgentResponseValidationError(
            "RESPONSE_INDEX_RECOVERY_HISTORY_PRESERVATION_REQUIRED"
        )
    if intent.get("authoritativeAcceptance") is not False:
        raise AgentResponseValidationError(
            "RESPONSE_INDEX_RECOVERY_CANNOT_ASSERT_ACCEPTANCE"
        )

    readback = _mapping(provider_readback, "providerReadback")
    if readback.get("casSucceeded") is not True:
        raise AgentResponseValidationError(
            "RESPONSE_INDEX_RECOVERY_PROVIDER_CAS_NOT_CONFIRMED"
        )
    if readback.get("readbackVerified") is not True:
        raise AgentResponseValidationError(
            "RESPONSE_INDEX_RECOVERY_PROVIDER_READBACK_UNVERIFIED"
        )
    observed_blob = _nonempty(
        readback.get("observedBlobSha"),
        "RESPONSE_INDEX_RECOVERY_PROVIDER_BLOB_SHA_MISSING",
    )
    observed = deepcopy(
        dict(_mapping(readback.get("observedIndex"), "observedResponseIndex"))
    )
    proposed = deepcopy(dict(_mapping(intent.get("proposedIndex"), "proposedIndex")))
    validate_agent_response_index(
        observed,
        expected_project_id=str(proposed.get("projectId")),
        expected_agent_id=str(proposed.get("agentId")),
        expected_identity_revision=int(proposed.get("identityRevision")),
    )
    if observed != proposed:
        raise AgentResponseValidationError(
            "RESPONSE_INDEX_RECOVERY_PROVIDER_READBACK_MISMATCH"
        )
    if observed.get("revision") != intent.get("proposedRevision"):
        raise AgentResponseValidationError(
            "RESPONSE_INDEX_RECOVERY_PROVIDER_REVISION_MISMATCH"
        )
    return {
        "format": "SAFOR_CONFIRMED_AGENT_RESPONSE_INDEX_RECOVERY",
        "schemaVersion": "0.14.0",
        "authoritative": True,
        "stateOwner": "AGENT",
        "providerBlobSha": observed_blob,
        "index": observed,
    }

def validate_agent_response_index(
    index: Mapping[str, Any],
    *,
    expected_project_id: str,
    expected_agent_id: str,
    expected_identity_revision: int,
    expected_response: Mapping[str, Any] | None = None,
) -> None:
    index = _mapping(index, "responseIndex")
    required = {
        "format", "schemaVersion", "projectId", "agentId", "identityRevision",
        "revision", "authoritativeAcceptance", "entries", "updatedAt",
    }
    if set(index) != required:
        raise AgentResponseValidationError("RESPONSE_INDEX_FIELDS_INVALID")
    if index.get("format") != "SAFOR_AGENT_RESPONSE_INDEX":
        raise AgentResponseValidationError("RESPONSE_INDEX_FORMAT_INVALID")
    if index.get("schemaVersion") != "0.14.0":
        raise AgentResponseValidationError("RESPONSE_INDEX_SCHEMA_VERSION_INVALID")
    if index.get("projectId") != expected_project_id:
        raise AgentResponseValidationError("RESPONSE_INDEX_PROJECT_MISMATCH")
    if index.get("agentId") != expected_agent_id:
        raise AgentResponseValidationError("RESPONSE_INDEX_AGENT_MISMATCH")
    if index.get("identityRevision") != expected_identity_revision:
        raise AgentResponseValidationError("RESPONSE_INDEX_IDENTITY_REVISION_MISMATCH")
    if not isinstance(index.get("revision"), int) or index["revision"] < 1:
        raise AgentResponseValidationError("RESPONSE_INDEX_REVISION_INVALID")
    if index.get("authoritativeAcceptance") is not False:
        raise AgentResponseValidationError("RESPONSE_INDEX_MUST_NOT_BE_ACCEPTANCE_AUTHORITY")
    if not isinstance(index.get("entries"), list):
        raise AgentResponseValidationError("RESPONSE_INDEX_ENTRIES_INVALID")
    _nonempty(index.get("updatedAt"), "RESPONSE_INDEX_UPDATED_AT_MISSING")

    entry_required = {
        "responseId", "responseType", "jobId", "responseRef",
        "createdAt", "responseState", "resolutionRef",
    }
    matching_entries = []
    for raw in index["entries"]:
        entry = _mapping(raw, "responseIndexEntry")
        if set(entry) != entry_required:
            raise AgentResponseValidationError("RESPONSE_INDEX_ENTRY_FIELDS_INVALID")
        _nonempty(entry.get("responseId"), "RESPONSE_INDEX_RESPONSE_ID_MISSING")
        if entry.get("responseType") not in _RESPONSE_RULES:
            raise AgentResponseValidationError("RESPONSE_INDEX_RESPONSE_TYPE_INVALID")
        _nonempty(entry.get("jobId"), "RESPONSE_INDEX_JOB_ID_MISSING")
        _validate_pointer(entry.get("responseRef"), "responseRef")
        _nonempty(entry.get("createdAt"), "RESPONSE_INDEX_CREATED_AT_MISSING")
        if entry.get("responseState") not in {
            "SUBMITTED", "ACKNOWLEDGED", "RESOLVED", "SUPERSEDED", "CLOSED"
        }:
            raise AgentResponseValidationError("RESPONSE_INDEX_STATE_INVALID")
        resolution_ref = entry.get("resolutionRef")
        if resolution_ref is not None:
            _validate_pointer(resolution_ref, "resolutionRef")
        if expected_response is not None and entry.get("responseId") == expected_response.get("responseId"):
            matching_entries.append(entry)

    if expected_response is not None:
        if len(matching_entries) != 1:
            raise AgentResponseValidationError("RESPONSE_INDEX_EXPECTED_RESPONSE_ENTRY_MISSING_OR_DUPLICATE")
        validate_response_index_binding(
            response=expected_response,
            index_entry=matching_entries[0],
        )
        if matching_entries[0].get("responseState") != "SUBMITTED":
            raise AgentResponseValidationError("RESPONSE_INDEX_EXPECTED_RESPONSE_NOT_SUBMITTED")


def validate_response_index_binding(
    *, response: Mapping[str, Any], index_entry: Mapping[str, Any]
) -> None:
    response = _mapping(response, "response")
    index_entry = _mapping(index_entry, "indexEntry")
    for field in ("responseId", "responseType", "jobId"):
        if index_entry.get(field) != response.get(field):
            raise AgentResponseValidationError(
                f"RESPONSE_INDEX_BINDING_MISMATCH:{field}"
            )
    ref = _validate_pointer(index_entry.get("responseRef"), "responseRef")
    expected_suffix = f"/outbox/{response['jobId']}/{response['responseId']}.json"
    if not str(ref.get("path", "")).endswith(expected_suffix):
        raise AgentResponseValidationError("RESPONSE_INDEX_PATH_MISMATCH")
