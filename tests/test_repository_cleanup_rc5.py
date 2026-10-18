import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryCleanupRc5Tests(unittest.TestCase):
    def setUp(self):
        self.version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.facts = json.loads((ROOT / "RELEASE-FACTS.json").read_text(encoding="utf-8"))

    def test_root_contains_only_current_release_candidate_artifacts(self):
        expected = {
            f"RELEASE-EVIDENCE-{self.version}.json",
            f"RELEASE-NOTES-{self.version}.md",
            f"SHA256SUMS-{self.version}.txt",
        }
        actual = {
            p.name
            for pattern in ("RELEASE-EVIDENCE-*.json", "RELEASE-NOTES-*.md", "SHA256SUMS-*.txt")
            for p in ROOT.glob(pattern)
        }
        self.assertEqual(expected, actual)

    def test_historical_release_candidates_are_archived(self):
        archive = ROOT / "docs" / "releases" / "archive"
        self.assertTrue((archive / "README.md").is_file())
        for version in ("0.13.0-rc.9", "0.14.0-rc.2", "0.14.0-rc.3", "0.14.0-rc.4"):
            with self.subTest(version=version):
                folder = archive / version
                self.assertTrue((folder / f"RELEASE-EVIDENCE-{version}.json").is_file())
                self.assertTrue((folder / f"RELEASE-NOTES-{version}.md").is_file())
                self.assertTrue((folder / f"SHA256SUMS-{version}.txt").is_file())

    def test_one_time_release_workflows_are_not_on_mainline_tree(self):
        workflows = ROOT / ".github" / "workflows"
        for name in ("materialize-rc4.yml", "materialize-rc5.yml", "rc4-step-validation.yml"):
            with self.subTest(name=name):
                self.assertFalse((workflows / name).exists())
        self.assertTrue((workflows / "validate.yml").is_file())
        self.assertTrue((workflows / "rc5-inbox-pull-validation.yml").is_file())

    def test_active_start_docs_match_current_release_facts(self):
        docs = {
            name: (ROOT / name).read_text(encoding="utf-8")
            for name in ("README.md", "START-HIER.md", "QUICKSTART.md")
        }
        for name, text in docs.items():
            with self.subTest(document=name):
                self.assertIn(self.version, text)

        defaults = self.facts["domainDefaults"]
        expected_versions = {
            defaults["WEBSITE"]["factoryVersion"],
            defaults["WEBSITE"]["operatingModelVersion"],
            defaults["SAAS"]["factoryVersion"],
            defaults["SAAS"]["operatingModelVersion"],
            defaults["BOOK_CREATION"]["factoryVersion"],
            defaults["BOOK_CREATION"]["operatingModelVersion"],
        }
        combined = "\n".join(docs.values())
        for version in expected_versions:
            self.assertIn(version, combined)

    def test_start_here_negative_access_case_uses_book_bundle_for_saas(self):
        text = (ROOT / "START-HIER.md").read_text(encoding="utf-8")
        section = text.split("### Test C – falscher Testzugang", 1)[1].split("### Test D", 1)[0]
        self.assertIn("SAFOR-FRAMEWORK-SAAS.json", section)
        self.assertIn("SAFOR-TEST-ACCESS-BOOK-CREATION.json", section)
        self.assertNotIn("SAFOR-TEST-ACCESS-SAAS.json", section)

    def test_release_checklist_is_version_agnostic(self):
        text = (ROOT / "RELEASE-CHECKLIST.md").read_text(encoding="utf-8")
        self.assertIn("VERSION", text)
        self.assertIn("RELEASE-FACTS.json", text)
        self.assertNotIn("0.14.0-rc.3", text)
        self.assertNotIn("0.14.0-rc.4", text)


if __name__ == "__main__":
    unittest.main()
