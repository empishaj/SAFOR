#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.creation_type_contract import validate_creation_type_contract

BUNDLE_CONFIG = json.loads((ROOT / "v0.14.0/bundle-module-map.json").read_text(encoding="utf-8"))
MODULE_PATHS = BUNDLE_CONFIG["modulePaths"]
REFERENCE_RESOLUTION = BUNDLE_CONFIG["referenceResolution"]


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def load_module(key: str, rel_path: str):
    path = ROOT / rel_path
    raw = path.read_bytes()
    return {
        "key": key,
        "sourcePath": rel_path,
        "sourceBlobSha": git_blob_sha(raw),
        "content": json.loads(raw.decode("utf-8")),
    }


def build_bundle():
    modules = {key: load_module(key, path) for key, path in MODULE_PATHS.items()}
    recovery_profiles = {
        p["moduleKey"]: p
        for p in modules["moduleSelfHealing"]["content"]["moduleProfiles"]
    }
    module_keys = set(modules)
    if set(recovery_profiles) != module_keys:
        missing = sorted(module_keys - set(recovery_profiles))
        extra = sorted(set(recovery_profiles) - module_keys)
        raise ValueError(f"Module recovery coverage mismatch: missing={missing}, extra={extra}")

    forbidden_domain_keys = {
        "operatingModelSaas", "operatingModelBook",
        "factorySoftwareWebsite", "factoryBook",
    }
    leaked = sorted(forbidden_domain_keys & module_keys)
    if leaked:
        raise ValueError(f"Public Framework must not embed domain package modules: {leaked}")

    for key, module in modules.items():
        module["selfHealingProfileId"] = recovery_profiles[key]["profileId"]

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    bundle = {
        "format": "SAFOR_FRAMEWORK_SINGLE_FILE",
        "schemaVersion": "0.14.0",
        "bundleVersion": version,
        "definitionId": "safor-framework",
        "productName": "SAFOR",
        "productExpansion": "Systemic AI Factory Orchestration Runtime",
        "purpose": "Portable integrated SAFOR 0.14 JSON-governed Framework for ordinary compatible LLM chats, with free Website and licensed Software/SaaS and Book domain packages, HUMAN-GO-only subagents, typed Git responses and compact MASTER status.",
        "entrypoint": "embeddedModules.kernel.content",
        "distributionMode": "FRAMEWORK_PLUS_EXTERNAL_DOMAIN_PACKAGES",
        "runtimeContract": {
            "moduleResolutionOrder": [
                "EMBEDDED_FRAMEWORK_MODULES",
                "DOMAIN_DISTRIBUTION_EMBEDDED_DEFAULTS_WHEN_PRESENT",
                "EXTERNAL_DOMAIN_PACKAGE_REPLACEMENT_WHEN_REQUESTED",
            ],
            "embeddedModulesAuthoritativeForFrameworkBootstrap": True,
            "canonicalRepository": "empishaj/SAFOR",
            "canonicalBranch": "main",
            "executionEnvironment": {
                "primaryMode": "DECLARATIVE_LLM_CHAT",
                "customerInstalledRuntimeRequired": False,
                "requiredCustomerInstallation": "NONE",
                "referenceRuntimeRole": "OPTIONAL_VALIDATION_AND_HOST_INTEGRATION",
                "missingReferenceRuntimeBlocksNormalChatUse": False,
            },
            "domainPackagePolicy": {
                "artifactFormat": "SAFOR_DOMAIN_PACKAGE",
                "embeddedDomainPackageContent": False,
                "freePublicSourceClass": "PUBLIC_CANONICAL_REPOSITORY",
                "paidPublicResolutionForbidden": True,
                "paidRequiresVerifiedEntitlement": True,
                "accessEvaluatedPerSelectedPackage": True,
                "independentFactoryOverrideAllowed": True,
                "independentOperatingModelOverrideAllowed": True,
                "mixedFreeAndPaidPairAllowed": True,
                "creationProfileAccessPolicyEnforced": True,
                "softwareSaasRequiresPaidFactoryAndOperatingModel": True,
                "strictEntitlementVerificationRequired": True,
                "entitledSourceDeliveryEvidenceRequired": True,
                "deliveryDigestBindingRequired": True,
                "entitlementEvidenceExternal": True,
                "declaredContractDigestRequired": True,
                "compatibilityDecisionRequiredBeforeBinding": True,
            },
            "initializationOrder": [
                "VERIFY_MODULE_RECOVERY_BASELINE",
                "VERIFY_DETERMINISTIC_CONTROL_BASELINE",
                "SELECT_CREATION_TYPE",
                "RESOLVE_PACKAGE_SELECTION_PROFILE",
                "RESOLVE_SELECTED_FACTORY_AND_OPERATING_MODEL_ACCESS",
                "VERIFY_PACKAGE_INTEGRITY_AND_ACCESS",
                "VERIFY_FACTORY_OPERATING_MODEL_COMPATIBILITY",
                "MATERIALIZE_PACKAGE_SELECTION_AND_COMPATIBILITY_DECISION",
                "SELECT_PROJECT_WORKSPACE_TYPE",
                "VERIFY_PROJECT_WORKSPACE_CAPABILITIES",
                "SELECT_OR_DEFINE_HUMAN_PROJECT",
                "BIND_CONTROL_WORKSPACE",
                "MATERIALIZE_PACKAGE_AND_WORKSPACE_BINDINGS",
                "APPROVE_AND_MATERIALIZE_PROJECT",
            ],
            "domainFrameworkDistributionPolicy": {
                "containerFormat": "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION",
                "profileCatalog": "v0.14.0/domain-framework-profiles.json",
                "domainPreselectedByDistribution": True,
                "embeddedDefaultFactoryAndOperatingModel": True,
                "creationTypeQuestionSuppressedForDomainDistribution": True,
                "factoryReplacementAllowed": True,
                "operatingModelReplacementAllowed": True,
                "replacementRequiresSameDomain": True,
                "replacementRequiresBidirectionalCompatibility": True,
                "replacementRequiresPackageFamilyCompatibility": True,
                "crossDomainPairForbidden": True,
                "publicDistributions": [
                    "SAFOR-FRAMEWORK-WEBSITE.json",
                    "SAFOR-FRAMEWORK-SAAS.json",
                    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
                ],
                "publicTestEvaluationDistributions": [
                    "SAFOR-FRAMEWORK-SAAS.json",
                    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
                ],
                "commercialProductionDistributions": [
                    "SAFOR-FRAMEWORK-SAAS.json",
                    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
                ],
                "publicTestBytesDoNotDefineCommercialProductionSource": True,
            },
            "creationProfiles": [
                {
                    "id": "WEBSITE",
                    "label": "Website",
                    "defaultFactoryPackageId": "safor.factory.website-delivery",
                    "defaultOperatingModelPackageId": "safor.om.website-team",
                    "selectedPackageAccessPolicy": "ANY_COMPATIBLE_ACCESS",
                    "defaultAccess": "FREE_PUBLIC",
                    "independentOverridesAllowed": True,
                },
                {
                    "id": "SOFTWARE_SAAS",
                    "label": "Software / SaaS",
                    "defaultFactoryPackageId": "safor.factory.software-delivery",
                    "defaultOperatingModelPackageId": "safor.om.saas-engineering",
                    "selectedPackageAccessPolicy": "BOTH_PAID_ENTITLEMENT_REQUIRED",
                    "defaultAccess": "PAID_ENTITLEMENT_REQUIRED",
                    "independentOverridesAllowed": True,
                },
                {
                    "id": "BOOK",
                    "label": "Buch",
                    "defaultFactoryPackageId": "safor.factory.book-production",
                    "defaultOperatingModelPackageId": "safor.om.book-authoring",
                    "selectedPackageAccessPolicy": "BOTH_PAID_ENTITLEMENT_REQUIRED",
                    "defaultAccess": "PAID_ENTITLEMENT_REQUIRED",
                    "independentOverridesAllowed": True,
                },
            ],
            "projectWorkspaceRule": "All project-specific work stays in a HUMAN-selected REMOTE_GIT or LOCAL_GIT workspace. The canonical SAFOR repository and package sources are never project targets.",
            "controlWorkspaceRule": "REMOTE_GIT uses a HUMAN-controlled separate safor-memory; LOCAL_GIT uses a Git-tracked MASTER-only .safor/ control root.",
            "entitlementRule": "Commercial entitlement gates each selected paid package independently. Strict verification requires ACTIVE status, explicit evaluatedAt, subject match, trusted issuer/verifier and commercial-basis evidence. ENTITLED_PACKAGE_SOURCE additionally requires trusted time-valid delivery evidence bound to entitlement, package/version and artifact digest. SOFTWARE_SAAS still requires separate entitlements for Factory and Operating Model.",
            "factoryBindingRule": "Discovery, Planning and domain Evidence use only the selected, access-verified, digest-verified, same-domain and bidirectionally COMPATIBLE Factory/Operating Model pair. Domain distributions start from embedded defaults but Factory and Operating Model remain independently replaceable.",
            "commercialVerificationContextRule": "Pure package-access policy receives evaluatedAt, subjectRef, trustedIssuerIds, trustedEntitlementVerifierIds and trustedDeliveryVerifierIds explicitly; it never reads the wall clock or trusts identities declared only inside commercial records.",
            "chatUiRule": "Use chat-native UI only.",
            "platformHumanResponseGovernorRule": "The SAFOR platform owns HUMAN-visible response classification, compression, progressive disclosure and menus; Factory and Operating Model may supply domain facts only and cannot override presentation.",
            "humanCommunicationRule": "Use the embedded HUMAN buddy profile.",
            "humanCognitiveLoadRule": "Derive/reuse before asking; keep package mechanics and workspace internals behind Details unless HUMAN action is required.",
            "humanDecisionGateRule": "Every HUMAN question or approval passes the embedded Decision Gate.",
            "humanTerminalMenuRule": "Platform informational notices are content-only and non-interactive. Interactive checkpoints and genuine decisions contain exactly one terminal menu and render no SAFOR-visible content after it.",
            "deterministicControlRule": "Within the executable transition boundary, external observations enter as typed events and only the deterministic control kernel materializes authoritative state transitions.",
            "deterministicAcceptanceRule": "Work Item acceptance is evaluated only from an approved hash-valid Acceptance Contract and replayed typed Evidence/Review/Authority records.",
            "selfHealingRule": "Use conservative profile-constrained recovery; never invent entitlement, authority, evidence or workspace ownership.",
            "agentWorkspaceRule": "AGENT work uses persistent chat-bound identities and repository-native jobs; local .safor/ is never a worker write target.",
            "agentActivationRule": "Only explicit HUMAN GO in the bound agent chat may activate, claim or start a subagent job; Git and automation events never wake an agent.",
            "agentResponseRule": "Every dispatched job binds all five typed response templates and exact separate Git return targets before READY.",
            "agentChatRule": "Subagent chats render only minimal operational status; all substantive results, errors, questions and conflicts are versioned Git responses for MASTER.",
            "masterStatusIndexRule": "Routine status is read from compact versioned pointer indexes; global repository scans are forbidden in the normal path.",
            "multiAgentSchedulerRule": "Dispatch only atomic READY conflict-free work with explicit capacity, leases and isolated Git mutation scope.",
        },
        "productRepository": {
            "repository": "empishaj/SAFOR",
            "role": "PUBLIC_FRAMEWORK_AND_FREE_WEBSITE_PACKAGE_SOURCE",
            "independentFromHumanProjectContext": True,
            "projectTargetForbidden": True,
        },
        "controlWorkspacePolicy": {
            "REMOTE_GIT": {
                "strategy": "REMOTE_SEPARATE_SAFOR_MEMORY",
                "pattern": "{selectedOwner}/safor-memory",
                "humanControlled": True,
            },
            "LOCAL_GIT": {
                "strategy": "LOCAL_MASTER_CONTROL_ROOT",
                "root": ".safor/",
                "humanControlled": True,
                "masterOnly": True,
            },
        },
        "referenceResolution": REFERENCE_RESOLUTION,
        "integrityManifest": {
            key: {
                "sourcePath": module["sourcePath"],
                "sourceBlobSha": module["sourceBlobSha"],
                "selfHealingProfileId": module["selfHealingProfileId"],
            }
            for key, module in modules.items()
        },
        "embeddedModules": modules,
    }

    decision = validate_creation_type_contract(bundle)
    if not decision["valid"]:
        raise ValueError(f"Creation type contract invalid: {decision}")
    return bundle


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if committed Framework bundle differs from a reproducible build.")
    args = parser.parse_args()

    built = build_bundle()
    version = built["bundleVersion"]
    latest_output = ROOT / "SAFOR-FRAMEWORK.json"
    versioned_output = ROOT / f"SAFOR-FRAMEWORK-v{version}.json"

    if args.check:
        expected = canonical(built)
        for output in (latest_output, versioned_output):
            committed = json.loads(output.read_text(encoding="utf-8"))
            if canonical(committed) != expected:
                print(f"SAFOR Framework reproducibility: FAIL ({output.name})")
                print("Run: python tools/build_bundle.py")
                raise SystemExit(1)
        print("SAFOR Framework reproducibility: PASS")
        return

    payload = json.dumps(built, indent=2, ensure_ascii=False) + "\n"
    latest_output.write_text(payload, encoding="utf-8")
    versioned_output.write_text(payload, encoding="utf-8")
    print(f"Wrote {latest_output}")
    print(f"Wrote {versioned_output}")
    print(f"Embedded Framework modules: {len(built['embeddedModules'])}")


if __name__ == "__main__":
    main()
