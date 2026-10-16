#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULE_PATHS = {
    "kernel": "v0.5.0/SAFOR-MASTER.json",
    "initialization": "v0.5.0/initialization-model.json",
    "interaction": "v0.5.0/interaction-model.json",
    "memoryModel": "v0.5.0/memory-model.json",
    "selfHealing": "v0.5.0/self-healing-model.json",
    "repositoryPolicy": "v0.5.0/repository-policy.json",
    "packageRegistry": "v0.5.0/package-registry.json",
    "providerGithub": "v0.5.0/providers/github/0.1.0/package.json",
    "providerGitlab": "v0.5.0/providers/gitlab/0.1.0/package.json",
    "providerGenericGit": "v0.5.0/providers/git-generic/0.1.0/package.json",
    "providerPlastic": "v0.5.0/providers/plastic-scm/0.1.0/package.json",
    "memoryVersionedRepository": "v0.5.0/memory-providers/versioned-repository/1.0.0/package.json",
    "memoryHostFilesystem": "v0.5.0/memory-providers/host-filesystem/0.1.0/package.json",
    "operatingModelSaas": "v0.5.0/packages/operating-models/saas-engineering/1.0.0/package.json",
    "operatingModelBook": "v0.5.0/packages/operating-models/book-authoring/0.1.0/package.json",
    "factorySoftwareWebsite": "v0.5.0/packages/factories/software-delivery/1.0.0/package.json",
    "factoryBook": "v0.5.0/packages/factories/book-production/0.1.0/package.json",
    "schemaPackageManifest": "v0.5.0/schemas/package-manifest.schema.json",
    "schemaControlState": "v0.5.0/schemas/control-state.schema.json",
    "schemaValueStreamState": "v0.5.0/schemas/value-stream-state.schema.json",
    "schemaExecutionState": "v0.5.0/schemas/execution-state.schema.json",
    "schemaWorkItem": "v0.5.0/schemas/work-item.schema.json",
    "schemaProject": "v0.5.0/schemas/project.schema.json",
    "schemaBindings": "v0.5.0/schemas/bindings.schema.json",
    "schemaMemoryBinding": "v0.5.0/schemas/memory-binding.schema.json",
    "schemaSessionRecord": "v0.5.0/schemas/session-record.schema.json",
    "schemaOutputRecord": "v0.5.0/schemas/output-record.schema.json",
    "schemaDecisionRecord": "v0.5.0/schemas/decision-record.schema.json",
    "schemaEvidenceRecord": "v0.5.0/schemas/evidence-record.schema.json",
    "schemaInteractionMenu": "v0.5.0/schemas/interaction-menu.schema.json",
    "schemaSelfHealingRecord": "v0.5.0/schemas/self-healing-record.schema.json",
    "conformance": "v0.5.0/conformance.json",
}

REFERENCE_RESOLUTION = {
    "initialization-model.json": "initialization",
    "interaction-model.json": "interaction",
    "memory-model.json": "memoryModel",
    "self-healing-model.json": "selfHealing",
    "repository-policy.json": "repositoryPolicy",
    "package-registry.json": "packageRegistry",
    "schemas/package-manifest.schema.json": "schemaPackageManifest",
    "schemas/control-state.schema.json": "schemaControlState",
    "schemas/value-stream-state.schema.json": "schemaValueStreamState",
    "schemas/execution-state.schema.json": "schemaExecutionState",
    "schemas/work-item.schema.json": "schemaWorkItem",
    "schemas/project.schema.json": "schemaProject",
    "schemas/bindings.schema.json": "schemaBindings",
    "schemas/memory-binding.schema.json": "schemaMemoryBinding",
    "schemas/session-record.schema.json": "schemaSessionRecord",
    "schemas/output-record.schema.json": "schemaOutputRecord",
    "schemas/decision-record.schema.json": "schemaDecisionRecord",
    "schemas/evidence-record.schema.json": "schemaEvidenceRecord",
    "schemas/interaction-menu.schema.json": "schemaInteractionMenu",
    "schemas/self-healing-record.schema.json": "schemaSelfHealingRecord",
    "providers/github/0.1.0/package.json": "providerGithub",
    "providers/gitlab/0.1.0/package.json": "providerGitlab",
    "providers/git-generic/0.1.0/package.json": "providerGenericGit",
    "providers/plastic-scm/0.1.0/package.json": "providerPlastic",
    "memory-providers/versioned-repository/1.0.0/package.json": "memoryVersionedRepository",
    "memory-providers/host-filesystem/0.1.0/package.json": "memoryHostFilesystem",
    "packages/operating-models/saas-engineering/1.0.0/package.json": "operatingModelSaas",
    "packages/operating-models/book-authoring/0.1.0/package.json": "operatingModelBook",
    "packages/factories/software-delivery/1.0.0/package.json": "factorySoftwareWebsite",
    "packages/factories/book-production/0.1.0/package.json": "factoryBook",
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
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "format": "SAFOR_MASTER_COMPLETE_SINGLE_FILE",
        "schemaVersion": "0.5.0",
        "bundleVersion": version,
        "definitionId": "safor-master-complete",
        "productName": "SAFOR",
        "productExpansion": "Systemic AI Factory Orchestration Runtime",
        "purpose": "Self-contained SAFOR distribution with provider-neutral durable Memory, independent work-provider binding, multi-session collaboration and output provenance.",
        "entrypoint": "embeddedModules.kernel.content",
        "distributionMode": "SELF_CONTAINED_SINGLE_FILE",
        "runtimeContract": {
            "moduleResolutionOrder": ["EMBEDDED_MODULES", "CANONICAL_REPOSITORY_FALLBACK"],
            "embeddedModulesAuthoritativeForBootstrap": True,
            "canonicalRepository": "empishaj/SAFOR",
            "canonicalBranch": "main",
            "memoryRequirement": {
                "providerNeutral": True,
                "humanSelectionOrApprovalRequired": True,
                "mandatoryCapabilities": [
                    "memory.object.read",
                    "memory.object.write",
                    "memory.revision.read",
                    "memory.durability.prove",
                    "memory.resume.prove",
                ],
                "eligibleProviderTypes": ["VERSIONED_REPOSITORY", "HOST_FILESYSTEM", "CUSTOM"],
                "newLocationCreationRequiresExplicitHumanApproval": True,
                "onNoEligibleMemory": "STOP",
            },
            "collaboration": {
                "modes": ["PERSONAL", "SHARED_TEAM"],
                "sharedTeamRequires": ["memory.shared_access", "memory.compare_and_swap OR memory.lock"],
                "conflictOutcome": "RECONCILE_REQUIRED",
                "chatHistoryIsAuthoritative": False,
            },
            "initializationOrder": [
                "DISCOVER_MEMORY_PROVIDER_OPTIONS",
                "SELECT_MEMORY_PROVIDER",
                "VERIFY_MEMORY_PROVIDER",
                "SELECT_MEMORY_OWNER",
                "SELECT_COLLABORATION_MODE",
                "VERIFY_COLLABORATION_SAFETY",
                "BIND_AND_INITIALIZE_MEMORY_ROOT",
                "SELECT_CREATION_TYPE",
                "DISCOVER_AND_SELECT_WORK_PROVIDER",
                "VERIFY_WORK_PROVIDER",
                "SELECT_OR_DEFINE_PROJECT",
                "RESOLVE_AND_CONFIRM_PACKAGES",
                "MATERIALIZE_PROJECT_AND_REGISTER_SESSION",
            ],
            "mandatoryCreationTypes": [
                {"id": "SOFTWARE_WEBSITE", "label": "Software / Website", "factoryModule": "factorySoftwareWebsite", "operatingModelModule": "operatingModelSaas"},
                {"id": "BOOK", "label": "Buch", "factoryModule": "factoryBook", "operatingModelModule": "operatingModelBook"},
            ],
            "memoryAndWorkProviderIndependent": True,
            "factoryBindingRule": "Discovery, Planning and domain Evidence always use the HUMAN-selected Factory contracts.",
            "outputProvenanceRequired": True,
            "freshSessionResumeFromMemory": True,
            "chatUiRule": "Use chat-native UI only.",
            "selfHealingRule": "Use bounded conservative recovery; Memory conflicts reconcile before retry.",
        },
        "productRepository": {
            "repository": "empishaj/SAFOR",
            "role": "CANONICAL_SAFOR_PRODUCT_REPOSITORY",
            "independentFromHumanProjectContext": True,
        },
        "runtimeMemory": {
            "role": "HUMAN_OR_ORGANIZATION_CONTROLLED_AUTHORITATIVE_PROJECT_MEMORY",
            "logicalOwner": "SAFOR_PROJECT",
            "physicalOwner": "HUMAN_OR_ORGANIZATION",
            "providerNeutral": True,
        },
        "referenceResolution": REFERENCE_RESOLUTION,
        "integrityManifest": {
            key: {"sourcePath": module["sourcePath"], "sourceBlobSha": module["sourceBlobSha"]}
            for key, module in modules.items()
        },
        "embeddedModules": modules,
    }

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    built = build_bundle()
    output = ROOT / "SAFOR-MASTER-COMPLETE.json"
    if args.check:
        committed = json.loads(output.read_text(encoding="utf-8"))
        if canonical(committed) != canonical(built):
            print("SAFOR bundle reproducibility: FAIL")
            print("Run: python tools/build_bundle.py")
            raise SystemExit(1)
        print("SAFOR bundle reproducibility: PASS")
        return
    output.write_text(json.dumps(built, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Embedded modules: {len(built['embeddedModules'])}")

if __name__ == "__main__":
    main()
