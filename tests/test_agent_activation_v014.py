import copy
import json
import unittest
from pathlib import Path

from runtime.agent_orchestration import (
    AgentIdentityError,
    evaluate_human_go_activation,
    validate_chat_agent_identity,
)


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class AgentActivationV014Tests(unittest.TestCase):
    def setUp(self):
        self.identity = {
            "format": "SAFOR_AGENT_IDENTITY",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "agentId": "agent-dev-003",
            "displayName": "Nova Dev",
            "agentKind": "CHAT_AGENT",
            "masterId": "SAFOR-MASTER:project-001",
            "controlRepository": {
                "provider": "github",
                "repository": "example/safor-memory",
                "ref": "main",
            },
            "workspaceRoot": "projects/example/agents/agent-dev-003/",
            "identityRevision": 2,
            "status": "ACTIVE",
            "registeredAt": "2026-10-17T20:00:00Z",
            "initializedBy": {
                "repository": "example/safor-memory",
                "ref": "abc1234",
                "path": "projects/example/decisions/agent-registration.json",
                "blobSha": "def5678",
            },
            "roleIds": ["DEVELOPER"],
            "capabilityIds": ["code_contribution"],
            "chatBinding": {
                "bindingId": "chat-binding-agent-dev-003-r2",
                "bindingMode": "CONTINUED_CHAT_HISTORY",
                "status": "BOUND",
                "establishedAt": "2026-10-17T20:00:00Z",
                "initializedFromPromptRef": {
                    "repository": "example/safor-memory",
                    "ref": "abc1234",
                    "path": "projects/example/agents/agent-dev-003/initialization.json",
                    "blobSha": "9876abc",
                },
                "expectedSessionContinuity": True,
                "onUncertain": "REIDENTIFICATION_REQUIRED",
            },
            "activationContract": {
                "activationMode": "HUMAN_GO_REQUIRED",
                "acceptedToken": "GO",
                "tokenCaseSensitive": False,
                "additionalTextAllowed": False,
                "source": "DIRECT_HUMAN_INPUT_IN_BOUND_AGENT_CHAT",
                "backgroundWakeupAssumed": False,
                "automationActivationAllowed": False,
                "hostTriggerActivationAllowed": False,
                "gitEventActivationAllowed": False,
                "schedulerMayActivateChat": False,
                "initialBootstrapFields": [
                    "CONTROL_REPOSITORY",
                    "PROJECT_ID",
                    "AGENT_ID",
                    "DISPLAY_NAME",
                    "IDENTITY_REF",
                    "AGENT_STATE_REF",
                    "INBOX_INDEX_REF",
                    "COMMUNICATION_CONTRACT_REF",
                ],
                "onGo": [
                    "LOAD_IDENTITY",
                    "VERIFY_IDENTITY_STATUS_ACTIVE",
                    "VERIFY_CHAT_BINDING_BOUND",
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
                ],
                "jobPromptTransportRequired": False,
            },
            "communicationContractRef": {
                "repository": "empishaj/SAFOR",
                "ref": "v0.14.0-rc.1",
                "path": "v0.14.0/agent-communication-model.json",
                "blobSha": "1234567",
            },
        }
        self.state = {
            "format": "SAFOR_AGENT_STATE",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "agentId": "agent-dev-003",
            "identityRevision": 2,
            "revision": 4,
            "runtimeStatus": "WAITING_HUMAN_GO",
            "session": None,
            "currentJob": None,
            "lastResponseRef": None,
            "updatedAt": "2026-10-17T20:01:00Z",
        }
        pointer = {
            "repository": "example/safor-memory",
            "ref": "abc1234",
            "path": "placeholder",
            "blobSha": "def5678",
        }
        self.inbox = {
            "format": "SAFOR_AGENT_INBOX_INDEX",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "agentId": "agent-dev-003",
            "identityRevision": 2,
            "revision": 3,
            "authoritativeLifecycle": False,
            "sourceOfTruth": "master/jobs/{jobId}.json",
            "verificationRule": "READ_MASTER_JOB_STATE_BEFORE_CLAIM",
            "directoryEnumerationRequired": False,
            "entries": [
                {
                    "jobId": "0199f0aa-7e40-7abc-8a12-000000000014",
                    "jobRef": dict(pointer, path="projects/example/agents/agent-dev-003/inbox/job.json"),
                    "masterJobStateRef": dict(pointer, path="projects/example/master/jobs/job.json"),
                    "humanJobRef": dict(pointer, path="projects/example/agents/agent-dev-003/inbox/job.md"),
                    "dispatchRevision": 1,
                    "discoverabilityState": "AVAILABLE",
                    "activationState": "WAITING_HUMAN_GO",
                    "queuedAt": "2026-10-17T20:02:00Z",
                    "packageId": "WP-014",
                    "workItemId": "WP-014-IMPL",
                    "planSequence": 14,
                    "dispatchSequence": 1,
                    "roleId": "DEVELOPER",
                    "requiredIdentityRevision": 2,
                }
            ],
            "updatedAt": "2026-10-17T20:02:00Z",
        }

    def activate(self, message="GO"):
        return evaluate_human_go_activation(
            identity=self.identity,
            agent_state=self.state,
            inbox_index=self.inbox,
            human_message=message,
            session_id="session-001",
            activation_id="activation-001",
            observed_at="2026-10-17T20:03:00Z",
        )

    def test_wp01_json_files_parse_and_declare_v014(self):
        paths = [
            "v0.14.0/agent-activation-model.json",
            "v0.14.0/schemas/agent-identity.schema.json",
            "v0.14.0/schemas/agent-registry.schema.json",
            "v0.14.0/schemas/agent-state.schema.json",
            "v0.14.0/schemas/agent-inbox-index.schema.json",
            "v0.14.0/schemas/agent-initialization.schema.json",
            "v0.14.0/templates/agent-initialization.template.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                doc = load(path)
                if "/schemas/" in path:
                    self.assertEqual(
                        doc["properties"]["schemaVersion"]["const"], "0.14.0"
                    )
                else:
                    self.assertEqual(doc["schemaVersion"], "0.14.0")

    def test_valid_chat_identity(self):
        validate_chat_agent_identity(self.identity)

    def test_display_name_must_differ_from_agent_id(self):
        invalid = copy.deepcopy(self.identity)
        invalid["displayName"] = "agent-dev-003"
        with self.assertRaisesRegex(
            AgentIdentityError, "DISPLAY_NAME_MUST_DIFFER_FROM_AGENT_ID"
        ):
            validate_chat_agent_identity(invalid)

    def test_automatic_activation_is_forbidden(self):
        invalid = copy.deepcopy(self.identity)
        invalid["activationContract"]["automationActivationAllowed"] = True
        with self.assertRaisesRegex(
            AgentIdentityError, "AUTOMATIONACTIVATIONALLOWED_MUST_BE_FALSE"
        ):
            validate_chat_agent_identity(invalid)

    def test_uncertain_chat_binding_requires_reidentification(self):
        invalid = copy.deepcopy(self.identity)
        invalid["chatBinding"]["status"] = "UNVERIFIED"
        result = evaluate_human_go_activation(
            identity=invalid,
            agent_state=self.state,
            inbox_index=self.inbox,
            human_message="GO",
            session_id="session-001",
            activation_id="activation-001",
            observed_at="2026-10-17T20:03:00Z",
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["outcome"], "REIDENTIFICATION_REQUIRED")
        self.assertIsNone(result["activationEvidence"])

    def test_exact_human_go_is_required(self):
        for message in ("start", "GO und implementiere", "", " G O "):
            with self.subTest(message=message):
                result = self.activate(message)
                self.assertFalse(result["allowed"])
                self.assertEqual(result["reasonCode"], "EXACT_HUMAN_GO_REQUIRED")

    def test_go_is_case_insensitive_and_whitespace_trimmed(self):
        result = self.activate("  go  ")
        self.assertTrue(result["allowed"])
        self.assertEqual(result["outcome"], "PREFLIGHT_REQUIRED")

    def test_go_binds_to_selected_job_without_prompt_transport(self):
        result = self.activate()
        self.assertTrue(result["allowed"])
        evidence = result["activationEvidence"]
        self.assertEqual(
            evidence["targetJobId"], "0199f0aa-7e40-7abc-8a12-000000000014"
        )
        self.assertEqual(evidence["intent"], "GO")
        self.assertFalse(evidence["jobPromptTransported"])
        self.assertTrue(evidence["singleUse"])

    def test_stale_identity_revision_is_not_claimable(self):
        stale = copy.deepcopy(self.inbox)
        stale["entries"][0]["requiredIdentityRevision"] = 1
        result = evaluate_human_go_activation(
            identity=self.identity,
            agent_state=self.state,
            inbox_index=stale,
            human_message="GO",
            session_id="session-001",
            activation_id="activation-001",
            observed_at="2026-10-17T20:03:00Z",
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["reasonCode"], "NO_DISCOVERABLE_JOB_FOR_ACTIVE_IDENTITY"
        )

    def test_pointer_only_read_contract_forbids_full_scan(self):
        result = self.activate()
        self.assertEqual(
            result["requiredReads"],
            [
                "PINNED_IDENTITY",
                "AGENT_STATE",
                "PERSONAL_INBOX_INDEX",
                "SELECTED_JOB_CONTRACT",
                "SELECTED_MASTER_JOB_STATE",
                "JOB_REFERENCED_INPUTS_ONLY",
            ],
        )
        self.assertIn("PROJECT_TREE_FULL_SCAN", result["forbiddenReads"])
        self.assertIn("OTHER_AGENT_INBOX_READ", result["forbiddenReads"])

    def test_template_contains_one_time_prompt_and_go_reuse(self):
        template = load("v0.14.0/templates/agent-initialization.template.json")
        self.assertTrue(template["renderingRules"]["oneTimeOnly"])
        self.assertEqual(template["renderingRules"]["subsequentHumanInput"], "GO")
        self.assertFalse(template["renderingRules"]["includeJobContent"])
        self.assertFalse(template["renderingRules"]["includeDomainTaskPrompt"])

    def test_activation_model_requires_human_go_and_no_runtime_install(self):
        model = load("v0.14.0/agent-activation-model.json")
        self.assertFalse(model["scope"]["endCustomerRuntimeInstallationRequired"])
        contract = model["chatAgentActivationContract"]
        self.assertEqual(contract["activationMode"], "HUMAN_GO_REQUIRED")
        self.assertFalse(contract["automationActivationAllowed"])
        self.assertFalse(contract["hostTriggerActivationAllowed"])
        self.assertFalse(contract["gitEventActivationAllowed"])
        self.assertFalse(contract["schedulerMayActivateChat"])


if __name__ == "__main__":
    unittest.main()
