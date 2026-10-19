import copy
import hashlib
import json
import unittest
from pathlib import Path

from runtime.agent_responses import (
    AgentResponseValidationError,
    confirm_agent_response_after_provider_readback,
    prepare_agent_response,
    validate_agent_response,
    validate_agent_response_index,
    validate_response_index_binding,
    validate_response_resolution,
)


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class AgentResponsesV014Tests(unittest.TestCase):
    def setUp(self):
        self.pointer = {
            "repository": "example/safor-memory",
            "ref": "abc1234",
            "path": "projects/example/agents/agent-dev-003/inbox/job.json",
            "blobSha": "def5678",
        }
        self.expected_job = {
            "projectId": "project-001",
            "jobId": "job-014",
            "packageId": "WP-014",
            "workItemId": "WP-014-IMPL",
            "agentId": "agent-dev-003",
            "identityRevision": 2,
            "jobContractBlobSha": "def5678",
            "jobContractPath": self.pointer["path"],
        }

    def base(self, response_type, template_path, status, chat_status):
        return {
            "format": "SAFOR_AGENT_RESPONSE",
            "schemaVersion": "0.14.0",
            "responseId": f"response-{response_type.lower()}-001",
            "responseType": response_type,
            "projectId": "project-001",
            "jobId": "job-014",
            "packageId": "WP-014",
            "workItemId": "WP-014-IMPL",
            "agentId": "agent-dev-003",
            "identityRevision": 2,
            "jobContractRef": copy.deepcopy(self.pointer),
            "observedJobContractBlobSha": "def5678",
            "responseContractRef": {
                "repository": "empishaj/SAFOR",
                "ref": "v0.14.0-rc.1",
                "path": template_path,
                "blobSha": "1234567",
            },
            "targetMasterRef": "projects/example/master/jobs/job-014.json",
            "createdAt": "2026-10-17T21:00:00Z",
            "status": status,
            "summary": "Verifizierbare Rückmeldung.",
            "executionControl": {
                "controlsJobLifecycle": response_type != "IMPROVEMENT_PROPOSAL",
                "executionStopped": response_type != "IMPROVEMENT_PROPOSAL",
                "furtherProductMutationAllowed": False,
                "scopeExpansionAllowed": False,
                "agentMayAskHumanDomainQuestions": False,
            },
            "chatStatus": chat_status,
            "evidenceRefs": [],
            "providerMutationRefs": [],
            "payload": {},
            "immutable": True,
        }

    def job(self):
        response_types = {
            "JOB_RESULT": "job-result",
            "JOB_ERROR": "job-error",
            "CLARIFICATION_REQUEST": "clarification-request",
            "CAPABILITY_MISMATCH": "capability-mismatch",
            "IMPROVEMENT_PROPOSAL": "improvement-proposal",
        }
        contracts = {}
        for response_type, slug in response_types.items():
            contracts[response_type] = {
                "responseType": response_type,
                "templateRef": {
                    "repository": "empishaj/SAFOR",
                    "ref": "commit-rc6",
                    "path": f"v0.14.0/templates/responses/{slug}.template.json",
                    "blobSha": "template123",
                },
                "schemaRef": {
                    "repository": "empishaj/SAFOR",
                    "ref": "commit-rc6",
                    "path": "v0.14.0/schemas/agent-response.schema.json",
                    "blobSha": "schema123",
                },
                "writeTarget": {
                    "repositoryClass": "CONTROL_REPOSITORY",
                    "repository": "example/safor-memory",
                    "branch": "main",
                    "pathPattern": "projects/example/agents/agent-dev-003/outbox/{jobId}/{responseId}.json",
                    "allowedOperations": ["READ", "CREATE", "COMMIT", "PUSH"],
                },
                "required": True,
                "preWriteSchemaValidationRequired": True,
                "providerReadbackRequired": True,
                "postReadbackSchemaValidationRequired": True,
            }
        return {
            "identity": {"jobId": "job-014"},
            "lineage": {
                "projectId": "project-001",
                "packageId": "WP-014",
                "workItemId": "WP-014-IMPL",
            },
            "assignment": {"agentId": "agent-dev-003", "identityRevision": 2},
            "responseContracts": contracts,
        }

    def conflict(self, conflict_type="TECHNICAL_FAILURE"):
        return {
            "conflictId": "conflict-001",
            "conflictType": conflict_type,
            "severity": "HIGH",
            "description": "Ausführung ist nicht sicher möglich.",
            "blockedStep": "PREFLIGHT",
            "affectedRefs": ["job:job-014"],
            "suggestedResolution": "MASTER soll einen korrigierten Job erzeugen.",
            "status": "OPEN",
            "responseTemplateVersion": "1.0.0",
        }

    def result(self):
        response = self.base(
            "JOB_RESULT",
            "v0.14.0/templates/responses/job-result.template.json",
            "SUBMITTED",
            "SUBMITTED",
        )
        response["payload"] = {
            "completionStatus": "COMPLETED",
            "outputs": [{"ref": "product:artifact", "expectedType": "CONTRIBUTION"}],
            "gitTrace": [],
            "checks": [],
            "openItems": [],
        }
        return response

    def error(self):
        response = self.base(
            "JOB_ERROR",
            "v0.14.0/templates/responses/job-error.template.json",
            "FAILED",
            "BLOCKED",
        )
        response["payload"] = {
            "errorClass": "PROVIDER_WRITE_FAILED",
            "failedStep": "WRITE_PRODUCT_ARTIFACT",
            "reproducibleFinding": "Provider denied the requested write.",
            "retryable": False,
            "safeState": "No unverified product mutation was recorded.",
            "blockedArtifacts": ["product:artifact"],
            "conflict": self.conflict(),
        }
        return response

    def clarification(self):
        response = self.base(
            "CLARIFICATION_REQUEST",
            "v0.14.0/templates/responses/clarification-request.template.json",
            "BLOCKED",
            "BLOCKED",
        )
        response["payload"] = {
            "question": "Which contradictory acceptance rule is authoritative?",
            "affectedJobFields": ["task.completionDefinition", "verificationContract"],
            "options": ["Use task rule", "Use verification rule"],
            "recommendedOption": "Use verification rule",
            "conflict": self.conflict("CONTRADICTORY_JOB"),
        }
        return response

    def mismatch(self):
        response = self.base(
            "CAPABILITY_MISMATCH",
            "v0.14.0/templates/responses/capability-mismatch.template.json",
            "BLOCKED",
            "BLOCKED",
        )
        response["payload"] = {
            "expected": {
                "roleIds": ["JAVA_DEVELOPER"],
                "skillIds": ["java-spring"],
                "domainIds": ["SOFTWARE_SAAS"],
                "technologyIds": ["JAVA", "SPRING"],
            },
            "available": {
                "roleIds": ["EDITOR"],
                "skillIds": ["proofreading"],
                "domainIds": ["BOOK_CREATION"],
                "technologyIds": [],
            },
            "risk": "Fachfremde Bearbeitung.",
            "affectedScope": ["implementation"],
            "conflict": self.conflict("ROLE_MISMATCH"),
        }
        return response

    def proposal(self):
        response = self.base(
            "IMPROVEMENT_PROPOSAL",
            "v0.14.0/templates/responses/improvement-proposal.template.json",
            "ADVISORY",
            "NONE",
        )
        response["payload"] = {
            "proposalId": "proposal-001",
            "problem": "A repeated read could be replaced by a pointer.",
            "suggestion": "Add a compact projection.",
            "expectedBenefit": "Less latency.",
            "risk": "Projection can become stale.",
            "affectedProcess": "status reporting",
            "blocking": False,
            "requiresSeparateDecision": True,
            "jobScopeChanged": False,
        }
        return response

    def test_wp02_json_files_parse(self):
        paths = [
            "v0.14.0/agent-response-contract-model.json",
            "v0.14.0/schemas/agent-response.schema.json",
            "v0.14.0/schemas/agent-response-index.schema.json",
            "v0.14.0/schemas/agent-response-resolution.schema.json",
            "v0.14.0/templates/responses/job-result.template.json",
            "v0.14.0/templates/responses/job-error.template.json",
            "v0.14.0/templates/responses/clarification-request.template.json",
            "v0.14.0/templates/responses/capability-mismatch.template.json",
            "v0.14.0/templates/responses/improvement-proposal.template.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                doc = load(path)
                if "/schemas/" in path:
                    self.assertEqual(
                        doc["properties"]["schemaVersion"]["const"], "0.14.0"
                    )
                else:
                    self.assertEqual(doc["schemaVersion"], "0.14.0")

    def test_all_five_response_types_validate(self):
        for response in (
            self.result(), self.error(), self.clarification(),
            self.mismatch(), self.proposal(),
        ):
            with self.subTest(response_type=response["responseType"]):
                validate_agent_response(response, expected_job=self.expected_job)

    def test_prepare_response_uses_bound_template_and_schema(self):
        job_contract_ref = copy.deepcopy(self.pointer)
        response = prepare_agent_response(
            job=self.job(),
            response_type="JOB_RESULT",
            response_id="response-job_result-002",
            created_at="2026-10-19T13:38:00Z",
            summary="Completed.",
            payload={
                "completionStatus": "COMPLETED",
                "outputs": [{"ref": "product:artifact", "expectedType": "CONTRIBUTION"}],
                "gitTrace": [],
                "checks": [],
                "openItems": [],
            },
            job_contract_ref=job_contract_ref,
            target_master_ref="projects/example/master/jobs/job-014.json",
            evidence_refs=["evidence:claim"],
            provider_mutation_refs=["git:product:commit"],
        )
        self.assertEqual(set(response), {
            "format", "schemaVersion", "responseId", "responseType", "projectId",
            "jobId", "packageId", "workItemId", "agentId", "identityRevision",
            "jobContractRef", "observedJobContractBlobSha", "responseContractRef",
            "targetMasterRef", "createdAt", "status", "summary", "executionControl",
            "chatStatus", "evidenceRefs", "providerMutationRefs", "payload", "immutable",
        })
        self.assertEqual(
            "v0.14.0/templates/responses/job-result.template.json",
            response["responseContractRef"]["path"],
        )
        validate_agent_response(response, expected_job=self.expected_job)

    def test_provider_readback_must_match_and_revalidate_response(self):
        response = self.result()
        digest = "sha256:" + hashlib.sha256(
            json.dumps(
                response,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        confirmed = confirm_agent_response_after_provider_readback(
            proposed_response=response,
            provider_readback={
                "writeSucceeded": True,
                "readbackVerified": True,
                "observedResponse": copy.deepcopy(response),
                "observedResponseDigest": digest,
                "readbackRef": "git:response:commit",
                "observedBlobSha": "responseblob123",
            },
            expected_job=self.expected_job,
        )
        self.assertTrue(confirmed["authoritativePersistence"])
        self.assertEqual(response["responseId"], confirmed["responseId"])

    def test_echo_e2e_simplified_job_result_is_rejected(self):
        response = {
            "format": "SAFOR_AGENT_RESPONSE",
            "schemaVersion": "0.14.0",
            "responseType": "JOB_RESULT",
            "responseId": "019d9f6b-0000-7abc-8d21-000000000001",
            "projectId": "project-001",
            "jobId": "job-014",
            "jobKey": "or03-human-go-real-git-001",
            "agentId": "agent-dev-003",
            "identityRevision": 2,
            "status": "SUBMITTED",
            "createdAt": "2026-10-19T13:38:00Z",
            "summary": "Plausible but nonconforming result.",
            "result": {"productArtifact": {"path": "proof.md"}},
            "evidence": {"claimReadback": {"commitSha": "abc1234"}},
        }
        with self.assertRaisesRegex(
            AgentResponseValidationError, "RESPONSE_FIELDS_INVALID"
        ):
            validate_agent_response(response, expected_job=self.expected_job)

    def test_readback_with_extra_field_is_rejected_before_submission(self):
        response = self.result()
        observed = copy.deepcopy(response)
        observed["jobKey"] = "forbidden-freeform-field"
        digest = "sha256:" + hashlib.sha256(
            json.dumps(
                observed,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        with self.assertRaisesRegex(
            AgentResponseValidationError, "RESPONSE_FIELDS_INVALID"
        ):
            confirm_agent_response_after_provider_readback(
                proposed_response=response,
                provider_readback={
                    "writeSucceeded": True,
                    "readbackVerified": True,
                    "observedResponse": observed,
                    "observedResponseDigest": digest,
                    "readbackRef": "git:response:commit",
                    "observedBlobSha": "responseblob123",
                },
                expected_job=self.expected_job,
            )

    def test_result_requires_output(self):
        response = self.result()
        response["payload"]["outputs"] = []
        with self.assertRaisesRegex(
            AgentResponseValidationError, "JOB_RESULT_OUTPUTS_REQUIRED"
        ):
            validate_agent_response(response)

    def test_blocker_cannot_allow_more_product_mutation(self):
        response = self.error()
        response["executionControl"]["furtherProductMutationAllowed"] = True
        with self.assertRaisesRegex(
            AgentResponseValidationError,
            "RESPONSE_CANNOT_AUTHORIZE_PRODUCT_MUTATION",
        ):
            validate_agent_response(response)

    def test_clarification_must_go_to_master_not_human(self):
        response = self.clarification()
        response["executionControl"]["agentMayAskHumanDomainQuestions"] = True
        with self.assertRaisesRegex(
            AgentResponseValidationError,
            "AGENT_HUMAN_DOMAIN_DIALOG_FORBIDDEN",
        ):
            validate_agent_response(response)

    def test_capability_mismatch_has_explicit_expected_and_available_sets(self):
        response = self.mismatch()
        del response["payload"]["expected"]["technologyIds"]
        with self.assertRaisesRegex(
            AgentResponseValidationError,
            "EXPECTED_CAPABILITY_FIELDS_INVALID",
        ):
            validate_agent_response(response)

    def test_improvement_proposal_cannot_change_job_scope(self):
        response = self.proposal()
        response["payload"]["jobScopeChanged"] = True
        with self.assertRaisesRegex(
            AgentResponseValidationError,
            "IMPROVEMENT_PROPOSAL_CANNOT_CHANGE_JOB_SCOPE",
        ):
            validate_agent_response(response)

    def test_template_must_match_discriminator(self):
        response = self.result()
        response["responseContractRef"]["path"] = (
            "v0.14.0/templates/responses/job-error.template.json"
        )
        with self.assertRaisesRegex(
            AgentResponseValidationError, "RESPONSE_TEMPLATE_PATH_MISMATCH"
        ):
            validate_agent_response(response)

    def test_job_binding_mismatch_is_rejected(self):
        response = self.result()
        response["agentId"] = "other-agent"
        with self.assertRaisesRegex(
            AgentResponseValidationError,
            "RESPONSE_JOB_BINDING_MISMATCH:agentId",
        ):
            validate_agent_response(response, expected_job=self.expected_job)

    def test_conflict_requires_open_status_and_full_fields(self):
        response = self.error()
        response["payload"]["conflict"]["status"] = "CLOSED"
        with self.assertRaisesRegex(
            AgentResponseValidationError, "NEW_CONFLICT_MUST_BE_OPEN"
        ):
            validate_agent_response(response)

    def test_resolution_is_separate_and_can_supersede(self):
        response = self.clarification()
        resolution = {
            "format": "SAFOR_AGENT_RESPONSE_RESOLUTION",
            "schemaVersion": "0.14.0",
            "resolutionId": "resolution-001",
            "projectId": "project-001",
            "responseId": response["responseId"],
            "responseRef": {
                "repository": "example/safor-memory",
                "ref": "commit123",
                "path": (
                    "projects/example/agents/agent-dev-003/outbox/"
                    "job-014/response-clarification_request-001.json"
                ),
                "blobSha": "blob1234",
            },
            "jobId": "job-014",
            "masterId": "SAFOR-MASTER:project-001",
            "decisionRef": {
                "repository": "example/safor-memory",
                "ref": "commit234",
                "path": "projects/example/decisions/clarification-001.json",
                "blobSha": "blob2345",
            },
            "resolutionStatus": "SUPERSEDED_BY_JOB",
            "supersedingJobId": "job-015",
            "resolvedAt": "2026-10-17T21:05:00Z",
            "immutable": True,
        }
        validate_response_resolution(resolution, response=response)
        self.assertEqual(response["payload"]["conflict"]["status"], "OPEN")

    def test_superseded_resolution_requires_new_job_id(self):
        response = self.clarification()
        resolution = {
            "format": "SAFOR_AGENT_RESPONSE_RESOLUTION",
            "schemaVersion": "0.14.0",
            "resolutionId": "resolution-001",
            "projectId": "project-001",
            "responseId": response["responseId"],
            "responseRef": {
                "repository": "example/safor-memory",
                "ref": "commit123",
                "path": "response.json",
                "blobSha": "blob1234",
            },
            "jobId": "job-014",
            "masterId": "SAFOR-MASTER:project-001",
            "decisionRef": {
                "repository": "example/safor-memory",
                "ref": "commit234",
                "path": "decision.json",
                "blobSha": "blob2345",
            },
            "resolutionStatus": "SUPERSEDED_BY_JOB",
            "supersedingJobId": None,
            "resolvedAt": "2026-10-17T21:05:00Z",
            "immutable": True,
        }
        with self.assertRaisesRegex(
            AgentResponseValidationError, "SUPERSEDING_JOB_ID_REQUIRED"
        ):
            validate_response_resolution(resolution, response=response)

    def test_canonical_response_index_validates(self):
        response = self.result()
        index = {
            "format": "SAFOR_AGENT_RESPONSE_INDEX",
            "schemaVersion": "0.14.0",
            "projectId": response["projectId"],
            "agentId": response["agentId"],
            "identityRevision": response["identityRevision"],
            "revision": 1,
            "authoritativeAcceptance": False,
            "entries": [
                {
                    "responseId": response["responseId"],
                    "responseType": response["responseType"],
                    "jobId": response["jobId"],
                    "responseRef": {
                        "repository": "example/safor-memory",
                        "ref": "commit123",
                        "path": (
                            "projects/example/agents/agent-dev-003/outbox/"
                            f"{response['jobId']}/{response['responseId']}.json"
                        ),
                        "blobSha": "blob1234",
                    },
                    "createdAt": response["createdAt"],
                    "responseState": "SUBMITTED",
                    "resolutionRef": None,
                }
            ],
            "updatedAt": response["createdAt"],
        }
        validate_agent_response_index(
            index,
            expected_project_id=response["projectId"],
            expected_agent_id=response["agentId"],
            expected_identity_revision=response["identityRevision"],
            expected_response=response,
        )

    def test_real_git_outbox_index_shape_is_rejected(self):
        response = self.result()
        invalid = {
            "format": "SAFOR_AGENT_OUTBOX_INDEX",
            "schemaVersion": "0.14.0",
            "projectId": response["projectId"],
            "agentId": response["agentId"],
            "identityRevision": response["identityRevision"],
            "revision": 1,
            "entries": [],
            "updatedAt": response["createdAt"],
        }
        with self.assertRaisesRegex(
            AgentResponseValidationError,
            "RESPONSE_INDEX_FIELDS_INVALID|RESPONSE_INDEX_FORMAT_INVALID",
        ):
            validate_agent_response_index(
                invalid,
                expected_project_id=response["projectId"],
                expected_agent_id=response["agentId"],
                expected_identity_revision=response["identityRevision"],
                expected_response=response,
            )

    def test_response_index_path_is_deterministic(self):
        response = self.result()
        entry = {
            "responseId": response["responseId"],
            "responseType": response["responseType"],
            "jobId": response["jobId"],
            "responseRef": {
                "repository": "example/safor-memory",
                "ref": "commit123",
                "path": (
                    "projects/example/agents/agent-dev-003/outbox/"
                    f"{response['jobId']}/{response['responseId']}.json"
                ),
                "blobSha": "blob1234",
            },
            "createdAt": response["createdAt"],
            "responseState": "SUBMITTED",
            "resolutionRef": None,
        }
        validate_response_index_binding(response=response, index_entry=entry)

    def test_unknown_response_type_fails_closed(self):
        response = self.result()
        response["responseType"] = "GENERIC_MESSAGE"
        with self.assertRaisesRegex(
            AgentResponseValidationError, "UNKNOWN_RESPONSE_TYPE"
        ):
            validate_agent_response(response)


if __name__ == "__main__":
    unittest.main()
