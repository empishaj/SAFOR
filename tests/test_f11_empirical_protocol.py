import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class F11EmpiricalProtocolTests(unittest.TestCase):
    def setUp(self):
        self.protocol = (ROOT / "docs/master-subagent-orchestration/F11-EMPIRICAL-USABILITY-PROTOCOL.md").read_text(encoding="utf-8")
        self.template = json.loads((ROOT / "docs/master-subagent-orchestration/evidence/F11-EMPIRICAL-RUN.template.json").read_text(encoding="utf-8"))
        self.manifest = json.loads((ROOT / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))

    def test_protocol_does_not_claim_automated_evidence_as_empirical(self):
        self.assertIn("Empirical acceptance remains OPEN", self.protocol)
        self.assertIn("Automated tests may verify the protocol", self.protocol)
        self.assertIn("may not substitute for HUMAN empirical evidence", self.protocol)

    def test_internal_load_heuristic_is_not_recast_as_psychometric(self):
        self.assertIn("not validated psychometric", self.protocol)
        self.assertFalse(self.template["subjectiveFeedback"]["ratingsAreValidatedPsychometrics"])
        self.assertFalse(self.template["behavioralMetrics"]["internalHeuristicPresentedAsScientificMeasure"])

    def test_run_template_enforces_privacy_and_immutability_defaults(self):
        self.assertTrue(self.template["privacy"]["participantPseudonymized"])
        self.assertFalse(self.template["privacy"]["directPersonalIdentifiersStored"])
        self.assertTrue(self.template["immutable"])

    def test_hard_behavioral_metrics_cover_existing_policy(self):
        metrics = self.template["behavioralMetrics"]
        required = {
            "maxNewDecisionContextsPerTurn",
            "repeatedUnchangedApprovalCount",
            "safelyDerivableQuestionViolationCount",
            "internalOrchestrationQuestionCountAfterPlan",
            "rawInternalIdentifierExposureViolationCount",
            "executionUnnecessaryHumanQuestionCount",
            "returnedToPhaseTargetAfterEscalation",
            "inferredHumanApprovalViolationCount",
        }
        self.assertTrue(required.issubset(metrics))

    def test_f11_and_cognitive_load_ga_blocker_remain_open(self):
        self.assertEqual(
            "OPEN_EMPIRICAL_USABILITY_EVIDENCE",
            self.manifest["auditResolution"]["findings"]["F-11"],
        )
        self.assertIn(
            "V014_COGNITIVE_LOAD_EMPIRICAL_ACCEPTANCE",
            self.manifest["gaBlockers"],
        )


if __name__ == "__main__":
    unittest.main()
