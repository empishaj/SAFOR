"""Regression for the v0.14 WEBSITE / SOFTWARE_WEBSITE contract mismatch."""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from runtime.creation_type_contract import validate_creation_type_contract

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class CreationTypeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.framework = load("SAFOR-FRAMEWORK.json")

    def test_each_current_type_is_supported(self):
        for value in ("WEBSITE", "SOFTWARE_SAAS", "BOOK"):
            with self.subTest(value=value):
                self.assertTrue(validate_creation_type_contract(self.framework, value)["valid"])

    def test_legacy_and_unknown_types_fail_closed(self):
        for value in ("SOFTWARE_WEBSITE", "UNKNOWN", "website", ""):
            with self.subTest(value=value):
                self.assertFalse(validate_creation_type_contract(self.framework, value)["valid"])

    def test_original_schema_regression_is_rejected(self):
        fw = copy.deepcopy(self.framework)
        fw["embeddedModules"]["schemaProject"]["content"]["properties"]["creationType"]["enum"] = ["SOFTWARE_WEBSITE", "BOOK"]
        self.assertIn("PROJECT_CREATION_TYPE_CONTRACT_MISMATCH", validate_creation_type_contract(fw)["errors"])

    def test_extra_schema_type_is_not_silently_accepted(self):
        fw = copy.deepcopy(self.framework)
        fw["embeddedModules"]["schemaProject"]["content"]["properties"]["creationType"]["enum"].append("SOFTWARE_WEBSITE")
        self.assertFalse(validate_creation_type_contract(fw)["valid"])

    def test_missing_and_duplicate_declarations_fail_closed(self):
        for values in ([], ["WEBSITE", "WEBSITE"], [None], "WEBSITE"):
            with self.subTest(values=values):
                fw = copy.deepcopy(self.framework)
                fw["embeddedModules"]["schemaProject"]["content"]["properties"]["creationType"]["enum"] = values
                self.assertFalse(validate_creation_type_contract(fw)["valid"])

    def test_catalog_drift_is_rejected(self):
        fw = copy.deepcopy(self.framework)
        fw["embeddedModules"]["packageCatalog"]["content"]["creationProfiles"][0]["creationType"] = "UNKNOWN"
        self.assertFalse(validate_creation_type_contract(fw)["valid"])

    def test_runtime_profile_drift_is_rejected(self):
        fw = copy.deepcopy(self.framework)
        fw["runtimeContract"]["creationProfiles"][0]["id"] = "UNKNOWN"
        self.assertFalse(validate_creation_type_contract(fw)["valid"])

    def test_source_enum_matches_current_profile(self):
        schema = load("v0.14.0/schemas/project.schema.json")
        self.assertEqual(["WEBSITE", "SOFTWARE_SAAS", "BOOK"], schema["properties"]["creationType"]["enum"])

    def test_embedded_schema_matches_source_and_blob(self):
        module = self.framework["embeddedModules"]["schemaProject"]
        raw = (ROOT / module["sourcePath"]).read_bytes()
        sha = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        self.assertEqual(json.loads(raw), module["content"])
        self.assertEqual(sha, module["sourceBlobSha"])
        self.assertEqual(sha, self.framework["integrityManifest"]["schemaProject"]["sourceBlobSha"])

    def test_canonical_menu_has_three_distinct_options(self):
        model = load("v0.14.0/interaction-model.json")
        step = next(s for s in model["initializationExperience"]["steps"] if s["id"] == "CREATION_TYPE")
        self.assertEqual(["SELECT_CREATION_TYPE_WEBSITE", "SELECT_CREATION_TYPE_SOFTWARE_SAAS", "SELECT_CREATION_TYPE_BOOK"], [o["intent"] for o in step["options"]])
        self.assertEqual("CONTAINER_FORMAT == SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION", step["skipWhen"])

    def test_current_normative_sources_do_not_advertise_legacy_type(self):
        for path in ("v0.14.0/SAFOR-MASTER.json", "v0.14.0/interaction-model.json", "v0.14.0/conformance.json"):
            with self.subTest(path=path):
                self.assertNotIn("SOFTWARE_WEBSITE", (ROOT / path).read_text(encoding="utf-8"))

    def test_every_domain_uses_consistent_framework(self):
        for path in ("SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json", "SAFOR-FRAMEWORK-BOOK-CREATION.json"):
            with self.subTest(path=path):
                distribution = load(path)
                self.assertTrue(validate_creation_type_contract(distribution["framework"], distribution["domain"]["creationType"])["valid"])
                self.assertEqual(self.framework, distribution["framework"])


if __name__ == "__main__":
    unittest.main()
