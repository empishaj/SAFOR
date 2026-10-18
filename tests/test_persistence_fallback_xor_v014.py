import json
import unittest
from pathlib import Path

from runtime.agent_jobs import AgentJobValidationError, render_agent_chat_output

ROOT = Path(__file__).resolve().parents[1]


class PersistenceFallbackXorV014Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_persisted_blocker_has_reference_and_no_failure_object(self):
        output = render_agent_chat_output(
            status="BLOCKED",
            project_id="project-001",
            agent_id="agent-a",
            display_name="Nova Dev",
            job_key="WP-001",
            details_ref="git:response:123",
        )
        self.assertEqual("git:response:123", output["detailsRef"])
        self.assertIsNone(output["persistence"])

    def test_persistence_failure_has_no_reference(self):
        output = render_agent_chat_output(
            status="BLOCKED",
            project_id="project-001",
            agent_id="agent-a",
            display_name="Nova Dev",
            job_key="WP-001",
            details_ref=None,
            persistence_state="FAILED",
            attempt_id="attempt-001",
            phase="WRITE_RESPONSE",
            reason_code="CONTROL_WRITE_UNAVAILABLE",
        )
        self.assertIsNone(output["detailsRef"])
        self.assertEqual("FAILED", output["persistence"]["state"])
        self.assertFalse(output["persistence"]["authoritativeResponsePersisted"])

    def test_reference_and_persistence_failure_cannot_coexist(self):
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "MUTUALLY_EXCLUSIVE",
        ):
            render_agent_chat_output(
                status="BLOCKED",
                project_id="project-001",
                agent_id="agent-a",
                display_name="Nova Dev",
                job_key="WP-001",
                details_ref="git:response:123",
                persistence_state="FAILED",
                attempt_id="attempt-001",
                phase="WRITE_RESPONSE",
                reason_code="CONTROL_WRITE_UNAVAILABLE",
            )

    def test_persistence_context_for_nonblocked_status_is_rejected(self):
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "ONLY_ALLOWED_FOR_BLOCKED",
        ):
            render_agent_chat_output(
                status="READY",
                project_id="project-001",
                agent_id="agent-a",
                display_name="Nova Dev",
                persistence_state="FAILED",
            )

    def test_schema_contains_both_blocked_xor_branches(self):
        schema = self.load("v0.14.0/schemas/agent-chat-output.schema.json")
        branches = schema["allOf"]
        null_branch = [
            branch for branch in branches
            if branch.get("if", {}).get("properties", {}).get("status", {}).get("const") == "BLOCKED"
            and branch.get("if", {}).get("properties", {}).get("detailsRef", {}).get("type") == "null"
        ]
        ref_branch = [
            branch for branch in branches
            if branch.get("if", {}).get("properties", {}).get("status", {}).get("const") == "BLOCKED"
            and branch.get("if", {}).get("properties", {}).get("detailsRef", {}).get("type") == "string"
        ]
        self.assertEqual(1, len(null_branch))
        self.assertEqual("object", null_branch[0]["then"]["properties"]["persistence"]["type"])
        self.assertEqual(1, len(ref_branch))
        self.assertEqual("null", ref_branch[0]["then"]["properties"]["persistence"]["type"])

    def test_communication_contract_declares_mutual_exclusion(self):
        model = self.load("v0.14.0/agent-communication-model.json")
        contract = model["persistenceXorContract"]
        self.assertTrue(contract["mutuallyExclusive"])
        self.assertEqual("MUST_BE_NULL", contract["variants"]["PERSISTED_RESPONSE"]["persistence"])
        self.assertEqual("MUST_BE_NULL", contract["variants"]["PERSISTENCE_FAILURE"]["detailsRef"])


if __name__ == "__main__":
    unittest.main()
