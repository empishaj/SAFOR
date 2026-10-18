import json
import unittest
from pathlib import Path

from runtime.agent_chat_governor import AgentChatStatusError, render_agent_chat_status
from runtime.agent_response_validation import AgentResponseError, RESPONSE_TYPES, validate_agent_response
from runtime.master_status_index import build_master_status_index

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class HumanNoticeConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.framework = load("SAFOR-FRAMEWORK.json")
        cls.modules = cls.framework["embeddedModules"]
        cls.kernel = cls.modules["kernel"]["content"]

    def test_ordinary_chat_is_primary_and_runtime_install_is_not_required(self):
        model = self.modules["chatExecution"]["content"]
        self.assertEqual(model["primaryExecutionMode"], "DECLARATIVE_LLM_CHAT")
        self.assertFalse(model["customerInstalledRuntimeRequired"])
        self.assertFalse(model["referenceImplementations"]["requiredForNormalChatUse"])
        start = (ROOT / "START-HIER.md").read_text(encoding="utf-8")
        self.assertIn("nicht erforderlich", start)
        self.assertNotIn("Host-/Runtime-Integration Pflicht", start)

    def test_human_go_is_the_only_agent_activation(self):
        bootstrap = self.modules["agentBootstrap"]["content"]
        activation = bootstrap["activationContract"]
        self.assertEqual(activation["mode"], "HUMAN_GO_ONLY")
        self.assertEqual(activation["acceptedCommand"], "GO")
        self.assertTrue({"GIT_PUSH", "GIT_POLL", "AUTOMATION_EVENT"}.issubset(activation["forbiddenTriggers"]))
        workspace = self.modules["agentWorkspace"]["content"]
        self.assertFalse(workspace["activationContract"]["gitPushActivatesAgent"])
        self.assertFalse(workspace["activationContract"]["automationActivatesAgent"])

    def test_agent_identity_requires_display_name_binding_and_rebind_policy(self):
        schema = self.modules["schemaAgentIdentity"]["content"]
        required = set(schema["required"])
        self.assertTrue({"agentId", "displayName", "bootstrapBinding", "activationContract", "rebindPolicy"}.issubset(required))
        self.assertEqual(
            schema["properties"]["activationContract"]["properties"]["activationMode"]["const"],
            "HUMAN_GO_ONLY",
        )

    def test_job_requires_domain_response_and_chat_contracts(self):
        schema = self.modules["schemaAgentJob"]["content"]
        self.assertTrue({"domainContext", "responseContract", "agentChatContract"}.issubset(schema["required"]))
        required_templates = set(schema["$defs"]["responseContract"]["properties"]["templates"]["required"])
        self.assertEqual(
            required_templates,
            {"jobResult", "jobError", "clarificationRequest", "capabilityMismatch", "improvementProposal"},
        )

    def test_template_catalog_has_exact_five_types(self):
        catalog = self.modules["agentResponseTemplates"]["content"]
        self.assertEqual(
            set(catalog["templates"]),
            {"job_result", "job_error", "clarification_request", "capability_mismatch", "improvement_proposal"},
        )
        self.assertEqual(set(RESPONSE_TYPES), {t["responseType"] for t in catalog["templates"].values()})

    def _job(self):
        template_ref = "embeddedModules.agentResponseTemplates.content#templates/"
        return {
            "identity": {"jobId": "job-1"},
            "lineage": {"projectId": "project-1", "packageId": "wp-1"},
            "assignment": {"agentId": "agent-1", "identityRevision": 2},
            "responseContract": {
                "templates": {
                    "jobResult": {"templateRef": template_ref + "job_result"},
                    "jobError": {"templateRef": template_ref + "job_error"},
                    "clarificationRequest": {"templateRef": template_ref + "clarification_request"},
                    "capabilityMismatch": {"templateRef": template_ref + "capability_mismatch"},
                    "improvementProposal": {"templateRef": template_ref + "improvement_proposal"},
                }
            },
        }

    def _response(self, response_type, payload):
        template_id = {
            "JOB_RESULT": "job_result",
            "JOB_ERROR": "job_error",
            "CLARIFICATION_REQUEST": "clarification_request",
            "CAPABILITY_MISMATCH": "capability_mismatch",
            "IMPROVEMENT_PROPOSAL": "improvement_proposal",
        }[response_type]
        status = RESPONSE_TYPES[response_type][0]
        return {
            "format": "SAFOR_AGENT_RESPONSE",
            "schemaVersion": "0.13.0",
            "responseId": "response-1",
            "responseType": response_type,
            "projectId": "project-1",
            "workPackageId": "wp-1",
            "jobId": "job-1",
            "agentId": "agent-1",
            "identityRevision": 2,
            "createdAt": "2026-10-17T20:00:00Z",
            "contractRef": "jobs/job-1.json@blob",
            "responseTemplateRef": "embeddedModules.agentResponseTemplates.content#templates/" + template_id,
            "targetMasterRef": "master/jobs/job-1.json",
            "lifecycleStatus": status,
            "summary": "summary",
            "affectedRefs": [],
            "evidenceRefs": [],
            "masterDecisionRef": None,
            "supersedesResponseId": None,
            "payload": payload,
        }

    def test_all_five_response_types_validate(self):
        payloads = {
            "JOB_RESULT": {"artifactRefs": ["a"], "gitTrace": [], "verification": [], "openItems": []},
            "JOB_ERROR": {"errorClass": "E", "failedStep": "S", "reproducibleFinding": "F", "blockedArtifacts": [], "suggestedMasterAction": "A"},
            "CLARIFICATION_REQUEST": {"question": "Q", "affectedJobFields": ["task"], "conflictType": "AMBIGUOUS", "options": [], "suggestedMasterAction": "A"},
            "CAPABILITY_MISMATCH": {"expectedCapabilities": ["java"], "availableCapabilities": [], "affectedScope": "src", "risk": "wrong result", "suggestedMasterAction": "reassign"},
            "IMPROVEMENT_PROPOSAL": {"problem": "P", "proposal": "X", "expectedBenefit": "B", "risk": "R", "affectedProcess": "planning", "suggestedMasterAction": "consider"},
        }
        for response_type, payload in payloads.items():
            with self.subTest(response_type=response_type):
                self.assertTrue(validate_agent_response(self._response(response_type, payload), self._job())["valid"])

    def test_invalid_response_fails_closed(self):
        response = self._response("JOB_RESULT", {"artifactRefs": ["a"], "gitTrace": [], "verification": [], "openItems": []})
        response["responseType"] = "OTHER"
        with self.assertRaises(AgentResponseError):
            validate_agent_response(response, self._job())
        response = self._response("JOB_ERROR", {"errorClass": "E", "failedStep": "S", "reproducibleFinding": "F", "blockedArtifacts": [], "suggestedMasterAction": "A"})
        response["agentId"] = "other"
        with self.assertRaises(AgentResponseError):
            validate_agent_response(response, self._job())

    def test_agent_chat_is_single_line_and_rejects_substantive_fields(self):
        status = render_agent_chat_status(
            {"status": "STARTED", "agentId": "agent-1", "displayName": "Nova Dev", "jobId": "job-1", "targetBranch": "agent/job-1", "gitRef": None}
        )
        self.assertNotIn("\n", status["renderedText"])
        self.assertLessEqual(len(status["renderedText"]), 240)
        with self.assertRaises(AgentChatStatusError):
            render_agent_chat_status(
                {"status": "STARTED", "agentId": "agent-1", "displayName": "Nova Dev", "jobId": "job-1", "targetBranch": "agent/job-1", "gitRef": None, "domainExplanation": "too much"}
            )

    def test_master_status_index_is_compact_and_start_aware(self):
        index = build_master_status_index(
            project_id="project-1",
            revision=1,
            authoritative_control_state_ref="state/control.json@1",
            registry_ref="agents/index.json@1",
            scheduler_state_ref="master/scheduler/state.json@1",
            generated_at="2026-10-17T20:00:00Z",
            provider_readback_ref="github:commit",
            registry={"agents": [{"agentId": "agent-1", "displayName": "Nova Dev", "status": "ACTIVE"}]},
            job_states=[{"jobId": "job-1", "assignedAgentId": "agent-1", "lifecycleStatus": "READY", "contractRef": "jobs/job-1.json", "reviewRef": None}],
            responses=[],
        )
        self.assertTrue(index["agents"][0]["startRequired"])
        self.assertEqual(index["jobs"][0]["jobId"], "job-1")
        self.assertNotIn("fullProjectTree", index)

    def test_all_domain_distributions_embed_rc8_contracts(self):
        for file_name in (
            "SAFOR-FRAMEWORK-WEBSITE.json",
            "SAFOR-FRAMEWORK-SAAS.json",
            "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        ):
            distribution = load(file_name)
            framework = distribution["framework"]
            self.assertEqual(framework["bundleVersion"], "0.13.0-rc.9")
            modules = framework["embeddedModules"]
            for key in (
                "chatExecution", "agentBootstrap", "agentResponseContract", "agentResponseTemplates",
                "agentChatContract", "masterStatusIndex", "schemaAgentResponse", "schemaAgentChatStatus",
            ):
                self.assertIn(key, modules)

    def test_platform_not_factory_or_operating_model_owns_chat(self):
        self.assertTrue(self.kernel["kernelPrinciples"]["platformOwnsHumanVisibleCommunication"])
        self.assertTrue(self.kernel["kernelPrinciples"]["minimalSubagentChatStatusOnly"])
        for file_name in (
            "SAFOR-FRAMEWORK-WEBSITE.json",
            "SAFOR-FRAMEWORK-SAAS.json",
            "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        ):
            distribution = load(file_name)
            for package in distribution["embeddedDomainModules"].values():
                serialized = json.dumps(package)
                self.assertNotIn("agentChatResponseLength", serialized)
                self.assertNotIn("humanGoActivationOverride", serialized)


if __name__ == "__main__":
    unittest.main()
