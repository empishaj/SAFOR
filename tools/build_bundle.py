#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULE_PATHS = {
    "kernel": "v0.4.0/SAFOR-MASTER.json",
    "initialization": "v0.4.0/initialization-model.json",
    "interaction": "v0.4.0/interaction-model.json",
    "selfHealing": "v0.4.0/self-healing-model.json",
    "repositoryPolicy": "v0.4.0/repository-policy.json",
    "packageRegistry": "v0.4.0/package-registry.json",
    "providerGithub": "v0.4.0/providers/github/0.1.0/package.json",
    "providerGitlab": "v0.4.0/providers/gitlab/0.1.0/package.json",
    "operatingModelSaas": "v0.4.0/packages/operating-models/saas-engineering/1.0.0/package.json",
    "operatingModelBook": "v0.4.0/packages/operating-models/book-authoring/0.1.0/package.json",
    "factorySoftwareWebsite": "v0.4.0/packages/factories/software-delivery/1.0.0/package.json",
    "factoryBook": "v0.4.0/packages/factories/book-production/0.1.0/package.json",
    "schemaPackageManifest": "v0.4.0/schemas/package-manifest.schema.json",
    "schemaControlState": "v0.4.0/schemas/control-state.schema.json",
    "schemaValueStreamState": "v0.4.0/schemas/value-stream-state.schema.json",
    "schemaExecutionState": "v0.4.0/schemas/execution-state.schema.json",
    "schemaWorkItem": "v0.4.0/schemas/work-item.schema.json",
    "schemaProject": "v0.4.0/schemas/project.schema.json",
    "schemaBindings": "v0.4.0/schemas/bindings.schema.json",
    "schemaDecisionRecord": "v0.4.0/schemas/decision-record.schema.json",
    "schemaEvidenceRecord": "v0.4.0/schemas/evidence-record.schema.json",
    "schemaInteractionMenu": "v0.4.0/schemas/interaction-menu.schema.json",
    "schemaSelfHealingRecord": "v0.4.0/schemas/self-healing-record.schema.json",
    "conformance": "v0.4.0/conformance.json",
}

REFERENCE_RESOLUTION = {
    "initialization-model.json": "initialization",
    "interaction-model.json": "interaction",
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
    "schemas/decision-record.schema.json": "schemaDecisionRecord",
    "schemas/evidence-record.schema.json": "schemaEvidenceRecord",
    "schemas/interaction-menu.schema.json": "schemaInteractionMenu",
    "schemas/self-healing-record.schema.json": "schemaSelfHealingRecord",
    "providers/github/0.1.0/package.json": "providerGithub",
    "providers/gitlab/0.1.0/package.json": "providerGitlab",
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
        "schemaVersion": "0.4.0",
        "bundleVersion": version,
        "definitionId": "safor-master-complete",
        "productName": "SAFOR",
        "productExpansion": "Systemic AI Factory Orchestration Runtime",
        "purpose": "Self-contained SAFOR MASTER distribution for direct upload into a compatible chat.",
        "entrypoint": "embeddedModules.kernel.content",
        "distributionMode": "SELF_CONTAINED_SINGLE_FILE",
        "runtimeContract": {
            "moduleResolutionOrder": ["EMBEDDED_MODULES", "CANONICAL_REPOSITORY_FALLBACK"],
            "embeddedModulesAuthoritativeForBootstrap": True,
            "canonicalRepository": "empishaj/SAFOR",
            "canonicalBranch": "main",
            "absoluteRuntimePrerequisite": {
                "repositoryPattern": "{selectedOwner}/safor-memory",
                "mustPreExist": True,
                "mustBeReadable": True,
                "mustBeWritable": True,
                "autoCreate": False,
                "onFailure": "STOP",
            },
            "initializationOrder": [
                "SELECT_PROVIDER",
                "VERIFY_PROVIDER_READ_WRITE_ACCESS",
                "SELECT_OWNER_NAMESPACE",
                "VERIFY_OWNER_ACCESS",
                "VERIFY_REQUIRED_SAFOR_MEMORY",
                "SELECT_CREATION_TYPE",
                "SELECT_PROJECT_MODE",
                "SELECT_OR_DEFINE_PROJECT",
                "BIND_REQUIRED_SAFOR_MEMORY",
                "CONFIRM_CREATION_PROFILE_BINDINGS",
                "MATERIALIZE_PROJECT_CONTROL",
            ],
            "mandatoryCreationTypes": [
                {
                    "id": "SOFTWARE_WEBSITE",
                    "label": "Software / Website",
                    "factoryModule": "factorySoftwareWebsite",
                    "operatingModelModule": "operatingModelSaas",
                },
                {
                    "id": "BOOK",
                    "label": "Buch",
                    "factoryModule": "factoryBook",
                    "operatingModelModule": "operatingModelBook",
                },
            ],
            "factoryBindingRule": "Discovery, Planning and domain Evidence must always use the discoveryContract, planningContract and evidenceContract from the HUMAN-selected Factory. Cross-factory substitution is forbidden.",
            "chatUiRule": "Use chat-native UI only.",
            "humanCommunicationRule": "Use the embedded HUMAN buddy profile.",
            "selfHealingRule": "Use the embedded conservative self-healing model.",
        },
        "productRepository": {
            "repository": "empishaj/SAFOR",
            "role": "CANONICAL_SAFOR_PRODUCT_REPOSITORY",
            "independentFromHumanProjectContext": True,
        },
        "runtimeMemoryRepository": {
            "pattern": "{selectedOwner}/safor-memory",
            "role": "MANDATORY_HUMAN_PROJECT_CONTROL_MEMORY",
            "preExistingReadWriteRequired": True,
            "onFailure": "STOP",
        },
        "referenceResolution": REFERENCE_RESOLUTION,
        "integrityManifest": {
            key: {
                "sourcePath": module["sourcePath"],
                "sourceBlobSha": module["sourceBlobSha"],
            }
            for key, module in modules.items()
        },
        "embeddedModules": modules,
    }

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if committed bundle differs from a reproducible build.")
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
