from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping, MutableSet


class GoEvidenceValidationError(ValueError):
    """Raised when HUMAN-GO evidence is not safely bound to one job claim."""


_REQUIRED_FIELDS = {
    "format", "schemaVersion", "activationId", "projectId", "agentId",
    "identityRevision", "chatBindingId", "sessionId", "targetJobId",
    "targetDispatchRevision", "intent", "source", "observedAt",
    "singleUse", "jobPromptTransported",
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
    if evidence.get("source") != "DIRECT_HUMAN_INPUT_IN_BOUND_AGENT_CHAT":
        raise GoEvidenceValidationError("GO_EVIDENCE_SOURCE_INVALID")
    if evidence.get("singleUse") is not True:
        raise GoEvidenceValidationError("GO_EVIDENCE_MUST_BE_SINGLE_USE")
    if evidence.get("jobPromptTransported") is not False:
        raise GoEvidenceValidationError("GO_EVIDENCE_JOB_PROMPT_TRANSPORT_FORBIDDEN")
    activation_id = _nonempty(evidence.get("activationId"), "GO_ACTIVATION_ID_MISSING")
    _nonempty(evidence.get("sessionId"), "GO_SESSION_ID_MISSING")
    _parse_datetime(evidence.get("observedAt"), "GO_OBSERVED_AT_INVALID")
    if activation_id in set(consumed_activation_ids or ()):
        raise GoEvidenceValidationError("GO_EVIDENCE_ALREADY_CONSUMED")
    fields = (
        "projectId", "agentId", "identityRevision", "chatBindingId",
        "targetJobId", "targetDispatchRevision",
    )
    for field in fields:
        if evidence.get(field) != expected.get(field):
            raise GoEvidenceValidationError(f"GO_EVIDENCE_BINDING_MISMATCH:{field}")


def prepare_go_claim(
    *,
    job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_state_revision: int,
    consumed_activation_ids: set[str] | frozenset[str] | None,
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Prepare a non-authoritative provider CAS intent; do not consume GO yet."""
    state = deepcopy(dict(_mapping(job_state, "jobState")))
    if state.get("format") != "SAFOR_AGENT_JOB_STATE":
        raise GoEvidenceValidationError("JOB_STATE_FORMAT_INVALID")
    if state.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("JOB_STATE_SCHEMA_VERSION_INVALID")
    if state.get("lifecycleStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("JOB_NOT_WAITING_HUMAN_GO")
    if state.get("revision") != expected_state_revision:
        raise GoEvidenceValidationError("JOB_STATE_REVISION_CONFLICT")
    expected = {
        "projectId": state.get("projectId"),
        "agentId": state.get("assignedAgentId"),
        "identityRevision": state.get("assignedIdentityRevision"),
        "chatBindingId": state.get("chatBindingId"),
        "targetJobId": state.get("jobId"),
        "targetDispatchRevision": state.get("dispatchRevision"),
    }
    validate_human_go_evidence(
        go_evidence,
        expected=expected,
        consumed_activation_ids=set(consumed_activation_ids or ()),
    )
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(go_evidence_ref.get(field), f"GO_EVIDENCE_REF_{field.upper()}_MISSING")
    activation_id = str(go_evidence["activationId"])
    proposed = deepcopy(state)
    proposed["revision"] = expected_state_revision + 1
    proposed["lifecycleStatus"] = "CLAIMED"
    proposed["claimConfirmationStatus"] = "PENDING_PROVIDER_CAS_READBACK"
    proposed["goEvidenceRef"] = dict(go_evidence_ref)
    proposed.setdefault("transitionHistory", []).extend(
        [
            {"from": "WAITING_HUMAN_GO", "to": "GO_OBSERVED", "at": go_evidence["observedAt"], "actorId": go_evidence["agentId"], "evidenceRefs": [str(go_evidence_ref["path"])]},
            {"from": "GO_OBSERVED", "to": "CLAIMED", "at": go_evidence["observedAt"], "actorId": go_evidence["agentId"], "evidenceRefs": [str(go_evidence_ref["path"])]},
        ]
    )
    proposed["updatedAt"] = go_evidence["observedAt"]
    return {
        "format": "SAFOR_GO_CLAIM_INTENT",
        "schemaVersion": "0.14.0",
        "authoritative": False,
        "activationId": activation_id,
        "expectedRevision": expected_state_revision,
        "proposedRevision": expected_state_revision + 1,
        "requiredProviderSequence": ["CAS_COMMIT_EXPECTED_REVISION", "PROVIDER_READBACK", "PERSIST_ACTIVATION_CONSUMPTION"],
        "proposedState": proposed,
    }


def confirm_go_claim_after_provider_readback(
    *,
    claim_intent: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
    consumed_activation_ids: MutableSet[str],
) -> dict[str, Any]:
    """Confirm authority only after provider CAS and readback prove the claim."""
    intent = _mapping(claim_intent, "claimIntent")
    readback = _mapping(provider_readback, "providerReadback")
    if intent.get("format") != "SAFOR_GO_CLAIM_INTENT" or intent.get("authoritative") is not False:
        raise GoEvidenceValidationError("GO_CLAIM_INTENT_INVALID")
    activation_id = _nonempty(intent.get("activationId"), "GO_ACTIVATION_ID_MISSING")
    if activation_id in consumed_activation_ids:
        raise GoEvidenceValidationError("GO_EVIDENCE_ALREADY_CONSUMED")
    if readback.get("casSucceeded") is not True:
        raise GoEvidenceValidationError("PROVIDER_CAS_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_READBACK_UNVERIFIED")
    if readback.get("observedRevision") != intent.get("proposedRevision"):
        raise GoEvidenceValidationError("PROVIDER_CLAIM_REVISION_MISMATCH")
    if readback.get("observedLifecycleStatus") != "CLAIMED":
        raise GoEvidenceValidationError("PROVIDER_CLAIM_STATUS_MISMATCH")
    if readback.get("observedActivationId") != activation_id:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_ACTIVATION_MISMATCH")
    state = deepcopy(dict(_mapping(intent.get("proposedState"), "proposedState")))
    consumed_activation_ids.add(activation_id)
    state["consumedActivationIds"] = sorted(set(state.get("consumedActivationIds") or ()) | {activation_id})
    state["claimConfirmationStatus"] = "CONFIRMED_PROVIDER_CAS_READBACK"
    state["claimProviderReadbackRef"] = readback.get("readbackRef")
    return state


def atomically_observe_go_and_claim(
    *,
    job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_state_revision: int,
    consumed_activation_ids: MutableSet[str],
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility alias returning a non-authoritative claim intent.

    Provider CAS and readback remain mandatory; use
    confirm_go_claim_after_provider_readback() before treating CLAIMED as true.
    """
    return prepare_go_claim(
        job_state=job_state,
        go_evidence=go_evidence,
        expected_state_revision=expected_state_revision,
        consumed_activation_ids=set(consumed_activation_ids),
        go_evidence_ref=go_evidence_ref,
    )
