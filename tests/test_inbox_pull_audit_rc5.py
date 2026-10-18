import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InboxPullAuditRc5Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_identity_is_bound_to_personal_inbox_not_host_session(self):
        schema = self.load("v0.14.0/schemas/agent-identity.schema.json")
        required = set(schema["required"])
        self.assertIn("inboxBinding", required)
        self.assertNotIn("chatBinding", required)
        self.assertIn("inboxBinding", schema["$defs"])
        self.assertNotIn("chatBinding", schema["$defs"])

    def test_go_evidence_has_no_host_session_binding_fields(self):
        schema = self.load("v0.14.0/schemas/human-go-evidence.schema.json")
        required = set(schema["required"])
        self.assertNotIn("chatBindingId", required)
        self.assertNotIn("sessionId", required)
        self.assertNotIn("chatBindingId", schema["properties"])
        self.assertNotIn("sessionId", schema["properties"])
        self.assertEqual(
            "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT",
            schema["properties"]["source"]["const"],
        )

    def test_job_and_agent_state_do_not_require_host_binding(self):
        job_state = self.load("v0.14.0/schemas/agent-job-state.schema.json")
        self.assertNotIn("chatBindingId", job_state["required"])
        self.assertNotIn("chatBindingId", job_state["properties"])

        agent_state = self.load("v0.14.0/schemas/agent-state.schema.json")
        logical_session = agent_state["$defs"]["session"]
        self.assertNotIn("sessionId", logical_session["required"])
        self.assertNotIn("chatBindingId", logical_session["required"])
        self.assertIn("activationId", logical_session["required"])

    def test_registry_uses_inbox_binding_status(self):
        schema = self.load("v0.14.0/schemas/agent-registry.schema.json")
        agent = schema["$defs"]["agent"]
        self.assertIn("inboxBindingStatus", agent["required"])
        self.assertNotIn("chatBindingStatus", agent["required"])
        self.assertIn("inboxBindingStatus", agent["properties"])
        self.assertNotIn("chatBindingStatus", agent["properties"])

    def test_activation_contract_is_master_inbox_pull(self):
        model = self.load("v0.14.0/agent-activation-model.json")
        activation = model["chatAgentActivationContract"]
        self.assertEqual("HUMAN_GO_REQUIRED", activation["activationMode"])
        self.assertEqual(
            "ATOMIC_INBOX_JOB_CLAIM_WITH_SINGLE_USE_GO_EVIDENCE",
            activation["claimMode"],
        )
        self.assertFalse(activation["hostSessionAttestationRequired"])
        self.assertEqual(
            "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT",
            activation["source"],
        )
        self.assertNotIn(
            "CHAT_BINDING_BOUND",
            set(model["onHumanGo"]["preClaimChecks"]),
        )
        self.assertIn(
            "PERSONAL_INBOX_PROJECT_AND_AGENT_MATCH",
            set(model["onHumanGo"]["preClaimChecks"]),
        )

    def test_master_dispatches_job_to_personal_inbox(self):
        workspace = self.load("v0.14.0/agent-workspace-model.json")
        contract = workspace["dispatchContract"]
        self.assertEqual("MASTER", contract["sender"])
        self.assertEqual("PERSONAL_AGENT_INBOX_IN_GIT", contract["transport"])
        self.assertEqual(
            "agents/{agentId}/inbox/{jobId}.json",
            contract["authoritativeJobPath"],
        )
        self.assertEqual(
            "agents/{agentId}/inbox/index.json",
            contract["discoverabilityIndexPath"],
        )
        self.assertFalse(contract["jobPromptTransportRequired"])
        self.assertFalse(contract["hostSessionBindingRequired"])

    def test_active_rules_do_not_reintroduce_bound_chat_requirement(self):
        master = self.load("v0.14.0/SAFOR-MASTER.json")
        forbidden = (
            "same bound chat",
            "continued_chat_history",
            "verify_chat_binding",
            "chat_binding_bound",
            "cannot prove its binding",
        )
        for invariant in master["invariants"]:
            if invariant.get("status") != "ACTIVE":
                continue
            text = invariant.get("rule", "").lower()
            with self.subTest(invariant=invariant["id"]):
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)

        conformance = self.load("v0.14.0/conformance.json")
        for assertion in conformance["assertions"]:
            if assertion.get("status") != "ACTIVE":
                continue
            text = assertion.get("statement", "").lower()
            with self.subTest(assertion=assertion["id"]):
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)

    def test_materialized_bundle_contains_inbox_pull_contract(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        framework = self.load(f"SAFOR-FRAMEWORK-v{version}.json")
        self.assertEqual("0.14.0-rc.5", framework["bundleVersion"])
        modules = framework["embeddedModules"]

        activation = modules["agentActivation"]["content"]
        identity = modules["schemaAgentIdentity"]["content"]
        go_schema = modules["schemaHumanGoEvidence"]["content"]
        workspace = modules["agentWorkspace"]["content"]

        self.assertFalse(
            activation["chatAgentActivationContract"]["hostSessionAttestationRequired"]
        )
        self.assertIn("inboxBinding", identity["required"])
        self.assertNotIn("chatBinding", identity["required"])
        self.assertNotIn("sessionId", go_schema["required"])
        self.assertEqual(
            "PERSONAL_AGENT_INBOX_IN_GIT",
            workspace["dispatchContract"]["transport"],
        )


if __name__ == "__main__":
    unittest.main()
