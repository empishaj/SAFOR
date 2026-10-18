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
    def pointer(self, path, blob):
        return {
            "repository": "example/safor-memory",
            "ref": "commit-go",
            "path": path,
            "blobSha": blob,
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
            "contractRef": self.pointer(
                "projects/example/agents/agent-a/inbox/job-001.json", "jobblob123"
            ),
            "updatedAt": "2026-10-18T09:59:00Z",
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
            "updatedAt": "2026-10-18T09:59:00Z",
        }

    def evidence(self):
        return {
            "format": "SAFOR_HUMAN_GO_EVIDENCE",
            "schemaVersion": "0.14.0",
            "activationId": "activation-rc5-001",
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

    def intent(self):
        return prepare_go_claim(
            master_job_state=self.master_state(),
            master_job_state_ref=self.pointer(
                "projects/example/master/jobs/job-001.json", "masterjob123"
            ),
            agent_state=self.agent_state(),
            go_evidence=self.evidence(),
            expected_agent_state_revision=4,
            consumed_activation_ids=set(),
            go_evidence_ref=self.pointer(
                "projects/example/evidence/go.json", "goblob123"
            ),
        )

    def readback(self, intent, observed=None, target_path=None):
        observed = json.loads(
            json.dumps(observed or intent["proposedAgentState"])
        )
        return {
            "casSucceeded": True,
            "readbackVerified": True,
            "targetPath": target_path or intent["casTargetPath"],
            "observedState": observed,
            "observedStateDigest": digest(observed),
            "readbackRef": "git:commit:claim",
            "observedBlobSha": "blob-claim-123",
        }

    def test_claim_persists_activation_consumption_inside_agent_state(self):
        intent = self.intent()
        self.assertIn(
            "activation-rc5-001",
            intent["proposedAgentState"]["consumedActivationIds"],
        )
        self.assertEqual("agents/agent-a/state.json", intent["casTargetPath"])

    def test_exact_provider_readback_confirms_agent_claim(self):
        intent = self.intent()
        result = confirm_go_claim_after_provider_readback(
            claim_intent=intent,
            provider_readback=self.readback(intent),
            consumed_activation_ids=set(),
        )
        self.assertTrue(result["authoritative"])
        self.assertEqual(
            intent["proposedAgentStateDigest"], result["stateDigest"]
        )
        self.assertEqual(intent["bindings"], result["bindings"])
        self.assertEqual(
            "SAFOR_AGENT_CLAIM_PROVIDER_VERIFIED",
            result["masterTransitionInput"]["format"],
        )
        self.assertEqual(
            7, result["masterTransitionInput"]["expectedMasterJobRevision"]
        )
        self.assertEqual("MASTER", result["masterTransitionInput"]["requiredWriter"])

    def test_tampered_job_binding_is_rejected(self):
        intent = self.intent()
        observed = json.loads(json.dumps(intent["proposedAgentState"]))
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
        observed = json.loads(json.dumps(intent["proposedAgentState"]))
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
        observed = json.loads(json.dumps(intent["proposedAgentState"]))
        observed["consumedActivationIds"] = []
        tampered_intent = dict(intent)
        tampered_intent["proposedAgentState"] = observed
        tampered_intent["proposedAgentStateDigest"] = digest(observed)
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CLAIM_ACTIVATION_NOT_PERSISTED"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=tampered_intent,
                provider_readback=self.readback(tampered_intent, observed),
                consumed_activation_ids=set(),
            )

    def test_master_job_path_can_never_be_agent_cas_target(self):
        intent = self.intent()
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "PROVIDER_CLAIM_TARGET_PATH_MISMATCH"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback=self.readback(
                    intent, target_path="master/jobs/job-001.json"
                ),
                consumed_activation_ids=set(),
            )

    def test_agent_master_lifecycle_write_flag_is_rejected(self):
        intent = self.intent()
        intent["agentMayWriteMasterLifecycle"] = True
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "AGENT_MASTER_LIFECYCLE_WRITE_FORBIDDEN"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback=self.readback(intent),
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
