"""Pure SAFOR operation-mode and Agent Runtime policy reference.

No provider I/O, agent activation, wall-clock read, randomness, or authority mutation
occurs here. The functions only evaluate pinned governance inputs.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

AUTO_CAPABILITIES = {"HOST_NATIVE_AUTOMATIC", "EXTERNAL_AUTOMATION"}
ACTIVATION_CAPABILITIES = AUTO_CAPABILITIES | {"HUMAN_MANUAL_TEST_ONLY", "UNAVAILABLE"}

FORBIDDEN_HUMAN_EXECUTION_REQUESTS = {
    "OPEN_AGENT_CHAT_FOR_ROUTINE_JOB",
    "WAKE_AGENT_CHAT",
    "COPY_JOB_PROMPT",
    "COPY_JOB_CONTRACT",
    "POLL_AGENT_INBOX",
    "MOVE_AGENT_RESULT_BETWEEN_CHATS",
    "MANUALLY_ADVANCE_DISPATCH_SEQUENCE",
}


def resolve_operation_mode(intent_class: str, target_class: str, isolated: bool) -> Dict[str, Any]:
    if intent_class == "FRAMEWORK_OR_SCHEMA_DESIGN" and target_class in {
        "FRAMEWORK_REPOSITORY", "PACKAGE_DEVELOPMENT_WORKSPACE"
    }:
        return {"outcome": "MODE_RESOLVED", "mode": "DESIGN", "humanDecisionRequired": False}

    if intent_class in {"TEST", "E2E", "REPLAY", "CONFORMANCE"}:
        if target_class != "ISOLATED_TEST_WORKSPACE" or isolated is not True:
            return {"outcome": "VALIDATION_TARGET_NOT_ISOLATED", "mode": None, "humanDecisionRequired": False}
        return {"outcome": "MODE_RESOLVED", "mode": "VALIDATION", "humanDecisionRequired": False}

    if intent_class == "HUMAN_PROJECT_VALUE_CREATION" and target_class == "HUMAN_PROJECT":
        return {"outcome": "MODE_RESOLVED", "mode": "EXECUTION", "humanDecisionRequired": False}

    return {"outcome": "MODE_AMBIGUOUS", "mode": None, "humanDecisionRequired": True}


def validate_runtime_binding(binding: Mapping[str, Any]) -> Dict[str, Any]:
    errors = []
    activation = binding.get("activationCapability")
    continuation = binding.get("continuationCapability")
    modes = set(binding.get("supportedOperationModes", []))
    adapter_kind = binding.get("adapterKind")
    evidence = binding.get("actualCapabilityEvidenceRefs", [])
    wakeup = binding.get("backgroundWakeup", {})
    bootstrap = binding.get("identityBootstrap", {})
    job_transport = binding.get("jobTransport", {})

    if activation not in ACTIVATION_CAPABILITIES:
        errors.append("UNKNOWN_ACTIVATION_CAPABILITY")
    if continuation not in ACTIVATION_CAPABILITIES:
        errors.append("UNKNOWN_CONTINUATION_CAPABILITY")
    if not evidence:
        errors.append("RUNTIME_CAPABILITY_EVIDENCE_MISSING")
    if wakeup.get("supported") is True and not wakeup.get("evidenceRef"):
        errors.append("BACKGROUND_WAKEUP_EVIDENCE_MISSING")
    if job_transport.get("mode") != "REPOSITORY_PULL":
        errors.append("JOB_TRANSPORT_NOT_REPOSITORY_PULL")
    if job_transport.get("promptTransportForbidden") is not True:
        errors.append("JOB_PROMPT_TRANSPORT_NOT_FORBIDDEN")
    if bootstrap.get("jobContractTransportForbidden") is not True:
        errors.append("IDENTITY_BOOTSTRAP_COULD_TRANSPORT_JOB")

    if adapter_kind == "MANUAL_TEST_HARNESS":
        if activation != "HUMAN_MANUAL_TEST_ONLY" or continuation != "HUMAN_MANUAL_TEST_ONLY":
            errors.append("MANUAL_HARNESS_CAPABILITY_MISMATCH")
        if modes != {"VALIDATION"}:
            errors.append("MANUAL_HARNESS_MODE_MISMATCH")
        if bootstrap.get("mode") != "ONE_TIME_MANUAL_TEST_ONLY":
            errors.append("MANUAL_HARNESS_BOOTSTRAP_MISMATCH")

    if "EXECUTION" in modes and (
        activation not in AUTO_CAPABILITIES or continuation not in AUTO_CAPABILITIES
    ):
        errors.append("EXECUTION_AUTOMATION_CAPABILITY_MISSING")

    return {"valid": not errors, "errors": errors}


def evaluate_agent_dispatch(
    operation_mode: str,
    binding: Mapping[str, Any] | None,
    agent_work_required: bool = True,
) -> Dict[str, Any]:
    if not agent_work_required:
        return {
            "allowed": True,
            "outcome": "NO_AGENT_RUNTIME_REQUIRED",
            "humanOperationalActionRequired": False,
        }

    if binding is None:
        return {
            "allowed": False,
            "outcome": "AGENT_RUNTIME_CAPABILITY_UNVERIFIED",
            "humanOperationalActionRequired": False,
        }

    validated = validate_runtime_binding(binding)
    if not validated["valid"]:
        return {
            "allowed": False,
            "outcome": "AGENT_RUNTIME_CAPABILITY_UNVERIFIED",
            "errors": validated["errors"],
            "humanOperationalActionRequired": False,
        }

    if operation_mode not in binding.get("supportedOperationModes", []):
        return {
            "allowed": False,
            "outcome": "AGENT_RUNTIME_MODE_INCOMPATIBLE",
            "humanOperationalActionRequired": False,
        }

    activation = binding["activationCapability"]
    continuation = binding["continuationCapability"]

    if operation_mode == "EXECUTION":
        if activation not in AUTO_CAPABILITIES or continuation not in AUTO_CAPABILITIES:
            return {
                "allowed": False,
                "outcome": "AGENT_RUNTIME_AUTOMATION_UNAVAILABLE",
                "humanOperationalActionRequired": False,
            }
        return {
            "allowed": True,
            "outcome": "AGENT_DISPATCH_ALLOWED",
            "activationResponsibility": "SYSTEM_RUNTIME",
            "productionEvidenceEligible": True,
            "humanOperationalActionRequired": False,
        }

    if operation_mode == "VALIDATION":
        if activation == "HUMAN_MANUAL_TEST_ONLY":
            return {
                "allowed": True,
                "outcome": "MANUAL_VALIDATION_HARNESS_ALLOWED",
                "activationResponsibility": "HUMAN_TEST_HARNESS",
                "productionEvidenceEligible": False,
                "humanOperationalActionRequired": True,
            }
        if activation in AUTO_CAPABILITIES and continuation in AUTO_CAPABILITIES:
            return {
                "allowed": True,
                "outcome": "AGENT_DISPATCH_ALLOWED",
                "activationResponsibility": "SYSTEM_RUNTIME",
                "productionEvidenceEligible": False,
                "humanOperationalActionRequired": False,
            }
        return {
            "allowed": False,
            "outcome": "AGENT_RUNTIME_AUTOMATION_UNAVAILABLE",
            "humanOperationalActionRequired": False,
        }

    if operation_mode == "DESIGN":
        if activation in AUTO_CAPABILITIES and continuation in AUTO_CAPABILITIES:
            return {
                "allowed": True,
                "outcome": "AGENT_DISPATCH_ALLOWED",
                "activationResponsibility": "SYSTEM_RUNTIME",
                "productionEvidenceEligible": False,
                "humanOperationalActionRequired": False,
            }
        return {
            "allowed": False,
            "outcome": "AGENT_RUNTIME_AUTOMATION_UNAVAILABLE",
            "humanOperationalActionRequired": False,
        }

    return {
        "allowed": False,
        "outcome": "OPERATION_MODE_UNRESOLVED",
        "humanOperationalActionRequired": False,
    }


def human_activation_request_allowed(operation_mode: str, request_type: str) -> bool:
    if operation_mode == "EXECUTION" and request_type in FORBIDDEN_HUMAN_EXECUTION_REQUESTS:
        return False
    if operation_mode == "VALIDATION" and request_type == "OPEN_AGENT_CHAT_FOR_ROUTINE_JOB":
        return True
    return request_type not in FORBIDDEN_HUMAN_EXECUTION_REQUESTS


def can_recover_by_mode_change(current_mode: str, proposed_mode: str, reason: str) -> bool:
    if current_mode == "EXECUTION" and proposed_mode == "VALIDATION" and reason == "MISSING_AGENT_AUTOMATION":
        return False
    return current_mode == proposed_mode
