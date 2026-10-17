import copy
import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_active_conditional_requirements,
    evaluate_domain_package_pair,
    resolve_composable_creation_packages,
    validate_domain_package,
    validate_factory_contract_consistency,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def entitlement(package_id, version, entitlement_id):
    return {
        "format": "SAFOR_COMMERCIAL_ENTITLEMENT",
        "schemaVersion": "0.13.0",
        "entitlementId": entitlement_id,
        "status": "ACTIVE",
        "subject": {"subjectType": "HUMAN", "subjectRef": "human-1"},
        "commercialBasis": {
            "basisType": "PURCHASE",
            "evidenceRef": "order://" + entitlement_id,
            "sku": "TEST-SKU",
        },
        "grant": {
            "sku": "TEST-SKU",
            "packageId": package_id,
            "versionRange": version,
            "licenseType": "PERPETUAL",
        },
        "validity": {"validFrom": "2026-10-17T00:00:00Z", "validUntil": None},
        "issuer": {"issuerId": "safor-licensing", "issuerName": "SAFOR"},
        "verification": {
            "method": "AUTHORIZED_ENTITLEMENT_PROVIDER_READBACK",
            "verifierId": "license-verifier",
            "evidenceRef": "license://" + entitlement_id,
            "verifiedAt": "2026-10-17T00:00:01Z",
            "result": "VERIFIED",
        },
    }



def verification_context():
    return {
        "evaluatedAt": "2026-10-17T12:00:00Z",
        "subjectRef": "human-1",
        "trustedIssuerIds": ["safor-licensing"],
        "trustedEntitlementVerifierIds": ["license-verifier"],
        "trustedDeliveryVerifierIds": ["delivery-verifier"],
    }


def paid_package(package_id, kind, capabilities, authorities, creation_type):
    pkg = {
        "format": "SAFOR_DOMAIN_PACKAGE",
        "schemaVersion": "0.13.0",
        "packageId": package_id,
        "packageKind": kind,
        "version": "2.0.0",
        "name": "Synthetic commercial package",
        "description": "Test fixture only.",
        "commercial": {
            "accessMode": "PAID_ENTITLEMENT_REQUIRED",
            "sku": "TEST-SKU",
            "entitlementRequired": True,
            "entitlementEvidenceMode": "EXTERNAL_ONLY",
            "independentlySelectable": True,
        },
        "compatibility": {
            "framework": {"minimum": "0.13.0", "maximumExclusive": "0.14.0"},
            "supportedCreationTypes": [creation_type],
            "counterpart": {
                "requiredKind": "OPERATING_MODEL" if kind == "FACTORY" else "FACTORY",
                "requiredCapabilities": capabilities if kind == "FACTORY" else [],
                "requiredAuthorities": authorities if kind == "FACTORY" else [],
            },
        },
        "exports": {
            "capabilities": capabilities,
            "authorities": authorities,
            "workItemTypes": [],
            "artifactTypes": [],
            "providerCapabilities": [],
        },
        "dependencies": [],
        "integrity": {
            "canonicalization": "SAFOR_CANONICAL_JSON_V1",
            "digestAlgorithm": "SHA-256",
            "digestScope": "DECLARED_DOMAIN_CONTRACT",
            "contentDigest": "",
            "verificationMode": "TRUSTED_PACKAGE_SOURCE_READBACK",
        },
        "model": {},
    }
    pkg["integrity"]["contentDigest"] = compute_domain_package_digest(pkg)
    return pkg


class ComposablePackageTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_json("v0.13.0/package-catalog.json")
        self.website_factory = load_json(
            "v0.13.0/packages/factories/website-delivery/1.1.0/package.json"
        )
        self.website_om = load_json(
            "v0.13.0/packages/operating-models/website-team/1.1.0/package.json"
        )

    def test_free_website_defaults_resolve_from_public_catalog(self):
        result = resolve_composable_creation_packages("WEBSITE", self.catalog, [], [])
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertFalse(result["mixedAccessModes"])
        self.assertEqual(
            {"safor.factory.website-delivery", "safor.om.website-team"},
            {x["packageId"] for x in result["packages"]},
        )
        self.assertTrue(all(x["mode"] == "RESOLVE_PUBLIC_FREE" for x in result["packages"]))

    def test_software_saas_without_commercial_packages_is_blocked(self):
        result = resolve_composable_creation_packages("SOFTWARE_SAAS", self.catalog, [], [])
        self.assertEqual("PACKAGE_ACCESS_REQUIRED", result["outcome"])
        self.assertEqual("safor.factory.software-delivery", result["missingPackageId"])

    def test_software_saas_free_override_cannot_bypass_paid_pair_policy(self):
        catalog = copy.deepcopy(self.catalog)
        package_id = "safor.factory.software-free-bypass"
        catalog["entries"].append({
            "packageId": package_id,
            "kind": "FACTORY",
            "version": "1.0.0",
            "label": "Forbidden free software override",
            "accessMode": "FREE_PUBLIC",
            "sku": "FREE-BYPASS",
            "supportedCreationTypes": ["SOFTWARE_SAAS"],
            "selectionClass": "CUSTOM",
            "distribution": {
                "sourceClass": "PUBLIC_CANONICAL_REPOSITORY",
                "path": "tests/fixture-not-read.json",
            },
        })
        result = resolve_composable_creation_packages(
            "SOFTWARE_SAAS",
            catalog,
            [],
            [],
            {"factoryPackageId": package_id},
            verification_context=verification_context(),
        )
        self.assertEqual(
            "CREATION_PROFILE_REQUIRES_BOTH_PAID_PACKAGES",
            result["outcome"],
        )

    def test_software_saas_resolves_only_with_two_paid_packages_and_two_entitlements(self):
        factory = paid_package(
            "safor.factory.software-delivery",
            "FACTORY",
            ["solution_design", "code_contribution"],
            ["product_scope_approval"],
            "SOFTWARE_SAAS",
        )
        om = paid_package(
            "safor.om.saas-engineering",
            "OPERATING_MODEL",
            ["solution_design", "code_contribution"],
            ["product_scope_approval"],
            "SOFTWARE_SAAS",
        )
        loaded = [
            {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": factory},
            {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": om},
        ]
        entitlements = [
            entitlement(factory["packageId"], factory["version"], "ENT-SW-F"),
            entitlement(om["packageId"], om["version"], "ENT-SW-OM"),
        ]
        result = resolve_composable_creation_packages(
            "SOFTWARE_SAAS", self.catalog, loaded, entitlements,
            verification_context=verification_context(),
        )
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertFalse(result["mixedAccessModes"])
        self.assertTrue(all(x["mode"] == "USE_ENTITLED_PACKAGE" for x in result["packages"]))
        self.assertEqual(2, len({x["entitlementId"] for x in result["packages"]}))

    def test_software_saas_missing_operating_model_entitlement_fails(self):
        factory = paid_package(
            "safor.factory.software-delivery",
            "FACTORY",
            ["solution_design"],
            [],
            "SOFTWARE_SAAS",
        )
        om = paid_package(
            "safor.om.saas-engineering",
            "OPERATING_MODEL",
            ["solution_design"],
            [],
            "SOFTWARE_SAAS",
        )
        result = resolve_composable_creation_packages(
            "SOFTWARE_SAAS",
            self.catalog,
            [
                {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": factory},
                {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": om},
            ],
            [entitlement(factory["packageId"], factory["version"], "ENT-SW-F")],
            verification_context=verification_context(),
        )
        self.assertEqual("PACKAGE_ENTITLEMENT_UNVERIFIED", result["outcome"])
        self.assertEqual("safor.om.saas-engineering", result["packageId"])

    def test_website_paid_factory_override_may_mix_with_free_website_om(self):
        catalog = copy.deepcopy(self.catalog)
        package_id = "safor.factory.website-pro"
        catalog["entries"].append({
            "packageId": package_id,
            "kind": "FACTORY",
            "label": "Premium Website Factory",
            "accessMode": "PAID_ENTITLEMENT_REQUIRED",
            "sku": "SAFOR-WEBSITE-PRO",
            "supportedCreationTypes": ["WEBSITE"],
            "selectionClass": "PREMIUM",
            "versionPolicy": "COMMERCIAL_CURRENT",
            "distribution": {
                "sourceClass": "ENTITLED_PACKAGE_SOURCE",
                "publicModelPath": None,
            },
        })
        artifact = paid_package(
            package_id,
            "FACTORY",
            self.website_factory["compatibility"]["counterpart"]["requiredCapabilities"],
            self.website_factory["compatibility"]["counterpart"]["requiredAuthorities"],
            "WEBSITE",
        )
        result = resolve_composable_creation_packages(
            "WEBSITE",
            catalog,
            [{"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": artifact}],
            [entitlement(package_id, "2.0.0", "ENT-WEB-PRO")],
            {"factoryPackageId": package_id},
            verification_context=verification_context(),
        )
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertTrue(result["mixedAccessModes"])

    def test_free_website_packages_have_valid_integrity_and_framework_range(self):
        for pkg in (self.website_factory, self.website_om):
            result = validate_domain_package(pkg, "0.13.0-rc.5", "WEBSITE")
            self.assertTrue(result["valid"], result["errors"])

    def test_website_package_tampering_is_detected(self):
        tampered = copy.deepcopy(self.website_factory)
        tampered["model"]["tampered"] = True
        result = validate_domain_package(tampered, "0.13.0-rc.5", "WEBSITE")
        self.assertFalse(result["valid"])
        self.assertIn("DOMAIN_PACKAGE_INTEGRITY_MISMATCH", result["errors"])

    def test_free_website_factory_and_operating_model_are_compatible(self):
        result = evaluate_domain_package_pair(
            self.website_factory, self.website_om, "0.13.0-rc.5", "WEBSITE"
        )
        self.assertTrue(result["compatible"], result)

    def test_missing_website_operating_model_capability_fails_closed(self):
        om = copy.deepcopy(self.website_om)
        om["exports"]["capabilities"] = [
            x for x in om["exports"]["capabilities"] if x != "accessibility_verification"
        ]
        om["integrity"]["contentDigest"] = compute_domain_package_digest(om)
        result = evaluate_domain_package_pair(
            self.website_factory, om, "0.13.0-rc.5", "WEBSITE"
        )
        self.assertFalse(result["compatible"])
        self.assertIn("accessibility_verification", result["missingCapabilities"])

    def test_search_visibility_is_conditional_for_website(self):
        om = copy.deepcopy(self.website_om)
        om["exports"]["capabilities"] = [
            x for x in om["exports"]["capabilities"] if x != "search_visibility_verification"
        ]
        om["integrity"]["contentDigest"] = compute_domain_package_digest(om)
        base = evaluate_domain_package_pair(
            self.website_factory, om, "0.13.0-rc.5", "WEBSITE"
        )
        self.assertTrue(base["compatible"], base)
        active = evaluate_active_conditional_requirements(
            self.website_factory, om, {"PUBLIC_DISCOVERABILITY_REQUIRED"}
        )
        self.assertFalse(active["satisfied"])
        self.assertEqual(["search_visibility_verification"], active["missingCapabilities"])

    def test_website_factory_contract_is_internally_consistent(self):
        result = validate_factory_contract_consistency(self.website_factory)
        self.assertTrue(result["valid"], result["errors"])

    def test_package_id_must_match_package_kind(self):
        invalid = copy.deepcopy(self.website_factory)
        invalid["packageId"] = "safor.om.not-a-factory"
        invalid["integrity"]["contentDigest"] = compute_domain_package_digest(invalid)
        result = validate_domain_package(invalid, "0.13.0-rc.5", "WEBSITE")
        self.assertFalse(result["valid"])
        self.assertIn("DOMAIN_PACKAGE_ID_KIND_MISMATCH", result["errors"])

    def test_creation_type_scope_is_enforced(self):
        result = validate_domain_package(
            self.website_factory, "0.13.0-rc.5", "SOFTWARE_SAAS"
        )
        self.assertFalse(result["valid"])
        self.assertIn("DOMAIN_PACKAGE_CREATION_TYPE_UNSUPPORTED", result["errors"])

    def test_catalog_has_three_distinct_creation_profiles(self):
        profiles = {x["creationType"]: x for x in self.catalog["creationProfiles"]}
        self.assertEqual({"WEBSITE", "SOFTWARE_SAAS", "BOOK"}, set(profiles))
        self.assertEqual("ANY_COMPATIBLE_ACCESS", profiles["WEBSITE"]["selectedPackageAccessPolicy"])
        self.assertEqual(
            "BOTH_PAID_ENTITLEMENT_REQUIRED",
            profiles["SOFTWARE_SAAS"]["selectedPackageAccessPolicy"],
        )
        self.assertEqual(
            "BOTH_PAID_ENTITLEMENT_REQUIRED",
            profiles["BOOK"]["selectedPackageAccessPolicy"],
        )


if __name__ == "__main__":
    unittest.main()
