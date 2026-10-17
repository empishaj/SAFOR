import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UserOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.start_here = (ROOT / "START-HIER.md").read_text(encoding="utf-8")
        self.quickstart = (ROOT / "QUICKSTART.md").read_text(encoding="utf-8")
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.support = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")

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

    def test_chat_use_requires_no_additional_end_user_runtime_installation(self):
        required = (
            "keine zusätzliche SAFOR-Runtime",
            "normaler Chat führt diese Module nicht automatisch aus",
            "optionale Referenzimplementierungen",
        )
        combined = "\n".join((self.start_here, self.readme, self.support))
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_reference_runtime_and_machine_enforcement_are_distinguished(self):
        self.assertIn("runtime/public_evaluation_access.py", self.readme)
        self.assertIn("optional deterministic reference implementation", self.readme)
        self.assertIn("model-level contract following", self.readme)
        self.assertIn("machine-enforced controls", self.readme)
        self.assertIn("JSON never grants credentials", self.quickstart)

    def test_agent_activation_is_exact_human_go(self):
        for document in (self.start_here, self.quickstart, self.readme, self.support):
            with self.subTest(document=document[:30]):
                self.assertIn("GO", document)
        self.assertIn("Git-Push", self.start_here)
        self.assertIn("startet ihn nicht", self.start_here)
        self.assertIn("WAITING_HUMAN_GO", self.readme)
        self.assertIn("not activated by a Git push", self.quickstart)

    def test_master_is_only_domain_and_organizational_human_interface(self):
        self.assertIn("einzige fachliche und organisatorische Schnittstelle", self.start_here)
        self.assertIn("only fachliche and organizational HUMAN interface", self.readme)
        self.assertIn("only fachliche and organizational HUMAN interface", self.support)

    def test_quickstart_separates_end_user_and_generic_engineering_routes(self):
        self.assertIn("## Recommended end-user start", self.quickstart)
        self.assertIn("## Generic engineering start — advanced", self.quickstart)
        self.assertIn("Do not load the generic `SAFOR-FRAMEWORK.json`", self.quickstart)
        self.assertIn("does **not** ask the HUMAN", self.quickstart)

    def test_readme_links_orchestration_and_preserves_evaluation_boundary(self):
        self.assertIn("MASTER-SUBAGENT-ORCHESTRATION.md", self.readme)
        self.assertIn("productionAuthorization = false", self.readme)
        self.assertIn("provider rights", self.readme.casefold())
        self.assertIn("Release Candidate", self.readme)

    def test_forbidden_runtime_requirement_phrases_are_absent(self):
        combined = "\n".join((self.start_here, self.quickstart, self.readme, self.support))
        forbidden = (
            "Host-/Runtime-Integration Pflicht",
            "Production use therefore requires an integrated SAFOR host/runtime boundary",
            "requires an external activation trigger: HUMAN, automation or a host-supported agent trigger",
            "The activation instruction can be minimal: **check workspace**",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
