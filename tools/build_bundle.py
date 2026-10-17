#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULE_PATHS = {
    "kernel": "v0.11.0/SAFOR-MASTER.json",
    "initialization": "v0.11.0/initialization-model.json",
    "interaction": "v0.10.0/interaction-model.json",
    "humanDecisionGate": "v0.10.0/human-decision-gate-model.json",
    "selfHealing": "v0.11.0/self-healing-model.json",
    "moduleSelfHealing": "v0.11.0/module-self-healing-model.json",
    "agentWorkspace": "v0.10.0/agent-workspace-model.json",
    "agentJobContract": "v0.10.0/agent-job-contract-model.json",
    "multiAgentScheduler": "v0.10.0/multi-agent-scheduler-model.json",
    "repositoryPolicy": "v0.10.0/repository-policy.json",
    "packageRegistry": "v0.10.0/package-registry.json",
    "providerGithub": "v0.10.0/providers/github/0.5.0/package.json",
    "providerGitlab": "v0.10.0/providers/gitlab/0.5.0/package.json",
    "operatingModelSaas": "v0.10.0/packages/operating-models/saas-engineering/1.4.0/package.json",
    "operatingModelBook": "v0.10.0/packages/operating-models/book-authoring/0.5.0/package.json",
    "factorySoftwareWebsite": "v0.10.0/packages/factories/software-delivery/1.4.0/package.json",
    "factoryBook": "v0.10.0/packages/factories/book-production/0.5.0/package.json",
    "schemaPackageManifest": "v0.10.0/schemas/package-manifest.schema.json",
    "schemaControlState": "v0.10.0/schemas/control-state.schema.json",
    "schemaValueStreamState": "v0.10.0/schemas/value-stream-state.schema.json",
    "schemaExecutionState": "v0.10.0/schemas/execution-state.schema.json",
    "schemaWorkItem": "v0.10.0/schemas/work-item.schema.json",
    "schemaProject": "v0.10.0/schemas/project.schema.json",
    "schemaBindings": "v0.10.0/schemas/bindings.schema.json",
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
    "schemaEvent": "v0.11.0/schemas/event.schema.json",
    "schemaPredicate": "v0.11.0/schemas/predicate.schema.json",
    "schemaTransition": "v0.11.0/schemas/transition.schema.json",
    "schemaEffectIntent": "v0.11.0/schemas/effect-intent.schema.json",
    "schemaTransitionRecord": "v0.11.0/schemas/transition-record.schema.json",
    "schemaStateSnapshot": "v0.11.0/schemas/state-snapshot.schema.json",
    "conformance": "v0.11.0/conformance.json",
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
    "deterministic-control-model.json": "deterministicControl",
    "event-model.json": "eventModel",
    "predicate-registry.json": "predicateRegistry",
    "transition-registry.json": "transitionRegistry",
    "effect-model.json": "effectModel",
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
    "providers/github/0.5.0/package.json": "providerGithub",
    "providers/gitlab/0.5.0/package.json": "providerGitlab",
    "packages/operating-models/saas-engineering/1.4.0/package.json": "operatingModelSaas",
    "packages/operating-models/book-authoring/0.5.0/package.json": "operatingModelBook",
    "packages/factories/software-delivery/1.4.0/package.json": "factorySoftwareWebsite",
    "packages/factories/book-production/0.5.0/package.json": "factoryBook",
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
    for key, module in modules.items():
        module["selfHealingProfileId"] = recovery_profiles[key]["profileId"]
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "format": "SAFOR_MASTER_COMPLETE_SINGLE_FILE",
        "schemaVersion": "0.11.0",
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
                "VERIFY_MODULE_RECOVERY_BASELINE",
                "VERIFY_DETERMINISTIC_CONTROL_BASELINE",
                "SELECT_PROVIDER",
                "VERIFY_PROVIDER_READ_WRITE_ACCESS",
                "SELECT_OWNER_NAMESPACE",
                "VERIFY_OWNER_ACCESS",
                "VERIFY_REQUIRED_SAFOR_MEMORY",
                "SELECT_CREATION_TYPE",
                "SELECT_PROJECT_MODE",
                "SELECT_OR_DEFINE_PROJECT",
                "BIND_REQUIRED_SAFOR_MEMORY",
                "RESOLVE_CREATION_PROFILE_BINDINGS",
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
            "humanCognitiveLoadRule": "Use the embedded phase-aware HUMAN Cognitive Load Policy: high load is acceptable for non-derivable Discovery knowledge, then reduce routine HUMAN load after planning; derive/reuse before asking.",
            "humanDecisionGateRule": "Every HUMAN question or approval passes the embedded Decision Gate. Deterministic internal orchestration and unchanged prior approvals must not be delegated back to the HUMAN.",
            "humanTerminalMenuRule": "Every SAFOR-generated HUMAN-facing response validates against the embedded HUMAN response schema, contains exactly one interaction menu as the final rendered SAFOR-visible element, and stops rendering immediately after that menu. Menu presence does not itself imply a HUMAN decision.",
            "deterministicControlRule": "Within the explicit 0.11 rc.1 executable transition slice, external HUMAN/AGENT/PROVIDER observations enter as typed events and only the pure embedded deterministic control kernel may materialize authoritative state transitions. External mutations are emitted as effect intents and completion requires later authoritative provider evidence.",
            "selfHealingRule": "Use the embedded conservative self-healing model.",
            "moduleSelfHealingRule": "Every embedded module must resolve to exactly one embedded recovery profile. Repairs are constrained by module authority/repairability, failure-class policy, active authority and actual provider rights.",
            "agentWorkspaceRule": "For AGENT actors, persist identity once and dispatch/receive jobs through the embedded repository-native Agent Workspace Protocol; copied job prompts are not authoritative.",
            "canonicalAgentJobRule": "Every AGENT dispatch uses the embedded canonical Agent Job Contract with explicit package/sequence lineage, MASTER provenance, role, versioned skills, immutable inputs, granular authorization, Git workspace, fixed return routes, verification contract and a provider-readback HUMAN job Markdown projection.",
            "multiAgentSchedulerRule": "Dispatch AGENT work only through the embedded conflict-aware scheduler: atomic READY work, explicit capacity, immutable read inputs, conflict-free resource leases and dedicated job branches.",
            "humanReadableAgentResultRule": "Every agent job persists machine-readable JSON plus a Git-persisted HUMAN-readable Markdown result; mutating jobs also provide provider-verifiable Git commit/path traceability.",
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
    parser.add_argument("--check", action="store_true", help="Fail if committed bundle differs from a reproducible build.")
    args = parser.parse_args()

    built = build_bundle()
    version = built["bundleVersion"]
    latest_output = ROOT / "SAFOR-MASTER-COMPLETE.json"
    versioned_output = ROOT / f"SAFOR-MASTER-COMPLETE-v{version}.json"

    if args.check:
        expected = canonical(built)
        for output in (latest_output, versioned_output):
            committed = json.loads(output.read_text(encoding="utf-8"))
            if canonical(committed) != expected:
                print(f"SAFOR bundle reproducibility: FAIL ({output.name})")
                print("Run: python tools/build_bundle.py")
                raise SystemExit(1)
        print("SAFOR bundle reproducibility: PASS")
        return

    payload = json.dumps(built, indent=2, ensure_ascii=False) + "\n"
    latest_output.write_text(payload, encoding="utf-8")
    versioned_output.write_text(payload, encoding="utf-8")
    print(f"Wrote {latest_output}")
    print(f"Wrote {versioned_output}")
    print(f"Embedded modules: {len(built['embeddedModules'])}")

if __name__ == "__main__":
    main()
