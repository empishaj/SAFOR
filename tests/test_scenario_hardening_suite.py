import json
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "scenario-hardening"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ScenarioHardeningSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(SUITE / "manifest.json")
        cls.status = load(SUITE / "status" / "status-index.json")
        cls.log = load(SUITE / "status" / "status-log.json")
        cls.protocol = load(SUITE / "status" / "status-protocol.json")
        cls.scenario_paths = sorted((SUITE / "scenarios").glob("SC-*.json"))
        cls.scenarios = {load(path)["scenarioId"]: load(path) for path in cls.scenario_paths}

    def test_exactly_200_unique_immutable_scenarios_exist(self):
        expected_ids = {f"SC-{number:03d}" for number in range(1, 201)}
        self.assertEqual(200, len(self.scenario_paths))
        self.assertEqual(expected_ids, set(self.scenarios))
        for scenario_id, scenario in self.scenarios.items():
            with self.subTest(scenario=scenario_id):
                self.assertEqual("SAFOR_SCENARIO_TEST", scenario["format"])
                self.assertEqual("SAFOR-HARDENING-200", scenario["suiteId"])
                self.assertTrue(scenario["immutableDefinition"])
                self.assertIn(scenario["priority"], {"P0", "P1", "P2"})
                self.assertTrue(scenario["expectedInvariants"])
                self.assertTrue(scenario["forbiddenOutcomes"])

    def test_manifest_counts_and_categories_match_files(self):
        self.assertEqual(200, self.manifest["scenarioCount"])
        self.assertEqual(20, self.manifest["categoryCount"])
        self.assertEqual(200, sum(item["count"] for item in self.manifest["categories"]))
        self.assertEqual(200, sum(self.manifest["priorityCounts"].values()))
        actual_priorities = Counter(item["priority"] for item in self.scenarios.values())
        self.assertEqual(self.manifest["priorityCounts"], dict(actual_priorities))

    def resolved_statuses(self):
        default = self.status["defaultRecord"]
        overrides = self.status["overrides"]
        return {
            scenario_id: overrides.get(scenario_id, default)
            for scenario_id in self.scenarios
        }

    def test_compact_status_index_resolves_all_200_scenarios(self):
        self.assertEqual("1.1", self.status["schemaVersion"])
        self.assertEqual("DEFAULT_PLUS_OVERRIDES", self.manifest["statusIndexModel"])
        self.assertEqual(200, self.status["scenarioUniverse"]["scenarioCount"])
        self.assertTrue(set(self.status["overrides"]).issubset(self.scenarios))

        resolved = self.resolved_statuses()
        self.assertEqual(200, len(resolved))
        allowed = set(self.status["allowedStatuses"])
        for scenario_id, record in resolved.items():
            with self.subTest(scenario=scenario_id):
                self.assertIn(record["status"], allowed)
                self.assertGreaterEqual(record["attempts"], 0)
                if record["status"] == "PASS":
                    self.assertTrue(record["latestEvidenceRefs"])
                    self.assertTrue(record["latestVerdictReason"])

    def test_status_summary_equals_resolved_counts(self):
        counts = Counter(record["status"] for record in self.resolved_statuses().values())
        expected = {status: counts.get(status, 0) for status in self.status["allowedStatuses"]}
        expected["total"] = 200
        self.assertEqual(expected, self.status["summary"])

    def test_append_only_event_log_is_unique_and_orders_current_status(self):
        self.assertTrue(self.log["appendOnly"])
        events = self.log["events"]
        event_ids = [event["eventId"] for event in events]
        self.assertEqual(len(event_ids), len(set(event_ids)))

        latest_by_scenario = {}
        for event in events:
            datetime.fromisoformat(event["occurredAt"].replace("Z", "+00:00"))
            if event.get("scenarioId"):
                latest_by_scenario[event["scenarioId"]] = event

        resolved = self.resolved_statuses()
        for scenario_id, event in latest_by_scenario.items():
            with self.subTest(scenario=scenario_id):
                self.assertEqual(event["toStatus"], resolved[scenario_id]["status"])
                self.assertEqual(event.get("runId"), resolved[scenario_id]["lastRunId"])

    def test_run_records_are_immutable_attempt_evidence(self):
        run_paths = sorted((SUITE / "runs").glob("SC-*/SC*-RUN-*.json"))
        self.assertGreaterEqual(len(run_paths), 2)
        run_ids = set()
        for path in run_paths:
            run = load(path)
            with self.subTest(run=run["runId"]):
                self.assertEqual("SAFOR_SCENARIO_RUN_RECORD", run["format"])
                self.assertIn(run["scenarioId"], self.scenarios)
                self.assertNotIn(run["runId"], run_ids)
                run_ids.add(run["runId"])
                self.assertTrue(run["preconditionEvidence"])
                self.assertTrue(run["observations"])
                self.assertTrue(run["evidenceRefs"])
                if run.get("status") == "RUNNING":
                    self.assertIsNone(run["finishedAt"])
                    self.assertIsNone(run["verdict"])
                if run.get("status") == "PASS":
                    self.assertIsNotNone(run["finishedAt"])
                    self.assertEqual("PASS", run["verdict"])
                    self.assertTrue(run["verdictReason"])

    def test_sc091_retest_preserves_prior_failure_and_passes_with_master_acceptance(self):
        record = self.status["overrides"]["SC-091"]
        self.assertEqual("PASS", record["status"])
        self.assertEqual(2, record["attempts"])
        self.assertEqual("SC091-RUN-002", record["lastRunId"])
        self.assertEqual("FAIL", record["previousTerminalStatus"])
        self.assertEqual("SC091-RUN-001", record["previousTerminalRunId"])
        self.assertTrue(record["latestEvidenceRefs"])

        prior = load(SUITE / "runs" / "SC-091" / "SC091-RUN-001.json")
        self.assertEqual("FAIL", prior["verdict"])
        self.assertTrue(prior["retestRequired"])

        run = load(SUITE / "runs" / "SC-091" / "SC091-RUN-002.json")
        self.assertEqual("PASS", run["status"])
        self.assertEqual("PASS", run["verdict"])
        self.assertEqual("MASTER_ACCEPTED_OR10_GATE_PASS", run["phase"])
        self.assertIsNone(run["nextAuthorizedAction"])
        self.assertIn("OR-10", run["verdictReason"])
        self.assertFalse(run["retestRequired"])


if __name__ == "__main__":
    unittest.main()
