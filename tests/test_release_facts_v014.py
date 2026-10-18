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
        self.assertEqual("0.14.0-rc.4", version)
        self.assertEqual(version, facts["targetVersion"])
        self.assertEqual(version, manifest["version"])
        self.assertEqual(version, trace["releaseTarget"])

    def test_release_artifacts_are_explicitly_pending_wp_a7(self):
        facts = self.load("RELEASE-FACTS.json")
        manifest = self.load("RELEASE-MANIFEST.json")
        self.assertEqual("PENDING_WP_A7", facts["releaseArtifacts"]["state"])
        self.assertEqual("PENDING_WP_A7_MATERIALIZATION", manifest["releaseArtifactsState"])

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
        self.assertEqual("0.14.0-rc.4", migration["candidateMigration"]["targetVersion"])
        self.assertIn(
            "V014_ISOLATED_REAL_GIT_END_TO_END_ACCEPTANCE",
            migration["candidateMigration"]["prerequisites"],
        )

    def test_rc4_traceability_does_not_claim_unmaterialized_bundle_pass(self):
        trace = self.load("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
        for item in trace["requirements"]:
            with self.subTest(requirement=item["id"]):
                self.assertEqual("PENDING", item["coverage"]["automatedTest"])
                self.assertEqual("PENDING", item["coverage"]["bundle"])
                self.assertEqual("NOT_VERIFIED", item["coverage"]["realGitE2E"])
                self.assertEqual("NOT_VERIFIED", item["coverage"]["crossHost"])


if __name__ == "__main__":
    unittest.main()
