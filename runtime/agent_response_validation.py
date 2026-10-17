from __future__ import annotations

from typing import Any, Mapping

RESPONSE_TYPES = {
    "JOB_RESULT": ("SUBMITTED", {"artifactRefs", "gitTrace", "verification", "openItems"}),
    "JOB_ERROR": ("FAILED", {"errorClass", "failedStep", "reproducibleFinding", "blockedArtifacts", "suggestedMasterAction"}),
    "CLARIFICATION_REQUEST": ("BLOCKED", {"question", "affectedJobFields", "conflictType", "options", "suggestedMasterAction"}),
    "CAPABILITY_MISMATCH": ("BLOCKED", {"expectedCapabilities", "availableCapabilities", "affectedScope", "risk", "suggestedMasterAction"}),
    "IMPROVEMENT_PROPOSAL": ("PROPOSED", {"problem", "proposal", "expectedBenefit", "risk", "affectedProcess", "suggestedMasterAction"}),
}

COMMON_FIELDS = {
    "format", "schemaVersion", "responseId", "responseType", "projectId", "workPackageId",
    "jobId", "agentId", "identityRevision", "createdAt", "contractRef", "responseTemplateRef",
    "targetMasterRef", "lifecycleStatus", "summary", "affectedRefs", "evidenceRefs",
    "masterDecisionRef", "supersedesResponseId", "payload",
}


class AgentResponseError(ValueError):
    pass


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentResponseError(f"{name} must be an object")
    return value


def validate_agent_response(response: Mapping[str, Any], job: Mapping[str, Any]) -> dict[str, Any]:
    response = _mapping(response, "response")
    job = _mapping(job, "job")
    missing = sorted(COMMON_FIELDS - set(response))
    unknown = sorted(set(response) - COMMON_FIELDS)
    if missing or unknown:
        raise AgentResponseError(f"AGENT_RESPONSE_SHAPE_INVALID missing={missing} unknown={unknown}")
    if response.get("format") != "SAFOR_AGENT_RESPONSE" or response.get("schemaVersion") != "0.13.0":
        raise AgentResponseError("AGENT_RESPONSE_IDENTITY_INVALID")
    response_type = response.get("responseType")
    if response_type not in RESPONSE_TYPES:
        raise AgentResponseError(f"AGENT_RESPONSE_TYPE_INVALID: {response_type}")
    expected_status, required_payload = RESPONSE_TYPES[str(response_type)]
    if response.get("lifecycleStatus") != expected_status:
        raise AgentResponseError("AGENT_RESPONSE_STATUS_TYPE_MISMATCH")
    payload = _mapping(response.get("payload"), "payload")
    if set(payload) != required_payload:
        raise AgentResponseError(
            f"AGENT_RESPONSE_PAYLOAD_INVALID expected={sorted(required_payload)} got={sorted(payload)}"
        )
    identity = _mapping(job.get("identity"), "job.identity")
    assignment = _mapping(job.get("assignment"), "job.assignment")
    lineage = _mapping(job.get("lineage"), "job.lineage")
    if response.get("jobId") != identity.get("jobId"):
        raise AgentResponseError("AGENT_RESPONSE_JOB_MISMATCH")
    if response.get("agentId") != assignment.get("agentId"):
        raise AgentResponseError("AGENT_RESPONSE_AGENT_MISMATCH")
    if response.get("identityRevision") != assignment.get("identityRevision"):
        raise AgentResponseError("AGENT_RESPONSE_IDENTITY_REVISION_MISMATCH")
    if response.get("projectId") != lineage.get("projectId"):
        raise AgentResponseError("AGENT_RESPONSE_PROJECT_MISMATCH")
    if response.get("workPackageId") != lineage.get("packageId"):
        raise AgentResponseError("AGENT_RESPONSE_WORK_PACKAGE_MISMATCH")
    contract = _mapping(job.get("responseContract"), "job.responseContract")
    templates = _mapping(contract.get("templates"), "job.responseContract.templates")
    key_by_type = {
        "JOB_RESULT": "jobResult",
        "JOB_ERROR": "jobError",
        "CLARIFICATION_REQUEST": "clarificationRequest",
        "CAPABILITY_MISMATCH": "capabilityMismatch",
        "IMPROVEMENT_PROPOSAL": "improvementProposal",
    }
    binding = _mapping(templates.get(key_by_type[str(response_type)]), "response template binding")
    if response.get("responseTemplateRef") != binding.get("templateRef"):
        raise AgentResponseError("AGENT_RESPONSE_TEMPLATE_MISMATCH")
    return {
        "valid": True,
        "responseType": response_type,
        "blocksFurtherMutation": expected_status in {"BLOCKED", "FAILED"},
        "masterActionRequired": response_type != "IMPROVEMENT_PROPOSAL" or expected_status != "PROPOSED",
    }
