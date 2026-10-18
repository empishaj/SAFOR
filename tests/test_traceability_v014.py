import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TraceabilityV014Tests(unittest.TestCase):
    def setUp(self):
        self.trace = json.loads((ROOT / "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json").read_text(encoding="utf-8"))

    def test_all_33_requirements_have_separate_evidence_dimensions(self):
        requirements = self.trace["requirements"]
        self.assertEqual([f"REQ-{number:03d}" for number in range(1, 34)], [item["id"] for item in requirements])
        for item in requirements:
            with self.subTest(requirement=item["id"]):
                self.assertTrue(item["designEvidence"])
                self.assertTrue(item["implementationEvidence"])
                self.assertTrue(item["automatedTests"])
                self.assertTrue(item["bundleModuleKeys"])
                self.assertEqual("NOT_VERIFIED", item["coverage"]["realGitE2E"])
                self.assertEqual("NOT_VERIFIED", item["coverage"]["crossHost"])

    def test_referenced_design_code_and_test_files_exist(self):
        for item in self.trace["requirements"]:
            for field in ("designEvidence", "implementationEvidence", "automatedTests"):
                for ref in item[field]:
                    with self.subTest(requirement=item["id"], ref=ref):
                        self.assertTrue((ROOT / ref).exists())

    def test_no_false_100_percent_e2e_claim(self):
        summary = self.trace["summary"]
        self.assertTrue(summary["percentageClaimForbidden"])
        self.assertEqual(0, summary["realGitE2EVerified"])
        self.assertEqual(0, summary["crossHostVerified"])


if __name__ == "__main__":
    unittest.main()
