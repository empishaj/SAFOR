import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.14.0-rc.3"


class V014BundleIntegrationTests(unittest.TestCase):
    def load(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_version_schema_and_alias(self):
        self.assertEqual(VERSION, (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        alias = (ROOT / "SAFOR-FRAMEWORK.json").read_bytes()
        versioned = (ROOT / f"SAFOR-FRAMEWORK-v{VERSION}.json").read_bytes()
        self.assertEqual(alias, versioned)
        framework = json.loads(alias)
        self.assertEqual("0.14.0", framework["schemaVersion"])
        self.assertEqual(VERSION, framework["bundleVersion"])

    def test_every_module_comes_from_v014_and_has_recovery_profile(self):
        framework = self.load("SAFOR-FRAMEWORK.json")
        modules = framework["embeddedModules"]
        profiles = {item["moduleKey"] for item in modules["moduleSelfHealing"]["content"]["moduleProfiles"]}
        self.assertEqual(set(modules), profiles)
        for key, module in modules.items():
            with self.subTest(module=key):
                self.assertTrue(module["sourcePath"].startswith("v0.14.0/"))
                self.assertTrue(module["selfHealingProfileId"].startswith("MRP-"))

    def test_all_domain_distributions_embed_v014_framework_and_upgraded_packages(self):
        expectations = {
            "SAFOR-FRAMEWORK-WEBSITE.json": ("1.2.0", "1.2.0"),
            "SAFOR-FRAMEWORK-SAAS.json": ("1.8.0-test.1", "1.8.0-test.1"),
            "SAFOR-FRAMEWORK-BOOK-CREATION.json": ("1.1.0-test.1", "1.1.0-test.1"),
        }
        for relative, versions in expectations.items():
            with self.subTest(relative=relative):
                distribution = self.load(relative)
                self.assertEqual("0.14.0", distribution["schemaVersion"])
                self.assertEqual(VERSION, distribution["distributionVersion"])
                self.assertEqual("0.14.0", distribution["framework"]["schemaVersion"])
                self.assertEqual(versions[0], distribution["embeddedDomainModules"]["factory"]["version"])
                self.assertEqual(versions[1], distribution["embeddedDomainModules"]["operatingModel"]["version"])

    def test_security_modules_are_embedded(self):
        modules = self.load("SAFOR-FRAMEWORK.json")["embeddedModules"]
        for key in ("agentActivation", "schemaHumanGoEvidence", "executionAttempt", "schemaExecutionAttempt", "schemaReconciliationRecord", "masterStatus", "schemaRequirementsTraceability"):
            self.assertIn(key, modules)


if __name__ == "__main__":
    unittest.main()
