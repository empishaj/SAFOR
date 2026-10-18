import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.13.0-rc.9"


class Rc9ReleaseTests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_version_and_manifest_are_aligned(self):
        self.assertEqual(VERSION, (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        manifest = self.load("RELEASE-MANIFEST.json")
        self.assertEqual(VERSION, manifest["version"])
        self.assertEqual(f"SAFOR-FRAMEWORK-v{VERSION}.json", manifest["distributable"])
        self.assertEqual("0.13.0-rc.8", manifest["previousVersion"])

    def test_reference_project_migration_is_closed_with_evidence(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        migration = manifest["referenceProjectMigration"]
        self.assertEqual("COMPLETED", migration["status"])
        self.assertEqual(9, migration["agentCount"])
        self.assertEqual(5, migration["typedResponseTemplateCount"])
        self.assertNotIn("REFERENCE_PROJECT_RC8_MIGRATION_ACCEPTANCE", manifest["gaBlockers"])

    def test_release_evidence_matches_manifest(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        evidence = self.load(manifest["releaseEvidenceRef"])
        self.assertEqual(VERSION, evidence["version"])
        self.assertEqual("85e08eab15b18a86868090d7b18573b9e2484aea", evidence["referenceProjectMigration"]["mergeCommit"])
        self.assertEqual("bc18643d0c23d60094cd5c350bba68f0607d27a8", evidence["referenceProjectMigration"]["migrationAuditBlobSha"])

    def test_current_generic_alias_equals_versioned_file(self):
        alias = (ROOT / "SAFOR-FRAMEWORK.json").read_bytes()
        versioned = (ROOT / f"SAFOR-FRAMEWORK-v{VERSION}.json").read_bytes()
        self.assertEqual(alias, versioned)
        self.assertFalse((ROOT / "SAFOR-FRAMEWORK-v0.13.0-rc.8.json").exists())

    def test_checksum_file_covers_all_declared_artifacts(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        evidence = self.load(manifest["releaseEvidenceRef"])
        checksums = {
            line.split("  ", 1)[1]: line.split("  ", 1)[0]
            for line in (ROOT / manifest["checksumFile"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        for artifact in evidence["artifacts"]:
            path = artifact["path"]
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            self.assertEqual(actual, artifact["sha256"])
            self.assertEqual(actual, checksums[path])

    def test_saas_onboarding_uses_matching_access_bundle(self):
        text = (ROOT / "START-HIER.md").read_text(encoding="utf-8")
        self.assertIn("`SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-SAAS.json`", text)
        self.assertNotIn("`SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-BOOK-CREATION.json`", text)

    def test_current_docs_use_rc9_and_plan_remains_historical(self):
        for path in ("README.md", "QUICKSTART.md", "PRODUCT-READINESS.md", "SUPPORT.md"):
            with self.subTest(path=path):
                self.assertIn(VERSION, (ROOT / path).read_text(encoding="utf-8"))
        plan = (ROOT / "HUMAN-NOTICE-IMPLEMENTATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("0.13.0-rc.8", plan)


if __name__ == "__main__":
    unittest.main()
