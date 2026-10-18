import copy
import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import compute_domain_package_digest
from runtime.public_evaluation_access import (
    compute_domain_framework_distribution_digest,
    resolve_public_evaluation_access,
)


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def redigest_distribution(distribution):
    distribution["integrity"]["contentDigest"] = (
        compute_domain_framework_distribution_digest(distribution)
    )
    return distribution


class PublicEvaluationAccessTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_json("v0.14.0/package-catalog.json")
        self.saas_distribution = load_json("SAFOR-FRAMEWORK-SAAS.json")
        self.saas_access = load_json("SAFOR-TEST-ACCESS-SAAS.json")
        self.book_distribution = load_json("SAFOR-FRAMEWORK-BOOK-CREATION.json")
        self.book_access = load_json("SAFOR-TEST-ACCESS-BOOK-CREATION.json")
        self.website_distribution = load_json("SAFOR-FRAMEWORK-WEBSITE.json")

    def resolve_saas(self, access=None, distribution=None, catalog=None, filename=None):
        return resolve_public_evaluation_access(
            self.saas_distribution if distribution is None else distribution,
            self.saas_access if access is None else access,
            self.catalog if catalog is None else catalog,
            access_file_name=(
                "SAFOR-TEST-ACCESS-SAAS.json" if filename is None else filename
            ),
        )

    def test_saas_public_evaluation_resolves_and_skips_redundant_domain_choice(self):
        result = self.resolve_saas()
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_RESOLVED", result["outcome"], result)
        self.assertEqual("SAAS_ENGINEERING", result["domainId"])
        self.assertEqual("SOFTWARE_SAAS", result["creationType"])
        self.assertEqual("SELECT_PROJECT_WORKSPACE_TYPE", result["nextOperation"])
        self.assertFalse(result["productionAuthorization"])
        self.assertEqual(
            "PACKAGE_ACCESS_RESOLVED",
            result["packageAccess"]["outcome"],
        )

    def test_book_public_evaluation_resolves_and_skips_redundant_domain_choice(self):
        result = resolve_public_evaluation_access(
            self.book_distribution,
            self.book_access,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-BOOK-CREATION.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_RESOLVED", result["outcome"], result)
        self.assertEqual("BOOK_CREATION", result["domainId"])
        self.assertEqual("BOOK", result["creationType"])
        self.assertEqual("SELECT_PROJECT_WORKSPACE_TYPE", result["nextOperation"])
        self.assertFalse(result["productionAuthorization"])

    def test_cross_domain_access_bundle_is_rejected(self):
        result = resolve_public_evaluation_access(
            self.saas_distribution,
            self.book_access,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-BOOK-CREATION.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_FILENAME_MISMATCH", result["reason"])

    def test_cross_domain_bundle_is_rejected_even_when_filename_is_spoofed(self):
        result = self.resolve_saas(access=self.book_access)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_DOMAIN_MISMATCH", result["reason"])

    def test_production_authorization_cannot_be_asserted_by_test_bundle(self):
        tampered = copy.deepcopy(self.saas_access)
        tampered["restrictions"]["productionAuthorization"] = True
        result = self.resolve_saas(access=tampered)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual(
            "PUBLIC_EVALUATION_PRODUCTION_AUTHORIZATION_FORBIDDEN",
            result["reason"],
        )

    def test_access_bundle_must_grant_exactly_the_two_embedded_test_modules(self):
        tampered = copy.deepcopy(self.saas_access)
        tampered["entitlements"][0]["grant"]["versionRange"] = "*"
        result = self.resolve_saas(access=tampered)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_GRANT_SET_MISMATCH", result["reason"])

    def test_activation_contract_cannot_point_to_another_framework(self):
        tampered = copy.deepcopy(self.book_access)
        tampered["activationContract"]["requiredDistributionFile"] = (
            "SAFOR-FRAMEWORK-SAAS.json"
        )
        result = resolve_public_evaluation_access(
            self.book_distribution,
            tampered,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-BOOK-CREATION.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_ACTIVATION_FILE_MISMATCH", result["reason"])

    def test_activation_contract_missing_distribution_route_is_enforced(self):
        tampered = copy.deepcopy(self.saas_access)
        tampered["activationContract"]["onMissingDistribution"] = "IGNORE"
        result = self.resolve_saas(access=tampered)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual(
            "PUBLIC_EVALUATION_ACTIVATION_MISSING_ROUTE_INVALID",
            result["reason"],
        )

    def test_free_website_distribution_does_not_accept_public_paid_test_bundle(self):
        result = resolve_public_evaluation_access(
            self.website_distribution,
            self.saas_access,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-SAAS.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("DOMAIN_FRAMEWORK_NOT_PUBLIC_EVALUATION", result["reason"])

    def test_outer_distribution_tampering_is_detected(self):
        tampered = copy.deepcopy(self.saas_distribution)
        tampered["evaluationNotice"] = "tampered"
        result = self.resolve_saas(distribution=tampered)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("DOMAIN_FRAMEWORK_INTEGRITY_MISMATCH", result["reason"])

    def test_embedded_factory_tampering_is_detected_after_outer_redigest(self):
        tampered = copy.deepcopy(self.saas_distribution)
        tampered["embeddedDomainModules"]["factory"]["exports"][
            "capabilities"
        ].append("tampered-capability")
        redigest_distribution(tampered)
        result = self.resolve_saas(distribution=tampered)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("DOMAIN_FRAMEWORK_EMBEDDED_FACTORY_INVALID", result["reason"])
        self.assertIn("DOMAIN_PACKAGE_INTEGRITY_MISMATCH", result["packageErrors"])

    def test_recomputed_but_incompatible_embedded_pair_is_rejected(self):
        tampered = copy.deepcopy(self.saas_distribution)
        operating_model = tampered["embeddedDomainModules"]["operatingModel"]
        operating_model["exports"]["capabilities"] = []
        new_digest = compute_domain_package_digest(operating_model)
        operating_model["integrity"]["contentDigest"] = new_digest
        tampered["defaultBinding"]["operatingModel"]["contentDigest"] = new_digest
        redigest_distribution(tampered)

        result = self.resolve_saas(distribution=tampered)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual(
            "DOMAIN_FRAMEWORK_EMBEDDED_PAIR_INCOMPATIBLE",
            result["reason"],
        )

    def test_default_binding_must_match_embedded_module_identity(self):
        tampered = copy.deepcopy(self.saas_distribution)
        tampered["defaultBinding"]["factory"]["version"] = "0.0.0"
        redigest_distribution(tampered)
        result = self.resolve_saas(distribution=tampered)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual(
            "DOMAIN_FRAMEWORK_DEFAULT_FACTORY_BINDING_MISMATCH",
            result["reason"],
        )

    def test_malformed_distribution_nested_object_fails_closed(self):
        malformed = copy.deepcopy(self.saas_distribution)
        malformed["evaluationAccess"] = []
        redigest_distribution(malformed)
        result = self.resolve_saas(distribution=malformed)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("DOMAIN_FRAMEWORK_EVALUATION_ACCESS_INVALID", result["reason"])

    def test_malformed_verification_context_fails_closed(self):
        malformed = copy.deepcopy(self.saas_access)
        malformed["verificationContext"] = []
        result = self.resolve_saas(access=malformed)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual(
            "PUBLIC_EVALUATION_VERIFICATION_CONTEXT_INVALID",
            result["reason"],
        )

    def test_malformed_entitlement_nested_object_fails_closed(self):
        malformed = copy.deepcopy(self.saas_access)
        malformed["entitlements"][0]["grant"] = "not-an-object"
        result = self.resolve_saas(access=malformed)
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_ENTITLEMENT_SHAPE_INVALID", result["reason"])

    def test_non_mapping_access_container_fails_closed(self):
        result = resolve_public_evaluation_access(
            self.saas_distribution,
            [],
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-SAAS.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_CONTAINER_INVALID", result["reason"])

    def test_non_mapping_catalog_fails_closed(self):
        result = self.resolve_saas(catalog=[])
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_PACKAGE_CATALOG_INVALID", result["reason"])


if __name__ == "__main__":
    unittest.main()
