from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Any, Mapping, MutableSet


class GoEvidenceValidationError(ValueError):
    """Raised when HUMAN-GO evidence is not safely bound to one agent-owned claim."""


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
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_pointer(value: Mapping[str, Any], prefix: str) -> Mapping[str, Any]:
    pointer = _mapping(value, prefix)
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(pointer.get(field), f"{prefix.upper()}_{field.upper()}_MISSING")
    return pointer


def _claim_bindings(agent_state: Mapping[str, Any], activation_id: str) -> dict[str, Any]:
    current = _mapping(agent_state.get("currentJob"), "currentJob")
    return {
        "projectId": agent_state.get("projectId"),
        "jobId": current.get("jobId"),
        "agentId": agent_state.get("agentId"),
        "identityRevision": agent_state.get("identityRevision"),
        "masterJobRevision": current.get("masterJobRevision"),
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
    master_job_state: Mapping[str, Any],
    master_job_state_ref: Mapping[str, Any],
    agent_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_agent_state_revision: int,
    consumed_activation_ids: set[str] | frozenset[str] | None,
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Prepare a non-authoritative CAS intent against agent-owned state only."""

    master = deepcopy(dict(_mapping(master_job_state, "masterJobState")))
    if master.get("format") != "SAFOR_AGENT_JOB_STATE":
        raise GoEvidenceValidationError("MASTER_JOB_STATE_FORMAT_INVALID")
    if master.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("MASTER_JOB_STATE_SCHEMA_VERSION_INVALID")
    if master.get("owner") != "MASTER":
        raise GoEvidenceValidationError("MASTER_JOB_STATE_OWNER_INVALID")
    if master.get("lifecycleStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("MASTER_JOB_NOT_WAITING_HUMAN_GO")

    agent = deepcopy(dict(_mapping(agent_state, "agentState")))
    if agent.get("format") != "SAFOR_AGENT_STATE":
        raise GoEvidenceValidationError("AGENT_STATE_FORMAT_INVALID")
    if agent.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("AGENT_STATE_SCHEMA_VERSION_INVALID")
    if agent.get("revision") != expected_agent_state_revision:
        raise GoEvidenceValidationError("AGENT_STATE_REVISION_CONFLICT")
    if agent.get("runtimeStatus") not in {"IDLE", "WAITING_HUMAN_GO"}:
        raise GoEvidenceValidationError("AGENT_NOT_WAITING_HUMAN_GO")
    if agent.get("currentJob") is not None:
        raise GoEvidenceValidationError("AGENT_ALREADY_HAS_CURRENT_JOB")

    expected = {
        "projectId": master.get("projectId"),
        "agentId": master.get("assignedAgentId"),
        "identityRevision": master.get("assignedIdentityRevision"),
        "targetJobId": master.get("jobId"),
        "targetDispatchRevision": master.get("dispatchRevision"),
    }
    persisted_consumed = set(agent.get("consumedActivationIds") or ())
    validate_human_go_evidence(
        go_evidence,
        expected=expected,
        consumed_activation_ids=persisted_consumed | set(consumed_activation_ids or ()),
    )

    if agent.get("projectId") != expected["projectId"]:
        raise GoEvidenceValidationError("AGENT_STATE_PROJECT_MISMATCH")
    if agent.get("agentId") != expected["agentId"]:
        raise GoEvidenceValidationError("AGENT_STATE_AGENT_MISMATCH")
    if agent.get("identityRevision") != expected["identityRevision"]:
        raise GoEvidenceValidationError("AGENT_STATE_IDENTITY_REVISION_MISMATCH")

    go_ref = _validate_pointer(go_evidence_ref, "goEvidenceRef")
    master_ref = _validate_pointer(master_job_state_ref, "masterJobStateRef")
    contract_ref = _validate_pointer(master.get("contractRef"), "jobContractRef")

    activation_id = str(go_evidence["activationId"])
    proposed = deepcopy(agent)
    proposed["revision"] = expected_agent_state_revision + 1
    proposed["runtimeStatus"] = "RUNNING"
    proposed["session"] = {
        "activationId": activation_id,
        "activationEvidenceRef": str(go_ref["path"]),
        "activatedAt": go_evidence["observedAt"],
        "selectedJobId": master["jobId"],
        "selectedDispatchRevision": master["dispatchRevision"],
    }
    proposed["currentJob"] = {
        "jobId": master["jobId"],
        "jobRef": str(contract_ref["path"]),
        "jobBlobSha": str(contract_ref["blobSha"]),
        "masterJobStateRef": str(master_ref["path"]),
        "masterJobRevision": master["revision"],
        "dispatchRevision": master["dispatchRevision"],
        "claimId": activation_id,
    }
    proposed["consumedActivationIds"] = sorted(persisted_consumed | {activation_id})
    proposed["updatedAt"] = go_evidence["observedAt"]

    cas_target_path = f"agents/{agent['agentId']}/state.json"
    master_lifecycle_path = f"master/jobs/{master['jobId']}.json"
    return {
        "format": "SAFOR_GO_CLAIM_INTENT",
        "schemaVersion": "0.14.0",
        "authoritative": False,
        "activationId": activation_id,
        "bindings": _claim_bindings(proposed, activation_id),
        "casTargetPath": cas_target_path,
        "casTargetAuthority": "ASSIGNED_AGENT_ONLY",
        "masterLifecyclePath": master_lifecycle_path,
        "masterLifecycleAuthority": "MASTER_ONLY",
        "agentMayWriteMasterLifecycle": False,
        "expectedAgentStateRevision": expected_agent_state_revision,
        "proposedAgentStateRevision": expected_agent_state_revision + 1,
        "expectedMasterJobRevision": master["revision"],
        "masterJobStateDigest": _canonical_digest(master),
        "priorAgentStateDigest": _canonical_digest(agent),
        "proposedAgentStateDigest": _canonical_digest(proposed),
        "goEvidenceRef": dict(go_ref),
        "masterJobStateRef": dict(master_ref),
        "requiredProviderSequence": [
            "CAS_COMMIT_AGENT_STATE_AT_EXPECTED_AGENT_REVISION",
            "PROVIDER_READBACK_FULL_AGENT_STATE",
            "VERIFY_CANONICAL_AGENT_STATE_DIGEST_AND_BINDINGS",
            "EMIT_AGENT_CLAIM_PROVIDER_VERIFIED_EVENT",
            "MASTER_UPDATES_MASTER_JOB_LIFECYCLE_SEPARATELY",
        ],
        "proposedAgentState": proposed,
    }


def confirm_go_claim_after_provider_readback(
    *,
    claim_intent: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
    consumed_activation_ids: MutableSet[str],
) -> dict[str, Any]:
    """Confirm an agent-owned claim and emit MASTER transition input."""

    intent = _mapping(claim_intent, "claimIntent")
    readback = _mapping(provider_readback, "providerReadback")
    if intent.get("format") != "SAFOR_GO_CLAIM_INTENT" or intent.get("authoritative") is not False:
        raise GoEvidenceValidationError("GO_CLAIM_INTENT_INVALID")
    if intent.get("agentMayWriteMasterLifecycle") is not False:
        raise GoEvidenceValidationError("AGENT_MASTER_LIFECYCLE_WRITE_FORBIDDEN")

    activation_id = _nonempty(intent.get("activationId"), "GO_ACTIVATION_ID_MISSING")
    if activation_id in consumed_activation_ids:
        raise GoEvidenceValidationError("GO_EVIDENCE_ALREADY_CONSUMED")
    if readback.get("casSucceeded") is not True:
        raise GoEvidenceValidationError("PROVIDER_CAS_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_READBACK_UNVERIFIED")

    target_path = _nonempty(readback.get("targetPath"), "PROVIDER_CLAIM_TARGET_PATH_MISSING")
    if target_path != intent.get("casTargetPath"):
        raise GoEvidenceValidationError("PROVIDER_CLAIM_TARGET_PATH_MISMATCH")

    proposed = deepcopy(dict(_mapping(intent.get("proposedAgentState"), "proposedAgentState")))
    observed = deepcopy(dict(_mapping(readback.get("observedState"), "observedState")))
    expected_digest = _nonempty(
        intent.get("proposedAgentStateDigest"),
        "GO_CLAIM_PROPOSED_AGENT_STATE_DIGEST_MISSING",
    )
    observed_digest = _canonical_digest(observed)
    declared_observed_digest = _nonempty(
        readback.get("observedStateDigest"),
        "PROVIDER_CLAIM_OBSERVED_DIGEST_MISSING",
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

    if observed.get("revision") != intent.get("proposedAgentStateRevision"):
        raise GoEvidenceValidationError("PROVIDER_CLAIM_REVISION_MISMATCH")
    if observed.get("runtimeStatus") != "RUNNING":
        raise GoEvidenceValidationError("PROVIDER_CLAIM_AGENT_STATUS_MISMATCH")
    current = _mapping(observed.get("currentJob"), "currentJob")
    if current.get("claimId") != activation_id:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_ID_MISMATCH")
    if activation_id not in set(observed.get("consumedActivationIds") or ()):
        raise GoEvidenceValidationError("PROVIDER_CLAIM_ACTIVATION_NOT_PERSISTED")

    readback_ref = _nonempty(readback.get("readbackRef"), "PROVIDER_CLAIM_READBACK_REF_MISSING")
    observed_blob_sha = _nonempty(readback.get("observedBlobSha"), "PROVIDER_CLAIM_BLOB_SHA_MISSING")
    consumed_activation_ids.add(activation_id)

    transition_input = {
        "format": "SAFOR_AGENT_CLAIM_PROVIDER_VERIFIED",
        "schemaVersion": "0.14.0",
        "projectId": observed["projectId"],
        "jobId": current["jobId"],
        "agentId": observed["agentId"],
        "identityRevision": observed["identityRevision"],
        "dispatchRevision": current["dispatchRevision"],
        "activationId": activation_id,
        "expectedMasterJobRevision": current["masterJobRevision"],
        "agentStateRevision": observed["revision"],
        "agentStateReadbackRef": readback_ref,
        "agentStateBlobSha": observed_blob_sha,
        "agentStateDigest": observed_digest,
        "masterLifecyclePath": intent["masterLifecyclePath"],
        "requiredWriter": "MASTER",
    }

    return {
        "format": "SAFOR_CONFIRMED_GO_CLAIM",
        "schemaVersion": "0.14.0",
        "authoritative": True,
        "activationId": activation_id,
        "claimAuthority": "AGENT_STATE_PROVIDER_READBACK",
        "bindings": dict(expected_bindings),
        "casTargetPath": intent["casTargetPath"],
        "stateDigest": observed_digest,
        "providerReadbackRef": readback_ref,
        "providerBlobSha": observed_blob_sha,
        "masterLifecycleMutationPerformed": False,
        "masterLifecycleUpdateRequired": True,
        "masterTransitionInput": transition_input,
        "state": observed,
    }


def atomically_observe_go_and_claim(
    *,
    master_job_state: Mapping[str, Any],
    master_job_state_ref: Mapping[str, Any],
    agent_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_agent_state_revision: int,
    consumed_activation_ids: MutableSet[str],
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility alias returning a non-authoritative agent-state claim intent."""
    return prepare_go_claim(
        master_job_state=master_job_state,
        master_job_state_ref=master_job_state_ref,
        agent_state=agent_state,
        go_evidence=go_evidence,
        expected_agent_state_revision=expected_agent_state_revision,
        consumed_activation_ids=set(consumed_activation_ids),
        go_evidence_ref=go_evidence_ref,
    )
