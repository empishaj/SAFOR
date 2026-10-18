import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseFactsV014Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_version_manifest_traceability_align(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        facts = self.load("RELEASE-FACTS.json")
        manifest = self.load("RELEASE-MANIFEST.json")
        trace = self.load("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
        self.assertEqual("0.14.0-rc.5", version)
        self.assertEqual(version, facts["targetVersion"])
        self.assertEqual(version, manifest["version"])
        self.assertEqual(version, trace["releaseTarget"])

    def test_release_artifact_state_is_consistent(self):
        facts = self.load("RELEASE-FACTS.json")
        manifest = self.load("RELEASE-MANIFEST.json")
        state = facts["releaseArtifacts"]["state"]
        self.assertIn(
            state,
            {"PENDING_MATERIALIZATION", "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"},
        )
        if state == "PENDING_MATERIALIZATION":
            self.assertEqual("PENDING_RELEASE_MATERIALIZATION", manifest["releaseArtifactsState"])
        else:
            self.assertEqual("MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS", manifest["releaseArtifactsState"])

    def test_website_defaults_match_canonical_profile(self):
        facts = self.load("RELEASE-FACTS.json")
        manifest = self.load("RELEASE-MANIFEST.json")
        profiles = self.load("v0.14.0/domain-framework-profiles.json")
        website = next(item for item in profiles["profiles"] if item["id"] == "WEBSITE")
        self.assertEqual(website["defaultFactory"]["version"], facts["domainDefaults"]["WEBSITE"]["factoryVersion"])
        self.assertEqual(website["defaultOperatingModel"]["version"], facts["domainDefaults"]["WEBSITE"]["operatingModelVersion"])
        self.assertEqual("1.2.0", manifest["freeStarterProfile"]["defaultFactoryVersion"])
        self.assertEqual("1.2.0", manifest["freeStarterProfile"]["defaultOperatingModelVersion"])

    def test_candidate_migration_is_not_confused_with_historical_migration(self):
        migration = self.load("RELEASE-FACTS.json")["referenceProjectMigration"]
        self.assertEqual("COMPLETED", migration["historicalBaselineMigration"]["status"])
        self.assertEqual("NOT_STARTED", migration["candidateMigration"]["status"])
        self.assertEqual(version := (ROOT / "VERSION").read_text(encoding="utf-8").strip(), migration["candidateMigration"]["targetVersion"])
        self.assertIn(
            "V014_ISOLATED_REAL_GIT_END_TO_END_ACCEPTANCE",
            migration["candidateMigration"]["prerequisites"],
        )

    def test_current_traceability_matches_materialization_state(self):
        facts = self.load("RELEASE-FACTS.json")
        trace = self.load("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
        expected = (
            "PASS"
            if facts["releaseArtifacts"]["state"] == "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
            else "PENDING"
        )
        real_git_pass = 0
        for item in trace["requirements"]:
            with self.subTest(requirement=item["id"]):
                self.assertEqual(expected, item["coverage"]["automatedTest"])
                self.assertEqual(expected, item["coverage"]["bundle"])
                self.assertIn(item["coverage"]["realGitE2E"], {"PASS", "NOT_VERIFIED"})
                if item["coverage"]["realGitE2E"] == "PASS":
                    real_git_pass += 1
                    refs = item.get("realGitE2EEvidence") or []
                    self.assertTrue(refs)
                    for ref in refs:
                        self.assertTrue((ROOT / ref.split("#", 1)[0]).exists())
                self.assertEqual("NOT_VERIFIED", item["coverage"]["crossHost"])
        self.assertEqual(real_git_pass, trace["summary"]["realGitE2EVerified"])
        if real_git_pass < len(trace["requirements"]):
            self.assertEqual("NOT_VERIFIED", facts["traceability"]["realGitE2E"])

    def test_live_provider_audit_evidence_closes_only_f09_f10(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        findings = manifest["auditResolution"]["findings"]
        self.assertTrue(findings["F-09"].startswith("RESOLVED_BY_ISOLATED_LIVE_GITHUB"))
        self.assertTrue(findings["F-10"].startswith("RESOLVED_BY_ISOLATED_LIVE_GITHUB"))
        self.assertEqual("OPEN_REAL_GIT_E2E_REQUIRED", findings["F-02"])
        evidence = ROOT / manifest["auditResolution"]["liveProviderEvidenceRef"]
        self.assertTrue(evidence.exists())


if __name__ == "__main__":
    unittest.main()
