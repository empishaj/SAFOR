import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ClaimAuthoritySeparationV014Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_workspace_separates_agent_claim_and_master_lifecycle(self):
        model = self.load("v0.14.0/agent-workspace-model.json")
        claim = model["claimAuthority"]
        self.assertEqual("agents/{agentId}/state.json", claim["agentClaimTarget"])
        self.assertEqual("ASSIGNED_AGENT_ONLY", claim["agentClaimWriter"])
        self.assertEqual("master/jobs/{jobId}.json", claim["masterLifecycleTarget"])
        self.assertEqual("MASTER_ONLY", claim["masterLifecycleWriter"])
        self.assertTrue(model["safety"]["noAgentMasterStateWrite"])

    def test_activation_contract_uses_agent_state_as_only_cas_target(self):
        model = self.load("v0.14.0/agent-activation-model.json")
        claim = model["atomicClaimContract"]
        self.assertEqual("agents/{agentId}/state.json", claim["claimStateTarget"])
        self.assertEqual("ASSIGNED_AGENT_ONLY", claim["claimStateWriteAuthority"])
        self.assertEqual("master/jobs/{jobId}.json", claim["masterLifecycleTarget"])
        self.assertEqual("MASTER_ONLY", claim["masterLifecycleWriteAuthority"])
        self.assertFalse(claim["agentMayWriteMasterLifecycle"])
        self.assertIn(
            "MASTER_UPDATES_MASTER_JOB_LIFECYCLE_SEPARATELY",
            claim["authoritativeSequence"],
        )

    def test_agent_state_persists_claim_and_activation_consumption(self):
        schema = self.load("v0.14.0/schemas/agent-state.schema.json")
        self.assertIn("consumedActivationIds", schema["required"])
        current = schema["$defs"]["currentJob"]
        self.assertIn("masterJobRevision", current["required"])
        self.assertEqual("string", current["properties"]["claimId"]["type"])

    def test_master_job_state_remains_master_owned(self):
        schema = self.load("v0.14.0/schemas/agent-job-state.schema.json")
        self.assertEqual("MASTER", schema["properties"]["owner"]["const"])
        self.assertIn("MASTER-owned", schema["description"])
        self.assertIn("never CAS or mutate", schema["description"])

    def test_provider_claim_contracts_target_agent_state(self):
        for path in (
            "v0.14.0/providers/github/0.6.0/package.json",
            "v0.14.0/providers/gitlab/0.6.0/package.json",
        ):
            with self.subTest(path=path):
                protocol = self.load(path)["model"]["agentClaimProtocol"]
                self.assertEqual("agents/{agentId}/state.json", protocol["casTargetPath"])
                self.assertEqual("ASSIGNED_AGENT_ONLY", protocol["casTargetAuthority"])
                self.assertEqual("master/jobs/{jobId}.json", protocol["masterLifecyclePath"])
                self.assertEqual("MASTER_ONLY", protocol["masterLifecycleAuthority"])
                self.assertFalse(protocol["agentMayWriteMasterLifecycle"])

    def test_runtime_does_not_prepare_master_job_claim_mutation(self):
        source = (ROOT / "runtime/go_evidence.py").read_text(encoding="utf-8")
        self.assertIn('"proposedAgentState": proposed', source)
        self.assertIn('"agentMayWriteMasterLifecycle": False', source)
        self.assertNotIn('proposed["lifecycleStatus"] = "CLAIMED"', source)
        self.assertNotIn('"proposedState": proposed', source)

    def test_conformance_contains_authority_separation_rule(self):
        assertions = {
            item["id"]: item
            for item in self.load("v0.14.0/conformance.json")["assertions"]
        }
        rule = assertions["CF-RC5-005"]
        self.assertEqual("ACTIVE", rule["status"])
        self.assertEqual(
            "AGENT_MASTER_CLAIM_AUTHORITY_SEPARATION",
            rule["semanticKey"],
        )


if __name__ == "__main__":
    unittest.main()
