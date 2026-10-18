import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UserOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.start_here = (ROOT / "START-HIER.md").read_text(encoding="utf-8")
        self.quickstart = (ROOT / "QUICKSTART.md").read_text(encoding="utf-8")
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_all_end_user_entry_artifacts_exist(self):
        for path in (
            "SAFOR-FRAMEWORK-WEBSITE.json",
            "SAFOR-FRAMEWORK-SAAS.json",
            "SAFOR-TEST-ACCESS-SAAS.json",
            "SAFOR-FRAMEWORK-BOOK-CREATION.json",
            "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file(), path)

    def test_german_guide_states_exact_upload_sets(self):
        self.assertIn("SAFOR-FRAMEWORK-WEBSITE.json` | 1", self.start_here)
        self.assertIn(
            "SAFOR-FRAMEWORK-SAAS.json` **und** `SAFOR-TEST-ACCESS-SAAS.json` | 2",
            self.start_here,
        )
        self.assertIn(
            "SAFOR-FRAMEWORK-BOOK-CREATION.json` **und** `SAFOR-TEST-ACCESS-BOOK-CREATION.json` | 2",
            self.start_here,
        )
        self.assertIn("frage mich nicht erneut", self.start_here)
        self.assertIn("productionAuthorization = false", self.start_here)

    def test_german_guide_explains_declarative_chat_and_optional_reference_runtime(self):
        self.assertIn("führt den Python-Referenzcode", self.start_here)
        self.assertIn("nicht automatisch", self.start_here)
        self.assertIn("nicht erforderlich", self.start_here)
        self.assertIn("optionale Referenz-", self.start_here)
        self.assertNotIn("Host-/Runtime-Integration Pflicht", self.start_here)

    def test_quickstart_separates_end_user_and_generic_engineering_routes(self):
        self.assertIn("## Recommended end-user start", self.quickstart)
        self.assertIn("## Generic engineering start — advanced", self.quickstart)
        self.assertIn("Do not load the generic `SAFOR-FRAMEWORK.json`", self.quickstart)
        self.assertIn("does **not** ask the HUMAN", self.quickstart)

    def test_readme_uses_current_rc_and_has_no_stale_path_typo(self):
        self.assertIn("v0.14.0-rc.2", self.readme)
        self.assertNotIn("Paid package access in rc.4", self.readme)
        self.assertNotIn("v0.13.0/ packages/", self.readme)
        self.assertIn("runtime/public_evaluation_access.py", self.readme)

    def test_readme_does_not_overstate_generic_chat_execution(self):
        self.assertIn("deterministic reference implementation", self.readme)
        self.assertIn("does not automatically execute this Python module", self.readme)
        self.assertIn("Optional host integration can provide stronger machine enforcement", self.readme)
        self.assertIn("does not require a separately installed customer runtime", self.readme)
        self.assertNotIn("Production use therefore requires an integrated SAFOR host/runtime boundary", self.readme)


if __name__ == "__main__":
    unittest.main()
