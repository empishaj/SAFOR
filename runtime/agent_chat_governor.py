from __future__ import annotations

from typing import Any, Mapping


class AgentChatStatusError(ValueError):
    pass


def _clean(value: Any, field: str, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    text = str(value or "").strip()
    if required and not text:
        raise AgentChatStatusError(f"{field} is required")
    if "\n" in text or "\r" in text:
        raise AgentChatStatusError(f"{field} must be single-line")
    return text or None


def render_agent_chat_status(event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise AgentChatStatusError("event must be an object")
    allowed = {"status", "agentId", "displayName", "jobId", "targetBranch", "gitRef"}
    unknown = sorted(set(event) - allowed)
    if unknown:
        raise AgentChatStatusError("AGENT_CHAT_SUBSTANTIVE_OR_UNKNOWN_FIELDS_FORBIDDEN: " + ", ".join(unknown))
    status = _clean(event.get("status"), "status")
    if status not in {"STARTED", "SUBMITTED", "BLOCKED", "REBIND_REQUIRED"}:
        raise AgentChatStatusError(f"unsupported status: {status}")
    agent_id = _clean(event.get("agentId"), "agentId")
    display_name = _clean(event.get("displayName"), "displayName")
    job_id = _clean(event.get("jobId"), "jobId", required=status != "REBIND_REQUIRED")
    branch = _clean(event.get("targetBranch"), "targetBranch", required=False)
    git_ref = _clean(event.get("gitRef"), "gitRef", required=False)
    if status == "STARTED":
        text = f"GO bestätigt | Agent: {display_name} ({agent_id}) | Job: {job_id} | Status: RUNNING"
        if branch:
            text += f" | Zielbranch: {branch}"
    elif status == "SUBMITTED":
        if not git_ref:
            raise AgentChatStatusError("gitRef is required for SUBMITTED")
        text = f"Job {job_id} abgeschlossen | Status: SUBMITTED | Ergebnis und Response: {git_ref}"
    elif status == "BLOCKED":
        if not git_ref:
            raise AgentChatStatusError("gitRef is required for BLOCKED")
        text = f"Job {job_id} blockiert | Meldung: {git_ref} | MASTER-Klärung erforderlich"
    else:
        text = f"Agent {display_name} ({agent_id}) | Status: REBIND_REQUIRED | MASTER-Bindung erforderlich"
    if len(text) > 240 or "\n" in text or "\r" in text:
        raise AgentChatStatusError("AGENT_CHAT_STATUS_BUDGET_EXCEEDED")
    return {
        "format": "SAFOR_AGENT_CHAT_STATUS",
        "schemaVersion": "0.13.0",
        "chatStatusId": f"chat-status:{agent_id}:{job_id or 'rebind'}:{status.lower()}",
        "agentId": agent_id,
        "displayName": display_name,
        "jobId": job_id,
        "status": status,
        "targetBranch": branch,
        "gitRef": git_ref,
        "renderedText": text,
    }
