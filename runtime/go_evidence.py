from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Any, Mapping, MutableSet

from runtime.agent_responses import AgentResponseValidationError, validate_agent_response, validate_agent_response_index


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


_AGENT_STATE_FIELDS = {
    "format", "schemaVersion", "projectId", "agentId", "identityRevision",
    "revision", "runtimeStatus", "session", "currentJob", "lastResponseRef",
    "consumedActivationIds", "updatedAt",
}
_AGENT_SESSION_FIELDS = {
    "activationId", "activationEvidenceRef", "activatedAt",
    "selectedJobId", "selectedDispatchRevision",
}
_AGENT_CURRENT_JOB_FIELDS = {
    "jobId", "jobRef", "jobBlobSha", "masterJobStateRef",
    "dispatchRevision", "claimId",
}
_AGENT_RUNTIME_STATUSES = {
    "IDLE", "WAITING_HUMAN_GO", "PREFLIGHT", "CLAIMING", "RUNNING",
    "RESULT_SUBMITTED", "BLOCKED", "REIDENTIFICATION_REQUIRED", "PAUSED",
    "REVOKED",
}


def _exact_fields(value: Mapping[str, Any], expected: set[str], code: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        raise GoEvidenceValidationError(
            f"{code}:missing={missing},unknown={unknown}"
        )


def _positive_int(value: Any, code: str, *, minimum: int = 1) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise GoEvidenceValidationError(code)
    return value


def validate_agent_state_contract(
    state: Mapping[str, Any],
    *,
    require_claim: bool = False,
    expected_activation_id: str | None = None,
    expected_job_id: str | None = None,
    expected_dispatch_revision: int | None = None,
    expected_runtime_status: str | None = None,
) -> None:
    """Validate the exact v0.14 Agent-State shape used for persistence."""

    state = _mapping(state, "agentState")
    _exact_fields(state, _AGENT_STATE_FIELDS, "AGENT_STATE_FIELDS_INVALID")
    if state.get("format") != "SAFOR_AGENT_STATE":
        raise GoEvidenceValidationError("AGENT_STATE_FORMAT_INVALID")
    if state.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("AGENT_STATE_SCHEMA_VERSION_INVALID")
    _nonempty(state.get("projectId"), "AGENT_STATE_PROJECT_ID_MISSING")
    _nonempty(state.get("agentId"), "AGENT_STATE_AGENT_ID_MISSING")
    _positive_int(state.get("identityRevision"), "AGENT_STATE_IDENTITY_REVISION_INVALID")
    _positive_int(state.get("revision"), "AGENT_STATE_REVISION_INVALID", minimum=0)
    if state.get("runtimeStatus") not in _AGENT_RUNTIME_STATUSES:
        raise GoEvidenceValidationError("AGENT_STATE_RUNTIME_STATUS_INVALID")
    _parse_datetime(state.get("updatedAt"), "AGENT_STATE_UPDATED_AT_INVALID")

    consumed = state.get("consumedActivationIds")
    if not isinstance(consumed, list):
        raise GoEvidenceValidationError("AGENT_STATE_CONSUMED_ACTIVATIONS_INVALID")
    if len(consumed) != len(set(consumed)):
        raise GoEvidenceValidationError("AGENT_STATE_CONSUMED_ACTIVATIONS_DUPLICATE")
    for activation in consumed:
        if not isinstance(activation, str) or len(activation.strip()) < 8:
            raise GoEvidenceValidationError("AGENT_STATE_CONSUMED_ACTIVATION_INVALID")

    last_response = state.get("lastResponseRef")
    if last_response is not None and (
        not isinstance(last_response, str) or not last_response.strip()
    ):
        raise GoEvidenceValidationError("AGENT_STATE_LAST_RESPONSE_REF_INVALID")

    session_value = state.get("session")
    current_value = state.get("currentJob")
    if session_value is None:
        if require_claim:
            raise GoEvidenceValidationError("AGENT_STATE_CLAIM_SESSION_REQUIRED")
        session = None
    else:
        session = _mapping(session_value, "session")
        _exact_fields(session, _AGENT_SESSION_FIELDS, "AGENT_SESSION_FIELDS_INVALID")
        activation_id = _nonempty(
            session.get("activationId"), "AGENT_SESSION_ACTIVATION_ID_MISSING"
        )
        _nonempty(
            session.get("activationEvidenceRef"),
            "AGENT_SESSION_ACTIVATION_EVIDENCE_REF_MISSING",
        )
        _parse_datetime(session.get("activatedAt"), "AGENT_SESSION_ACTIVATED_AT_INVALID")
        _nonempty(session.get("selectedJobId"), "AGENT_SESSION_JOB_ID_MISSING")
        _positive_int(
            session.get("selectedDispatchRevision"),
            "AGENT_SESSION_DISPATCH_REVISION_INVALID",
        )
        if expected_activation_id is not None and activation_id != expected_activation_id:
            raise GoEvidenceValidationError("AGENT_STATE_ACTIVATION_BINDING_MISMATCH")
        if expected_job_id is not None and session.get("selectedJobId") != expected_job_id:
            raise GoEvidenceValidationError("AGENT_STATE_SESSION_JOB_BINDING_MISMATCH")
        if (
            expected_dispatch_revision is not None
            and session.get("selectedDispatchRevision") != expected_dispatch_revision
        ):
            raise GoEvidenceValidationError(
                "AGENT_STATE_SESSION_DISPATCH_BINDING_MISMATCH"
            )

    if current_value is None:
        if require_claim:
            raise GoEvidenceValidationError("AGENT_STATE_CURRENT_JOB_REQUIRED")
        current = None
    else:
        current = _mapping(current_value, "currentJob")
        _exact_fields(
            current, _AGENT_CURRENT_JOB_FIELDS, "AGENT_CURRENT_JOB_FIELDS_INVALID"
        )
        _nonempty(current.get("jobId"), "AGENT_CURRENT_JOB_ID_MISSING")
        _nonempty(current.get("jobRef"), "AGENT_CURRENT_JOB_REF_MISSING")
        _nonempty(current.get("jobBlobSha"), "AGENT_CURRENT_JOB_BLOB_SHA_MISSING")
        _nonempty(
            current.get("masterJobStateRef"),
            "AGENT_CURRENT_JOB_MASTER_STATE_REF_MISSING",
        )
        _positive_int(
            current.get("dispatchRevision"),
            "AGENT_CURRENT_JOB_DISPATCH_REVISION_INVALID",
        )
        claim_id = current.get("claimId")
        if claim_id is not None:
            claim_id = _nonempty(claim_id, "AGENT_CURRENT_JOB_CLAIM_ID_INVALID")
        if expected_job_id is not None and current.get("jobId") != expected_job_id:
            raise GoEvidenceValidationError("AGENT_STATE_CURRENT_JOB_BINDING_MISMATCH")
        if (
            expected_dispatch_revision is not None
            and current.get("dispatchRevision") != expected_dispatch_revision
        ):
            raise GoEvidenceValidationError(
                "AGENT_STATE_CURRENT_JOB_DISPATCH_BINDING_MISMATCH"
            )
        if expected_activation_id is not None and claim_id != expected_activation_id:
            raise GoEvidenceValidationError("AGENT_STATE_CLAIM_ID_BINDING_MISMATCH")

    if require_claim:
        required_status = expected_runtime_status or "RUNNING"
        if state.get("runtimeStatus") != required_status:
            raise GoEvidenceValidationError("AGENT_STATE_CLAIM_STATUS_INVALID")
        if expected_activation_id is None:
            raise GoEvidenceValidationError("AGENT_STATE_EXPECTED_ACTIVATION_REQUIRED")
        if expected_activation_id not in consumed:
            raise GoEvidenceValidationError(
                "AGENT_STATE_CLAIM_ACTIVATION_NOT_CONSUMED"
            )
        if session is None or current is None:
            raise GoEvidenceValidationError("AGENT_STATE_CLAIM_BINDINGS_REQUIRED")
        if session["activationId"] != current["claimId"]:
            raise GoEvidenceValidationError("AGENT_STATE_SESSION_CLAIM_ID_MISMATCH")


def confirm_human_go_evidence_after_provider_readback(
    *,
    go_evidence: Mapping[str, Any],
    expected: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
    consumed_activation_ids: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Confirm persisted HUMAN-GO evidence before any Agent-State claim is built."""

    validate_human_go_evidence(
        go_evidence,
        expected=expected,
        consumed_activation_ids=consumed_activation_ids,
    )
    readback = _mapping(provider_readback, "goEvidenceProviderReadback")
    if readback.get("writeSucceeded") is not True:
        raise GoEvidenceValidationError("GO_EVIDENCE_PROVIDER_WRITE_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise GoEvidenceValidationError("GO_EVIDENCE_PROVIDER_READBACK_UNVERIFIED")
    observed = _mapping(readback.get("observedEvidence"), "observedEvidence")
    validate_human_go_evidence(
        observed,
        expected=expected,
        consumed_activation_ids=consumed_activation_ids,
    )
    if dict(observed) != dict(go_evidence):
        raise GoEvidenceValidationError("GO_EVIDENCE_PROVIDER_READBACK_MISMATCH")
    readback_ref = _nonempty(
        readback.get("readbackRef"), "GO_EVIDENCE_PROVIDER_READBACK_REF_MISSING"
    )
    observed_blob_sha = _nonempty(
        readback.get("observedBlobSha"), "GO_EVIDENCE_PROVIDER_BLOB_SHA_MISSING"
    )
    return {
        "format": "SAFOR_CONFIRMED_HUMAN_GO_EVIDENCE",
        "schemaVersion": "0.14.0",
        "activationId": go_evidence["activationId"],
        "authoritativePersistence": True,
        "readbackRef": readback_ref,
        "observedBlobSha": observed_blob_sha,
        "evidence": dict(observed),
    }


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



_SETTLED_MASTER_JOB_STATUSES = {
    "REJECTED",
    "ACCEPTED",
    "INTEGRATED",
    "CANCELED",
    "SUPERSEDED",
}


def prepare_agent_state_rearm_after_settlement(
    *,
    agent_state: Mapping[str, Any],
    settled_master_job_state: Mapping[str, Any],
    expected_agent_state_revision: int,
    human_message: str,
    human_input_source: str,
    observed_at: str,
) -> dict[str, Any]:
    """Prepare an AGENT-owned CAS that clears a settled prior execution slot.

    This is used only after a new direct HUMAN GO reaches an initialized chat
    whose previous result has already been terminally reconciled by MASTER.
    It does not itself consume or manufacture HUMAN-GO evidence for the next Job.
    """

    if str(human_input_source) != "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT":
        raise GoEvidenceValidationError("AGENT_REARM_HUMAN_SOURCE_INVALID")
    if str(human_message).strip().casefold() != "go":
        raise GoEvidenceValidationError("AGENT_REARM_REQUIRES_SEPARATE_HUMAN_GO")
    _parse_datetime(observed_at, "AGENT_REARM_HUMAN_GO_AT_INVALID")

    state = deepcopy(dict(_mapping(agent_state, "agentState")))
    master = deepcopy(dict(_mapping(settled_master_job_state, "settledMasterJobState")))
    validate_agent_state_contract(state)

    if state.get("revision") != expected_agent_state_revision:
        raise GoEvidenceValidationError("AGENT_REARM_STATE_REVISION_CONFLICT")
    if state.get("runtimeStatus") != "RESULT_SUBMITTED":
        raise GoEvidenceValidationError("AGENT_REARM_REQUIRES_RESULT_SUBMITTED")
    current = _mapping(state.get("currentJob"), "currentJob")
    session = _mapping(state.get("session"), "session")
    activation_id = _nonempty(
        session.get("activationId"), "AGENT_REARM_PRIOR_ACTIVATION_ID_MISSING"
    )
    validate_agent_state_contract(
        state,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=str(current.get("jobId")),
        expected_dispatch_revision=int(current.get("dispatchRevision")),
        expected_runtime_status="RESULT_SUBMITTED",
    )
    if not state.get("lastResponseRef"):
        raise GoEvidenceValidationError("AGENT_REARM_LAST_RESPONSE_REQUIRED")

    if master.get("format") != "SAFOR_AGENT_JOB_STATE":
        raise GoEvidenceValidationError("AGENT_REARM_MASTER_JOB_FORMAT_INVALID")
    if master.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("AGENT_REARM_MASTER_JOB_SCHEMA_INVALID")
    if master.get("projectId") != state.get("projectId"):
        raise GoEvidenceValidationError("AGENT_REARM_PROJECT_MISMATCH")
    if master.get("jobId") != current.get("jobId"):
        raise GoEvidenceValidationError("AGENT_REARM_JOB_MISMATCH")
    if master.get("assignedAgentId") != state.get("agentId"):
        raise GoEvidenceValidationError("AGENT_REARM_AGENT_MISMATCH")
    if master.get("assignedIdentityRevision") != state.get("identityRevision"):
        raise GoEvidenceValidationError("AGENT_REARM_IDENTITY_REVISION_MISMATCH")
    if master.get("dispatchRevision") != current.get("dispatchRevision"):
        raise GoEvidenceValidationError("AGENT_REARM_DISPATCH_REVISION_MISMATCH")
    if master.get("lifecycleStatus") not in _SETTLED_MASTER_JOB_STATUSES:
        raise GoEvidenceValidationError("AGENT_REARM_MASTER_JOB_NOT_SETTLED")
    if current.get("claimId") != activation_id:
        raise GoEvidenceValidationError("AGENT_REARM_PRIOR_CLAIM_BINDING_MISMATCH")
    if activation_id not in set(state.get("consumedActivationIds") or ()):
        raise GoEvidenceValidationError("AGENT_REARM_PRIOR_ACTIVATION_NOT_CONSUMED")
    proposed = deepcopy(state)
    proposed["revision"] = expected_agent_state_revision + 1
    proposed["runtimeStatus"] = "WAITING_HUMAN_GO"
    proposed["session"] = None
    proposed["currentJob"] = None
    proposed["updatedAt"] = observed_at

    required_top_level = set(_AGENT_STATE_FIELDS)
    if set(proposed) != required_top_level:
        raise GoEvidenceValidationError("AGENT_REARM_REQUIRED_TOP_LEVEL_FIELDS_MISSING")
    if proposed.get("session") is not None or proposed.get("currentJob") is not None:
        raise GoEvidenceValidationError("AGENT_REARM_BINDINGS_MUST_BE_EXPLICIT_NULL")

    validate_agent_state_contract(proposed)
    return {
        "format": "SAFOR_AGENT_STATE_REARM_INTENT",
        "schemaVersion": "0.14.0",
        "authoritative": False,
        "stateOwner": "AGENT",
        "masterJobStateMutationAllowed": False,
        "settledJobId": master.get("jobId"),
        "settledLifecycleStatus": master.get("lifecycleStatus"),
        "priorActivationId": activation_id,
        "humanGoObservedAt": observed_at,
        "humanInputSource": human_input_source,
        "expectedRevision": expected_agent_state_revision,
        "proposedRevision": expected_agent_state_revision + 1,
        "priorStateDigest": _canonical_digest(state),
        "readOnlyMasterJobStateDigest": _canonical_digest(master),
        "proposedStateDigest": _canonical_digest(proposed),
        "proposedState": proposed,
        "requiredProviderSequence": [
            "READ_AGENT_STATE_AT_EXPECTED_REVISION",
            "READ_PRIOR_MASTER_JOB_STATE_READ_ONLY",
            "VERIFY_PRIOR_JOB_IS_TERMINALLY_SETTLED",
            "BUILD_REARMED_AGENT_STATE_WITHOUT_CONSUMING_NEW_GO",
            "VALIDATE_REARMED_AGENT_STATE",
            "CAS_COMMIT_EXACT_REARMED_AGENT_STATE",
            "PROVIDER_READBACK_FULL_REARMED_AGENT_STATE",
            "VERIFY_REARMED_STATE_DIGEST",
            "CONTINUE_SAME_DIRECT_HUMAN_GO_AGAINST_CURRENT_PERSONAL_INBOX",
        ],
    }


def confirm_agent_state_rearm_after_provider_readback(
    *,
    rearm_intent: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
) -> dict[str, Any]:
    """Confirm a rearm only after exact provider CAS/readback."""

    intent = _mapping(rearm_intent, "rearmIntent")
    readback = _mapping(provider_readback, "providerReadback")
    if (
        intent.get("format") != "SAFOR_AGENT_STATE_REARM_INTENT"
        or intent.get("authoritative") is not False
    ):
        raise GoEvidenceValidationError("AGENT_REARM_INTENT_INVALID")
    if intent.get("stateOwner") != "AGENT":
        raise GoEvidenceValidationError("AGENT_REARM_OWNER_INVALID")
    if intent.get("masterJobStateMutationAllowed") is not False:
        raise GoEvidenceValidationError("AGENT_REARM_MASTER_MUTATION_FORBIDDEN")
    if readback.get("casSucceeded") is not True:
        raise GoEvidenceValidationError("AGENT_REARM_PROVIDER_CAS_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise GoEvidenceValidationError("AGENT_REARM_PROVIDER_READBACK_UNVERIFIED")

    proposed = deepcopy(dict(_mapping(intent.get("proposedState"), "proposedState")))
    observed = deepcopy(dict(_mapping(readback.get("observedState"), "observedState")))
    validate_agent_state_contract(proposed)
    validate_agent_state_contract(observed)
    if proposed.get("runtimeStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("AGENT_REARM_PROPOSED_STATUS_INVALID")
    if proposed.get("session") is not None or proposed.get("currentJob") is not None:
        raise GoEvidenceValidationError("AGENT_REARM_PROPOSED_BINDINGS_NOT_CLEARED")
    observed_digest = _canonical_digest(observed)
    if readback.get("observedStateDigest") != observed_digest:
        raise GoEvidenceValidationError("AGENT_REARM_PROVIDER_DIGEST_INVALID")
    if (
        observed != proposed
        or observed_digest != intent.get("proposedStateDigest")
    ):
        raise GoEvidenceValidationError("AGENT_REARM_PROVIDER_STATE_MISMATCH")
    if observed.get("revision") != intent.get("proposedRevision"):
        raise GoEvidenceValidationError("AGENT_REARM_PROVIDER_REVISION_MISMATCH")
    if observed.get("runtimeStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("AGENT_REARM_PROVIDER_STATUS_MISMATCH")
    readback_ref = _nonempty(
        readback.get("readbackRef"), "AGENT_REARM_PROVIDER_READBACK_REF_MISSING"
    )
    observed_blob_sha = _nonempty(
        readback.get("observedBlobSha"), "AGENT_REARM_PROVIDER_BLOB_SHA_MISSING"
    )
    return {
        "format": "SAFOR_CONFIRMED_AGENT_STATE_REARM",
        "schemaVersion": "0.14.0",
        "authoritative": True,
        "stateOwner": "AGENT",
        "settledJobId": intent.get("settledJobId"),
        "settledLifecycleStatus": intent.get("settledLifecycleStatus"),
        "stateDigest": observed_digest,
        "providerReadbackRef": readback_ref,
        "providerBlobSha": observed_blob_sha,
        "state": observed,
    }

def prepare_go_claim(
    *,
    agent_state: Mapping[str, Any],
    master_job_state: Mapping[str, Any],
    job_contract: Mapping[str, Any],
    job_contract_ref: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_agent_state_revision: int,
    go_evidence_ref: Mapping[str, Any],
    master_job_state_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Prepare an AGENT-state CAS claim intent without mutating MASTER lifecycle."""
    agent = deepcopy(dict(_mapping(agent_state, "agentState")))
    master = deepcopy(dict(_mapping(master_job_state, "masterJobState")))

    validate_agent_state_contract(agent)

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

    job = deepcopy(dict(_mapping(job_contract, "jobContract")))
    from runtime.agent_jobs import AgentJobValidationError, validate_agent_job
    try:
        validate_agent_job(job)
    except AgentJobValidationError as exc:
        raise GoEvidenceValidationError(f"AGENT_JOB_CONTRACT_INVALID:{exc}") from exc

    job_identity = _mapping(job.get("identity"), "job.identity")
    job_lineage = _mapping(job.get("lineage"), "job.lineage")
    job_assignment = _mapping(job.get("assignment"), "job.assignment")
    if job_identity.get("jobId") != master.get("jobId"):
        raise GoEvidenceValidationError("JOB_CONTRACT_MASTER_JOB_ID_MISMATCH")
    if job_lineage.get("projectId") != master.get("projectId"):
        raise GoEvidenceValidationError("JOB_CONTRACT_PROJECT_BINDING_MISMATCH")
    if job_assignment.get("agentId") != master.get("assignedAgentId"):
        raise GoEvidenceValidationError("JOB_CONTRACT_AGENT_BINDING_MISMATCH")
    if job_assignment.get("identityRevision") != master.get("assignedIdentityRevision"):
        raise GoEvidenceValidationError("JOB_CONTRACT_IDENTITY_REVISION_MISMATCH")
    contract_ref_for_job = _mapping(master.get("contractRef"), "contractRef")
    observed_contract_ref = _mapping(job_contract_ref, "jobContractRef")
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(
            observed_contract_ref.get(field),
            f"JOB_CONTRACT_OBSERVED_REF_{field.upper()}_MISSING",
        )
        if observed_contract_ref.get(field) != contract_ref_for_job.get(field):
            raise GoEvidenceValidationError(
                f"JOB_CONTRACT_REF_BINDING_MISMATCH:{field}"
            )

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

    validate_agent_state_contract(
        proposed,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=master["jobId"],
        expected_dispatch_revision=master["dispatchRevision"],
    )

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
            "READ_PINNED_AGENT_JOB_CONTRACT",
            "VALIDATE_AGENT_JOB_SCHEMA_AND_RUNTIME_CONTRACT",
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
    expected_bindings_for_schema = _mapping(intent.get("bindings"), "claimBindings")
    validate_agent_state_contract(
        proposed,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=str(expected_bindings_for_schema.get("jobId")),
        expected_dispatch_revision=int(expected_bindings_for_schema.get("dispatchRevision")),
    )
    validate_agent_state_contract(
        observed,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=str(expected_bindings_for_schema.get("jobId")),
        expected_dispatch_revision=int(expected_bindings_for_schema.get("dispatchRevision")),
    )
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


def prepare_result_submitted_agent_state(
    *,
    agent_state: Mapping[str, Any],
    expected_agent_state_revision: int,
    response: Mapping[str, Any],
    response_index: Mapping[str, Any],
    expected_job: Mapping[str, Any],
    response_ref: str,
    submitted_at: str,
) -> dict[str, Any]:
    """Prepare the exact Agent-State transition after a validated response readback."""

    state = deepcopy(dict(_mapping(agent_state, "agentState")))
    current = _mapping(state.get("currentJob"), "currentJob")
    session = _mapping(state.get("session"), "session")
    activation_id = _nonempty(
        session.get("activationId"), "AGENT_SESSION_ACTIVATION_ID_MISSING"
    )
    validate_agent_state_contract(
        state,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=str(current.get("jobId")),
        expected_dispatch_revision=int(current.get("dispatchRevision")),
        expected_runtime_status="RUNNING",
    )
    if state.get("revision") != expected_agent_state_revision:
        raise GoEvidenceValidationError("AGENT_STATE_REVISION_CONFLICT")
    _parse_datetime(submitted_at, "RESULT_SUBMITTED_AT_INVALID")
    response_ref = _nonempty(response_ref, "RESULT_RESPONSE_REF_MISSING")
    response_value = deepcopy(dict(_mapping(response, "response")))
    response_index_value = deepcopy(dict(_mapping(response_index, "responseIndex")))
    expected_job_value = deepcopy(dict(_mapping(expected_job, "expectedJob")))
    try:
        validate_agent_response(response_value, expected_job=expected_job_value)
        validate_agent_response_index(
            response_index_value,
            expected_project_id=str(state.get("projectId")),
            expected_agent_id=str(state.get("agentId")),
            expected_identity_revision=int(state.get("identityRevision")),
            expected_response=response_value,
        )
    except AgentResponseValidationError as exc:
        raise GoEvidenceValidationError(f"RESULT_RESPONSE_CONTRACT_INVALID:{exc}") from exc

    proposed = deepcopy(state)
    proposed["revision"] = expected_agent_state_revision + 1
    proposed["runtimeStatus"] = "RESULT_SUBMITTED"
    proposed["lastResponseRef"] = response_ref
    proposed["updatedAt"] = submitted_at

    validate_agent_state_contract(
        proposed,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=str(current.get("jobId")),
        expected_dispatch_revision=int(current.get("dispatchRevision")),
        expected_runtime_status="RESULT_SUBMITTED",
    )
    return {
        "format": "SAFOR_RESULT_SUBMITTED_STATE_INTENT",
        "schemaVersion": "0.14.0",
        "authoritative": False,
        "expectedRevision": expected_agent_state_revision,
        "proposedRevision": expected_agent_state_revision + 1,
        "activationId": activation_id,
        "jobId": current.get("jobId"),
        "dispatchRevision": current.get("dispatchRevision"),
        "responseRef": response_ref,
        "proposedStateDigest": _canonical_digest(proposed),
        "proposedState": proposed,
    }


def confirm_result_submitted_state_after_provider_readback(
    *,
    state_intent: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
) -> dict[str, Any]:
    """Confirm RESULT_SUBMITTED only after exact provider CAS/readback."""

    intent = _mapping(state_intent, "stateIntent")
    if (
        intent.get("format") != "SAFOR_RESULT_SUBMITTED_STATE_INTENT"
        or intent.get("authoritative") is not False
    ):
        raise GoEvidenceValidationError("RESULT_STATE_INTENT_INVALID")
    readback = _mapping(provider_readback, "providerReadback")
    if readback.get("casSucceeded") is not True:
        raise GoEvidenceValidationError("RESULT_STATE_PROVIDER_CAS_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise GoEvidenceValidationError("RESULT_STATE_PROVIDER_READBACK_UNVERIFIED")

    proposed = deepcopy(dict(_mapping(intent.get("proposedState"), "proposedState")))
    observed = deepcopy(dict(_mapping(readback.get("observedState"), "observedState")))
    activation_id = _nonempty(intent.get("activationId"), "RESULT_STATE_ACTIVATION_ID_MISSING")
    job_id = _nonempty(intent.get("jobId"), "RESULT_STATE_JOB_ID_MISSING")
    dispatch_revision = _positive_int(
        intent.get("dispatchRevision"), "RESULT_STATE_DISPATCH_REVISION_INVALID"
    )
    validate_agent_state_contract(
        proposed,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=job_id,
        expected_dispatch_revision=dispatch_revision,
        expected_runtime_status="RESULT_SUBMITTED",
    )
    validate_agent_state_contract(
        observed,
        require_claim=True,
        expected_activation_id=activation_id,
        expected_job_id=job_id,
        expected_dispatch_revision=dispatch_revision,
        expected_runtime_status="RESULT_SUBMITTED",
    )
    observed_digest = _canonical_digest(observed)
    declared_digest = _nonempty(
        readback.get("observedStateDigest"),
        "RESULT_STATE_PROVIDER_DIGEST_MISSING",
    )
    if declared_digest != observed_digest:
        raise GoEvidenceValidationError("RESULT_STATE_PROVIDER_DIGEST_INVALID")
    if (
        observed != proposed
        or observed_digest != intent.get("proposedStateDigest")
    ):
        raise GoEvidenceValidationError("RESULT_STATE_PROVIDER_READBACK_MISMATCH")
    readback_ref = _nonempty(
        readback.get("readbackRef"), "RESULT_STATE_PROVIDER_READBACK_REF_MISSING"
    )
    observed_blob_sha = _nonempty(
        readback.get("observedBlobSha"), "RESULT_STATE_PROVIDER_BLOB_SHA_MISSING"
    )
    return {
        "format": "SAFOR_CONFIRMED_RESULT_SUBMITTED_STATE",
        "schemaVersion": "0.14.0",
        "authoritative": True,
        "stateDigest": observed_digest,
        "providerReadbackRef": readback_ref,
        "providerBlobSha": observed_blob_sha,
        "state": observed,
    }


def atomically_observe_go_and_claim(
    *,
    agent_state: Mapping[str, Any],
    master_job_state: Mapping[str, Any],
    job_contract: Mapping[str, Any],
    job_contract_ref: Mapping[str, Any],
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
        job_contract=job_contract,
        job_contract_ref=job_contract_ref,
        go_evidence=go_evidence,
        expected_agent_state_revision=expected_agent_state_revision,
        go_evidence_ref=go_evidence_ref,
        master_job_state_ref=master_job_state_ref,
    )
