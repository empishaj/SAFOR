from __future__ import annotations

import re
from typing import Any, Mapping


GOVERNOR_ID = "SAFOR_PLATFORM_HUMAN_RESPONSE_GOVERNOR"

_ALLOWED_DOMAIN_KEYS = {
    "facts",
    "risks",
    "requiredHumanDecision",
    "evidenceRefs",
    "nextSafeAction",
}

_FORBIDDEN_PRESENTATION_KEYS = {
    "visibleText",
    "responseText",
    "responseLength",
    "maxWords",
    "maxSentences",
    "menu",
    "terminalMenu",
    "choices",
    "headings",
    "progressiveDisclosure",
    "technicalDetailExposure",
}

_EVENT_POLICIES = {
    "FRAMEWORK_DETECTED": {
        "maxSentences": 2,
        "maxWords": 24,
        "template": (
            "Neues {domainLabel}-Framework erkannt. "
            "Ich prüfe den bestehenden Stand und plane die Migration; "
            "bis dahin ändere ich nichts."
        ),
    },
    "MIGRATION_PLANNING_STARTED": {
        "maxSentences": 2,
        "maxWords": 18,
        "template": (
            "Die Migration wird geplant. "
            "Bis der sichere Plan steht, ändere ich nichts."
        ),
    },
}


class ResponseGovernanceError(ValueError):
    """Raised when platform response governance cannot safely render."""


class HumanDecisionRequired(ResponseGovernanceError):
    """Raised when a real HUMAN decision must be routed to an interactive response."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResponseGovernanceError(f"{name} must be a mapping")
    return value


def _scan_forbidden_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_PRESENTATION_KEYS:
                found.add(str(key))
            found.update(_scan_forbidden_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_scan_forbidden_keys(child))
    return found


def _validate_domain_contribution(value: Any) -> Mapping[str, Any]:
    contribution = _mapping(value or {}, "domainContribution")
    unknown = set(contribution) - _ALLOWED_DOMAIN_KEYS
    forbidden = _scan_forbidden_keys(contribution)
    if unknown or forbidden:
        blocked = sorted(unknown | forbidden)
        raise ResponseGovernanceError(
            "DOMAIN_PRESENTATION_OVERRIDE_FORBIDDEN: " + ", ".join(blocked)
        )
    return contribution


def _sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def _word_count(text: str) -> int:
    return len(text.split())


def govern_platform_notice(event: Mapping[str, Any]) -> dict[str, Any]:
    """Create a deterministic, content-only HUMAN notice owned by SAFOR.

    Domain modules may contribute facts, risks, evidence and a genuine decision
    requirement. They cannot provide presentation controls. Events that require
    a real HUMAN decision are rejected from this non-interactive path and must
    be routed through the normal Decision Gate.
    """

    event = _mapping(event, "event")
    event_type = str(event.get("eventType", ""))
    if event_type not in _EVENT_POLICIES:
        raise ResponseGovernanceError(f"UNSUPPORTED_PLATFORM_NOTICE: {event_type}")

    contribution = _validate_domain_contribution(event.get("domainContribution", {}))
    decision_required = bool(event.get("humanDecisionRequired")) or bool(
        contribution.get("requiredHumanDecision")
    )
    material_escalation = any(
        bool(event.get(field))
        for field in (
            "scopeChangeRequired",
            "authorityChangeRequired",
            "materialRiskAcceptanceRequired",
            "irreversibleActionRequired",
            "goalConflictRequiresPriority",
        )
    )
    if decision_required or material_escalation:
        raise HumanDecisionRequired(
            "HUMAN_DECISION_REQUIRED: route through interactive Decision Gate"
        )

    policy = _EVENT_POLICIES[event_type]
    domain_label = str(event.get("domainLabel", "")).strip()
    if event_type == "FRAMEWORK_DETECTED" and not domain_label:
        raise ResponseGovernanceError("domainLabel is required for FRAMEWORK_DETECTED")

    text = policy["template"].format(domainLabel=domain_label)
    sentence_count = _sentence_count(text)
    word_count = _word_count(text)
    if sentence_count > policy["maxSentences"] or word_count > policy["maxWords"]:
        raise ResponseGovernanceError(
            "PLATFORM_RESPONSE_BUDGET_EXCEEDED: "
            f"sentences={sentence_count}, words={word_count}"
        )

    details_available = bool(
        event.get("internalDetails")
        or contribution.get("facts")
        or contribution.get("risks")
        or contribution.get("evidenceRefs")
    )
    response_id = str(event.get("eventId", "platform-notice"))
    phase = str(event.get("phase", "BOOTSTRAP"))

    return {
        "format": "SAFOR_HUMAN_RESPONSE",
        "schemaVersion": "0.10.0",
        "responseId": f"response:{response_id}",
        "phase": phase,
        "responseClass": "INFORMATIONAL_NOTICE",
        "surface": "SUMMARY",
        "content": [{"type": "STATUS", "text": text}],
        "governance": {
            "owner": "SAFOR_PLATFORM",
            "governorId": GOVERNOR_ID,
            "domainOverrideApplied": False,
            "decisionGateOutcome": "SUPPRESS_DERIVABLE",
            "detailsDisclosure": "SUMMARY_ONLY",
            "detailsAvailable": details_available,
            "evidenceRetained": True,
            "responseBudget": {
                "maxSentences": policy["maxSentences"],
                "maxWords": policy["maxWords"],
            },
        },
        "renderingContract": {
            "renderMode": "CONTENT_ONLY",
            "renderOrder": ["content"],
            "terminalElement": "content",
            "exactlyOneTerminalMenu": False,
            "contentAfterTerminalElementForbidden": True,
            "stopRenderingAfterTerminalMenu": False,
        },
    }
