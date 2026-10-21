import json
import unittest
from pathlib import Path

from tests.v014_fixtures import valid_agent_job


ROOT = Path(__file__).resolve().parents[1]


class AgentJobFixtureContractAlignmentTests(unittest.TestCase):
    def load(self, path: str):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_canonical_fixture_matches_claim_policy_schema_exactly(self):
        schema = self.load("v0.14.0/schemas/agent-job.schema.json")
        claim_schema = schema["$defs"]["scheduling"]["properties"]["claimPolicy"]
        claim_policy = valid_agent_job()["scheduling"]["claimPolicy"]

        self.assertEqual(set(claim_schema["properties"]), set(claim_policy))
        self.assertTrue(set(claim_schema["required"]).issubset(claim_policy))
        self.assertNotIn("settledRearmStateTemplateRef", claim_policy)

    def test_settled_rearm_is_preselection_framework_contract(self):
        activation = self.load("v0.14.0/agent-activation-model.json")
        handling = activation["onHumanGo"]["preSelectionAgentStateHandling"]
        self.assertEqual(
            "templates/agent-state-settled-rearm.template.json",
            handling["settledRearmStateTemplateRef"],
        )
        self.assertIn(
            "LOAD_PINNED_SETTLED_REARM_STATE_TEMPLATE",
            handling["onSettledPriorExecution"],
        )

        bundle_map = self.load("v0.14.0/bundle-module-map.json")
        self.assertEqual(
            "v0.14.0/templates/agent-state-settled-rearm.template.json",
            bundle_map["modulePaths"]["templateAgentStateSettledRearm"],
        )
        self.assertIn(
            "templateAgentStateSettledRearm",
            bundle_map["v014AuthoritativeKeys"],
        )

        template = self.load(
            "v0.14.0/templates/agent-state-settled-rearm.template.json"
        )
        self.assertEqual(
            "WAITING_HUMAN_GO",
            template["stateTemplate"]["runtimeStatus"],
        )
        self.assertIsNone(template["stateTemplate"]["session"])
        self.assertIsNone(template["stateTemplate"]["currentJob"])


if __name__ == "__main__":
    unittest.main()
