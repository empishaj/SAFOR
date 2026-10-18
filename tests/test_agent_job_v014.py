import copy
import json
import unittest
from pathlib import Path
from runtime.agent_jobs import AgentJobValidationError, render_agent_chat_output, validate_agent_job, validate_job_state_transition
ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

class AgentJobV014Tests(unittest.TestCase):

    def pointer(self, path, repository='example/safor-memory'):
        return {'repository': repository, 'ref': 'commit123', 'path': path, 'blobSha': 'blob1234'}

    def target(self, repository_class, repository, branch, path_pattern, operations=None):
        return {'repositoryClass': repository_class, 'repository': repository, 'branch': branch, 'pathPattern': path_pattern, 'allowedOperations': operations or ['READ', 'CREATE', 'MODIFY', 'COMMIT', 'PUSH']}

    def base_job(self):
        control = 'example/safor-memory'
        product = 'example/product'
        response_types = {'JOB_RESULT': 'job-result', 'JOB_ERROR': 'job-error', 'CLARIFICATION_REQUEST': 'clarification-request', 'CAPABILITY_MISMATCH': 'capability-mismatch', 'IMPROVEMENT_PROPOSAL': 'improvement-proposal'}
        response_contracts = {}
        for response_type, slug in response_types.items():
            response_contracts[response_type] = {'responseType': response_type, 'templateRef': self.pointer(f'v0.14.0/templates/responses/{slug}.template.json', 'empishaj/SAFOR'), 'schemaRef': self.pointer('v0.14.0/schemas/agent-response.schema.json', 'empishaj/SAFOR'), 'writeTarget': self.target('CONTROL_REPOSITORY', control, 'main', 'projects/example/agents/agent-dev-003/outbox/{jobId}/{responseId}.json', ['READ', 'CREATE', 'COMMIT', 'PUSH']), 'required': True}
        response_contracts['responseIndexTarget'] = self.target('CONTROL_REPOSITORY', control, 'main', 'projects/example/agents/agent-dev-003/outbox/index.json', ['READ', 'CREATE', 'MODIFY', 'COMMIT', 'PUSH', 'UPDATE_INDEX'])
        response_contracts['resolutionSchemaRef'] = self.pointer('v0.14.0/schemas/agent-response-resolution.schema.json', 'empishaj/SAFOR')
        return {'format': 'SAFOR_AGENT_JOB', 'schemaVersion': '0.14.0', 'identity': {'jobId': '0199f0aa-7e40-7abc-8a12-000000000014', 'jobKey': 'wp-014-impl', 'jobType': 'IMPLEMENTATION', 'contractRevision': 1, 'immutableAfterPublication': True}, 'lineage': {'projectId': 'project-001', 'valueStreamId': 'value-stream-001', 'packageId': 'WP-014', 'packageRevision': 1, 'workItemId': 'WP-014-IMPL', 'workItemRevision': 1, 'parentWorkItemId': None, 'rootPackageId': 'PLAN-001', 'sequence': {'planSequence': 14, 'packageSequence': 14, 'dispatchSequence': 1, 'attempt': 1, 'reworkCycle': 0}, 'supersedesJobId': None, 'triggerConflictRef': None}, 'provenance': {'createdAt': '2026-10-17T21:30:00Z', 'issuedAt': '2026-10-17T21:30:00Z', 'masterId': 'SAFOR-MASTER:project-001', 'masterVersion': '0.14.0', 'masterRunId': 'run-014', 'masterStateRevision': 10, 'planningRef': self.pointer('projects/example/planning/plan.json'), 'mandateRef': self.pointer('projects/example/decisions/mandate.json')}, 'assignment': {'agentId': 'agent-dev-003', 'displayName': 'Nova Dev', 'identityRevision': 2, 'identityRef': self.pointer('projects/example/agents/agent-dev-003/identity.json'), 'assignmentMode': 'EXCLUSIVE', 'assignmentReason': 'Role and immutable skills match.'}, 'domainContext': {'creationType': 'SOFTWARE_SAAS', 'domainId': 'SOFTWARE_SAAS', 'factoryRef': self.pointer('packages/factory.json'), 'operatingModelRef': self.pointer('packages/operating-model.json'), 'compatibilityDecisionRef': self.pointer('packages/compatibility-decision.json')}, 'roleContract': {'roleId': 'JAVA_DEVELOPER', 'roleName': 'Java Developer', 'roleDefinitionRef': self.pointer('profiles/roles/java-developer.json'), 'mission': 'Implement the accepted change.', 'responsibilities': ['Create code and tests.'], 'mustNotActAs': ['REVIEWER', 'MASTER'], 'decisionRights': [], 'authorityExpansionAllowed': False}, 'skills': [{'skillId': 'java-spring', 'skillVersion': '1.0.0', 'mandatory': True, 'description': 'Java and Spring implementation.', 'executionInstructions': ['Follow the pinned design.'], 'useFor': ['implementation'], 'skillRef': self.pointer('profiles/skills/java-spring-1.0.0.json'), 'requiredLevel': 'PROFICIENT'}], 'task': {'title': 'Implement WP-014', 'objective': 'Produce a tested contribution.', 'instruction': 'Implement only the pinned scope.', 'expectedOutcome': 'A reviewable contribution.', 'completionDefinition': 'All criteria and checks pass.', 'inScope': ['src', 'tests'], 'outOfScope': ['deployment'], 'assumptions': ['Pinned design is authoritative.'], 'acceptanceCriteria': ['Tests pass.', 'Scope is respected.']}, 'dependencies': {'requiredWorkItems': [self.pointer('decisions/wp-013-acceptance.json')], 'dependencyPredicate': 'ALL_REQUIRED_ACCEPTED'}, 'inputs': [{'inputId': 'design', 'artifactRef': self.pointer('artifacts/design.json'), 'mode': 'READ_ONLY', 'expectedType': 'SOLUTION_DESIGN', 'purpose': 'Implementation design.'}], 'authorization': {'authorityBasis': self.pointer('decisions/execution-mandate.json'), 'actualProviderRightsMustBeVerified': True, 'repositoryPermissions': [{'repositoryClass': 'WORK_REPOSITORY', 'repository': product, 'read': True, 'write': {'allowed': True, 'allowedBranches': ['safor/job/wp-014/agent-dev-003'], 'allowedPaths': ['src/', 'tests/']}, 'branchCreate': True, 'commit': True, 'push': True, 'changeRequestCreate': True, 'merge': False, 'deploy': False}, {'repositoryClass': 'CONTROL_REPOSITORY', 'repository': control, 'read': True, 'write': {'allowed': True, 'allowedBranches': ['main'], 'allowedPaths': ['projects/example/agents/agent-dev-003/state.json', 'projects/example/agents/agent-dev-003/outbox/', 'projects/example/agents/agent-dev-003/evidence/', 'projects/example/agents/agent-dev-003/audit/']}, 'branchCreate': False, 'commit': True, 'push': True, 'changeRequestCreate': False, 'merge': False, 'deploy': False}], 'responseWriteDoesNotGrantProductWrite': True, 'productWriteDoesNotGrantResponseWrite': True, 'explicitlyForbidden': ['default branch mutation', 'MASTER state write', 'merge', 'deployment']}, 'workspace': {'productWorkspace': {'workspaceClass': 'REMOTE_GIT', 'repository': product, 'defaultBranch': 'main', 'jobBranch': 'safor/job/wp-014/agent-dev-003', 'baseCommitSha': 'abcdef1234567', 'allowedPaths': ['src/', 'tests/'], 'mutating': True}, 'responseWorkspace': self.target('CONTROL_REPOSITORY', control, 'main', 'projects/example/agents/agent-dev-003/outbox/', ['READ', 'CREATE', 'MODIFY', 'COMMIT', 'PUSH']), 'readSet': [self.pointer('artifacts/design.json')], 'exclusiveKeys': ['branch:safor/job/wp-014/agent-dev-003']}, 'scheduling': {'priority': 10, 'dispatchRevision': 1, 'dispatchState': 'WAITING_HUMAN_GO', 'dispatchWaveRef': self.pointer('master/dispatch-waves/wave-014.json'), 'resourceLeaseRefs': [self.pointer('master/resource-leases/lease-014.json')], 'activationMode': 'HUMAN_GO_REQUIRED', 'claimPolicy': {'exclusiveAgentClaim': True, 'optimisticConcurrencyRequired': True, 'humanGoEvidenceRequired': True}}, 'outputContract': {'requiredOutputs': ['CONTRIBUTION', 'TEST_EVIDENCE'], 'productWriteTarget': self.target('WORK_REPOSITORY', product, 'safor/job/wp-014/agent-dev-003', '{allowedPaths}', ['READ', 'CREATE', 'MODIFY', 'COMMIT', 'PUSH', 'OPEN_CHANGE_REQUEST'])}, 'responseContracts': response_contracts, 'communicationContract': {'modelRef': self.pointer('v0.14.0/agent-communication-model.json', 'empishaj/SAFOR'), 'chatOutputSchemaRef': self.pointer('v0.14.0/schemas/agent-chat-output.schema.json', 'empishaj/SAFOR'), 'humanDomainConversationAllowed': False, 'detailedReportsInGit': True, 'allowedStatuses': ['READY', 'STARTED', 'SUBMITTED', 'BLOCKED', 'REIDENTIFICATION_REQUIRED']}, 'verificationContract': {'acceptanceCriteria': ['All task criteria pass.'], 'evidenceRequirements': ['CONTRIBUTION_REFERENCE', 'TEST_RESULT_EVIDENCE'], 'independentReviewRequired': True, 'reviewerMustDifferFromAuthor': True, 'acceptanceAuthority': 'MASTER', 'integrationAuthority': 'MASTER_OR_EXPLICIT_HUMAN_AUTHORITY'}, 'constraints': {'stopConditions': ['STOP', 'PAUSE', 'identity mismatch', 'stale input', 'missing skill', 'missing permission'], 'noScopeExpansion': True, 'noRoleSwitch': True, 'noSelfAcceptance': True, 'noMasterStateWrite': True, 'noAutomaticJobSwitch': True, 'noJobPromptTransport': True}, 'humanReadableProjection': self.pointer('projects/example/agents/agent-dev-003/inbox/job-014.md')}

    def test_wp03_files_parse(self):
        paths = ['v0.14.0/agent-communication-model.json', 'v0.14.0/agent-job-contract-model.json', 'v0.14.0/agent-workspace-model.json', 'v0.14.0/schemas/agent-job.schema.json', 'v0.14.0/schemas/agent-job-state.schema.json', 'v0.14.0/schemas/agent-chat-output.schema.json']
        for path in paths:
            with self.subTest(path=path):
                doc = load(path)
                if '/schemas/' in path:
                    self.assertEqual(doc['properties']['schemaVersion']['const'], '0.14.0')
                else:
                    self.assertEqual(doc['schemaVersion'], '0.14.0')
        self.assertIn('Response Contracts & Return Paths', (ROOT / 'v0.14.0/templates/agent-job-human.template.md').read_text(encoding='utf-8'))

    def test_valid_job_contract(self):
        validate_agent_job(self.base_job())

    def test_all_five_response_contracts_are_mandatory(self):
        job = self.base_job()
        del job['responseContracts']['JOB_ERROR']
        with self.assertRaisesRegex(AgentJobValidationError, 'REQUIRED_RESPONSE_CONTRACTS_MISSING'):
            validate_agent_job(job)

    def test_response_contract_cannot_point_to_wrong_template(self):
        job = self.base_job()
        job['responseContracts']['JOB_RESULT']['templateRef']['path'] = 'v0.14.0/templates/responses/job-error.template.json'
        with self.assertRaisesRegex(AgentJobValidationError, 'RESPONSE_TEMPLATE_MISMATCH'):
            validate_agent_job(job)

    def test_direct_default_branch_mutation_is_forbidden(self):
        job = self.base_job()
        job['workspace']['productWorkspace']['jobBranch'] = 'main'
        job['outputContract']['productWriteTarget']['branch'] = 'main'
        with self.assertRaisesRegex(AgentJobValidationError, 'DIRECT_DEFAULT_BRANCH_MUTATION_FORBIDDEN'):
            validate_agent_job(job)

    def test_remote_product_and_response_repositories_are_separate(self):
        job = self.base_job()
        same = job['workspace']['productWorkspace']['repository']
        job['workspace']['responseWorkspace']['repository'] = same
        for response_type in ('JOB_RESULT', 'JOB_ERROR', 'CLARIFICATION_REQUEST', 'CAPABILITY_MISMATCH', 'IMPROVEMENT_PROPOSAL'):
            job['responseContracts'][response_type]['writeTarget']['repository'] = same
        job['responseContracts']['responseIndexTarget']['repository'] = same
        with self.assertRaisesRegex(AgentJobValidationError, 'REMOTE_PRODUCT_AND_RESPONSE_REPOSITORIES_MUST_DIFFER'):
            validate_agent_job(job)

    def test_actual_provider_rights_check_is_mandatory(self):
        job = self.base_job()
        job['authorization']['actualProviderRightsMustBeVerified'] = False
        with self.assertRaisesRegex(AgentJobValidationError, 'ACTUAL_PROVIDER_RIGHTS_CHECK_REQUIRED'):
            validate_agent_job(job)

    def test_rework_requires_superseded_job_and_conflict(self):
        job = self.base_job()
        job['lineage']['sequence']['attempt'] = 2
        job['lineage']['sequence']['reworkCycle'] = 1
        with self.assertRaisesRegex(AgentJobValidationError, 'REWORK_MUST_REFERENCE_SUPERSEDED_JOB'):
            validate_agent_job(job)
        job['lineage']['supersedesJobId'] = '0199f0aa-7e40-7abc-8a12-000000000013'
        job['lineage']['triggerConflictRef'] = self.pointer('agents/agent-dev-003/outbox/job-013/conflict.json')
        validate_agent_job(job)

    def test_job_requires_human_go_and_no_prompt_transport(self):
        job = self.base_job()
        self.assertEqual(job['scheduling']['activationMode'], 'HUMAN_GO_REQUIRED')
        self.assertTrue(job['scheduling']['claimPolicy']['humanGoEvidenceRequired'])
        self.assertTrue(job['constraints']['noJobPromptTransport'])
        job['scheduling']['dispatchState'] = 'READY'
        with self.assertRaisesRegex(AgentJobValidationError, 'JOB_MUST_PUBLISH_AS_WAITING_HUMAN_GO'):
            validate_agent_job(job)

    def test_independent_reviewer_must_differ(self):
        job = self.base_job()
        job['verificationContract']['reviewerMustDifferFromAuthor'] = False
        with self.assertRaisesRegex(AgentJobValidationError, 'INDEPENDENT_REVIEWER_MUST_DIFFER'):
            validate_agent_job(job)

    def test_state_machine_separates_submission_verification_acceptance(self):
        validate_job_state_transition(from_status='RUNNING', to_status='RESPONSE_SUBMITTED', evidence_refs=['response:001'])
        with self.assertRaisesRegex(AgentJobValidationError, 'JOB_STATE_TRANSITION_FORBIDDEN'):
            validate_job_state_transition(from_status='RESPONSE_SUBMITTED', to_status='ACCEPTED', evidence_refs=['response:001'])
        validate_job_state_transition(from_status='RESPONSE_SUBMITTED', to_status='VERIFIED', evidence_refs=['verification:001'])
        validate_job_state_transition(from_status='VERIFIED', to_status='ACCEPTED', evidence_refs=['acceptance:001'])
        validate_job_state_transition(from_status='ACCEPTED', to_status='INTEGRATED', evidence_refs=['merge:001'])

    def test_go_transition_requires_go_evidence(self):
        with self.assertRaisesRegex(AgentJobValidationError, 'GO_EVIDENCE_REQUIRED'):
            validate_job_state_transition(from_status='WAITING_HUMAN_GO', to_status='GO_OBSERVED', evidence_refs=['generic:evidence'])
        validate_job_state_transition(from_status='WAITING_HUMAN_GO', to_status='GO_OBSERVED', evidence_refs=['go-evidence:activation-001'])

    def test_minimal_chat_output_for_all_allowed_statuses(self):
        cases = (('READY', None, None, None), ('STARTED', 'wp-014-impl', 'safor/job/wp-014/agent', None), ('SUBMITTED', 'wp-014-impl', None, 'git:response'), ('BLOCKED', 'wp-014-impl', None, 'git:conflict'), ('REIDENTIFICATION_REQUIRED', None, None, None))
        for status, job_key, branch, details in cases:
            with self.subTest(status=status):
                output = render_agent_chat_output(status=status, project_id='project-001', agent_id='agent-dev-003', display_name='Nova Dev', job_key=job_key, target_branch=branch, details_ref=details)
                self.assertNotIn('\n', output['text'])
                self.assertLessEqual(len(output['text'].split()), 36)
                self.assertFalse(output['containsDomainDetail'])

    def test_blocked_chat_requires_git_reference(self):
        with self.assertRaisesRegex(AgentJobValidationError, 'BLOCKED_REQUIRES_JOB_AND_DETAILS_REF'):
            render_agent_chat_output(status='BLOCKED', project_id='project-001', agent_id='agent-dev-003', display_name='Nova Dev', job_key='wp-014-impl')
if __name__ == '__main__':
    unittest.main()
