import copy
import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    resolve_composable_creation_packages,
    validate_commercial_delivery_evidence,
    validate_commercial_entitlement,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def verification_context(**overrides):
    context = {
        "evaluatedAt": "2026-10-17T12:00:00Z",
        "subjectRef": "human-1",
        "trustedIssuerIds": ["safor-licensing"],
        "trustedEntitlementVerifierIds": ["license-verifier"],
        "trustedDeliveryVerifierIds": ["delivery-verifier"],
    }
    context.update(overrides)
    return context


def entitlement(package_id, version, entitlement_id="ENT-1", **overrides):
    record = {
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
        "validity": {
            "validFrom": "2026-10-17T00:00:00Z",
            "validUntil": None,
        },
        "issuer": {"issuerId": "safor-licensing", "issuerName": "SAFOR"},
        "verification": {
            "method": "AUTHORIZED_ENTITLEMENT_PROVIDER_READBACK",
            "verifierId": "license-verifier",
            "evidenceRef": "license://" + entitlement_id,
            "verifiedAt": "2026-10-17T00:00:01Z",
            "result": "VERIFIED",
        },
    }
    for key, value in overrides.items():
        if "." in key:
            head, tail = key.split(".", 1)
            record[head][tail] = value
        else:
            record[key] = value
    return record


def paid_package(package_id, kind, creation_type="SOFTWARE_SAAS"):
    capabilities = ["solution_design", "code_contribution"]
    authorities = ["product_scope_approval"]
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


def delivery_evidence(artifact, entitlement_record, delivery_id="DEL-1", **overrides):
    record = {
        "format": "SAFOR_COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE",
        "schemaVersion": "0.13.0",
        "deliveryId": delivery_id,
        "entitlementId": entitlement_record["entitlementId"],
        "packageId": artifact["packageId"],
        "version": artifact["version"],
        "artifactDigest": artifact["integrity"]["contentDigest"],
        "sourceRef": "entitled://delivery/" + delivery_id,
        "issuedAt": "2026-10-17T11:59:00Z",
        "expiresAt": "2026-10-17T12:10:00Z",
        "verifierId": "delivery-verifier",
        "result": "VERIFIED",
    }
    record.update(overrides)
    return record


class CommercialDeliveryChannelTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_json("v0.13.0/package-catalog.json")
        self.factory = paid_package("safor.factory.software-delivery", "FACTORY")
        self.om = paid_package("safor.om.saas-engineering", "OPERATING_MODEL")
        self.factory_entitlement = entitlement(
            self.factory["packageId"], self.factory["version"], "ENT-F"
        )
        self.om_entitlement = entitlement(
            self.om["packageId"], self.om["version"], "ENT-OM"
        )

    def test_active_entitlement_with_trusted_context_is_valid(self):
        result = validate_commercial_entitlement(
            self.factory_entitlement,
            self.factory["packageId"],
            self.factory["version"],
            verification_context(),
        )
        self.assertTrue(result["valid"], result)

    def test_revoked_entitlement_is_rejected(self):
        record = copy.deepcopy(self.factory_entitlement)
        record["status"] = "REVOKED"
        result = validate_commercial_entitlement(
            record, self.factory["packageId"], self.factory["version"], verification_context()
        )
        self.assertFalse(result["valid"])
        self.assertEqual("PACKAGE_ENTITLEMENT_STATUS_INVALID", result["outcome"])

    def test_expired_entitlement_is_rejected(self):
        record = copy.deepcopy(self.factory_entitlement)
        record["validity"]["validUntil"] = "2026-10-17T11:00:00Z"
        result = validate_commercial_entitlement(
            record, self.factory["packageId"], self.factory["version"], verification_context()
        )
        self.assertFalse(result["valid"])
        self.assertEqual("PACKAGE_ENTITLEMENT_EXPIRED", result["outcome"])

    def test_subject_mismatch_is_rejected(self):
        result = validate_commercial_entitlement(
            self.factory_entitlement,
            self.factory["packageId"],
            self.factory["version"],
            verification_context(subjectRef="other-human"),
        )
        self.assertFalse(result["valid"])
        self.assertEqual("PACKAGE_ENTITLEMENT_SUBJECT_MISMATCH", result["outcome"])

    def test_untrusted_issuer_and_verifier_are_rejected(self):
        issuer = validate_commercial_entitlement(
            self.factory_entitlement,
            self.factory["packageId"],
            self.factory["version"],
            verification_context(trustedIssuerIds=["other-issuer"]),
        )
        self.assertEqual("PACKAGE_ENTITLEMENT_ISSUER_UNTRUSTED", issuer["outcome"])
        verifier = validate_commercial_entitlement(
            self.factory_entitlement,
            self.factory["packageId"],
            self.factory["version"],
            verification_context(trustedEntitlementVerifierIds=["other-verifier"]),
        )
        self.assertEqual("PACKAGE_ENTITLEMENT_VERIFIER_UNTRUSTED", verifier["outcome"])

    def test_entitled_source_requires_delivery_evidence(self):
        result = resolve_composable_creation_packages(
            "SOFTWARE_SAAS",
            self.catalog,
            [
                {"sourceClass": "ENTITLED_PACKAGE_SOURCE", "artifact": self.factory},
                {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": self.om},
            ],
            [self.factory_entitlement, self.om_entitlement],
            verification_context=verification_context(),
        )
        self.assertEqual("COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE_REQUIRED", result["outcome"])
        self.assertEqual(self.factory["packageId"], result["packageId"])

    def test_delivery_digest_mismatch_is_rejected(self):
        evidence = delivery_evidence(
            self.factory,
            self.factory_entitlement,
            artifactDigest="sha256:" + "0" * 64,
        )
        result = validate_commercial_delivery_evidence(
            evidence,
            self.factory,
            self.factory_entitlement,
            verification_context(),
        )
        self.assertFalse(result["valid"])
        self.assertEqual("COMMERCIAL_PACKAGE_DELIVERY_DIGEST_MISMATCH", result["outcome"])

    def test_expired_delivery_evidence_is_rejected(self):
        evidence = delivery_evidence(
            self.factory,
            self.factory_entitlement,
            expiresAt="2026-10-17T11:00:00Z",
        )
        result = validate_commercial_delivery_evidence(
            evidence,
            self.factory,
            self.factory_entitlement,
            verification_context(),
        )
        self.assertFalse(result["valid"])
        self.assertEqual("COMMERCIAL_PACKAGE_DELIVERY_EXPIRED", result["outcome"])

    def test_valid_protected_delivery_chain_resolves_both_software_packages(self):
        loaded = [
            {
                "sourceClass": "ENTITLED_PACKAGE_SOURCE",
                "artifact": self.factory,
                "deliveryEvidence": delivery_evidence(
                    self.factory, self.factory_entitlement, "DEL-F"
                ),
            },
            {
                "sourceClass": "ENTITLED_PACKAGE_SOURCE",
                "artifact": self.om,
                "deliveryEvidence": delivery_evidence(
                    self.om, self.om_entitlement, "DEL-OM"
                ),
            },
        ]
        result = resolve_composable_creation_packages(
            "SOFTWARE_SAAS",
            self.catalog,
            loaded,
            [self.factory_entitlement, self.om_entitlement],
            verification_context=verification_context(),
        )
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"], result)
        self.assertEqual(2, len(result["packages"]))
        self.assertEqual(
            {"DEL-F", "DEL-OM"},
            {x["deliveryId"] for x in result["packages"]},
        )
        self.assertTrue(all(x["deliveryVerifierId"] == "delivery-verifier" for x in result["packages"]))

    def test_human_loaded_paid_artifact_skips_delivery_evidence_but_not_entitlement(self):
        result = resolve_composable_creation_packages(
            "SOFTWARE_SAAS",
            self.catalog,
            [
                {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": self.factory},
                {"sourceClass": "HUMAN_LOADED_PACKAGE", "artifact": self.om},
            ],
            [self.factory_entitlement, self.om_entitlement],
            verification_context=verification_context(),
        )
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"], result)
        self.assertTrue(all("deliveryId" not in x for x in result["packages"]))


if __name__ == "__main__":
    unittest.main()
