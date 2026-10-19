from __future__ import annotations

from typing import Any, Mapping


class AgentRecoveryError(ValueError):
    """Raised when a BLOCKED agent cannot safely enter supersession recovery."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentRecoveryError(f"{name} must be a mapping")
    return value


def build_blocked_supersession_recovery_plan(
    *,
    agent_state: Mapping[str, Any],
    selected_job: Mapping[str, Any],
    response_resolution: Mapping[str, Any] | None,
    fresh_activation_id: str,
) -> dict[str, Any]:
    """Validate MASTER resolution and derive a non-mutating recovery plan.

    The caller still has to perform provider CAS/readback on agent state.
    Recovery never mutates product state and never consumes the fresh GO.
    """

    if agent_state.get("runtimeStatus") != "BLOCKED":
        raise AgentRecoveryError("AGENT_STATE_NOT_BLOCKED")
    if response_resolution is None:
        raise AgentRecoveryError("BLOCKED_STATE_REQUIRES_MASTER_RESOLUTION")

    resolution = _mapping(response_resolution, "responseResolution")
    if resolution.get("format") != "SAFOR_AGENT_RESPONSE_RESOLUTION":
        raise AgentRecoveryError("BLOCKED_RESOLUTION_FORMAT_INVALID")
    if resolution.get("schemaVersion") != "0.14.0":
        raise AgentRecoveryError("BLOCKED_RESOLUTION_SCHEMA_VERSION_INVALID")
    if resolution.get("resolutionStatus") != "SUPERSEDED_BY_JOB":
        raise AgentRecoveryError("BLOCKED_RESPONSE_NOT_SUPERSEDED_BY_JOB")
    if resolution.get("supersedingJobId") != selected_job.get("jobId"):
        raise AgentRecoveryError("BLOCKED_RESOLUTION_SUPERSEDING_JOB_MISMATCH")

    current_job = _mapping(agent_state.get("currentJob"), "currentJob")
    if resolution.get("jobId") != current_job.get("jobId"):
        raise AgentRecoveryError("BLOCKED_RESOLUTION_JOB_MISMATCH")

    response_ref = _mapping(resolution.get("responseRef"), "responseRef")
    if response_ref.get("path") != agent_state.get("lastResponseRef"):
        raise AgentRecoveryError("BLOCKED_RESOLUTION_RESPONSE_REF_MISMATCH")

    if selected_job.get("dispatchRevision", 0) <= current_job.get(
        "dispatchRevision", 0
    ):
        raise AgentRecoveryError("SUPERSEDING_DISPATCH_REVISION_NOT_NEWER")

    consumed = set(agent_state.get("consumedActivationIds") or ())
    if fresh_activation_id in consumed:
        raise AgentRecoveryError("ACTIVATION_ID_ALREADY_CONSUMED")

    return {
        "mode": "BLOCKED_SUPERSESSION_RECOVERY",
        "authority": "MASTER_RESPONSE_RESOLUTION",
        "resolutionId": resolution["resolutionId"],
        "expectedAgentStateRevision": agent_state["revision"],
        "fromStatus": "BLOCKED",
        "toStatus": "WAITING_HUMAN_GO",
        "clearSession": True,
        "clearCurrentJob": True,
        "preserveLastResponseRef": True,
        "preserveConsumedActivationIds": True,
        "freshActivationIdMustRemainUnconsumedDuringRecovery": fresh_activation_id,
        "supersedingJobId": selected_job["jobId"],
        "supersedingDispatchRevision": selected_job["dispatchRevision"],
        "providerCompareAndSwapRequired": True,
        "providerReadbackRequired": True,
        "productMutationAllowedDuringRecovery": False,
    }
