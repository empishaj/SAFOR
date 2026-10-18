"""Regression tests for the 0.14 project-schema/domain-type contradiction."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from runtime.creation_type_contract import validate_creation_type_contract

ROOT = Path(__file__).resolve().parents[1]
TYPES = {"WEBSITE", "SOFTWARE_SAAS", "BOOK"}
DOMAIN_FILES = ("SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json",
                "SAFOR-FRAMEWORK-BOOK-CREATION.json")


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class CreationTypeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.framework = load("SAFOR-FRAMEWORK.json")

    def test_source_project_schema_accepts_all_current_types_only(self):
        schema = load("v0.14.0/schemas/project.schema.json")
        values = schema["properties"]["creationType"]["enum"]
        self.assertEqual(set(values), TYPES)
        self.assertEqual(len(values), len(TYPES))
        for rejected in ("SOFTWARE_WEBSITE", "UNKNOWN", "website", "", None):
            with self.subTest(rejected=rejected):
                self.assertNotIn(rejected, values)

    def test_generic_and_versioned_frameworks_are_consistent(self):
        version = (ROOT / "VERSION").read_text().strip()
        for name in ("SAFOR-FRAMEWORK.json", f"SAFOR-FRAMEWORK-v{version}.json"):
            with self.subTest(file=name):
                decision = validate_creation_type_contract(load(name))
                self.assertTrue(decision["valid"], decision)
                self.assertEqual(set(decision["supportedCreationTypes"]), TYPES)

    def test_every_domain_type_validates_and_matches_both_packages(self):
        for name in DOMAIN_FILES:
            with self.subTest(file=name):
                distribution = load(name)
                kind = distribution["domain"]["creationType"]
                decision = validate_creation_type_contract(distribution["framework"], kind)
                self.assertTrue(decision["valid"], decision)
                for package in distribution["embeddedDomainModules"].values():
                    self.assertIn(kind, package["compatibility"]["supportedCreationTypes"])

    def test_embedded_schemas_equal_the_authoritative_source(self):
        source = load("v0.14.0/schemas/project.schema.json")
        for name in DOMAIN_FILES:
            with self.subTest(file=name):
                embedded = load(name)["framework"]["embeddedModules"]
                self.assertEqual(embedded["schemaProject"]["content"], source)

    def test_all_framework_module_pins_match_actual_source_bytes(self):
        for key, module in self.framework["embeddedModules"].items():
            with self.subTest(module=key):
                raw = (ROOT / module["sourcePath"]).read_bytes()
                digest = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
                self.assertEqual(module["sourceBlobSha"], digest)
                self.assertEqual(self.framework["integrityManifest"][key]
                                 ["sourceBlobSha"], digest)
                self.assertEqual(module["content"], json.loads(raw))

    def test_domain_distribution_digests_are_recomputed(self):
        for name in DOMAIN_FILES:
            with self.subTest(file=name):
                distribution = load(name)
                projection = {k: v for k, v in distribution.items() if k != "integrity"}
                raw = json.dumps(projection, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")).encode()
                digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                self.assertEqual(distribution["integrity"]["contentDigest"], digest)

    def test_legacy_schema_regression_fails_closed(self):
        mutated = copy.deepcopy(self.framework)
        mutated["embeddedModules"]["schemaProject"]["content"]["properties"]\
            ["creationType"]["enum"] = ["SOFTWARE_WEBSITE", "BOOK"]
        decision = validate_creation_type_contract(mutated, "WEBSITE")
        self.assertFalse(decision["valid"])
        self.assertIn("PROJECT_SCHEMA_CREATION_TYPES_MISMATCH", decision["errors"])

    def test_stale_initialization_menu_fails_closed(self):
        mutated = copy.deepcopy(self.framework)
        step = next(s for s in mutated["embeddedModules"]["initialization"]["content"]
                    ["sequence"] if s["id"] == "INIT-01")
        step["menu"]["options"] = [{"id": "BOOK"}]
        self.assertFalse(validate_creation_type_contract(mutated)["valid"])

    def test_missing_schema_fails_closed(self):
        mutated = copy.deepcopy(self.framework)
        del mutated["embeddedModules"]["schemaProject"]
        self.assertFalse(validate_creation_type_contract(mutated)["valid"])

    def test_duplicate_profile_fails_closed(self):
        mutated = copy.deepcopy(self.framework)
        profiles = mutated["runtimeContract"]["creationProfiles"]
        profiles.append(copy.deepcopy(profiles[0]))
        self.assertIn("RUNTIME_CREATION_TYPES_DUPLICATE",
                      validate_creation_type_contract(mutated)["errors"])

    def test_unknown_or_legacy_requested_type_fails_closed(self):
        for kind in ("SOFTWARE_WEBSITE", "UNKNOWN", "website", "", 42, []):
            with self.subTest(kind=kind):
                self.assertFalse(validate_creation_type_contract(self.framework, kind)["valid"])

    def test_builder_rejects_mismatched_embedded_schema(self):
        from unittest.mock import patch
        from tools import build_bundle
        original = build_bundle.load_module

        def load_with_regression(key, path):
            module = original(key, path)
            if key == "schemaProject":
                module["content"]["properties"]["creationType"]["enum"] = ["BOOK"]
            return module

        with patch.object(build_bundle, "load_module", side_effect=load_with_regression):
            with self.assertRaisesRegex(ValueError, "Creation-type contract"):
                build_bundle.build_bundle()

    def test_distribution_validator_rejects_type_conflict_even_with_valid_digest(self):
        from tools.build_domain_framework import distribution_digest, validate_distribution
        mutated = load("SAFOR-FRAMEWORK-WEBSITE.json")
        mutated["framework"]["embeddedModules"]["schemaProject"]["content"]\
            ["properties"]["creationType"]["enum"] = ["BOOK"]
        mutated["integrity"]["contentDigest"] = distribution_digest(mutated)
        decision = validate_distribution(mutated, "WEBSITE")
        self.assertFalse(decision["valid"])
        self.assertIn("PROJECT_SCHEMA_CREATION_TYPES_MISMATCH", decision["errors"])

    def test_kernel_and_interaction_use_current_type_vocabulary(self):
        kernel = load("v0.14.0/SAFOR-MASTER.json")
        inv = next(i for i in kernel["invariants"] if i["id"] == "INV-039")
        for kind in TYPES:
            self.assertIn(kind, inv["rule"])
        self.assertNotIn("SOFTWARE_WEBSITE", inv["rule"])
        interaction = load("v0.14.0/interaction-model.json")
        step = next(s for s in interaction["initializationExperience"]["steps"]
                    if s["id"] == "CREATION_TYPE")
        self.assertEqual({s["intent"] for s in step["options"]},
                         {f"SELECT_CREATION_TYPE_{kind}" for kind in TYPES})
        self.assertEqual(step["skipWhen"],
                         "CONTAINER_FORMAT == SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION")

    def test_conformance_no_longer_claims_legacy_type_is_free_website(self):
        conformance = load("v0.14.0/conformance.json")
        assertion = next(a for a in conformance["assertions"] if a["id"] == "CF-195")
        self.assertTrue(assertion["statement"].startswith("WEBSITE "))
        self.assertNotIn("SOFTWARE_WEBSITE", assertion["statement"])


if __name__ == "__main__":
    unittest.main()
