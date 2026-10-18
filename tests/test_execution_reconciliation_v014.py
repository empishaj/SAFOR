import unittest
from runtime.execution_reconciliation import ExecutionReconciliationError, create_execution_attempt, record_product_commit, record_response_persistence, reconcile_partial_attempt


class ExecutionReconciliationV014Tests(unittest.TestCase):
    def ref(self, path, sha="blob1234"):
        return {"repository": "example/repo", "ref": "commit123", "path": path, "blobSha": sha}

    def attempt(self):
        return create_execution_attempt(attempt_id="attempt-001", project_id="project-001", job_id="job-001", agent_id="agent-a", dispatch_revision=1, started_at="2026-10-18T08:00:00Z", product_target=self.ref("src/"), response_target=self.ref("outbox/job-001/"))

    def test_product_commit_then_response_failure_requires_response_only_reconcile(self):
        commit = self.ref("commit", "commitsha")
        recorded = record_product_commit(self.attempt(), commit_ref=commit, observed_at="2026-10-18T08:01:00Z")
        result = reconcile_partial_attempt(recorded, product_commit_readback=commit, response_readback=None, observed_at="2026-10-18T08:02:00Z")
        self.assertEqual("RESPONSE_PERSISTENCE_RECONCILE_REQUIRED", result["outcome"])
        self.assertFalse(result["retryProductMutationAllowed"])
        self.assertTrue(result["retryResponsePersistenceAllowed"])

    def test_read_before_retry_prevents_duplicate_product_mutation(self):
        commit = self.ref("commit", "commitsha")
        recorded = record_product_commit(self.attempt(), commit_ref=commit, observed_at="2026-10-18T08:01:00Z")
        same = record_product_commit(recorded, commit_ref=commit, observed_at="2026-10-18T08:03:00Z")
        self.assertEqual(recorded, same)
        with self.assertRaisesRegex(ExecutionReconciliationError, "PRODUCT_MUTATION_ALREADY_RECORDED_DIFFERENTLY"):
            record_product_commit(recorded, commit_ref=self.ref("commit", "different"), observed_at="2026-10-18T08:03:00Z")

    def test_response_cannot_be_recorded_before_product_commit(self):
        with self.assertRaisesRegex(ExecutionReconciliationError, "RESPONSE_CANNOT_PRECEDE_PRODUCT_COMMIT"):
            record_response_persistence(self.attempt(), response_ref=self.ref("response"), observed_at="2026-10-18T08:01:00Z")

    def test_complete_attempt_is_idempotent(self):
        commit = self.ref("commit", "commitsha")
        response = self.ref("response", "responsesha")
        attempt = record_product_commit(self.attempt(), commit_ref=commit, observed_at="2026-10-18T08:01:00Z")
        attempt = record_response_persistence(attempt, response_ref=response, observed_at="2026-10-18T08:02:00Z")
        result = reconcile_partial_attempt(attempt, product_commit_readback=commit, response_readback=response, observed_at="2026-10-18T08:03:00Z")
        self.assertEqual("COMPLETED", result["outcome"])
        self.assertFalse(result["retryProductMutationAllowed"])


if __name__ == "__main__":
    unittest.main()
