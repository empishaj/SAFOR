from __future__ import annotations

from typing import Any, Iterable, Mapping


class MasterStatusIndexError(ValueError):
    pass


def build_master_status_index(
    *,
    project_id: str,
    revision: int,
    authoritative_control_state_ref: str,
    registry_ref: str,
    scheduler_state_ref: str,
    generated_at: str,
    provider_readback_ref: str,
    registry: Mapping[str, Any],
    job_states: Iterable[Mapping[str, Any]],
    responses: Iterable[Mapping[str, Any]],
    reviews: Iterable[Mapping[str, Any]] = (),
    blockers: Iterable[Mapping[str, Any]] = (),
    next_human_actions: Iterable[Mapping[str, Any]] = (),
    stale_pointers: Iterable[str] = (),
) -> dict[str, Any]:
    required_strings = {
        "project_id": project_id,
        "authoritative_control_state_ref": authoritative_control_state_ref,
        "registry_ref": registry_ref,
        "scheduler_state_ref": scheduler_state_ref,
        "generated_at": generated_at,
        "provider_readback_ref": provider_readback_ref,
    }
    for name, value in required_strings.items():
        if not isinstance(value, str) or not value:
            raise MasterStatusIndexError(f"{name} is required")
    registry_agents = registry.get("agents")
    if not isinstance(registry_agents, list):
        raise MasterStatusIndexError("registry.agents must be a list")
    response_by_job = {str(r.get("jobId")): r for r in responses}
    jobs = []
    active_by_agent: dict[str, str] = {}
    last_response_by_agent: dict[str, str] = {}
    for state in job_states:
        job_id = str(state.get("jobId", ""))
        agent_id = str(state.get("assignedAgentId", ""))
        if not job_id or not agent_id:
            raise MasterStatusIndexError("job state missing jobId/assignedAgentId")
        response = response_by_job.get(job_id)
        status = str(state.get("lifecycleStatus", "UNKNOWN"))
        if status in {"READY", "CLAIMED", "RUNNING", "BLOCKED", "REWORK_READY"}:
            active_by_agent[agent_id] = job_id
        if response:
            last_response_by_agent[agent_id] = str(response.get("responseRef") or response.get("responseId"))
        jobs.append(
            {
                "jobId": job_id,
                "agentId": agent_id,
                "lifecycleStatus": status,
                "jobRef": str(state.get("contractRef", "")),
                "responseRef": str(response.get("responseRef") or response.get("responseId")) if response else None,
                "reviewRef": state.get("reviewRef"),
            }
        )
    agents = []
    for entry in registry_agents:
        agent_id = str(entry.get("agentId", ""))
        display_name = str(entry.get("displayName", ""))
        if not agent_id or not display_name:
            raise MasterStatusIndexError("registry entry missing agentId/displayName")
        current_job = active_by_agent.get(agent_id)
        agents.append(
            {
                "agentId": agent_id,
                "displayName": display_name,
                "status": str(entry.get("status", "UNKNOWN")),
                "currentJobId": current_job,
                "lastResponseRef": last_response_by_agent.get(agent_id),
                "startRequired": any(
                    j["agentId"] == agent_id and j["lifecycleStatus"] in {"READY", "REWORK_READY"}
                    for j in jobs
                ),
            }
        )
    return {
        "format": "SAFOR_MASTER_STATUS_INDEX",
        "schemaVersion": "0.13.0",
        "projectId": project_id,
        "revision": revision,
        "authoritativeControlStateRef": authoritative_control_state_ref,
        "registryRef": registry_ref,
        "schedulerStateRef": scheduler_state_ref,
        "generatedAt": generated_at,
        "providerReadbackRef": provider_readback_ref,
        "agents": agents,
        "jobs": jobs,
        "reviews": list(reviews),
        "blockers": list(blockers),
        "nextHumanActions": list(next_human_actions),
        "stalePointers": sorted(set(stale_pointers)),
    }
