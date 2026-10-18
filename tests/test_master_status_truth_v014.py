import unittest
from runtime.master_orchestration import build_compact_project_status


class MasterStatusTruthV014Tests(unittest.TestCase):
    def pointer(self, path):
        return {"repository": "example/safor-memory", "ref": "commit123", "path": path, "blobSha": "blob1234"}

    def status(self, job, responses=(), **kwargs):
        defaults = dict(project_id="project-001", project_slug="example", revision=1, roadmap_ref=self.pointer("planning/roadmap.json"), agent_status_index_ref=self.pointer("master/status/agents.json"), agent_status_entries=[], job_status_entries=[job], review_status_entries=[], blocker_status_entries=[], response_status_entries=list(responses), source_refs=[self.pointer("master/status/jobs.json")], observed_at="2026-10-18T10:00:00Z", stale_after="2026-10-18T11:00:00Z", provider_readback_verified=True)
        defaults.update(kwargs)
        return build_compact_project_status(**defaults)

    def test_canceled_or_superseded_without_decision_and_response_is_not_complete(self):
        for lifecycle in ("CANCELED", "SUPERSEDED", "REJECTED"):
            job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": lifecycle, "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": True}
            with self.subTest(lifecycle=lifecycle):
                result = self.status(job)
                self.assertFalse(result["allExpectedResponsesReceived"])
                self.assertEqual(["job-001"], result["missingResponseJobIds"])

    def test_explicit_decision_can_waive_response_expectation(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "CANCELED", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": True, "responseExpectation": {"status": "WAIVED_BY_DECISION", "decisionRef": self.pointer("decisions/cancel-job-001.json")}}
        result = self.status(job)
        self.assertTrue(result["allExpectedResponsesReceived"])
        self.assertEqual(["job-001"], result["waivedResponseJobIds"])

    def test_verified_response_readback_is_required(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "RESPONSE_SUBMITTED", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": True}
        invalid = {"jobId": "job-001", "readbackStatus": "VERIFIED_READBACK", "schemaValid": False, "jobBindingValid": True, "responseRef": self.pointer("agents/a/outbox/job-001/r.json")}
        self.assertFalse(self.status(job, [invalid])["allExpectedResponsesReceived"])
        valid = dict(invalid, schemaValid=True)
        self.assertTrue(self.status(job, [valid])["allExpectedResponsesReceived"])

    def test_stale_after_is_evaluated_without_manual_reason(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "WAITING_HUMAN_GO", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": False}
        result = self.status(job, observed_at="2026-10-18T12:00:00Z", stale_after="2026-10-18T11:00:00Z")
        self.assertEqual("STALE", result["freshness"]["status"])
        self.assertIn("staleAfter exceeded", result["freshness"]["staleReasons"])

    def test_unverified_readback_is_unknown_not_current(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "WAITING_HUMAN_GO", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": False}
        result = self.status(job, provider_readback_verified=None)
        self.assertEqual("UNKNOWN", result["freshness"]["status"])


if __name__ == "__main__":
    unittest.main()
