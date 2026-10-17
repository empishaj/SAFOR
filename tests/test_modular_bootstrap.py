import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import (
    factory_operating_model_compatible,
    resolve_creation_packages,
    validate_workspace_binding,
)

ROOT = Path(__file__).resolve().parents[1]


def catalog():
    return json.loads((ROOT / "v0.12.0/package-catalog.json").read_text(encoding="utf-8"))


def entitlement(package_id, version="1.0.0", entitlement_id="ENT-1", method="AUTHORIZED_ENTITLEMENT_PROVIDER_READBACK"):
    return {
        "format": "SAFOR_COMMERCIAL_ENTITLEMENT",
        "schemaVersion": "0.12.0",
        "entitlementId": entitlement_id,
        "subject": {"subjectType": "HUMAN", "subjectRef": "human-1"},
        "grant": {
            "sku": "SKU",
            "packageId": package_id,
            "versionRange": version,
            "licenseType": "PERPETUAL",
        },
        "validity": {"validFrom": "2026-10-17T00:00:00Z", "validUntil": None},
        "issuer": {"issuerId": "safor-licensing", "issuerName": "SAFOR"},
        "verification": {
            "method": method,
            "verifierId": "license-verifier",
            "evidenceRef": "license://ENT-1",
            "verifiedAt": "2026-10-17T00:00:01Z",
        },
    }


class ModularBootstrapTests(unittest.TestCase):
    def test_free_website_auto_resolves_from_public_framework_git(self):
        result = resolve_creation_packages("SOFTWARE_WEBSITE", catalog(), [], [])
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertEqual("FREE_PUBLIC", result["accessMode"])
        self.assertEqual(2, len(result["packages"]))
        self.assertTrue(all(x["mode"] == "RESOLVE_PUBLIC_FREE" for x in result["packages"]))
        self.assertTrue(all(x["sourceClass"] == "PUBLIC_CANONICAL_REPOSITORY" for x in result["packages"]))

    def test_book_without_packages_requires_access(self):
        result = resolve_creation_packages("BOOK", catalog(), [], [])
        self.assertEqual("PACKAGE_ACCESS_REQUIRED", result["outcome"])

    def test_paid_package_cannot_resolve_from_public_source(self):
        loaded = [
            {"packageId": "safor.factory.book-production", "version": "1.0.0", "sourceClass": "PUBLIC_CANONICAL_REPOSITORY"},
            {"packageId": "safor.om.book-authoring", "version": "1.0.0", "sourceClass": "PUBLIC_CANONICAL_REPOSITORY"},
        ]
        result = resolve_creation_packages("BOOK", catalog(), loaded, [])
        self.assertEqual("PAID_PUBLIC_RESOLUTION_FORBIDDEN", result["outcome"])

    def test_paid_loaded_packages_need_verified_entitlements(self):
        loaded = [
            {"packageId": "safor.factory.book-production", "version": "1.0.0", "sourceClass": "HUMAN_LOADED_PACKAGE"},
            {"packageId": "safor.om.book-authoring", "version": "1.0.0", "sourceClass": "HUMAN_LOADED_PACKAGE"},
        ]
        result = resolve_creation_packages("BOOK", catalog(), loaded, [])
        self.assertEqual("PACKAGE_ENTITLEMENT_UNVERIFIED", result["outcome"])

    def test_paid_loaded_packages_with_entitlements_resolve(self):
        loaded = [
            {"packageId": "safor.factory.book-production", "version": "1.0.0", "sourceClass": "HUMAN_LOADED_PACKAGE"},
            {"packageId": "safor.om.book-authoring", "version": "1.0.0", "sourceClass": "ENTITLED_PACKAGE_SOURCE"},
        ]
        entitlements = [
            entitlement("safor.factory.book-production", entitlement_id="ENT-F"),
            entitlement("safor.om.book-authoring", entitlement_id="ENT-O"),
        ]
        result = resolve_creation_packages("BOOK", catalog(), loaded, entitlements)
        self.assertEqual("PACKAGE_ACCESS_RESOLVED", result["outcome"])
        self.assertTrue(all(x["mode"] == "USE_ENTITLED_PACKAGE" for x in result["packages"]))

    def test_self_asserted_entitlement_method_is_rejected(self):
        loaded = [
            {"packageId": "safor.factory.book-production", "version": "1.0.0", "sourceClass": "HUMAN_LOADED_PACKAGE"},
            {"packageId": "safor.om.book-authoring", "version": "1.0.0", "sourceClass": "HUMAN_LOADED_PACKAGE"},
        ]
        entitlements = [
            entitlement("safor.factory.book-production", entitlement_id="ENT-F", method="HUMAN_SELF_ASSERTED"),
            entitlement("safor.om.book-authoring", entitlement_id="ENT-O"),
        ]
        result = resolve_creation_packages("BOOK", catalog(), loaded, entitlements)
        self.assertEqual("PACKAGE_ENTITLEMENT_UNVERIFIED", result["outcome"])

    def test_factory_operating_model_compatibility_passes_for_free_pair(self):
        factory = json.loads((ROOT / "v0.10.0/packages/factories/software-delivery/1.4.0/package.json").read_text(encoding="utf-8"))
        om = json.loads((ROOT / "v0.10.0/packages/operating-models/saas-engineering/1.4.0/package.json").read_text(encoding="utf-8"))
        result = factory_operating_model_compatible(factory, om)
        self.assertTrue(result["compatible"])

    def test_factory_operating_model_compatibility_fails_closed(self):
        factory = {"exports": {"capabilities": ["code_contribution", "security_evidence"], "authorities": ["production_release_approval"]}}
        om = {"exports": {"capabilities": ["code_contribution"], "authorities": []}}
        result = factory_operating_model_compatible(factory, om)
        self.assertFalse(result["compatible"])
        self.assertEqual(["security_evidence"], result["missingCapabilities"])
        self.assertEqual(["production_release_approval"], result["missingAuthorities"])

    def test_remote_workspace_rejects_safor_product_repository(self):
        binding = {
            "ownership": {"class": "HUMAN", "humanControlled": True},
            "projectWorkspace": {
                "type": "REMOTE_GIT", "provider": "GITHUB", "repository": "empishaj/SAFOR",
                "stableId": "1", "defaultBranch": "main", "capabilityEvidenceRefs": ["ev"]
            },
            "controlWorkspace": {
                "strategy": "REMOTE_SEPARATE_SAFOR_MEMORY", "repository": "empishaj/safor-memory",
                "stableId": "2", "capabilityEvidenceRefs": ["ev2"]
            },
        }
        result = validate_workspace_binding(
            binding,
            {
                "workspace.project.read","workspace.project.write","workspace.git.history.read",
                "workspace.git.branch.read","workspace.git.branch.write"
            },
            "empishaj/SAFOR",
        )
        self.assertFalse(result["valid"])
        self.assertIn("PROJECT_TARGET_IS_PRODUCT_OR_PACKAGE_SOURCE", result["errors"])

    def test_remote_workspace_rejects_package_source(self):
        binding = {
            "ownership": {"class": "HUMAN", "humanControlled": True},
            "projectWorkspace": {
                "type": "REMOTE_GIT", "provider": "GITHUB", "repository": "vendor/paid-packages",
                "stableId": "1", "defaultBranch": "main", "capabilityEvidenceRefs": ["ev"]
            },
            "controlWorkspace": {
                "strategy": "REMOTE_SEPARATE_SAFOR_MEMORY", "repository": "human/safor-memory",
                "stableId": "2", "capabilityEvidenceRefs": ["ev2"]
            },
        }
        result = validate_workspace_binding(
            binding,
            REMOTE_CAPS,
            "empishaj/SAFOR",
            {"vendor/paid-packages"},
        )
        self.assertFalse(result["valid"])

    def test_local_workspace_requires_git_capabilities(self):
        binding = {
            "ownership": {"class": "HUMAN", "humanControlled": True},
            "projectWorkspace": {
                "type": "LOCAL_GIT", "path": "/home/human/project", "gitRoot": "/home/human/project",
                "headCommit": "abc", "capabilityEvidenceRefs": ["ev"]
            },
            "controlWorkspace": {
                "strategy": "LOCAL_MASTER_CONTROL_ROOT", "root": ".safor/", "masterOnly": True, "gitTracked": True
            },
        }
        result = validate_workspace_binding(binding, {"workspace.local.read", "workspace.local.write"}, "empishaj/SAFOR")
        self.assertFalse(result["valid"])
        self.assertTrue(any(x.startswith("LOCAL_GIT_CAPABILITIES_MISSING") for x in result["errors"]))

    def test_local_workspace_validates_with_full_capabilities(self):
        binding = {
            "ownership": {"class": "HUMAN", "humanControlled": True},
            "projectWorkspace": {
                "type": "LOCAL_GIT", "path": "/home/human/project", "gitRoot": "/home/human/project",
                "headCommit": "abc", "capabilityEvidenceRefs": ["ev"]
            },
            "controlWorkspace": {
                "strategy": "LOCAL_MASTER_CONTROL_ROOT", "root": ".safor/", "masterOnly": True, "gitTracked": True
            },
        }
        result = validate_workspace_binding(binding, LOCAL_CAPS, "empishaj/SAFOR")
        self.assertTrue(result["valid"])

    def test_local_control_root_must_be_master_only_safor(self):
        binding = {
            "ownership": {"class": "HUMAN", "humanControlled": True},
            "projectWorkspace": {
                "type": "LOCAL_GIT", "path": "/home/human/project", "gitRoot": "/home/human/project",
                "headCommit": "abc", "capabilityEvidenceRefs": ["ev"]
            },
            "controlWorkspace": {
                "strategy": "LOCAL_MASTER_CONTROL_ROOT", "root": "control/", "masterOnly": False, "gitTracked": True
            },
        }
        result = validate_workspace_binding(binding, LOCAL_CAPS, "empishaj/SAFOR")
        self.assertFalse(result["valid"])
        self.assertIn("LOCAL_CONTROL_ROOT_INVALID", result["errors"])


REMOTE_CAPS = {
    "workspace.project.read","workspace.project.write","workspace.git.history.read",
    "workspace.git.branch.read","workspace.git.branch.write"
}

LOCAL_CAPS = {
    "workspace.local.read","workspace.local.write","workspace.git.repository.read",
    "workspace.git.history.read","workspace.git.branch.read","workspace.git.branch.write",
    "workspace.git.commit.write"
}


if __name__ == "__main__":
    unittest.main()
