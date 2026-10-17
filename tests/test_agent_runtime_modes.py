import unittest

from runtime.agent_runtime_policy import (
    can_recover_by_mode_change,
    evaluate_agent_dispatch,
    human_activation_request_allowed,
    resolve_operation_mode,
    validate_runtime_binding,
)


def binding(
    activation="HOST_NATIVE_AUTOMATIC",
    continuation="HOST_NATIVE_AUTOMATIC",
    modes=None,
    adapter_kind="HOST_NATIVE",
    wakeup=False,
):
    if modes is None:
        modes = ["DESIGN", "VALIDATION", "EXECUTION"]
    return {
        "format": "SAFOR_AGENT_RUNTIME_BINDING",
        "schemaVersion": "0.12.0",
        "bindingRevision": 1,
        "adapterId": "runtime-1",
        "adapterKind": adapter_kind,
        "adapterRef": "runtime://runtime-1",
        "activationCapability": activation,
        "continuationCapability": continuation,
        "supportedOperationModes": modes,
        "backgroundWakeup": {
            "supported": wakeup,
            "evidenceRef": "evidence://wakeup" if wakeup else None,
        },
        "identityBootstrap": {
            "mode": "AUTOMATIC" if adapter_kind != "MANUAL_TEST_HARNESS" else "ONE_TIME_MANUAL_TEST_ONLY",
            "jobContractTransportForbidden": True,
        },
        "jobTransport": {
            "mode": "REPOSITORY_PULL",
            "promptTransportForbidden": True,
        },
        "stateObservation": {"mode": "RUNTIME_NATIVE"},
        "resultAvailability": {"mode": "REPOSITORY_READBACK"},
        "actualCapabilityEvidenceRefs": ["evidence://runtime-capabilities"],
    }


class AgentRuntimeModeTests(unittest.TestCase):
    def test_design_mode_is_derived_for_framework_schema_work(self):
        result = resolve_operation_mode("FRAMEWORK_OR_SCHEMA_DESIGN", "FRAMEWORK_REPOSITORY", False)
        self.assertEqual("DESIGN", result["mode"])
        self.assertFalse(result["humanDecisionRequired"])

    def test_validation_requires_isolated_target(self):
        result = resolve_operation_mode("E2E", "HUMAN_PROJECT", False)
        self.assertEqual("VALIDATION_TARGET_NOT_ISOLATED", result["outcome"])
        self.assertIsNone(result["mode"])

    def test_execution_mode_is_derived_for_human_project_value_creation(self):
        result = resolve_operation_mode("HUMAN_PROJECT_VALUE_CREATION", "HUMAN_PROJECT", False)
        self.assertEqual("EXECUTION", result["mode"])

    def test_ambiguous_mode_requires_human_decision(self):
        result = resolve_operation_mode("UNKNOWN", "HUMAN_PROJECT", False)
        self.assertEqual("MODE_AMBIGUOUS", result["outcome"])
        self.assertTrue(result["humanDecisionRequired"])

    def test_execution_accepts_host_native_automatic(self):
        result = evaluate_agent_dispatch("EXECUTION", binding())
        self.assertTrue(result["allowed"])
        self.assertEqual("SYSTEM_RUNTIME", result["activationResponsibility"])
        self.assertTrue(result["productionEvidenceEligible"])

    def test_execution_accepts_external_automation(self):
        result = evaluate_agent_dispatch(
            "EXECUTION",
            binding("EXTERNAL_AUTOMATION", "EXTERNAL_AUTOMATION", adapter_kind="EXTERNAL_ORCHESTRATOR"),
        )
        self.assertTrue(result["allowed"])

    def test_execution_rejects_manual_test_harness(self):
        manual = binding(
            "HUMAN_MANUAL_TEST_ONLY",
            "HUMAN_MANUAL_TEST_ONLY",
            ["VALIDATION"],
            "MANUAL_TEST_HARNESS",
        )
        result = evaluate_agent_dispatch("EXECUTION", manual)
        self.assertFalse(result["allowed"])
        self.assertIn(result["outcome"], {"AGENT_RUNTIME_MODE_INCOMPATIBLE", "AGENT_RUNTIME_AUTOMATION_UNAVAILABLE"})
        self.assertFalse(result["humanOperationalActionRequired"])

    def test_validation_allows_manual_harness_but_marks_nonproduction(self):
        manual = binding(
            "HUMAN_MANUAL_TEST_ONLY",
            "HUMAN_MANUAL_TEST_ONLY",
            ["VALIDATION"],
            "MANUAL_TEST_HARNESS",
        )
        result = evaluate_agent_dispatch("VALIDATION", manual)
        self.assertTrue(result["allowed"])
        self.assertEqual("HUMAN_TEST_HARNESS", result["activationResponsibility"])
        self.assertFalse(result["productionEvidenceEligible"])
        self.assertTrue(result["humanOperationalActionRequired"])

    def test_execution_without_agent_work_needs_no_runtime(self):
        result = evaluate_agent_dispatch("EXECUTION", None, agent_work_required=False)
        self.assertTrue(result["allowed"])
        self.assertEqual("NO_AGENT_RUNTIME_REQUIRED", result["outcome"])

    def test_background_wakeup_requires_evidence(self):
        b = binding(wakeup=True)
        b["backgroundWakeup"]["evidenceRef"] = None
        result = validate_runtime_binding(b)
        self.assertFalse(result["valid"])
        self.assertIn("BACKGROUND_WAKEUP_EVIDENCE_MISSING", result["errors"])

    def test_job_prompt_transport_must_be_forbidden(self):
        b = binding()
        b["jobTransport"]["promptTransportForbidden"] = False
        result = validate_runtime_binding(b)
        self.assertFalse(result["valid"])
        self.assertIn("JOB_PROMPT_TRANSPORT_NOT_FORBIDDEN", result["errors"])

    def test_execution_human_chat_wakeup_request_is_forbidden(self):
        self.assertFalse(human_activation_request_allowed("EXECUTION", "WAKE_AGENT_CHAT"))
        self.assertFalse(human_activation_request_allowed("EXECUTION", "COPY_JOB_CONTRACT"))

    def test_validation_manual_chat_activation_can_be_test_harness(self):
        self.assertTrue(human_activation_request_allowed("VALIDATION", "OPEN_AGENT_CHAT_FOR_ROUTINE_JOB"))

    def test_recovery_cannot_downgrade_execution_to_validation_for_missing_automation(self):
        self.assertFalse(can_recover_by_mode_change("EXECUTION", "VALIDATION", "MISSING_AGENT_AUTOMATION"))

    def test_runtime_binding_does_not_need_to_exist_when_no_agent_work_is_requested(self):
        result = evaluate_agent_dispatch("DESIGN", None, agent_work_required=False)
        self.assertTrue(result["allowed"])


if __name__ == "__main__":
    unittest.main()
