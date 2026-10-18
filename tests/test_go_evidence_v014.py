import copy
import hashlib
import json
import unittest

from runtime.go_evidence import (
    GoEvidenceValidationError,
    confirm_go_claim_after_provider_readback,
    prepare_go_claim,
    validate_human_go_evidence,
)


class GoEvidenceV014Tests(unittest.TestCase):
    def pointer(self, path, blob="blob1234"):
        return {
            "repository": "example/safor-memory",
            "ref": "commit123",
            "path": path,
            "blobSha": blob,
        }

    def evidence(self):
        return {
            "format": "SAFOR_HUMAN_GO_EVIDENCE",
            "schemaVersion": "0.14.0",
            "activationId": "activation-001",
            "projectId": "project-001",
            "agentId": "agent-a",
            "identityRevision": 2,
            "targetJobId": "job-001",
            "targetDispatchRevision": 3,
            "intent": "GO",
            "source": "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT",
            "observedAt": "2026-10-18T08:00:00Z",
            "singleUse": True,
            "jobPromptTransported": False,
        }

    def expected(self):
        return {
            "projectId": "project-001",
            "agentId": "agent-a",
            "identityRevision": 2,
            "targetJobId": "job-001",
            "targetDispatchRevision": 3,
        }

    def master_state(self):
        return {
            "format": "SAFOR_AGENT_JOB_STATE",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "jobId": "job-001",
            "assignedAgentId": "agent-a",
            "assignedIdentityRevision": 2,
            "dispatchRevision": 3,
            "revision": 7,
            "owner": "MASTER",
            "lifecycleStatus": "WAITING_HUMAN_GO",
            "contractRef": self.pointer("projects/example/agents/agent-a/inbox/job-001.json", "jobblob1"),
            "updatedAt": "2026-10-18T07:59:00Z",
        }

    def agent_state(self):
        return {
            "format": "SAFOR_AGENT_STATE",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "agentId": "agent-a",
            "identityRevision": 2,
            "revision": 4,
            "runtimeStatus": "WAITING_HUMAN_GO",
            "session": None,
            "currentJob": None,
            "lastResponseRef": None,
            "consumedActivationIds": [],
            "updatedAt": "2026-10-18T07:59:00Z",
        }

    def go_ref(self):
        return self.pointer("projects/example/evidence/go.json")

    def master_ref(self):
        return self.pointer("projects/example/master/jobs/job-001.json", "masterjob1")

    def intent(self, agent_state=None, consumed=None):
        return prepare_go_claim(
            master_job_state=self.master_state(),
            master_job_state_ref=self.master_ref(),
            agent_state=agent_state or self.agent_state(),
            go_evidence=self.evidence(),
            expected_agent_state_revision=4,
            consumed_activation_ids=set(consumed or ()),
            go_evidence_ref=self.go_ref(),
        )

    def test_valid_evidence(self):
        validate_human_go_evidence(
            self.evidence(), expected=self.expected(), consumed_activation_ids=set()
        )

    def test_string_containing_go_is_not_evidence(self):
        with self.assertRaises(GoEvidenceValidationError):
            validate_human_go_evidence(
                {"value": "not-a-governed-evidence-but-contains-go"},
                expected=self.expected(),
            )

    def test_foreign_job_agent_binding_and_dispatch_fail(self):
        for field, value in (
            ("targetJobId", "job-other"),
            ("agentId", "agent-other"),
            ("identityRevision", 1),
            ("targetDispatchRevision", 2),
        ):
            evidence = self.evidence()
            evidence[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                GoEvidenceValidationError,
                f"GO_EVIDENCE_BINDING_MISMATCH:{field}",
            ):
                validate_human_go_evidence(evidence, expected=self.expected())

    def test_consumed_evidence_fails(self):
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "GO_EVIDENCE_ALREADY_CONSUMED"
        ):
            validate_human_go_evidence(
                self.evidence(),
                expected=self.expected(),
                consumed_activation_ids={"activation-001"},
            )

    def test_claim_requires_agent_state_provider_readback_before_consumption(self):
        consumed = set()
        master_before = copy.deepcopy(self.master_state())
        intent = self.intent(consumed=consumed)

        self.assertFalse(intent["authoritative"])
        self.assertEqual("agents/agent-a/state.json", intent["casTargetPath"])
        self.assertEqual("master/jobs/job-001.json", intent["masterLifecyclePath"])
        self.assertFalse(intent["agentMayWriteMasterLifecycle"])
        self.assertEqual(master_before, self.master_state())
        self.assertEqual(set(), consumed)

        observed = copy.deepcopy(intent["proposedAgentState"])
        observed_digest = "sha256:" + hashlib.sha256(
            json.dumps(
                observed,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        claimed = confirm_go_claim_after_provider_readback(
            claim_intent=intent,
            provider_readback={
                "casSucceeded": True,
                "readbackVerified": True,
                "targetPath": "agents/agent-a/state.json",
                "observedState": observed,
                "observedStateDigest": observed_digest,
                "readbackRef": "git:claim",
                "observedBlobSha": "blob-claim-001",
            },
            consumed_activation_ids=consumed,
        )
        self.assertTrue(claimed["authoritative"])
        self.assertEqual("RUNNING", claimed["state"]["runtimeStatus"])
        self.assertEqual(5, claimed["state"]["revision"])
        self.assertEqual("MASTER", claimed["masterTransitionInput"]["requiredWriter"])
        self.assertFalse(claimed["masterLifecycleMutationPerformed"])
        self.assertIn("activation-001", consumed)

    def test_failed_cas_does_not_consume_or_confirm(self):
        consumed = set()
        intent = self.intent(consumed=consumed)
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CAS_NOT_CONFIRMED"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback={"casSucceeded": False, "readbackVerified": False},
                consumed_activation_ids=consumed,
            )
        self.assertEqual(set(), consumed)

    def test_duplicate_claim_fails_from_persisted_agent_state(self):
        state = self.agent_state()
        state["consumedActivationIds"] = ["activation-001"]
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "GO_EVIDENCE_ALREADY_CONSUMED"
        ):
            self.intent(agent_state=state)


if __name__ == "__main__":
    unittest.main()
