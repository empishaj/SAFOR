import hashlib
import json
import unittest

from tests.v014_fixtures import (
    TEST_JOB_ID,
    canonical_response_index,
    expected_job_binding,
    pointer,
    valid_agent_job,
)
from runtime.agent_responses import prepare_agent_response
from runtime.go_evidence import (
    GoEvidenceValidationError,
    confirm_go_claim_after_provider_readback,
    confirm_result_submitted_state_after_provider_readback,
    prepare_go_claim,
    prepare_result_submitted_agent_state,
    validate_agent_state_contract,
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
            "jobId": TEST_JOB_ID,
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

    def job_contract(self):
        return valid_agent_job(
            project_id="project-001",
            job_id=TEST_JOB_ID,
            agent_id="agent-a",
            display_name="Agent Alpha",
            identity_revision=2,
            dispatch_revision=3,
            control_repository="example/safor-memory",
            control_branch="main",
            product_repository="example/product",
            product_branch="safor/job/test",
        )

    def job_contract_ref(self, master_state=None):
        return dict((master_state or self.master_job_state())["contractRef"])

    def evidence(self):
        return {
            "format": "SAFOR_HUMAN_GO_EVIDENCE",
            "schemaVersion": "0.14.0",
            "activationId": "activation-rc4-001",
            "projectId": "project-001",
            "agentId": "agent-a",
            "identityRevision": 2,
            "targetJobId": TEST_JOB_ID,
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
            job_contract=self.job_contract(),
            job_contract_ref=self.job_contract_ref(master_state),
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

    def test_claim_rejects_job_missing_required_claim_binding(self):
        invalid = self.job_contract()
        del invalid["scheduling"]["claimPolicy"]["agentStateSchemaRef"]
        with self.assertRaisesRegex(
            GoEvidenceValidationError,
            "AGENT_JOB_CONTRACT_INVALID",
        ):
            prepare_go_claim(
                agent_state=self.agent_state(),
                master_job_state=self.master_job_state(),
                job_contract=invalid,
                job_contract_ref=self.job_contract_ref(),
                go_evidence=self.evidence(),
                expected_agent_state_revision=7,
                go_evidence_ref=self.evidence_ref(),
                master_job_state_ref=self.master_ref(),
            )

    def test_claim_mutates_only_agent_state_and_persists_activation(self):
        master = self.master_job_state()
        intent = self.intent(master_state=master)
        self.assertEqual("AGENT", intent["claimStateOwner"])
        self.assertFalse(intent["masterJobStateMutationAllowed"])
        self.assertEqual("RUNNING", intent["proposedState"]["runtimeStatus"])
        self.assertEqual(TEST_JOB_ID, intent["proposedState"]["currentJob"]["jobId"])
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
            GoEvidenceValidationError, "AGENT_STATE_CURRENT_JOB_BINDING_MISMATCH"
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
            GoEvidenceValidationError, "AGENT_STATE_CLAIM_ACTIVATION_NOT_CONSUMED"
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
            GoEvidenceValidationError, "AGENT_STATE_CLAIM_ID_BINDING_MISMATCH"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=tampered_intent,
                provider_readback=self.readback(tampered_intent, observed),
                consumed_activation_ids=set(),
            )

    def test_proposed_claim_state_matches_exact_agent_state_contract(self):
        intent = self.intent()
        proposed = intent["proposedState"]
        validate_agent_state_contract(
            proposed,
            require_claim=True,
            expected_activation_id="activation-rc4-001",
            expected_job_id=TEST_JOB_ID,
            expected_dispatch_revision=3,
        )
        self.assertEqual(
            {
                "activationId",
                "activationEvidenceRef",
                "activatedAt",
                "selectedJobId",
                "selectedDispatchRevision",
            },
            set(proposed["session"]),
        )
        self.assertEqual(
            {
                "jobId",
                "jobRef",
                "jobBlobSha",
                "masterJobStateRef",
                "dispatchRevision",
                "claimId",
            },
            set(proposed["currentJob"]),
        )
        self.assertEqual(
            proposed["session"]["activationId"],
            proposed["currentJob"]["claimId"],
        )

    def test_echo_e2e_freeform_claim_state_is_rejected(self):
        intent = self.intent()
        observed = json.loads(json.dumps(intent["proposedState"]))
        observed["session"] = {
            "activationMode": "HUMAN_GO_REQUIRED",
            "activationId": "activation-rc4-001",
            "activatedAt": "2026-10-18T10:00:00Z",
            "source": "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT",
        }
        observed["currentJob"] = {
            "jobId": TEST_JOB_ID,
            "jobKey": "or03-human-go-real-git-001",
            "contractRevision": 1,
            "dispatchRevision": 3,
            "claimedAt": "2026-10-18T10:00:00Z",
            "claimAuthority": "AGENT_STATE_PROVIDER_CAS_READBACK",
        }
        with self.assertRaisesRegex(
            GoEvidenceValidationError, "AGENT_SESSION_FIELDS_INVALID"
        ):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback=self.readback(intent, observed),
                consumed_activation_ids=set(),
            )

    def test_result_submitted_state_uses_exact_schema_transition(self):
        intent = self.intent()
        running = intent["proposedState"]
        job = self.job_contract()
        contract_ref = self.job_contract_ref()
        payload = {
            "completionStatus": "COMPLETED",
            "outputs": [
                {
                    "ref": "example/product@safor/job/test:test-output/result.txt",
                    "expectedType": "TEST_OUTPUT",
                }
            ],
            "gitTrace": [
                {
                    "repository": "example/product",
                    "branch": "safor/job/test",
                    "baseCommitSha": "abcdef1234567",
                    "headCommitSha": "abcdef7654321",
                    "commitShas": ["abcdef7654321"],
                    "changedPaths": ["test-output/result.txt"],
                    "changeRequestRef": None,
                    "providerReadbackRef": "git:readback:product",
                }
            ],
            "checks": [
                {
                    "checkId": "product-readback",
                    "commandOrMethod": "provider readback",
                    "status": "PASS",
                    "evidenceRef": "git:readback:product",
                }
            ],
            "openItems": [],
        }
        response = prepare_agent_response(
            job=job,
            response_type="JOB_RESULT",
            response_id="response-001",
            created_at="2026-10-18T10:04:00Z",
            summary="Test result submitted.",
            payload=payload,
            job_contract_ref=contract_ref,
            target_master_ref="projects/example/master/jobs/job.json",
            evidence_refs=["git:claim"],
            provider_mutation_refs=["git:product"],
        )
        expected_job = expected_job_binding(
            job,
            blob_sha=contract_ref["blobSha"],
            contract_path=contract_ref["path"],
        )
        response_index = canonical_response_index(response=response)
        submitted = prepare_result_submitted_agent_state(
            agent_state=running,
            expected_agent_state_revision=8,
            response=response,
            response_index=response_index,
            expected_job=expected_job,
            response_ref="git:response:response-001",
            submitted_at="2026-10-18T10:05:00Z",
        )
        proposed = submitted["proposedState"]
        self.assertEqual("RESULT_SUBMITTED", proposed["runtimeStatus"])
        self.assertEqual("git:response:response-001", proposed["lastResponseRef"])
        self.assertEqual(
            running["currentJob"]["claimId"],
            proposed["currentJob"]["claimId"],
        )
        readback = {
            "casSucceeded": True,
            "readbackVerified": True,
            "observedState": json.loads(json.dumps(proposed)),
            "observedStateDigest": digest(proposed),
            "readbackRef": "git:commit:submitted",
            "observedBlobSha": "blob-submitted-123",
        }
        confirmed = confirm_result_submitted_state_after_provider_readback(
            state_intent=submitted,
            provider_readback=readback,
        )
        self.assertTrue(confirmed["authoritative"])
        self.assertEqual("RESULT_SUBMITTED", confirmed["state"]["runtimeStatus"])

    def test_result_submitted_rejects_noncanonical_response_index(self):
        intent = self.intent()
        running = intent["proposedState"]
        job = self.job_contract()
        contract_ref = self.job_contract_ref()
        payload = {
            "completionStatus": "COMPLETED",
            "outputs": [{"ref": "git:output", "expectedType": "TEST_OUTPUT"}],
            "gitTrace": [],
            "checks": [],
            "openItems": [],
        }
        response = prepare_agent_response(
            job=job,
            response_type="JOB_RESULT",
            response_id="response-001",
            created_at="2026-10-18T10:04:00Z",
            summary="Test result submitted.",
            payload=payload,
            job_contract_ref=contract_ref,
            target_master_ref="projects/example/master/jobs/job.json",
        )
        invalid_index = {
            "format": "SAFOR_AGENT_OUTBOX_INDEX",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "agentId": "agent-a",
            "identityRevision": 2,
            "revision": 1,
            "entries": [],
            "updatedAt": "2026-10-18T10:04:00Z",
        }
        with self.assertRaisesRegex(
            GoEvidenceValidationError,
            "RESULT_RESPONSE_CONTRACT_INVALID:RESPONSE_INDEX",
        ):
            prepare_result_submitted_agent_state(
                agent_state=running,
                expected_agent_state_revision=8,
                response=response,
                response_index=invalid_index,
                expected_job=expected_job_binding(
                    job,
                    blob_sha=contract_ref["blobSha"],
                    contract_path=contract_ref["path"],
                ),
                response_ref="git:response:response-001",
                submitted_at="2026-10-18T10:05:00Z",
            )

    def test_echo_e2e_freeform_submitted_state_is_rejected(self):
        intent = self.intent()
        invalid = json.loads(json.dumps(intent["proposedState"]))
        invalid["runtimeStatus"] = "SUBMITTED"
        invalid["lastResponseRef"] = {
            "repository": "example/safor-memory",
            "path": "response.json",
        }
        with self.assertRaisesRegex(
            GoEvidenceValidationError,
            "AGENT_STATE_RUNTIME_STATUS_INVALID|AGENT_STATE_LAST_RESPONSE_REF_INVALID",
        ):
            validate_agent_state_contract(
                invalid,
                require_claim=True,
                expected_activation_id="activation-rc4-001",
                expected_job_id=TEST_JOB_ID,
                expected_dispatch_revision=3,
                expected_runtime_status="RESULT_SUBMITTED",
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
