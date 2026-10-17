from __future__ import annotations

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
        for field in ("gitTrace", "checks", "openItems"):
            if not isinstance(payload[field], list):
                raise AgentResponseValidationError(
                    f"JOB_RESULT_{field.upper()}_INVALID"
                )

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
