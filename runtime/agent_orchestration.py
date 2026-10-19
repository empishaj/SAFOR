from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from runtime.agent_recovery import AgentRecoveryError, build_blocked_supersession_recovery_plan


class AgentOrchestrationError(ValueError):
    """Base error for deterministic SAFOR agent-orchestration checks."""


class AgentIdentityError(AgentOrchestrationError):
    """Raised when a CHAT_AGENT identity is not safe to use."""


@dataclass(frozen=True)
class ActivationDecision:
    allowed: bool
    outcome: str
    reason_code: str
    selected_job: Mapping[str, Any] | None = None
    activation_evidence: Mapping[str, Any] | None = None
    recovery_plan: Mapping[str, Any] | None = None
    required_reads: tuple[str, ...] = ()
    forbidden_reads: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "outcome": self.outcome,
            "reasonCode": self.reason_code,
            "selectedJob": dict(self.selected_job) if self.selected_job else None,
            "activationEvidence": (
                dict(self.activation_evidence) if self.activation_evidence else None
            ),
            "recoveryPlan": (
                dict(self.recovery_plan) if self.recovery_plan else None
            ),
            "requiredReads": list(self.required_reads),
            "forbiddenReads": list(self.forbidden_reads),
        }


_REQUIRED_BOOTSTRAP_FIELDS = {
    "CONTROL_REPOSITORY",
    "PROJECT_ID",
    "AGENT_ID",
    "DISPLAY_NAME",
    "IDENTITY_REF",
    "AGENT_STATE_REF",
    "INBOX_INDEX_REF",
    "INBOX_INDEX_LOCATION",
    "COMMUNICATION_CONTRACT_REF",
}

_REQUIRED_GO_STEPS = {
    "LOAD_IDENTITY",
    "VERIFY_IDENTITY_STATUS_ACTIVE",
    "VERIFY_PERSONAL_INBOX_BINDING",
    "LOAD_AGENT_STATE",
    "LOAD_PERSONAL_INBOX_INDEX",
    "SELECT_DISCOVERABLE_JOB",
    "READ_AUTHORITATIVE_JOB_JSON",
    "READ_MASTER_JOB_STATE",
    "BIND_HUMAN_GO_EVIDENCE",
    "VERIFY_ASSIGNMENT_ROLE_SKILLS_MANDATE_RIGHTS",
    "CLAIM_WITH_OPTIMISTIC_CONCURRENCY",
    "EXECUTE_ONLY_CLAIMED_JOB",
    "SUBMIT_TYPED_RESPONSE_AND_EVIDENCE",
}

_ALLOWED_READS = (
    "PINNED_IDENTITY",
    "AGENT_STATE",
    "PERSONAL_INBOX_INDEX",
    "SELECTED_JOB_CONTRACT",
    "SELECTED_MASTER_JOB_STATE",
    "JOB_REFERENCED_INPUTS_ONLY",
)

_FORBIDDEN_READS = (
    "GLOBAL_REPOSITORY_SEARCH",
    "OTHER_AGENT_INBOX_READ",
    "PROJECT_TREE_FULL_SCAN",
    "UNREFERENCED_ARTIFACT_DISCOVERY",
)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentIdentityError(f"{name} must be a mapping")
    return value


def _normalized(value: Any) -> str:
    return " ".join(str(value).strip().casefold().split())


def validate_chat_agent_identity(identity: Mapping[str, Any]) -> None:
    """Validate the invariants that make a persistent chat identity safe.

    This function is reference validation for CI/hosts. The normative rules are
    carried in the JSON models and schemas; installing this Python module is not
    required for normal end-user chat use.
    """

    identity = _mapping(identity, "identity")
    if identity.get("format") != "SAFOR_AGENT_IDENTITY":
        raise AgentIdentityError("IDENTITY_FORMAT_INVALID")
    if identity.get("schemaVersion") != "0.14.0":
        raise AgentIdentityError("IDENTITY_SCHEMA_VERSION_INVALID")
    if identity.get("agentKind") != "CHAT_AGENT":
        raise AgentIdentityError("NOT_A_CHAT_AGENT")
    if identity.get("status") != "ACTIVE":
        raise AgentIdentityError("IDENTITY_NOT_ACTIVE")

    agent_id = str(identity.get("agentId", "")).strip()
    display_name = str(identity.get("displayName", "")).strip()
    if len(agent_id) < 3:
        raise AgentIdentityError("AGENT_ID_INVALID")
    if len(display_name) < 3:
        raise AgentIdentityError("DISPLAY_NAME_INVALID")
    if _normalized(agent_id) == _normalized(display_name):
        raise AgentIdentityError("DISPLAY_NAME_MUST_DIFFER_FROM_AGENT_ID")

    inbox_binding = _mapping(identity.get("inboxBinding"), "inboxBinding")
    if inbox_binding.get("agentId") != agent_id:
        raise AgentIdentityError("INBOX_BINDING_AGENT_MISMATCH")
    if inbox_binding.get("identityRevision") != identity.get("identityRevision"):
        raise AgentIdentityError("INBOX_BINDING_IDENTITY_REVISION_MISMATCH")
    inbox_ref = _mapping(inbox_binding.get("inboxIndexRef"), "inboxIndexRef")
    inbox_location = _mapping(
        inbox_binding.get("inboxIndexLocation"), "inboxIndexLocation"
    )
    expected_suffix = f"agents/{agent_id}/inbox/index.json"
    if not str(inbox_ref.get("path", "")).endswith(expected_suffix):
        raise AgentIdentityError("INBOX_BINDING_BOOTSTRAP_PATH_INVALID")
    if not str(inbox_location.get("path", "")).endswith(expected_suffix):
        raise AgentIdentityError("INBOX_BINDING_LOCATION_PATH_INVALID")
    if inbox_location.get("path") != inbox_ref.get("path"):
        raise AgentIdentityError("INBOX_BOOTSTRAP_AND_LOCATION_PATH_MISMATCH")
    control_repository = _mapping(identity.get("controlRepository"), "controlRepository")
    if inbox_location.get("repository") != control_repository.get("repository"):
        raise AgentIdentityError("INBOX_LOCATION_REPOSITORY_MISMATCH")
    if inbox_location.get("ref") != control_repository.get("ref"):
        raise AgentIdentityError("INBOX_LOCATION_REF_MISMATCH")
    if inbox_binding.get("jobPathPattern") != "agents/{agentId}/inbox/{jobId}.json":
        raise AgentIdentityError("INBOX_JOB_PATH_PATTERN_INVALID")

    activation = _mapping(identity.get("activationContract"), "activationContract")
    expected_false = (
        "backgroundWakeupAssumed",
        "automationActivationAllowed",
        "hostTriggerActivationAllowed",
        "gitEventActivationAllowed",
        "schedulerMayActivateChat",
        "jobPromptTransportRequired",
    )
    if activation.get("activationMode") != "HUMAN_GO_REQUIRED":
        raise AgentIdentityError("CHAT_AGENT_MUST_REQUIRE_HUMAN_GO")
    if activation.get("acceptedToken") != "GO":
        raise AgentIdentityError("HUMAN_GO_TOKEN_INVALID")
    if activation.get("additionalTextAllowed") is not False:
        raise AgentIdentityError("GO_MUST_NOT_CARRY_JOB_PROMPT")
    for field in expected_false:
        if activation.get(field) is not False:
            raise AgentIdentityError(f"{field.upper()}_MUST_BE_FALSE")

    bootstrap_fields = set(activation.get("initialBootstrapFields") or ())
    if bootstrap_fields != _REQUIRED_BOOTSTRAP_FIELDS:
        raise AgentIdentityError("INITIAL_BOOTSTRAP_FIELDS_INCOMPLETE")
    go_steps = set(activation.get("onGo") or ())
    if not _REQUIRED_GO_STEPS.issubset(go_steps):
        raise AgentIdentityError("ON_GO_PROTOCOL_INCOMPLETE")


def _eligible_entries(
    inbox_index: Mapping[str, Any], identity_revision: int
) -> list[Mapping[str, Any]]:
    if inbox_index.get("format") != "SAFOR_AGENT_INBOX_INDEX":
        return []
    if inbox_index.get("schemaVersion") != "0.14.0":
        return []
    if inbox_index.get("directoryEnumerationRequired") is not False:
        return []

    entries: list[Mapping[str, Any]] = []
    for raw in inbox_index.get("entries") or ():
        if not isinstance(raw, Mapping):
            continue
        if raw.get("requiredIdentityRevision") != identity_revision:
            continue
        if raw.get("discoverabilityState") not in {"AVAILABLE", "REWORK_AVAILABLE"}:
            continue
        if raw.get("activationState") != "WAITING_HUMAN_GO":
            continue
        entries.append(raw)
    return entries


def evaluate_human_go_activation(
    *,
    identity: Mapping[str, Any],
    agent_state: Mapping[str, Any],
    inbox_index: Mapping[str, Any],
    human_message: str,
    activation_id: str,
    observed_at: str,
    response_resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one deliberate HUMAN-GO activation without mutating repositories."""

    try:
        validate_chat_agent_identity(identity)
    except AgentIdentityError as exc:
        return ActivationDecision(
            allowed=False,
            outcome="REIDENTIFICATION_REQUIRED",
            reason_code=str(exc),
            required_reads=_ALLOWED_READS[:3],
            forbidden_reads=_FORBIDDEN_READS,
        ).as_dict()

    agent_id = str(identity["agentId"])
    revision = int(identity["identityRevision"])
    if agent_state.get("format") != "SAFOR_AGENT_STATE":
        reason = "AGENT_STATE_FORMAT_INVALID"
    elif agent_state.get("schemaVersion") != "0.14.0":
        reason = "AGENT_STATE_SCHEMA_VERSION_INVALID"
    elif agent_state.get("agentId") != agent_id:
        reason = "AGENT_STATE_AGENT_MISMATCH"
    elif agent_state.get("identityRevision") != revision:
        reason = "AGENT_STATE_IDENTITY_REVISION_MISMATCH"
    elif agent_state.get("runtimeStatus") not in {"IDLE", "WAITING_HUMAN_GO", "BLOCKED"}:
        reason = "AGENT_NOT_WAITING_FOR_GO"
    else:
        reason = ""

    if reason:
        return ActivationDecision(
            allowed=False,
            outcome="BLOCKED",
            reason_code=reason,
            required_reads=_ALLOWED_READS[:3],
            forbidden_reads=_FORBIDDEN_READS,
        ).as_dict()

    activation = _mapping(identity["activationContract"], "activationContract")
    token = str(activation["acceptedToken"])
    incoming = str(human_message).strip()
    if activation.get("tokenCaseSensitive") is False:
        matches = incoming.casefold() == token.casefold()
    else:
        matches = incoming == token
    if not matches:
        return ActivationDecision(
            allowed=False,
            outcome="WAITING_HUMAN_GO",
            reason_code="EXACT_HUMAN_GO_REQUIRED",
            required_reads=_ALLOWED_READS[:3],
            forbidden_reads=_FORBIDDEN_READS,
        ).as_dict()

    if inbox_index.get("projectId") != identity.get("projectId"):
        reason = "INBOX_PROJECT_MISMATCH"
    elif inbox_index.get("agentId") != agent_id:
        reason = "INBOX_AGENT_MISMATCH"
    elif inbox_index.get("identityRevision") != revision:
        reason = "INBOX_IDENTITY_REVISION_MISMATCH"
    else:
        reason = ""

    if reason:
        return ActivationDecision(
            allowed=False,
            outcome="REIDENTIFICATION_REQUIRED",
            reason_code=reason,
            required_reads=_ALLOWED_READS[:3],
            forbidden_reads=_FORBIDDEN_READS,
        ).as_dict()

    eligible = _eligible_entries(inbox_index, revision)
    if not eligible:
        return ActivationDecision(
            allowed=False,
            outcome="WAITING_HUMAN_GO",
            reason_code="NO_DISCOVERABLE_JOB_FOR_ACTIVE_IDENTITY",
            required_reads=_ALLOWED_READS[:3],
            forbidden_reads=_FORBIDDEN_READS,
        ).as_dict()

    selected = eligible[0]
    evidence = {
        "format": "SAFOR_HUMAN_GO_EVIDENCE",
        "schemaVersion": "0.14.0",
        "activationId": activation_id,
        "projectId": identity["projectId"],
        "agentId": agent_id,
        "identityRevision": revision,
        "targetJobId": selected["jobId"],
        "targetDispatchRevision": selected["dispatchRevision"],
        "intent": "GO",
        "source": "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT",
        "observedAt": observed_at,
        "singleUse": True,
        "jobPromptTransported": False,
    }
    return ActivationDecision(
        allowed=True,
        outcome="PREFLIGHT_REQUIRED",
        reason_code="HUMAN_GO_BOUND_TO_PERSONAL_INBOX_JOB",
        selected_job=selected,
        activation_evidence=evidence,
        required_reads=_ALLOWED_READS,
        forbidden_reads=_FORBIDDEN_READS,
    ).as_dict()
