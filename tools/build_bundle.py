#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULE_PATHS = {
    "kernel": "v0.13.0/SAFOR-MASTER.json",
    "initialization": "v0.13.0/initialization-model.json",
    "interaction": "v0.10.0/interaction-model.json",
    "humanDecisionGate": "v0.10.0/human-decision-gate-model.json",
    "selfHealing": "v0.13.0/self-healing-model.json",
    "moduleSelfHealing": "v0.13.0/module-self-healing-model.json",
    "agentWorkspace": "v0.10.0/agent-workspace-model.json",
    "agentJobContract": "v0.10.0/agent-job-contract-model.json",
    "multiAgentScheduler": "v0.10.0/multi-agent-scheduler-model.json",
    "repositoryPolicy": "v0.12.0/repository-policy.json",
    "packageRegistry": "v0.13.0/package-registry.json",
    "packageDistribution": "v0.13.0/package-distribution-model.json",
    "commercialEntitlement": "v0.13.0/commercial-entitlement-model.json",
    "workspaceModel": "v0.12.0/workspace-model.json",
    "packageCatalog": "v0.13.0/package-catalog.json",
    "providerGithub": "v0.10.0/providers/github/0.5.0/package.json",
    "providerGitlab": "v0.10.0/providers/gitlab/0.5.0/package.json",
    "schemaPackageManifest": "v0.10.0/schemas/package-manifest.schema.json",
    "schemaControlState": "v0.10.0/schemas/control-state.schema.json",
    "schemaValueStreamState": "v0.10.0/schemas/value-stream-state.schema.json",
    "schemaExecutionState": "v0.10.0/schemas/execution-state.schema.json",
    "schemaWorkItem": "v0.10.0/schemas/work-item.schema.json",
    "schemaProject": "v0.12.0/schemas/project.schema.json",
    "schemaBindings": "v0.13.0/schemas/bindings.schema.json",
    "schemaDecisionRecord": "v0.10.0/schemas/decision-record.schema.json",
    "schemaEvidenceRecord": "v0.10.0/schemas/evidence-record.schema.json",
    "schemaInteractionMenu": "v0.10.0/schemas/interaction-menu.schema.json",
    "schemaHumanResponse": "v0.10.0/schemas/human-response.schema.json",
    "schemaHumanCognitiveLoadPolicy": "v0.10.0/schemas/human-cognitive-load-policy.schema.json",
    "schemaHumanDecisionGate": "v0.10.0/schemas/human-decision-gate.schema.json",
    "schemaSelfHealingRecord": "v0.10.0/schemas/self-healing-record.schema.json",
    "schemaModuleRecoveryProfile": "v0.10.0/schemas/module-recovery-profile.schema.json",
    "schemaAgentRegistry": "v0.10.0/schemas/agent-registry.schema.json",
    "schemaAgentIdentity": "v0.10.0/schemas/agent-identity.schema.json",
    "schemaAgentInboxIndex": "v0.10.0/schemas/agent-inbox-index.schema.json",
    "schemaAgentState": "v0.10.0/schemas/agent-state.schema.json",
    "schemaAgentJob": "v0.10.0/schemas/agent-job.schema.json",
    "schemaAgentJobState": "v0.10.0/schemas/agent-job-state.schema.json",
    "schemaAgentResult": "v0.10.0/schemas/agent-result.schema.json",
    "schemaSchedulerState": "v0.10.0/schemas/scheduler-state.schema.json",
    "schemaDispatchWave": "v0.10.0/schemas/dispatch-wave.schema.json",
    "schemaResourceLease": "v0.10.0/schemas/resource-lease.schema.json",
    "deterministicControl": "v0.11.0/deterministic-control-model.json",
    "eventModel": "v0.11.0/event-model.json",
    "predicateRegistry": "v0.11.0/predicate-registry.json",
    "transitionRegistry": "v0.11.0/transition-registry.json",
    "effectModel": "v0.11.0/effect-model.json",
    "acceptanceModel": "v0.11.0/acceptance-model.json",
    "schemaEvent": "v0.11.0/schemas/event.schema.json",
    "schemaPredicate": "v0.11.0/schemas/predicate.schema.json",
    "schemaTransition": "v0.11.0/schemas/transition.schema.json",
    "schemaEffectIntent": "v0.11.0/schemas/effect-intent.schema.json",
    "schemaTransitionRecord": "v0.11.0/schemas/transition-record.schema.json",
    "schemaStateSnapshot": "v0.11.0/schemas/state-snapshot.schema.json",
    "schemaAcceptanceContract": "v0.11.0/schemas/acceptance-contract.schema.json",
    "schemaReviewDecision": "v0.11.0/schemas/review-decision.schema.json",
    "schemaAuthorityDecision": "v0.11.0/schemas/authority-decision.schema.json",
    "schemaPackageCatalog": "v0.13.0/schemas/package-catalog.schema.json",
    "schemaEntitlement": "v0.13.0/schemas/entitlement.schema.json",
    "schemaWorkspaceBinding": "v0.12.0/schemas/workspace-binding.schema.json",
    "conformance": "v0.13.0/conformance.json",
    "composablePackageModel": "v0.13.0/composable-package-model.json",
    "schemaDomainPackage": "v0.13.0/schemas/domain-package.schema.json",
    "schemaPackageSelection": "v0.13.0/schemas/package-selection.schema.json",
    "schemaPackageCompatibilityDecision": "v0.13.0/schemas/package-compatibility-decision.schema.json",
}

REFERENCE_RESOLUTION = {
    "initialization-model.json": "initialization",
    "interaction-model.json": "interaction",
    "human-decision-gate-model.json": "humanDecisionGate",
    "self-healing-model.json": "selfHealing",
    "module-self-healing-model.json": "moduleSelfHealing",
    "agent-workspace-model.json": "agentWorkspace",
    "agent-job-contract-model.json": "agentJobContract",
    "multi-agent-scheduler-model.json": "multiAgentScheduler",
    "repository-policy.json": "repositoryPolicy",
    "package-registry.json": "packageRegistry",
    "package-distribution-model.json": "packageDistribution",
    "commercial-entitlement-model.json": "commercialEntitlement",
    "workspace-model.json": "workspaceModel",
    "package-catalog.json": "packageCatalog",
    "deterministic-control-model.json": "deterministicControl",
    "event-model.json": "eventModel",
    "predicate-registry.json": "predicateRegistry",
    "transition-registry.json": "transitionRegistry",
    "effect-model.json": "effectModel",
    "acceptance-model.json": "acceptanceModel",
    "schemas/package-manifest.schema.json": "schemaPackageManifest",
    "schemas/control-state.schema.json": "schemaControlState",
    "schemas/value-stream-state.schema.json": "schemaValueStreamState",
    "schemas/execution-state.schema.json": "schemaExecutionState",
    "schemas/work-item.schema.json": "schemaWorkItem",
    "schemas/project.schema.json": "schemaProject",
    "schemas/bindings.schema.json": "schemaBindings",
    "schemas/decision-record.schema.json": "schemaDecisionRecord",
    "schemas/evidence-record.schema.json": "schemaEvidenceRecord",
    "schemas/interaction-menu.schema.json": "schemaInteractionMenu",
    "schemas/human-response.schema.json": "schemaHumanResponse",
    "schemas/human-cognitive-load-policy.schema.json": "schemaHumanCognitiveLoadPolicy",
    "schemas/human-decision-gate.schema.json": "schemaHumanDecisionGate",
    "schemas/self-healing-record.schema.json": "schemaSelfHealingRecord",
    "schemas/module-recovery-profile.schema.json": "schemaModuleRecoveryProfile",
    "schemas/agent-registry.schema.json": "schemaAgentRegistry",
    "schemas/agent-identity.schema.json": "schemaAgentIdentity",
    "schemas/agent-inbox-index.schema.json": "schemaAgentInboxIndex",
    "schemas/agent-state.schema.json": "schemaAgentState",
    "schemas/agent-job.schema.json": "schemaAgentJob",
    "schemas/agent-job-state.schema.json": "schemaAgentJobState",
    "schemas/agent-result.schema.json": "schemaAgentResult",
    "schemas/scheduler-state.schema.json": "schemaSchedulerState",
    "schemas/dispatch-wave.schema.json": "schemaDispatchWave",
    "schemas/resource-lease.schema.json": "schemaResourceLease",
    "schemas/event.schema.json": "schemaEvent",
    "schemas/predicate.schema.json": "schemaPredicate",
    "schemas/transition.schema.json": "schemaTransition",
    "schemas/effect-intent.schema.json": "schemaEffectIntent",
    "schemas/transition-record.schema.json": "schemaTransitionRecord",
    "schemas/state-snapshot.schema.json": "schemaStateSnapshot",
    "schemas/acceptance-contract.schema.json": "schemaAcceptanceContract",
    "schemas/review-decision.schema.json": "schemaReviewDecision",
    "schemas/authority-decision.schema.json": "schemaAuthorityDecision",
    "schemas/package-catalog.schema.json": "schemaPackageCatalog",
    "schemas/entitlement.schema.json": "schemaEntitlement",
    "schemas/workspace-binding.schema.json": "schemaWorkspaceBinding",
    "composable-package-model.json": "composablePackageModel",
    "schemas/domain-package.schema.json": "schemaDomainPackage",
    "schemas/package-selection.schema.json": "schemaPackageSelection",
    "schemas/package-compatibility-decision.schema.json": "schemaPackageCompatibilityDecision",
    "providers/github/0.5.0/package.json": "providerGithub",
    "providers/gitlab/0.5.0/package.json": "providerGitlab",
}


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
    return {
        "format": "SAFOR_FRAMEWORK_SINGLE_FILE",
        "schemaVersion": "0.13.0",
        "bundleVersion": version,
        "definitionId": "safor-framework",
        "productName": "SAFOR",
        "productExpansion": "Systemic AI Factory Orchestration Runtime",
        "purpose": "Public SAFOR Framework distribution. Factory and Operating Model are independently selectable, chat-loadable domain packages with per-package access, integrity and compatibility binding.",
        "entrypoint": "embeddedModules.kernel.content",
        "distributionMode": "FRAMEWORK_PLUS_EXTERNAL_DOMAIN_PACKAGES",
        "runtimeContract": {
            "moduleResolutionOrder": [
                "EMBEDDED_FRAMEWORK_MODULES",
                "EXTERNAL_DOMAIN_PACKAGE_RESOLUTION",
            ],
            "embeddedModulesAuthoritativeForFrameworkBootstrap": True,
            "canonicalRepository": "empishaj/SAFOR",
            "canonicalBranch": "main",
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
            "creationProfiles": [
                {
                    "id": "SOFTWARE_WEBSITE",
                    "label": "Software / Website",
                    "defaultFactoryPackageId": "safor.factory.software-delivery",
                    "defaultOperatingModelPackageId": "safor.om.saas-engineering",
                    "defaultAccess": "FREE_PUBLIC",
                    "independentOverridesAllowed": True,
                },
                {
                    "id": "BOOK",
                    "label": "Buch",
                    "defaultFactoryPackageId": "safor.factory.book-production",
                    "defaultOperatingModelPackageId": "safor.om.book-authoring",
                    "defaultAccess": "PAID_ENTITLEMENT_REQUIRED",
                    "independentOverridesAllowed": True,
                },
            ],
            "projectWorkspaceRule": "All project-specific work stays in a HUMAN-selected REMOTE_GIT or LOCAL_GIT workspace. The canonical SAFOR repository and package sources are never project targets.",
            "controlWorkspaceRule": "REMOTE_GIT uses a HUMAN-controlled separate safor-memory; LOCAL_GIT uses a Git-tracked MASTER-only .safor/ control root.",
            "entitlementRule": "Commercial entitlement gates each selected paid package independently. It remains external to the package JSON and never grants organizational authority, provider rights, execution mandate or project scope.",
            "factoryBindingRule": "Discovery, Planning and domain Evidence use only the independently selected, access-verified, digest-verified, COMPATIBLE and immutable-pinned Factory/Operating Model pair.",
            "chatUiRule": "Use chat-native UI only.",
            "humanCommunicationRule": "Use the embedded HUMAN buddy profile.",
            "humanCognitiveLoadRule": "Derive/reuse before asking; keep package mechanics and workspace internals behind Details unless HUMAN action is required.",
            "humanDecisionGateRule": "Every HUMAN question or approval passes the embedded Decision Gate.",
            "humanTerminalMenuRule": "Every SAFOR-generated HUMAN-facing response contains exactly one valid terminal interaction menu and renders no SAFOR-visible content after it.",
            "deterministicControlRule": "Within the executable transition boundary, external observations enter as typed events and only the deterministic control kernel materializes authoritative state transitions.",
            "deterministicAcceptanceRule": "Work Item acceptance is evaluated only from an approved hash-valid Acceptance Contract and replayed typed Evidence/Review/Authority records.",
            "selfHealingRule": "Use conservative profile-constrained recovery; never invent entitlement, authority, evidence or workspace ownership.",
            "agentWorkspaceRule": "AGENT work uses persistent identities and repository-native jobs; local .safor/ is never a worker write target.",
            "multiAgentSchedulerRule": "Dispatch only atomic READY conflict-free work with explicit capacity, leases and isolated Git mutation scope.",
        },
        "productRepository": {
            "repository": "empishaj/SAFOR",
            "role": "PUBLIC_FRAMEWORK_AND_FREE_PACKAGE_SOURCE",
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
