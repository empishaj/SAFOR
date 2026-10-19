from __future__ import annotations

from typing import Any, Mapping

from runtime.agent_recovery import (
    AgentRecoveryError,
    build_blocked_supersession_recovery_plan,
)


def evaluate_human_go_activation_with_recovery(
    *,
    identity: Mapping[str, Any],
    agent_state: Mapping[str, Any],
    inbox_index: Mapping[str, Any],
    human_message: str,
    activation_id: str,
    observed_at: str,
    response_resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Overlay BLOCKED recovery on the normal deterministic activation path."""

    from runtime import agent_orchestration as base

    if agent_state.get("runtimeStatus") != "BLOCKED":
        return base._evaluate_human_go_activation_base(
            identity=identity,
            agent_state=agent_state,
            inbox_index=inbox_index,
            human_message=human_message,
            activation_id=activation_id,
            observed_at=observed_at,
        )

    try:
        base.validate_chat_agent_identity(identity)
    except base.AgentIdentityError as exc:
        return base.ActivationDecision(
            allowed=False,
            outcome="REIDENTIFICATION_REQUIRED",
            reason_code=str(exc),
            required_reads=base._ALLOWED_READS[:3],
            forbidden_reads=base._FORBIDDEN_READS,
        ).as_dict()

    activation = identity["activationContract"]
    token = str(activation["acceptedToken"])
    incoming = str(human_message).strip()
    matches = (
        incoming.casefold() == token.casefold()
        if activation.get("tokenCaseSensitive") is False
        else incoming == token
    )
    if not matches:
        return base.ActivationDecision(
            allowed=False,
            outcome="BLOCKED",
            reason_code="BLOCKED_STATE_REQUIRES_FRESH_HUMAN_GO_AFTER_MASTER_RESOLUTION",
            required_reads=base._ALLOWED_READS[:3],
            forbidden_reads=base._FORBIDDEN_READS,
        ).as_dict()

    consumed = set(agent_state.get("consumedActivationIds") or ())
    if activation_id in consumed:
        return base.ActivationDecision(
            allowed=False,
            outcome="BLOCKED",
            reason_code="ACTIVATION_ID_ALREADY_CONSUMED",
            required_reads=base._ALLOWED_READS[:3],
            forbidden_reads=base._FORBIDDEN_READS,
        ).as_dict()

    agent_id = str(identity["agentId"])
    revision = int(identity["identityRevision"])
    if agent_state.get("agentId") != agent_id:
        reason = "AGENT_STATE_AGENT_MISMATCH"
    elif agent_state.get("identityRevision") != revision:
        reason = "AGENT_STATE_IDENTITY_REVISION_MISMATCH"
    elif inbox_index.get("projectId") != identity.get("projectId"):
        reason = "INBOX_PROJECT_MISMATCH"
    elif inbox_index.get("agentId") != agent_id:
        reason = "INBOX_AGENT_MISMATCH"
    elif inbox_index.get("identityRevision") != revision:
        reason = "INBOX_IDENTITY_REVISION_MISMATCH"
    else:
        reason = ""
    if reason:
        return base.ActivationDecision(
            allowed=False,
            outcome="BLOCKED",
            reason_code=reason,
            required_reads=base._ALLOWED_READS[:3],
            forbidden_reads=base._FORBIDDEN_READS,
        ).as_dict()

    eligible = base._eligible_entries(inbox_index, revision)
    if not eligible:
        return base.ActivationDecision(
            allowed=False,
            outcome="BLOCKED",
            reason_code="NO_DISCOVERABLE_JOB_FOR_ACTIVE_IDENTITY",
            required_reads=base._ALLOWED_READS[:3],
            forbidden_reads=base._FORBIDDEN_READS,
        ).as_dict()
    selected = eligible[0]

    try:
        recovery_plan = build_blocked_supersession_recovery_plan(
            agent_state=agent_state,
            selected_job=selected,
            response_resolution=response_resolution,
            fresh_activation_id=activation_id,
        )
    except AgentRecoveryError as exc:
        return base.ActivationDecision(
            allowed=False,
            outcome="BLOCKED",
            reason_code=str(exc),
            required_reads=(
                "PINNED_IDENTITY",
                "AGENT_STATE",
                "BLOCKING_RESPONSE_RESOLUTION",
                "PERSONAL_INBOX_INDEX",
            ),
            forbidden_reads=base._FORBIDDEN_READS,
        ).as_dict()

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
    result = base.ActivationDecision(
        allowed=True,
        outcome="RECOVERY_THEN_PREFLIGHT_REQUIRED",
        reason_code="BLOCKED_STATE_RECOVERY_BOUND_TO_SUPERSEDING_JOB",
        selected_job=selected,
        activation_evidence=evidence,
        required_reads=(
            "PINNED_IDENTITY",
            "AGENT_STATE",
            "BLOCKING_RESPONSE_RESOLUTION",
            "PERSONAL_INBOX_INDEX",
            "SELECTED_JOB_CONTRACT",
            "SELECTED_MASTER_JOB_STATE",
            "JOB_REFERENCED_INPUTS_ONLY",
        ),
        forbidden_reads=base._FORBIDDEN_READS,
    ).as_dict()
    result["recoveryPlan"] = recovery_plan
    return result
