import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProductBoundaryV014Tests(unittest.TestCase):
    def setUp(self):
        self.docs = {
            path: (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "README.md",
                "START-HIER.md",
                "QUICKSTART.md",
                "SUPPORT.md",
                "AGENT-WORKSPACE.md",
                "AGENT-JOB-CONTRACT.md",
                "MULTI-AGENT-SCHEDULER.md",
                "MASTER-SUBAGENT-ORCHESTRATION.md",
            )
        }

    def test_all_product_boundary_documents_exist(self):
        for path in self.docs:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())
                self.assertGreater(len(self.docs[path]), 300)

    def test_no_document_requires_additional_end_user_runtime(self):
        forbidden = (
            "Host-/Runtime-Integration Pflicht",
            "Production use therefore requires an integrated SAFOR host/runtime boundary",
            "must install a SAFOR runtime",
            "requires a separately installed SAFOR runtime",
        )
        for path, text in self.docs.items():
            for phrase in forbidden:
                with self.subTest(path=path, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_docs_preserve_actual_tool_and_rights_boundary(self):
        combined = "\n".join(self.docs.values()).casefold()
        self.assertIn("actual provider", combined)
        self.assertIn("json", combined)
        self.assertIn("cannot", combined)
        self.assertIn("permissions", combined)

    def test_normal_chat_agent_has_only_human_go_activation(self):
        combined = "\n".join(self.docs.values())
        self.assertIn("HUMAN_GO_REQUIRED", combined)
        self.assertIn("WAITING_HUMAN_GO", combined)
        self.assertIn("Git push", combined)
        self.assertIn("does not activate", combined)
        forbidden = (
            "HUMAN, automation or a host-supported agent trigger",
            "check workspace",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)

    def test_master_only_human_domain_interface_is_documented(self):
        combined = "\n".join(self.docs.values()).casefold()
        self.assertIn("master is the only", combined)
        self.assertIn("agent does not conduct domain discussion", combined)
        self.assertIn("fachliche", combined)

    def test_all_five_typed_responses_are_documented(self):
        combined = "\n".join(self.docs.values())
        for response_type in (
            "JOB_RESULT",
            "JOB_ERROR",
            "CLARIFICATION_REQUEST",
            "CAPABILITY_MISMATCH",
            "IMPROVEMENT_PROPOSAL",
        ):
            with self.subTest(response_type=response_type):
                self.assertIn(response_type, combined)

    def test_job_lifecycle_separates_submission_acceptance_integration(self):
        workspace = self.docs["AGENT-WORKSPACE.md"]
        self.assertIn("RESPONSE_SUBMITTED", workspace)
        self.assertIn("VERIFIED", workspace)
        self.assertIn("ACCEPTED", workspace)
        self.assertIn("INTEGRATED", workspace)
        self.assertIn("is not verification", workspace)

    def test_minimal_chat_contract_is_documented(self):
        combined = "\n".join(
            (
                self.docs["AGENT-WORKSPACE.md"],
                self.docs["AGENT-JOB-CONTRACT.md"],
                self.docs["MASTER-SUBAGENT-ORCHESTRATION.md"],
            )
        )
        for status in (
            "READY",
            "STARTED",
            "SUBMITTED",
            "BLOCKED",
            "REIDENTIFICATION_REQUIRED",
        ):
            with self.subTest(status=status):
                self.assertIn(status, combined)
        self.assertIn("one-line", combined)

    def test_v014_models_declare_no_runtime_installation_requirement(self):
        activation = json.loads(
            (ROOT / "v0.14.0/agent-activation-model.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(
            activation["scope"]["endCustomerRuntimeInstallationRequired"]
        )
        self.assertTrue(activation["scope"]["normativeRulesEmbeddedInFramework"])
        self.assertTrue(activation["scope"]["referenceRuntimeOptionalForVerification"])


if __name__ == "__main__":
    unittest.main()
