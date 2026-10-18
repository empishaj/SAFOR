import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UserOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
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
        self.assertIn("SAFOR-FRAMEWORK-WEBSITE.json", self.start_here)
        self.assertIn("SAFOR-FRAMEWORK-SAAS.json", self.start_here)
        self.assertIn("SAFOR-TEST-ACCESS-SAAS.json", self.start_here)
        self.assertIn("SAFOR-FRAMEWORK-BOOK-CREATION.json", self.start_here)
        self.assertIn("SAFOR-TEST-ACCESS-BOOK-CREATION.json", self.start_here)
        self.assertIn("frage mich nicht noch einmal", self.start_here)
        self.assertIn("Die Testdateien sind keine Produktionslizenz", self.start_here)

    def test_german_guide_is_usage_only_and_keeps_technical_detail_elsewhere(self):
        self.assertIn("Du musst keine JSON-Datei öffnen oder verstehen", self.start_here)
        self.assertIn("Der **MASTER** ist dein Hauptchat", self.start_here)
        self.assertIn("Du musst den Job nicht zwischen Chats kopieren", self.start_here)
        self.assertNotIn("Python-Referenzcode", self.start_here)
        self.assertNotIn("providerReadback", self.start_here)
        self.assertIn("reference implementation", self.readme)
        self.assertIn("does not automatically execute this Python module", self.readme)

    def test_quickstart_separates_end_user_and_generic_engineering_routes(self):
        self.assertIn("## Recommended end-user start", self.quickstart)
        self.assertIn("## Generic engineering start — advanced", self.quickstart)
        self.assertIn("Do not load the generic `SAFOR-FRAMEWORK.json`", self.quickstart)
        self.assertIn("does **not** ask the HUMAN", self.quickstart)

    def test_readme_uses_current_rc_and_has_no_stale_path_typo(self):
        self.assertIn(f"v{self.version}", self.readme)
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
