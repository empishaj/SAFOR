import copy
import json
import unittest
from pathlib import Path

from runtime.public_evaluation_access import resolve_public_evaluation_access


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class PublicEvaluationAccessTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_json("v0.13.0/package-catalog.json")
        self.saas_distribution = load_json("SAFOR-FRAMEWORK-SAAS.json")
        self.saas_access = load_json("SAFOR-TEST-ACCESS-SAAS.json")
        self.book_distribution = load_json("SAFOR-FRAMEWORK-BOOK-CREATION.json")
        self.book_access = load_json("SAFOR-TEST-ACCESS-BOOK-CREATION.json")
        self.website_distribution = load_json("SAFOR-FRAMEWORK-WEBSITE.json")

    def test_saas_public_evaluation_resolves_and_skips_redundant_domain_choice(self):
        result = resolve_public_evaluation_access(
            self.saas_distribution,
            self.saas_access,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-SAAS.json",
        )
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
        result = resolve_public_evaluation_access(
            self.saas_distribution,
            self.book_access,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-SAAS.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_DOMAIN_MISMATCH", result["reason"])

    def test_production_authorization_cannot_be_asserted_by_test_bundle(self):
        tampered = copy.deepcopy(self.saas_access)
        tampered["restrictions"]["productionAuthorization"] = True
        result = resolve_public_evaluation_access(
            self.saas_distribution,
            tampered,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-SAAS.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_PRODUCTION_AUTHORIZATION_FORBIDDEN", result["reason"])

    def test_access_bundle_must_grant_exactly_the_two_embedded_test_modules(self):
        tampered = copy.deepcopy(self.saas_access)
        tampered["entitlements"][0]["grant"]["versionRange"] = "*"
        result = resolve_public_evaluation_access(
            self.saas_distribution,
            tampered,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-SAAS.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_GRANT_SET_MISMATCH", result["reason"])

    def test_activation_contract_cannot_point_to_another_framework(self):
        tampered = copy.deepcopy(self.book_access)
        tampered["activationContract"]["requiredDistributionFile"] = "SAFOR-FRAMEWORK-SAAS.json"
        result = resolve_public_evaluation_access(
            self.book_distribution,
            tampered,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-BOOK-CREATION.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("PUBLIC_EVALUATION_ACTIVATION_FILE_MISMATCH", result["reason"])

    def test_free_website_distribution_does_not_accept_public_paid_test_bundle(self):
        result = resolve_public_evaluation_access(
            self.website_distribution,
            self.saas_access,
            self.catalog,
            access_file_name="SAFOR-TEST-ACCESS-SAAS.json",
        )
        self.assertEqual("PUBLIC_EVALUATION_ACCESS_REJECTED", result["outcome"])
        self.assertEqual("DOMAIN_FRAMEWORK_NOT_PUBLIC_EVALUATION", result["reason"])


if __name__ == "__main__":
    unittest.main()
