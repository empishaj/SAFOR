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


def atomically_observe_go_and_claim(
    *,
    job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_state_revision: int,
    consumed_activation_ids: MutableSet[str],
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the only safe claimed state; provider compare-and-swap remains required."""
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
        consumed_activation_ids=set(consumed_activation_ids),
    )
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(go_evidence_ref.get(field), f"GO_EVIDENCE_REF_{field.upper()}_MISSING")
    activation_id = str(go_evidence["activationId"])
    consumed_activation_ids.add(activation_id)
    state["revision"] = expected_state_revision + 1
    state["lifecycleStatus"] = "CLAIMED"
    state["goEvidenceRef"] = dict(go_evidence_ref)
    state["consumedActivationIds"] = sorted(
        set(state.get("consumedActivationIds") or ()) | {activation_id}
    )
    state.setdefault("transitionHistory", []).extend(
        [
            {
                "from": "WAITING_HUMAN_GO",
                "to": "GO_OBSERVED",
                "at": go_evidence["observedAt"],
                "actorId": go_evidence["agentId"],
                "evidenceRefs": [str(go_evidence_ref["path"])],
            },
            {
                "from": "GO_OBSERVED",
                "to": "CLAIMED",
                "at": go_evidence["observedAt"],
                "actorId": go_evidence["agentId"],
                "evidenceRefs": [str(go_evidence_ref["path"])],
            },
        ]
    )
    state["updatedAt"] = go_evidence["observedAt"]
    return state
