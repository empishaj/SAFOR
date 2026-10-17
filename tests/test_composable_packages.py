import copy
import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_domain_package_pair,
    resolve_composable_creation_packages,
    validate_domain_package,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def entitlement(package_id, version, entitlement_id):
    return {
        "format": "SAFOR_COMMERCIAL_ENTITLEMENT",
        "schemaVersion": "0.13.0",
        "entitlementId": entitlement_id,
        "subject": {"subjectType": "HUMAN", "subjectRef": "human-1"},
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
        },
    }


def paid_package(package_id, kind, capabilities, authorities, creation_type="SOFTWARE_WEBSITE"):
    pkg = {
        "format": "SAFOR_DOMAIN_PACKAGE",
        "schemaVersion": "0.13.0",
        "packageId": package_id,
        "packageKind": kind,
        "version": "2.0.0",
        "name": "Synthetic paid package",
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
        self.free_factory = load_json(
            "v0.13.0/packages/factories/software-delivery/1.5.0/package.json"
        )
        self.free_om = load_json(
            "v0.13.0/packages/operating-models/saas-engineering/1.5.0/package.json"
        )

    def test_free_website_defaults_resolve_from_public_catalog(self):
        result = resolve_composable_creation_packages(
            "SOFTWARE_WEBSITE", self.catalog, [], []
        )
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertFalse(result["mixedAccessModes"])
        self.assertEqual(
            {"safor.factory.software-delivery", "safor.om.saas-engineering"},
            {x["packageId"] for x in result["packages"]},
        )
        self.assertTrue(all(x["mode"] == "RESOLVE_PUBLIC_FREE" for x in result["packages"]))

    def test_paid_factory_override_can_mix_with_free_operating_model(self):
        catalog = copy.deepcopy(self.catalog)
        package_id = "safor.factory.software-delivery-pro"
        catalog["entries"].append({
            "packageId": package_id,
            "kind": "FACTORY",
            "label": "Premium Software Factory",
            "accessMode": "PAID_ENTITLEMENT_REQUIRED",
            "sku": "SAFOR-SW-FACTORY-PRO",
            "supportedCreationTypes": ["SOFTWARE_WEBSITE"],
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
            self.free_factory["exports"]["capabilities"],
            self.free_factory["exports"]["authorities"],
        )
        result = resolve_composable_creation_packages(
            "SOFTWARE_WEBSITE",
            catalog,
            [{"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": artifact}],
            [entitlement(package_id, "2.0.0", "ENT-F-PRO")],
            {"factoryPackageId": package_id},
        )
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertTrue(result["mixedAccessModes"])
        self.assertEqual(package_id, result["selectedFactoryPackageId"])
        self.assertEqual("safor.om.saas-engineering", result["selectedOperatingModelPackageId"])

    def test_paid_operating_model_override_can_mix_with_free_factory(self):
        catalog = copy.deepcopy(self.catalog)
        package_id = "safor.om.saas-engineering-enterprise"
        catalog["entries"].append({
            "packageId": package_id,
            "kind": "OPERATING_MODEL",
            "label": "Enterprise SaaS Operating Model",
            "accessMode": "PAID_ENTITLEMENT_REQUIRED",
            "sku": "SAFOR-OM-SAAS-ENTERPRISE",
            "supportedCreationTypes": ["SOFTWARE_WEBSITE"],
            "selectionClass": "PREMIUM",
            "versionPolicy": "COMMERCIAL_CURRENT",
            "distribution": {
                "sourceClass": "ENTITLED_PACKAGE_SOURCE",
                "publicModelPath": None,
            },
        })
        artifact = paid_package(
            package_id,
            "OPERATING_MODEL",
            self.free_om["exports"]["capabilities"],
            self.free_om["exports"]["authorities"],
        )
        result = resolve_composable_creation_packages(
            "SOFTWARE_WEBSITE",
            catalog,
            [{"sourceClass": "ENTITLED_PACKAGE_SOURCE", "artifact": artifact}],
            [entitlement(package_id, "2.0.0", "ENT-OM-PRO")],
            {"operatingModelPackageId": package_id},
        )
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertTrue(result["mixedAccessModes"])
        self.assertEqual("safor.factory.software-delivery", result["selectedFactoryPackageId"])
        self.assertEqual(package_id, result["selectedOperatingModelPackageId"])

    def test_paid_override_without_entitlement_is_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        package_id = "safor.factory.software-delivery-pro"
        catalog["entries"].append({
            "packageId": package_id,
            "kind": "FACTORY",
            "label": "Premium Software Factory",
            "accessMode": "PAID_ENTITLEMENT_REQUIRED",
            "sku": "SAFOR-SW-FACTORY-PRO",
            "supportedCreationTypes": ["SOFTWARE_WEBSITE"],
            "selectionClass": "PREMIUM",
            "versionPolicy": "COMMERCIAL_CURRENT",
            "distribution": {
                "sourceClass": "ENTITLED_PACKAGE_SOURCE",
                "publicModelPath": None,
            },
        })
        artifact = paid_package(package_id, "FACTORY", [], [])
        result = resolve_composable_creation_packages(
            "SOFTWARE_WEBSITE",
            catalog,
            [{"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": artifact}],
            [],
            {"factoryPackageId": package_id},
        )
        self.assertEqual("PACKAGE_ENTITLEMENT_UNVERIFIED", result["outcome"])

    def test_free_domain_packages_have_valid_integrity_and_framework_range(self):
        for pkg in (self.free_factory, self.free_om):
            result = validate_domain_package(pkg, "0.13.0-rc.1", "SOFTWARE_WEBSITE")
            self.assertTrue(result["valid"], result["errors"])

    def test_package_tampering_is_detected(self):
        tampered = copy.deepcopy(self.free_factory)
        tampered["model"]["tampered"] = True
        result = validate_domain_package(tampered, "0.13.0-rc.1", "SOFTWARE_WEBSITE")
        self.assertFalse(result["valid"])
        self.assertIn("DOMAIN_PACKAGE_INTEGRITY_MISMATCH", result["errors"])

    def test_free_factory_and_operating_model_are_compatible(self):
        result = evaluate_domain_package_pair(
            self.free_factory, self.free_om, "0.13.0-rc.1", "SOFTWARE_WEBSITE"
        )
        self.assertTrue(result["compatible"], result)

    def test_missing_operating_model_capability_fails_closed(self):
        om = copy.deepcopy(self.free_om)
        om["exports"]["capabilities"] = [
            x for x in om["exports"]["capabilities"] if x != "security_evidence"
        ]
        om["integrity"]["contentDigest"] = compute_domain_package_digest(om)
        result = evaluate_domain_package_pair(
            self.free_factory, om, "0.13.0-rc.1", "SOFTWARE_WEBSITE"
        )
        self.assertFalse(result["compatible"])
        self.assertIn("security_evidence", result["missingCapabilities"])

    def test_package_id_must_match_package_kind(self):
        invalid = copy.deepcopy(self.free_factory)
        invalid["packageId"] = "safor.om.this-is-not-a-factory"
        invalid["integrity"]["contentDigest"] = compute_domain_package_digest(invalid)
        result = validate_domain_package(invalid, "0.13.0-rc.1", "SOFTWARE_WEBSITE")
        self.assertFalse(result["valid"])
        self.assertIn("DOMAIN_PACKAGE_ID_KIND_MISMATCH", result["errors"])

    def test_package_creation_type_scope_is_enforced(self):
        result = validate_domain_package(self.free_factory, "0.13.0-rc.1", "BOOK")
        self.assertFalse(result["valid"])
        self.assertIn("DOMAIN_PACKAGE_CREATION_TYPE_UNSUPPORTED", result["errors"])


if __name__ == "__main__":
    unittest.main()
