import copy
import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_domain_framework_pair,
    resolve_composable_creation_packages,
)
from tools.build_domain_framework import build_distribution, validate_distribution

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def redigest(pkg):
    pkg["integrity"]["contentDigest"] = compute_domain_package_digest(pkg)
    return pkg


class DomainFrameworkDistributionTests(unittest.TestCase):
    def setUp(self):
        self.factory = load_json(
            "v0.14.0/packages/factories/website-delivery/1.2.0/package.json"
        )
        self.om = load_json(
            "v0.14.0/packages/operating-models/website-team/1.2.0/package.json"
        )

    def test_website_default_pair_is_domain_compatible_bidirectionally(self):
        result = evaluate_domain_framework_pair(
            self.factory,
            self.om,
            "0.14.0-rc.3",
            "WEBSITE",
            "WEBSITE_CREATION",
        )
        self.assertTrue(result["compatible"], result)
        self.assertTrue(result["factoryToOperatingModel"]["familyAllowed"])
        self.assertTrue(result["operatingModelToFactory"]["familyAllowed"])

    def test_premium_factory_same_family_and_domain_is_adoptable(self):
        premium = copy.deepcopy(self.factory)
        premium["packageId"] = "safor.factory.website-premium"
        premium["version"] = "2.0.0"
        redigest(premium)
        result = evaluate_domain_framework_pair(
            premium,
            self.om,
            "0.14.0-rc.3",
            "WEBSITE",
            "WEBSITE_CREATION",
        )
        self.assertTrue(result["compatible"], result)

    def test_premium_operating_model_same_family_and_domain_is_adoptable(self):
        premium = copy.deepcopy(self.om)
        premium["packageId"] = "safor.om.website-premium"
        premium["version"] = "2.0.0"
        redigest(premium)
        result = evaluate_domain_framework_pair(
            self.factory,
            premium,
            "0.14.0-rc.3",
            "WEBSITE",
            "WEBSITE_CREATION",
        )
        self.assertTrue(result["compatible"], result)

    def test_factory_rejects_wrong_operating_model_family_even_same_domain(self):
        foreign = copy.deepcopy(self.om)
        foreign["packageId"] = "safor.om.website-foreign"
        foreign["packageFamily"] = "safor.om.other-domain-model"
        foreign["compatibility"]["domainIds"] = ["WEBSITE_CREATION"]
        redigest(foreign)
        result = evaluate_domain_framework_pair(
            self.factory,
            foreign,
            "0.14.0-rc.3",
            "WEBSITE",
            "WEBSITE_CREATION",
        )
        self.assertFalse(result["compatible"])
        self.assertFalse(result["factoryToOperatingModel"]["familyAllowed"])

    def test_operating_model_rejects_wrong_factory_family_even_same_domain(self):
        foreign = copy.deepcopy(self.factory)
        foreign["packageId"] = "safor.factory.website-foreign"
        foreign["packageFamily"] = "safor.factory.other-domain-factory"
        foreign["compatibility"]["domainIds"] = ["WEBSITE_CREATION"]
        redigest(foreign)
        result = evaluate_domain_framework_pair(
            foreign,
            self.om,
            "0.14.0-rc.3",
            "WEBSITE",
            "WEBSITE_CREATION",
        )
        self.assertFalse(result["compatible"])
        self.assertFalse(result["operatingModelToFactory"]["familyAllowed"])

    def test_book_factory_with_engineering_operating_model_is_rejected(self):
        book_factory = copy.deepcopy(self.factory)
        book_factory["packageId"] = "safor.factory.book-premium"
        book_factory["packageFamily"] = "safor.factory.book"
        book_factory["compatibility"]["supportedCreationTypes"] = ["BOOK"]
        book_factory["compatibility"]["domainIds"] = ["BOOK_CREATION"]
        book_factory["compatibility"]["counterpart"]["allowedPackageFamilies"] = [
            "safor.om.book"
        ]
        redigest(book_factory)

        engineering_om = copy.deepcopy(self.om)
        engineering_om["packageId"] = "safor.om.saas-premium"
        engineering_om["packageFamily"] = "safor.om.saas"
        engineering_om["compatibility"]["supportedCreationTypes"] = ["SOFTWARE_SAAS"]
        engineering_om["compatibility"]["domainIds"] = ["SAAS_ENGINEERING"]
        engineering_om["compatibility"]["counterpart"]["allowedPackageFamilies"] = [
            "safor.factory.saas"
        ]
        redigest(engineering_om)

        result = evaluate_domain_framework_pair(
            book_factory,
            engineering_om,
            "0.14.0-rc.3",
            "BOOK",
            "BOOK_CREATION",
        )
        self.assertFalse(result["compatible"])
        self.assertFalse(result["domainMatch"])

    def test_operating_model_required_factory_work_items_are_enforced(self):
        incomplete = copy.deepcopy(self.factory)
        incomplete["exports"]["workItemTypes"] = [
            x for x in incomplete["exports"]["workItemTypes"] if x != "PUBLISH"
        ]
        redigest(incomplete)
        result = evaluate_domain_framework_pair(
            incomplete,
            self.om,
            "0.14.0-rc.3",
            "WEBSITE",
            "WEBSITE_CREATION",
        )
        self.assertFalse(result["compatible"])
        self.assertIn(
            "PUBLISH",
            result["operatingModelToFactory"]["missingWorkItemTypes"],
        )

    def test_website_distribution_builder_embeds_default_modules(self):
        distribution = build_distribution("WEBSITE")
        self.assertEqual(
            "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION",
            distribution["format"],
        )
        self.assertEqual("WEBSITE_CREATION", distribution["domain"]["domainId"])
        self.assertEqual(
            "safor.factory.website-delivery",
            distribution["embeddedDomainModules"]["factory"]["packageId"],
        )
        self.assertEqual(
            "safor.om.website-team",
            distribution["embeddedDomainModules"]["operatingModel"]["packageId"],
        )
        self.assertEqual(
            "COMPATIBLE",
            distribution["defaultBinding"]["compatibility"],
        )
        decision = validate_distribution(distribution, "WEBSITE")
        self.assertTrue(decision["valid"], decision)

    def test_distribution_replacement_policy_keeps_modules_replaceable(self):
        distribution = build_distribution("WEBSITE")
        policy = distribution["replacementPolicy"]
        self.assertTrue(policy["factoryReplaceable"])
        self.assertTrue(policy["operatingModelReplaceable"])
        self.assertTrue(policy["sameDomainRequired"])
        self.assertTrue(policy["bidirectionalCounterpartRequired"])
        self.assertTrue(policy["packageFamilyConstraintsEnforced"])
        self.assertTrue(policy["crossDomainPairForbidden"])

    def test_saas_public_evaluation_framework_is_paid_and_compatible(self):
        distribution = build_distribution("SAAS")
        self.assertEqual("PUBLIC_TEST_EVALUATION", distribution["publicationMode"])
        self.assertEqual("SAAS_ENGINEERING", distribution["domain"]["domainId"])
        self.assertEqual("PAID_ENTITLEMENT_REQUIRED", distribution["domain"]["accessMode"])
        self.assertTrue(distribution["evaluationNotice"])
        self.assertEqual(
            "PAID_ENTITLEMENT_REQUIRED",
            distribution["embeddedDomainModules"]["factory"]["commercial"]["accessMode"],
        )
        self.assertEqual(
            "PAID_ENTITLEMENT_REQUIRED",
            distribution["embeddedDomainModules"]["operatingModel"]["commercial"]["accessMode"],
        )
        decision = validate_distribution(distribution, "SAAS")
        self.assertTrue(decision["valid"], decision)

    def test_book_public_evaluation_framework_is_paid_and_compatible(self):
        distribution = build_distribution("BOOK_CREATION")
        self.assertEqual("PUBLIC_TEST_EVALUATION", distribution["publicationMode"])
        self.assertEqual("BOOK_CREATION", distribution["domain"]["domainId"])
        self.assertEqual("PAID_ENTITLEMENT_REQUIRED", distribution["domain"]["accessMode"])
        self.assertTrue(distribution["evaluationNotice"])
        self.assertEqual(
            "safor.factory.book",
            distribution["embeddedDomainModules"]["factory"]["packageFamily"],
        )
        self.assertEqual(
            "safor.om.book",
            distribution["embeddedDomainModules"]["operatingModel"]["packageFamily"],
        )
        decision = validate_distribution(distribution, "BOOK_CREATION")
        self.assertTrue(decision["valid"], decision)

    def test_public_paid_test_framework_files_match_builder(self):
        for profile_id, filename in (
            ("SAAS", "SAFOR-FRAMEWORK-SAAS.json"),
            ("BOOK_CREATION", "SAFOR-FRAMEWORK-BOOK-CREATION.json"),
        ):
            committed = load_json(filename)
            built = build_distribution(profile_id)
            self.assertEqual(committed, built)

    def test_public_evaluation_access_bundles_unlock_only_paid_test_modules(self):
        catalog = load_json("v0.14.0/package-catalog.json")
        for profile_id, framework_file in (
            ("SAAS", "SAFOR-FRAMEWORK-SAAS.json"),
            ("BOOK_CREATION", "SAFOR-FRAMEWORK-BOOK-CREATION.json"),
        ):
            with self.subTest(profile_id=profile_id):
                distribution = load_json(framework_file)
                access_file = distribution["evaluationAccess"]["file"]
                access = load_json(access_file)
                modules = distribution["embeddedDomainModules"]
                result = resolve_composable_creation_packages(
                    distribution["domain"]["creationType"],
                    catalog,
                    [
                        {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": modules["factory"]},
                        {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": modules["operatingModel"]},
                    ],
                    access["entitlements"],
                    verification_context=access["verificationContext"],
                )
                self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"], result)
                self.assertFalse(access["restrictions"]["productionAuthorization"])
                self.assertTrue(access["restrictions"]["testPackageVersionsOnly"])


if __name__ == "__main__":
    unittest.main()
