import copy
import json
import unittest
from pathlib import Path
from runtime.master_orchestration import MasterOrchestrationError, build_compact_project_status, expire_resource_lease, jobs_conflict, select_dispatch_wave
ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

class MasterSchedulerV014Tests(unittest.TestCase):

    def pointer(self, path):
        return {'repository': 'example/safor-memory', 'ref': 'commit123', 'path': path, 'blobSha': 'blob1234'}

    def agent(self, agent_id, display_name, capabilities, *, active=0, maximum=1, binding='BOUND'):
        return {'agentId': agent_id, 'displayName': display_name, 'agentKind': 'CHAT_AGENT', 'identityStatus': 'ACTIVE', 'chatBindingStatus': binding, 'dispatchEnabled': True, 'capabilityIds': capabilities, 'maxConcurrentJobs': maximum, 'activeJobs': active}

    def work(self, work_id, job_key, capabilities, *, priority=0, domains=None, keys=None, branch=None, scope='DECLARED', mutating=True, author=None, prohibited=None):
        return {'workItemId': work_id, 'jobKey': job_key, 'executionUnit': 'ATOMIC', 'status': 'READY', 'dependenciesAccepted': True, 'immutableInputs': True, 'mandateActive': True, 'providerRightsVerified': True, 'requiredCapabilities': capabilities, 'prohibitedAgentIds': prohibited or [], 'reviewOfAuthorAgentId': author, 'priority': priority, 'readySince': '2026-10-17T20:00:00Z', 'mutation': {'mutating': mutating, 'scope': scope, 'conflictDomains': domains or [], 'exclusiveKeys': keys or [], 'jobBranch': branch or f'safor/job/{job_key}/assigned-agent'}}

    def test_wp04_files_parse(self):
        paths = ['v0.14.0/master-status-model.json', 'v0.14.0/multi-agent-scheduler-model.json', 'v0.14.0/schemas/project-agent-status-index.schema.json', 'v0.14.0/schemas/project-status-index.schema.json', 'v0.14.0/schemas/scheduler-state.schema.json', 'v0.14.0/schemas/dispatch-wave.schema.json', 'v0.14.0/schemas/resource-lease.schema.json']
        for path in paths:
            with self.subTest(path=path):
                doc = load(path)
                if '/schemas/' in path:
                    self.assertEqual(doc['properties']['schemaVersion']['const'], '0.14.0')
                else:
                    self.assertEqual(doc['schemaVersion'], '0.14.0')

    def test_safe_jobs_are_dispatched_but_chat_is_not_activated(self):
        jobs = [self.work('WI-1', 'wi-1', ['code'], priority=10, domains=['src/a'], branch='safor/job/wi-1/dev-a'), self.work('WI-2', 'wi-2', ['test'], priority=9, domains=['tests/b'], branch='safor/job/wi-2/qa-b')]
        agents = [self.agent('agent-a', 'Nova Dev', ['code']), self.agent('agent-b', 'Astra QA', ['test'])]
        result = select_dispatch_wave(work_items=jobs, agents=agents)
        self.assertEqual(len(result['assignments']), 2)
        self.assertFalse(result['normalChatAgentsActivated'])
        self.assertEqual(result['dispatchOutcome'], 'WAITING_HUMAN_GO')
        self.assertTrue(all((assignment['dispatchState'] == 'WAITING_HUMAN_GO' and assignment['humanInstruction'] == 'GO' and (assignment['normalChatActivated'] is False) for assignment in result['assignments'])))

    def test_intersecting_write_domains_serialize(self):
        first = self.work('WI-1', 'wi-1', ['code'], domains=['src/shared'])
        second = self.work('WI-2', 'wi-2', ['code'], domains=['src/shared'])
        self.assertTrue(jobs_conflict(first, second))
        result = select_dispatch_wave(work_items=[first, second], agents=[self.agent('agent-a', 'Nova Dev', ['code']), self.agent('agent-b', 'Orion Dev', ['code'])])
        self.assertEqual(len(result['assignments']), 1)
        self.assertEqual(result['blockedWork'][0]['reasonCode'], 'WRITE_CONFLICT')

    def test_unknown_scope_conflicts_with_every_mutating_job(self):
        unknown = self.work('WI-1', 'wi-1', ['code'], scope='UNKNOWN', domains=[])
        declared = self.work('WI-2', 'wi-2', ['code'], domains=['src/b'])
        self.assertTrue(jobs_conflict(unknown, declared))
        result = select_dispatch_wave(work_items=[unknown, declared], agents=[self.agent('agent-a', 'Nova Dev', ['code']), self.agent('agent-b', 'Orion Dev', ['code'])])
        self.assertEqual(len(result['assignments']), 1)
        self.assertIn(result['blockedWork'][0]['reasonCode'], {'UNKNOWN_MUTATION_SCOPE', 'WRITE_CONFLICT'})

    def test_read_only_jobs_do_not_conflict(self):
        first = self.work('WI-1', 'wi-1', ['review'], mutating=False, domains=[])
        second = self.work('WI-2', 'wi-2', ['review'], mutating=False, domains=[])
        self.assertFalse(jobs_conflict(first, second))

    def test_capability_and_capacity_are_enforced(self):
        jobs = [self.work('WI-1', 'wi-1', ['java'], domains=['src/a']), self.work('WI-2', 'wi-2', ['java'], domains=['src/b'])]
        result = select_dispatch_wave(work_items=jobs, agents=[self.agent('agent-a', 'Nova Dev', ['java'], active=0, maximum=1)])
        self.assertEqual(len(result['assignments']), 1)
        self.assertEqual(result['blockedWork'][0]['reasonCode'], 'CAPACITY_EXHAUSTED')

    def test_unbound_chat_agent_is_not_eligible(self):
        result = select_dispatch_wave(work_items=[self.work('WI-1', 'wi-1', ['code'], domains=['src/a'])], agents=[self.agent('agent-a', 'Nova Dev', ['code'], binding='UNVERIFIED')])
        self.assertEqual(result['assignments'], [])
        self.assertEqual(result['blockedWork'][0]['reasonCode'], 'NO_ELIGIBLE_AGENT')

    def test_separation_of_duties_blocks_author_review(self):
        review = self.work('REV-1', 'rev-1', ['review'], mutating=False, author='agent-author')
        result = select_dispatch_wave(work_items=[review], agents=[self.agent('agent-author', 'Nova Dev', ['review'])])
        self.assertEqual(result['assignments'], [])
        self.assertEqual(result['blockedWork'][0]['reasonCode'], 'SOD_CONFLICT')

    def test_expired_lease_requires_reconciliation_and_no_reassignment(self):
        lease = {'format': 'SAFOR_RESOURCE_LEASE', 'schemaVersion': '0.14.0', 'projectId': 'project-001', 'leaseId': 'lease-001', 'jobId': 'job-001', 'agentId': 'agent-a', 'resourceType': 'JOB_BRANCH', 'resourceKey': 'safor/job/wi-1/agent-a', 'status': 'ACTIVE', 'acquiredAt': '2026-10-17T20:00:00Z', 'expiresAt': '2026-10-17T21:00:00Z', 'lastProviderReadbackRef': None, 'onExpiry': 'RECONCILE_REQUIRED'}
        expired = expire_resource_lease(lease, observed_at='2026-10-17T21:01:00Z')
        self.assertEqual(expired['status'], 'RECONCILE_REQUIRED')
        self.assertFalse(expired['silentReassignmentAllowed'])
        self.assertEqual(lease['status'], 'ACTIVE')

    def compact_inputs(self):
        job_ref = self.pointer('master/jobs/job-001.json')
        job = {'jobId': 'job-001', 'jobKey': 'wp-001-impl', 'lifecycleStatus': 'WAITING_HUMAN_GO', 'masterJobStateRef': job_ref, 'expectsResponse': True}
        agent = {'agentId': 'agent-a', 'displayName': 'Nova Dev', 'chatRef': 'chat:agent-a', 'startableJob': {'jobId': 'job-001', 'jobKey': 'wp-001-impl', 'jobRef': self.pointer('agents/agent-a/inbox/job-001.json')}}
        return (agent, job)

    def test_compact_status_lists_agents_to_start_without_full_scan(self):
        agent, job = self.compact_inputs()
        status = build_compact_project_status(project_id='project-001', project_slug='example', revision=1, roadmap_ref=self.pointer('planning/roadmap.json'), agent_status_index_ref=self.pointer('master/status/agents.json'), agent_status_entries=[agent], job_status_entries=[job], review_status_entries=[], blocker_status_entries=[], source_refs=[self.pointer('agents/index.json'), self.pointer('master/status/jobs.json')], observed_at='2026-10-17T21:00:00Z', stale_after='2026-10-17T22:00:00Z')
        self.assertFalse(status['fullRepositoryScanPerformed'])
        self.assertEqual(status['counts']['agentsToStart'], 1)
        self.assertEqual(status['agentsToStart'][0]['humanInstruction'], 'GO')
        self.assertEqual(status['nextHumanAction'], 'Send GO in each listed bound agent chat.')
        self.assertFalse(status['allExpectedResponsesReceived'])

    def test_compact_status_rejects_full_repository_scan(self):
        agent, job = self.compact_inputs()
        with self.assertRaisesRegex(MasterOrchestrationError, 'FULL_REPOSITORY_SCAN_FOR_ROUTINE_STATUS_FORBIDDEN'):
            build_compact_project_status(project_id='project-001', project_slug='example', revision=1, roadmap_ref=self.pointer('planning/roadmap.json'), agent_status_index_ref=self.pointer('master/status/agents.json'), agent_status_entries=[agent], job_status_entries=[job], review_status_entries=[], blocker_status_entries=[], source_refs=[self.pointer('agents/index.json')], observed_at='2026-10-17T21:00:00Z', stale_after=None, full_repository_scan_performed=True)

    def test_status_reports_response_completion_separately_from_acceptance(self):
        agent, job = self.compact_inputs()
        job['lifecycleStatus'] = 'RESPONSE_SUBMITTED'
        status = build_compact_project_status(project_id='project-001', project_slug='example', revision=2, roadmap_ref=self.pointer('planning/roadmap.json'), agent_status_index_ref=self.pointer('master/status/agents.json'), agent_status_entries=[dict(agent, startableJob=None)], job_status_entries=[job], review_status_entries=[{'reviewId': 'review-001', 'label': 'Independent review', 'status': 'PENDING', 'reviewRef': self.pointer('reviews/review-001.json')}], blocker_status_entries=[], response_status_entries=[{'jobId': 'job-001', 'readbackStatus': 'VERIFIED_READBACK', 'schemaValid': True, 'jobBindingValid': True, 'responseRef': self.pointer('agents/agent-a/outbox/job-001/response.json')}], source_refs=[self.pointer('master/status/jobs.json')], observed_at='2026-10-17T21:05:00Z', stale_after='2026-10-17T22:00:00Z', provider_readback_verified=True)
        self.assertEqual(status['counts']['submittedJobs'], 1)
        self.assertEqual(status['counts']['acceptedJobs'], 0)
        self.assertEqual(status['counts']['openReviews'], 1)
        self.assertTrue(status['allExpectedResponsesReceived'])

    def test_stale_status_is_explicit(self):
        agent, job = self.compact_inputs()
        status = build_compact_project_status(project_id='project-001', project_slug='example', revision=3, roadmap_ref=self.pointer('planning/roadmap.json'), agent_status_index_ref=self.pointer('master/status/agents.json'), agent_status_entries=[agent], job_status_entries=[job], review_status_entries=[], blocker_status_entries=[], source_refs=[self.pointer('master/status/jobs.json')], observed_at='2026-10-17T21:10:00Z', stale_after='2026-10-17T21:09:00Z', stale_reason='Provider readback older than current branch head.')
        self.assertEqual(status['freshness']['status'], 'STALE')
        self.assertIn('Provider', status['freshness']['staleReason'])
if __name__ == '__main__':
    unittest.main()
