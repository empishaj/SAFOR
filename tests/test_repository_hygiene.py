import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryHygieneTests(unittest.TestCase):
    def test_root_contains_only_current_framework_distributions(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        expected = {
            "SAFOR-FRAMEWORK.json",
            f"SAFOR-FRAMEWORK-v{version}.json",
            "SAFOR-FRAMEWORK-WEBSITE.json",
            "SAFOR-FRAMEWORK-SAAS.json",
            "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        }
        actual = {path.name for path in ROOT.glob("SAFOR-FRAMEWORK*.json")}
        self.assertEqual(expected, actual)

    def test_legacy_complete_bundles_are_not_kept_on_main(self):
        legacy = sorted(path.name for path in ROOT.glob("SAFOR-MASTER-COMPLETE*.json"))
        self.assertEqual([], legacy)

    def test_only_active_source_baselines_remain(self):
        version_directory = re.compile(r"v\d+\.\d+\.\d+")
        actual = {
            path.name
            for path in ROOT.iterdir()
            if path.is_dir() and version_directory.fullmatch(path.name)
        }
        # v0.14 is the active source tree. v0.10-v0.13 remain explicit
        # compatibility and audit baselines; earlier versions are Git history.
        self.assertEqual(
            {"v0.10.0", "v0.11.0", "v0.12.0", "v0.13.0", "v0.14.0"},
            actual,
        )

    def test_superseded_package_worktrees_are_removed(self):
        obsolete = (
            "v0.13.0/packages/factories/website-delivery/1.0.0",
            "v0.13.0/packages/operating-models/website-team/1.0.0",
            "v0.13.0/packages/factories/software-delivery/1.5.0",
            "v0.13.0/packages/operating-models/saas-engineering/1.5.0",
        )
        for relative_path in obsolete:
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists())

    def test_current_user_entry_artifacts_remain_present(self):
        required = (
            "SAFOR-FRAMEWORK-WEBSITE.json",
            "SAFOR-FRAMEWORK-SAAS.json",
            "SAFOR-TEST-ACCESS-SAAS.json",
            "SAFOR-FRAMEWORK-BOOK-CREATION.json",
            "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
            "START-HIER.md",
        )
        for relative_path in required:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())


if __name__ == "__main__":
    unittest.main()
