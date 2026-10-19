import hashlib
import json
import unittest

from runtime.go_evidence import (
    GoEvidenceValidationError,
    confirm_go_claim_after_provider_readback,
    prepare_go_claim,
)


def digest(value):
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class GoClaimIntegrityV014Tests(unittest.TestCase):
    def agent_state(self):
        return {
            "format": "SAFOR_AGENT_STATE",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "agentId": "agent-a",
            "identityRevision": 2,
            "revision": 7,
            "runtimeStatus": "WAITING_HUMAN_GO",
            "session": None,
            "currentJob": None,
            "lastResponseRef": None,
            "consumedActivationIds": [],
            "updatedAt": "2026-10-18T09:59:00Z",
        }

    def master_job_state(self):
        return {
            "format": "SAFOR_AGENT_JOB_STATE",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "jobId": "job-001",
            "assignedAgentId": "agent-a",
            "assignedIdentityRevision": 2,
            "dispatchRevision": 3,
            "revision": 5,
            "lifecycleStatus": "WAITING_HUMAN_GO",
            "contractRef": {
                "repository": "example/safor-memory",
                "ref": "job-commit",
                "path": "projects/example/agents/agent-a/inbox/job-001.json",
                "blobSha": "jobblob123",
            },
        }

    def evidence(self):
        return {
            "format": "SAFOR_HUMAN_GO_EVIDENCE",
            "schemaVersion": "0.14.0",
            "activationId": "activation-rc4-001",
            "projectId": "project-001",
            "agentId": "agent-a",
            "identityRevision": 2,
            "targetJobId": "job-001",
            "targetDispatchRevision": 3,
            "intent": "GO",
            "source": "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT",
            "observedAt": "2026-10-18T10:00:00Z",
            "singleUse": True,
            "jobPromptTransported": False,
        }

    def evidence_ref(self):
        return {
            "repository": "example/safor-memory",
            "ref": "commit-go",
            "path": "projects/example/agents/agent-a/evidence/go.json",
            "blobSha": "blob-go-123",
        }

    def master_ref(self):
        return {
            "repository": "example/safor-memory",
            "ref": "master-commit",
            "path": "projects/example/master/jobs/job-001.json",
            "blobSha": "masterblob123",
        }

    def intent(self, agent_state=None, master_state=None):
        return prepare_go_claim(
            agent_state=agent_state or self.agent_state(),
            master_job_state=master_state or self.master_job_state(),
            go_evidence=self.evidence(),
            expected_agent_state_revision=7,
            go_evidence_ref=self.evidence_ref(),
            master_job_state_ref=self.master_ref(),
        )

    def readback(self, intent, observed=None):
        observed = json.loads(json.dumps(observed or intent["proposedState"]))
        return {
            "casSucceeded": True,
            "readbackVerified": True,
            "observedState": observed,
            "observedStateDigest": digest(observed),
            "readbackRef": "git:commit:claim",
            "observedBlobSha": "blob-claim-123",
        }

    def test_claim_mutates_only_agent_state_and_persists_activation(self):
        master = self.master_job_state()
        intent = self.intent(master_state=master)
        self.assertEqual("AGENT", intent["claimStateOwner"])
        self.assertFalse(intent["masterJobStateMutationAllowed"])
        self.assertEqual("RUNNING", intent["proposedState"]["runtimeStatus"])
        self.assertEqual("job-001", intent["proposedState"]["currentJob"]["jobId"])
        self.assertEqual(
            "activation-rc4-001",
            intent["proposedState"]["currentJob"]["claimId"],
        )
        self.assertIn(
            "activation-rc4-001",
            intent["proposedState"]["consumedActivationIds"],
        )
        self.assertEqual(
            digest(master),
            intent["readOnlyMasterJobStateDigest"],
        )

    def test_exact_provider_readback_confirms_claim(self):
        intent = self.intent()
        result = confirm_go_claim_after_provider_readback(
            claim_intent=intent,
            provider_readback=self.readback(intent),
            consumed_activation_ids=set(),
        )
        self.assertTrue(result["authoritative"])
        self.assertEqual("AGENT", result["claimStateOwner"])
        self.assertEqual(intent["proposedStateDigest"], result["stateDigest"])
        self.assertEqual(intent["bindings"], result["bindings"])

    def test_master_job_state_must_remain_waiting_and_read_only(self):
        master = self.master_job_state()
        master["lifecycleStatus"] = "CLAIMED"
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "JOB_NOT_WAITING_HUMAN_GO"
        ):
            self.intent(master_state=master)

    def test_tampered_job_binding_is_rejected(self):
        intent = self.intent()
        observed = json.loads(json.dumps(intent["proposedState"]))
        observed["currentJob"]["jobId"] = "job-other"
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CLAIM_STATE_MISMATCH"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback=self.readback(intent, observed),
                consumed_activation_ids=set(),
            )

    def test_tampered_agent_binding_is_rejected(self):
        intent = self.intent()
        observed = json.loads(json.dumps(intent["proposedState"]))
        observed["agentId"] = "agent-b"
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CLAIM_STATE_MISMATCH"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback=self.readback(intent, observed),
                consumed_activation_ids=set(),
            )

    def test_wrong_declared_digest_is_rejected(self):
        intent = self.intent()
        readback = self.readback(intent)
        readback["observedStateDigest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CLAIM_READBACK_DIGEST_INVALID"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback=readback,
                consumed_activation_ids=set(),
            )

    def test_missing_persisted_activation_is_rejected(self):
        intent = self.intent()
        observed = json.loads(json.dumps(intent["proposedState"]))
        observed["consumedActivationIds"] = []
        tampered_intent = dict(intent)
        tampered_intent["proposedState"] = observed
        tampered_intent["proposedStateDigest"] = digest(observed)
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CLAIM_ACTIVATION_NOT_PERSISTED"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=tampered_intent,
                provider_readback=self.readback(tampered_intent, observed),
                consumed_activation_ids=set(),
            )

    def test_missing_current_job_claim_id_is_rejected(self):
        intent = self.intent()
        observed = json.loads(json.dumps(intent["proposedState"]))
        observed["currentJob"]["claimId"] = "other-claim"
        tampered_intent = dict(intent)
        tampered_intent["proposedState"] = observed
        tampered_intent["proposedStateDigest"] = digest(observed)
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CLAIM_ID_NOT_PERSISTED"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=tampered_intent,
                provider_readback=self.readback(tampered_intent, observed),
                consumed_activation_ids=set(),
            )

    def test_duplicate_confirm_is_rejected_by_local_cache(self):
        intent = self.intent()
        consumed = set()
        confirm_go_claim_after_provider_readback(
            claim_intent=intent,
            provider_readback=self.readback(intent),
            consumed_activation_ids=consumed,
        )
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "GO_EVIDENCE_ALREADY_CONSUMED"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback=self.readback(intent),
                consumed_activation_ids=consumed,
            )


if __name__ == "__main__":
    unittest.main()
