from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Any, Mapping, MutableSet


class GoEvidenceValidationError(ValueError):
    """Raised when HUMAN-GO evidence is not safely bound to one job claim."""


_REQUIRED_FIELDS = {
    "format", "schemaVersion", "activationId", "projectId", "agentId",
    "identityRevision", "targetJobId", "targetDispatchRevision", "intent",
    "source", "observedAt", "singleUse", "jobPromptTransported",
}


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GoEvidenceValidationError(f"{name} must be a mapping")
    return value


def _nonempty(value: Any, code: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise GoEvidenceValidationError(code)
    return text


def _parse_datetime(value: Any, code: str) -> datetime:
    text = _nonempty(value, code)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GoEvidenceValidationError(code) from exc


def _canonical_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _claim_bindings(agent_state: Mapping[str, Any], activation_id: str) -> dict[str, Any]:
    current = _mapping(agent_state.get("currentJob"), "currentJob")
    return {
        "projectId": agent_state.get("projectId"),
        "jobId": current.get("jobId"),
        "agentId": agent_state.get("agentId"),
        "identityRevision": agent_state.get("identityRevision"),
        "dispatchRevision": current.get("dispatchRevision"),
        "activationId": activation_id,
    }


def validate_human_go_evidence(
    evidence: Mapping[str, Any],
    *,
    expected: Mapping[str, Any],
    consumed_activation_ids: set[str] | frozenset[str] | None = None,
) -> None:
    evidence = _mapping(evidence, "goEvidence")
    missing = sorted(_REQUIRED_FIELDS - set(evidence))
    unknown = sorted(set(evidence) - _REQUIRED_FIELDS)
    if missing or unknown:
        raise GoEvidenceValidationError(
            f"GO_EVIDENCE_FIELDS_INVALID:missing={missing},unknown={unknown}"
        )
    if evidence.get("format") != "SAFOR_HUMAN_GO_EVIDENCE":
        raise GoEvidenceValidationError("GO_EVIDENCE_FORMAT_INVALID")
    if evidence.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("GO_EVIDENCE_SCHEMA_VERSION_INVALID")
    if evidence.get("intent") != "GO":
        raise GoEvidenceValidationError("GO_EVIDENCE_INTENT_INVALID")
    if evidence.get("source") != "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT":
        raise GoEvidenceValidationError("GO_EVIDENCE_SOURCE_INVALID")
    if evidence.get("singleUse") is not True:
        raise GoEvidenceValidationError("GO_EVIDENCE_MUST_BE_SINGLE_USE")
    if evidence.get("jobPromptTransported") is not False:
        raise GoEvidenceValidationError("GO_EVIDENCE_JOB_PROMPT_TRANSPORT_FORBIDDEN")
    activation_id = _nonempty(evidence.get("activationId"), "GO_ACTIVATION_ID_MISSING")
    _parse_datetime(evidence.get("observedAt"), "GO_OBSERVED_AT_INVALID")
    if activation_id in set(consumed_activation_ids or ()):
        raise GoEvidenceValidationError("GO_EVIDENCE_ALREADY_CONSUMED")
    for field in (
        "projectId", "agentId", "identityRevision",
        "targetJobId", "targetDispatchRevision",
    ):
        if evidence.get(field) != expected.get(field):
            raise GoEvidenceValidationError(f"GO_EVIDENCE_BINDING_MISMATCH:{field}")


def prepare_go_claim(
    *,
    agent_state: Mapping[str, Any],
    master_job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_agent_state_revision: int,
    go_evidence_ref: Mapping[str, Any],
    master_job_state_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Prepare an AGENT-state CAS claim intent without mutating MASTER lifecycle."""
    agent = deepcopy(dict(_mapping(agent_state, "agentState")))
    master = deepcopy(dict(_mapping(master_job_state, "masterJobState")))

    if agent.get("format") != "SAFOR_AGENT_STATE":
        raise GoEvidenceValidationError("AGENT_STATE_FORMAT_INVALID")
    if agent.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("AGENT_STATE_SCHEMA_VERSION_INVALID")
    if agent.get("runtimeStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("AGENT_NOT_WAITING_HUMAN_GO")
    if agent.get("revision") != expected_agent_state_revision:
        raise GoEvidenceValidationError("AGENT_STATE_REVISION_CONFLICT")

    if master.get("format") != "SAFOR_AGENT_JOB_STATE":
        raise GoEvidenceValidationError("MASTER_JOB_STATE_FORMAT_INVALID")
    if master.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("MASTER_JOB_STATE_SCHEMA_VERSION_INVALID")
    if master.get("lifecycleStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("JOB_NOT_WAITING_HUMAN_GO")
    if master.get("projectId") != agent.get("projectId"):
        raise GoEvidenceValidationError("CLAIM_PROJECT_BINDING_MISMATCH")
    if master.get("assignedAgentId") != agent.get("agentId"):
        raise GoEvidenceValidationError("CLAIM_AGENT_BINDING_MISMATCH")
    if master.get("assignedIdentityRevision") != agent.get("identityRevision"):
        raise GoEvidenceValidationError("CLAIM_IDENTITY_REVISION_MISMATCH")

    expected = {
        "projectId": master.get("projectId"),
        "agentId": master.get("assignedAgentId"),
        "identityRevision": master.get("assignedIdentityRevision"),
        "targetJobId": master.get("jobId"),
        "targetDispatchRevision": master.get("dispatchRevision"),
    }
    consumed = set(agent.get("consumedActivationIds") or ())
    validate_human_go_evidence(
        go_evidence, expected=expected, consumed_activation_ids=consumed
    )
    for pointer_name, pointer in (
        ("goEvidenceRef", go_evidence_ref),
        ("masterJobStateRef", master_job_state_ref),
    ):
        pointer = _mapping(pointer, pointer_name)
        for field in ("repository", "ref", "path", "blobSha"):
            _nonempty(pointer.get(field), f"{pointer_name.upper()}_{field.upper()}_MISSING")

    contract_ref = _mapping(master.get("contractRef"), "contractRef")
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(contract_ref.get(field), f"JOB_CONTRACT_REF_{field.upper()}_MISSING")

    activation_id = str(go_evidence["activationId"])
    proposed = deepcopy(agent)
    proposed["revision"] = expected_agent_state_revision + 1
    proposed["runtimeStatus"] = "RUNNING"
    proposed["session"] = {
        "activationId": activation_id,
        "activationEvidenceRef": str(go_evidence_ref["path"]),
        "activatedAt": go_evidence["observedAt"],
        "selectedJobId": master["jobId"],
        "selectedDispatchRevision": master["dispatchRevision"],
    }
    proposed["currentJob"] = {
        "jobId": master["jobId"],
        "jobRef": str(contract_ref["path"]),
        "jobBlobSha": str(contract_ref["blobSha"]),
        "masterJobStateRef": str(master_job_state_ref["path"]),
        "dispatchRevision": master["dispatchRevision"],
        "claimId": activation_id,
    }
    proposed["consumedActivationIds"] = sorted(consumed | {activation_id})
    proposed["updatedAt"] = go_evidence["observedAt"]

    return {
        "format": "SAFOR_GO_CLAIM_INTENT",
        "schemaVersion": "0.14.0",
        "authoritative": False,
        "claimStateOwner": "AGENT",
        "masterJobStateMutationAllowed": False,
        "activationId": activation_id,
        "bindings": _claim_bindings(proposed, activation_id),
        "expectedRevision": expected_agent_state_revision,
        "proposedRevision": expected_agent_state_revision + 1,
        "priorStateDigest": _canonical_digest(agent),
        "proposedStateDigest": _canonical_digest(proposed),
        "readOnlyMasterJobStateDigest": _canonical_digest(master),
        "goEvidenceRef": dict(go_evidence_ref),
        "masterJobStateRef": dict(master_job_state_ref),
        "requiredProviderSequence": [
            "READ_AGENT_STATE_AT_EXPECTED_REVISION",
            "READ_MASTER_JOB_STATE_READ_ONLY",
            "VALIDATE_GO_AND_JOB_BINDINGS",
            "CAS_COMMIT_EXACT_PROPOSED_AGENT_STATE_AT_EXPECTED_REVISION",
            "PROVIDER_READBACK_FULL_COMMITTED_AGENT_STATE",
            "VERIFY_CANONICAL_STATE_DIGEST_AND_BINDINGS",
            "MARK_CLAIM_AUTHORITY_FROM_PROVIDER_EVIDENCE",
        ],
        "proposedState": proposed,
    }


def confirm_go_claim_after_provider_readback(
    *,
    claim_intent: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
    consumed_activation_ids: MutableSet[str],
) -> dict[str, Any]:
    """Confirm an AGENT-owned claim only after exact provider CAS/readback."""
    intent = _mapping(claim_intent, "claimIntent")
    readback = _mapping(provider_readback, "providerReadback")
    if intent.get("format") != "SAFOR_GO_CLAIM_INTENT" or intent.get("authoritative") is not False:
        raise GoEvidenceValidationError("GO_CLAIM_INTENT_INVALID")
    if intent.get("claimStateOwner") != "AGENT":
        raise GoEvidenceValidationError("GO_CLAIM_OWNER_INVALID")
    if intent.get("masterJobStateMutationAllowed") is not False:
        raise GoEvidenceValidationError("AGENT_MASTER_JOB_STATE_MUTATION_FORBIDDEN")

    activation_id = _nonempty(intent.get("activationId"), "GO_ACTIVATION_ID_MISSING")
    if activation_id in consumed_activation_ids:
        raise GoEvidenceValidationError("GO_EVIDENCE_ALREADY_CONSUMED")
    if readback.get("casSucceeded") is not True:
        raise GoEvidenceValidationError("PROVIDER_CAS_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_READBACK_UNVERIFIED")

    proposed = deepcopy(dict(_mapping(intent.get("proposedState"), "proposedState")))
    observed = deepcopy(dict(_mapping(readback.get("observedState"), "observedState")))
    expected_digest = _nonempty(intent.get("proposedStateDigest"), "GO_CLAIM_PROPOSED_DIGEST_MISSING")
    observed_digest = _canonical_digest(observed)
    declared_observed_digest = _nonempty(
        readback.get("observedStateDigest"), "PROVIDER_CLAIM_OBSERVED_DIGEST_MISSING"
    )
    if declared_observed_digest != observed_digest:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_READBACK_DIGEST_INVALID")
    if observed_digest != expected_digest or observed != proposed:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_STATE_MISMATCH")

    expected_bindings = _mapping(intent.get("bindings"), "claimBindings")
    actual_bindings = _claim_bindings(observed, activation_id)
    for field, expected_value in expected_bindings.items():
        if actual_bindings.get(field) != expected_value:
            raise GoEvidenceValidationError(f"PROVIDER_CLAIM_BINDING_MISMATCH:{field}")
    if observed.get("revision") != intent.get("proposedRevision"):
        raise GoEvidenceValidationError("PROVIDER_CLAIM_REVISION_MISMATCH")
    if observed.get("runtimeStatus") != "RUNNING":
        raise GoEvidenceValidationError("PROVIDER_CLAIM_STATUS_MISMATCH")
    if activation_id not in set(observed.get("consumedActivationIds") or ()):
        raise GoEvidenceValidationError("PROVIDER_CLAIM_ACTIVATION_NOT_PERSISTED")
    current = _mapping(observed.get("currentJob"), "currentJob")
    if current.get("claimId") != activation_id:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_ID_NOT_PERSISTED")

    readback_ref = _nonempty(readback.get("readbackRef"), "PROVIDER_CLAIM_READBACK_REF_MISSING")
    observed_blob_sha = _nonempty(
        readback.get("observedBlobSha"), "PROVIDER_CLAIM_BLOB_SHA_MISSING"
    )
    consumed_activation_ids.add(activation_id)
    return {
        "format": "SAFOR_CONFIRMED_GO_CLAIM",
        "schemaVersion": "0.14.0",
        "authoritative": True,
        "claimStateOwner": "AGENT",
        "activationId": activation_id,
        "bindings": dict(expected_bindings),
        "stateDigest": observed_digest,
        "providerReadbackRef": readback_ref,
        "providerBlobSha": observed_blob_sha,
        "masterJobStateRef": dict(_mapping(intent.get("masterJobStateRef"), "masterJobStateRef")),
        "state": observed,
    }


def atomically_observe_go_and_claim(
    *,
    agent_state: Mapping[str, Any],
    master_job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_agent_state_revision: int,
    consumed_activation_ids: MutableSet[str],
    go_evidence_ref: Mapping[str, Any],
    master_job_state_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility alias returning a non-authoritative AGENT-state claim intent."""
    return prepare_go_claim(
        agent_state=agent_state,
        master_job_state=master_job_state,
        go_evidence=go_evidence,
        expected_agent_state_revision=expected_agent_state_revision,
        go_evidence_ref=go_evidence_ref,
        master_job_state_ref=master_job_state_ref,
    )
