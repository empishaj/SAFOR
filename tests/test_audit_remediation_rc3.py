import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from runtime.agent_jobs import AgentJobValidationError, render_agent_chat_output
from runtime.go_evidence import (
    GoEvidenceValidationError,
    confirm_go_claim_after_provider_readback,
    prepare_go_claim,
)

ROOT = Path(__file__).resolve().parents[1]


class AuditRemediationRc3Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def evidence(self):
        return {
            "format": "SAFOR_HUMAN_GO_EVIDENCE", "schemaVersion": "0.14.0",
            "activationId": "activation-rc3-001", "projectId": "project-001",
            "agentId": "agent-a", "identityRevision": 2,
            "targetJobId": "job-001", "targetDispatchRevision": 3,
            "intent": "GO", "source": "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT",
            "observedAt": "2026-10-18T10:00:00Z", "singleUse": True,
            "jobPromptTransported": False,
        }

    def state(self):
        return {
            "format": "SAFOR_AGENT_JOB_STATE", "schemaVersion": "0.14.0",
            "projectId": "project-001", "jobId": "job-001",
            "assignedAgentId": "agent-a", "assignedIdentityRevision": 2, "dispatchRevision": 3,
            "revision": 7, "owner": "MASTER", "lifecycleStatus": "WAITING_HUMAN_GO",
            "contractRef": {"repository": "example/safor-memory", "ref": "commit123", "path": "projects/example/agents/agent-a/inbox/job-001.json", "blobSha": "jobblob123"},
            "goEvidenceRef": None, "consumedActivationIds": [],
            "transitionHistory": [], "updatedAt": "2026-10-18T09:59:00Z",
        }

    def ref(self):
        return {"repository": "example/safor-memory", "ref": "commit123", "path": "projects/example/evidence/go.json", "blobSha": "blob1234"}

    def master_ref(self):
        return {"repository": "example/safor-memory", "ref": "commit123", "path": "projects/example/master/jobs/job-001.json", "blobSha": "masterjob123"}

    def agent_state(self):
        return {
            "format": "SAFOR_AGENT_STATE", "schemaVersion": "0.14.0",
            "projectId": "project-001", "agentId": "agent-a", "identityRevision": 2,
            "revision": 4, "runtimeStatus": "WAITING_HUMAN_GO",
            "session": None, "currentJob": None, "lastResponseRef": None,
            "consumedActivationIds": [], "updatedAt": "2026-10-18T09:59:00Z",
        }

    def test_creation_type_contract_is_consistent(self):
        active = ["WEBSITE", "SOFTWARE_SAAS", "BOOK"]
        self.assertEqual(active, self.load("v0.14.0/creation-type-vocabulary.json")["activeCreationTypes"])
        self.assertEqual(active, self.load("v0.14.0/schemas/project.schema.json")["properties"]["creationType"]["enum"])
        self.assertEqual(set(active), {p["creationType"] for p in self.load("v0.14.0/domain-framework-profiles.json")["profiles"]})

    def test_legacy_creation_type_requires_explicit_contextual_migration(self):
        legacy = self.load("v0.14.0/creation-type-vocabulary.json")["legacyCreationTypes"]["SOFTWARE_WEBSITE"]
        self.assertEqual("LEGACY_ONLY", legacy["status"])
        self.assertTrue(legacy["automaticReplacementForbidden"])
        self.assertEqual("EXPLICIT_CONTEXTUAL_MIGRATION", legacy["migrationMode"])

    def test_active_invariants_are_unambiguous(self):
        invariants = self.load("v0.14.0/SAFOR-MASTER.json")["invariants"]
        indexed = {item["id"]: item for item in invariants}
        for legacy_id in ("INV-013", "INV-037", "INV-038", "INV-039", "INV-054", "INV-121", "INV-123", "INV-209", "INV-211", "INV-217", "INV-233", "INV-235"):
            self.assertEqual("SUPERSEDED", indexed[legacy_id]["status"])
            self.assertTrue(indexed[legacy_id]["supersededBy"])
        for active_id in ("INV-231", "INV-232", "INV-234", "INV-236", "INV-237", "INV-RC5-001", "INV-RC5-002", "INV-RC5-003"):
            self.assertEqual("ACTIVE", indexed[active_id]["status"])

    def test_local_and_remote_control_policies_are_mutually_explicit(self):
        policy = self.load("v0.14.0/repository-policy.json")["controlWorkspacePolicy"]
        self.assertEqual("PROJECT_WORKSPACE_TYPE", policy["discriminator"])
        self.assertFalse(policy["LOCAL_GIT"]["remoteMemoryRequired"])
        self.assertEqual("{selectedOwner}/safor-memory", policy["REMOTE_GIT"]["target"])

    def test_legacy_conformance_assertions_are_superseded(self):
        assertions = self.load("v0.14.0/conformance.json")["assertions"]
        indexed = {item["id"]: item for item in assertions}
        expected = {
            "CF-046": {"CF-RC4-001", "CF-RC4-002"},
            "CF-047": {"CF-RC4-001", "CF-RC4-002"},
            "CF-048": {"CF-RC4-001", "CF-RC4-002"},
            "CF-064": {"CF-RC5-001", "CF-RC5-003", "CF-271"},
            "CF-154": {"CF-267", "CF-RC4-003"},
            "CF-156": {"CF-267", "CF-RC4-003"},
            "CF-159": {"CF-267", "CF-RC4-003"},
            "CF-195": {"CF-229", "CF-231", "CF-232"},
        }
        for legacy_id, successors in expected.items():
            with self.subTest(legacy_id=legacy_id):
                self.assertEqual("SUPERSEDED", indexed[legacy_id]["status"])
                self.assertEqual(successors, set(indexed[legacy_id]["supersededBy"]))
                self.assertTrue(all(indexed[target]["status"] == "ACTIVE" for target in successors))
        self.assertEqual(["REMOTE_GIT"], indexed["CF-RC4-001"]["applicability"]["workspaceType"])
        self.assertEqual(["LOCAL_GIT"], indexed["CF-RC4-002"]["applicability"]["workspaceType"])

    def test_persistence_failure_chat_fallback_has_no_fake_reference(self):
        output = render_agent_chat_output(
            status="BLOCKED", project_id="project-001", agent_id="agent-a",
            display_name="Nova Dev", job_key="WP-001", details_ref=None,
            persistence_state="FAILED", attempt_id="attempt-001",
            phase="WRITE_RESPONSE", reason_code="CONTROL_WRITE_UNAVAILABLE",
        )
        self.assertIsNone(output["detailsRef"])
        self.assertEqual("FAILED", output["persistence"]["state"])
        self.assertFalse(output["persistence"]["authoritativeResponsePersisted"])
        self.assertNotIn("http", output["text"])
        with self.assertRaisesRegex(AgentJobValidationError, "PERSISTENCE_FAILURE_CONTEXT"):
            render_agent_chat_output(status="BLOCKED", project_id="project-001", agent_id="agent-a", display_name="Nova Dev", job_key="WP-001")

    def test_go_claim_is_not_authoritative_before_exact_provider_readback(self):
        consumed = set()
        intent = prepare_go_claim(
            master_job_state=self.state(),
            master_job_state_ref=self.master_ref(),
            agent_state=self.agent_state(),
            go_evidence=self.evidence(),
            expected_agent_state_revision=4,
            consumed_activation_ids=consumed,
            go_evidence_ref=self.ref(),
        )
        self.assertFalse(intent["authoritative"])
        self.assertEqual("agents/agent-a/state.json", intent["casTargetPath"])
        self.assertEqual("master/jobs/job-001.json", intent["masterLifecyclePath"])
        self.assertFalse(intent["agentMayWriteMasterLifecycle"])
        self.assertEqual(set(), consumed)
        self.assertIn(
            "activation-rc3-001",
            intent["proposedAgentState"]["consumedActivationIds"],
        )
        self.assertTrue(intent["proposedAgentStateDigest"].startswith("sha256:"))
        with self.assertRaisesRegex(GoEvidenceValidationError, "PROVIDER_CAS_NOT_CONFIRMED"):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback={"casSucceeded": False, "readbackVerified": False},
                consumed_activation_ids=consumed,
            )
        self.assertEqual(set(), consumed)

        observed = json.loads(json.dumps(intent["proposedAgentState"]))
        observed_digest = "sha256:" + hashlib.sha256(
            json.dumps(
                observed, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        confirmed = confirm_go_claim_after_provider_readback(
            claim_intent=intent,
            provider_readback={
                "casSucceeded": True,
                "readbackVerified": True,
                "targetPath": "agents/agent-a/state.json",
                "observedState": observed,
                "observedStateDigest": observed_digest,
                "readbackRef": "git:commit:claimed",
                "observedBlobSha": "blob-claimed-123",
            },
            consumed_activation_ids=consumed,
        )
        self.assertTrue(confirmed["authoritative"])
        self.assertEqual("SAFOR_CONFIRMED_GO_CLAIM", confirmed["format"])
        self.assertEqual(observed, confirmed["state"])
        self.assertEqual(intent["proposedAgentStateDigest"], confirmed["stateDigest"])
        self.assertEqual("MASTER", confirmed["masterTransitionInput"]["requiredWriter"])
        self.assertFalse(confirmed["masterLifecycleMutationPerformed"])
        self.assertIn("activation-rc3-001", consumed)

    def test_audit_validator_passes(self):
        subprocess.run([sys.executable, str(ROOT / "tools/validate_audit_remediation.py")], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
