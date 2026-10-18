#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ["WEBSITE", "SOFTWARE_SAAS", "BOOK"]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def collect_refs(value: Any, path="$"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}/{key}"
            if (key.endswith("Ref") or key.endswith("Refs") or key.endswith("CatalogRef")):
                values = child if isinstance(child, list) else [child]
                for item in values:
                    if isinstance(item, str) and ".json" in item:
                        found.append((child_path, item))
            found.extend(collect_refs(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(collect_refs(child, f"{path}/{index}"))
    return found


def validate():
    errors = []
    vocab = load("v0.14.0/creation-type-vocabulary.json")
    if vocab.get("activeCreationTypes") != ACTIVE:
        errors.append("canonical Creation Type vocabulary mismatch")
    project = load("v0.14.0/schemas/project.schema.json")
    if project.get("properties", {}).get("creationType", {}).get("enum") != ACTIVE:
        errors.append("project schema Creation Types mismatch")
    profiles = load("v0.14.0/domain-framework-profiles.json").get("profiles", [])
    profile_types = [item.get("creationType") for item in profiles]
    if sorted(profile_types) != sorted(ACTIVE):
        errors.append(f"domain profile Creation Types mismatch: {profile_types}")

    kernel = load("v0.14.0/SAFOR-MASTER.json")
    expected_protocols = {
        "agentActivationProtocol": ("modelRef", "agent-activation-model.json"),
        "agentChatProtocol": ("modelRef", "agent-communication-model.json"),
        "masterStatusProtocol": ("modelRef", "master-status-model.json"),
        "agentResponseProtocol": ("modelRef", "agent-response-contract-model.json"),
    }
    for protocol, (field, expected) in expected_protocols.items():
        if kernel.get(protocol, {}).get(field) != expected:
            errors.append(f"{protocol}.{field} does not resolve to {expected}")

    bundle_map = load("v0.14.0/bundle-module-map.json")
    resolution = bundle_map.get("referenceResolution", {})
    module_paths = set(bundle_map.get("modulePaths", {}).values())
    allowed_dynamic = ("BOUND_", "PROJECT_", "CURRENT_", "ACTIVE_", "embeddedModules.")
    for source_name, document in (("kernel", kernel), ("initialization", load("v0.14.0/initialization-model.json"))):
        for pointer, ref in collect_refs(document):
            base = ref.split("#", 1)[0]
            if base.startswith(allowed_dynamic):
                continue
            candidates = {base, Path(base).name}
            if not any(candidate in resolution for candidate in candidates) and base not in module_paths:
                errors.append(f"unresolved executable ref {source_name}{pointer}={ref}")

    invariants = kernel.get("invariants", [])
    statuses = {"ACTIVE", "SUPERSEDED", "LEGACY_ONLY"}
    for invariant in invariants:
        if invariant.get("status") not in statuses:
            errors.append(f"invariant {invariant.get('id')} has no valid status")
        if invariant.get("status") == "SUPERSEDED" and not invariant.get("supersededBy"):
            errors.append(f"superseded invariant {invariant.get('id')} has no supersededBy")
    active_rules = "\n".join(i.get("rule", "") for i in invariants if i.get("status") == "ACTIVE")
    for forbidden in ("SOFTWARE_WEBSITE or BOOK", "HUMAN, automation or host-supported activation", "Every SAFOR-generated HUMAN-facing response MUST end"):
        if forbidden in active_rules:
            errors.append(f"active invariant contains legacy contract: {forbidden}")

    conformance = load("v0.14.0/conformance.json").get("assertions", [])
    conformance_by_id = {item.get("id"): item for item in conformance}
    conformance_statuses = {"ACTIVE", "SUPERSEDED", "LEGACY_ONLY"}
    for assertion in conformance:
        aid = assertion.get("id")
        status = assertion.get("status")
        if status not in conformance_statuses:
            errors.append(f"conformance assertion {aid} has no valid status")
        if status == "SUPERSEDED":
            successors = assertion.get("supersededBy")
            if not isinstance(successors, list) or not successors:
                errors.append(f"superseded conformance assertion {aid} has no supersededBy")
                continue
            for successor in successors:
                target = conformance_by_id.get(successor)
                if target is None:
                    errors.append(f"conformance assertion {aid} points to missing successor {successor}")
                elif target.get("status") != "ACTIVE":
                    errors.append(f"conformance successor {successor} for {aid} is not ACTIVE")
    legacy_conformance = {
        "CF-046": {"CF-RC4-001", "CF-RC4-002"},
        "CF-047": {"CF-RC4-001", "CF-RC4-002"},
        "CF-048": {"CF-RC4-001", "CF-RC4-002"},
        "CF-064": {"CF-270", "CF-271"},
        "CF-154": {"CF-267", "CF-RC4-003"},
        "CF-156": {"CF-267", "CF-RC4-003"},
        "CF-159": {"CF-267", "CF-RC4-003"},
        "CF-195": {"CF-229", "CF-231", "CF-232"},
    }
    for legacy_id, expected_successors in legacy_conformance.items():
        item = conformance_by_id.get(legacy_id)
        if not item or item.get("status") != "SUPERSEDED":
            errors.append(f"legacy conformance assertion {legacy_id} is not SUPERSEDED")
            continue
        if set(item.get("supersededBy") or ()) != expected_successors:
            errors.append(f"legacy conformance assertion {legacy_id} successor set mismatch")
    for active_id in ("CF-RC4-001", "CF-RC4-002", "CF-RC4-003", "CF-RC4-004", "CF-267", "CF-270", "CF-271", "CF-229", "CF-231", "CF-232"):
        if conformance_by_id.get(active_id, {}).get("status") != "ACTIVE":
            errors.append(f"current conformance assertion {active_id} is not ACTIVE")
    if conformance_by_id.get("CF-RC4-001", {}).get("applicability", {}).get("workspaceType") != ["REMOTE_GIT"]:
        errors.append("REMOTE_GIT conformance applicability mismatch")
    if conformance_by_id.get("CF-RC4-002", {}).get("applicability", {}).get("workspaceType") != ["LOCAL_GIT"]:
        errors.append("LOCAL_GIT conformance applicability mismatch")

    policy = load("v0.14.0/repository-policy.json").get("controlWorkspacePolicy", {})
    if policy.get("discriminator") != "PROJECT_WORKSPACE_TYPE":
        errors.append("control workspace policy has no discriminator")
    if policy.get("LOCAL_GIT", {}).get("remoteMemoryRequired") is not False:
        errors.append("LOCAL_GIT still requires remote memory")
    if policy.get("REMOTE_GIT", {}).get("target") != "{selectedOwner}/safor-memory":
        errors.append("REMOTE_GIT memory target mismatch")

    initialization = load("v0.14.0/initialization-model.json")
    branch_contract = initialization.get("workspaceBranchContract", {})
    if branch_contract.get("discriminator") != "PROJECT_WORKSPACE_TYPE" or branch_contract.get("mutuallyExclusive") is not True:
        errors.append("initialization workspace branches are not mutually exclusive")
    if branch_contract.get("REMOTE_GIT", {}).get("remoteMemoryRequired") is not True:
        errors.append("REMOTE_GIT initialization does not require remote memory")
    if branch_contract.get("LOCAL_GIT", {}).get("remoteMemoryRequired") is not False:
        errors.append("LOCAL_GIT initialization still requires remote memory")
    if branch_contract.get("LOCAL_GIT", {}).get("controlWorkspace") != ".safor/":
        errors.append("LOCAL_GIT control workspace mismatch")
    required_behaviors = kernel.get("humanCommunication", {}).get("requiredBehavior", [])
    for behavior in required_behaviors:
        lower = behavior.lower()
        if "safor-memory" in lower and "remote_git" not in lower and "local_git" not in lower:
            errors.append(f"unscoped safor-memory HUMAN instruction remains: {behavior}")
    interaction = load("v0.14.0/interaction-model.json")
    init_exp = interaction.get("initializationExperience", {})
    if "Never surface REMOTE_GIT blockers in LOCAL_GIT" not in init_exp.get("workspaceBranchRule", ""):
        errors.append("interaction model lacks workspace-specific rendering rule")
    message_patterns = interaction.get("humanCommunication", {}).get("messagePatterns", {})
    if message_patterns.get("safMemoryStop", {}).get("appliesWhen") != "PROJECT_WORKSPACE_TYPE == REMOTE_GIT":
        errors.append("legacy safMemoryStop pattern is not scoped to REMOTE_GIT")
    if message_patterns.get("localControlWorkspaceStop", {}).get("appliesWhen") != "PROJECT_WORKSPACE_TYPE == LOCAL_GIT":
        errors.append("LOCAL_GIT blocker message pattern missing")

    response_schema = load("v0.14.0/schemas/human-response.schema.json")
    schema_classes = response_schema.get("properties", {}).get("responseClass", {}).get("enum", [])
    response_classes = interaction.get("responseClassification", {}).get("classes", {})
    if set(schema_classes) != set(response_classes):
        errors.append("HUMAN response classes differ between schema and interaction model")
    expected_menus = {
        "INFORMATIONAL_NOTICE": "FORBIDDEN",
        "INTERACTIVE_CHECKPOINT": "REQUIRED_EXACTLY_ONE",
        "DECISION_REQUEST": "REQUIRED_EXACTLY_ONE",
        "BLOCKER": "REQUIRED_EXACTLY_ONE",
        "DETAIL_RESPONSE": "REQUIRED_EXACTLY_ONE",
    }
    for response_class, expected_menu in expected_menus.items():
        if response_classes.get(response_class, {}).get("terminalMenu") != expected_menu:
            errors.append(f"response class {response_class} menu policy mismatch")
    human_contract = kernel.get("humanCommunication", {})
    if human_contract.get("terminalMenuRequired") is not False:
        errors.append("MASTER still declares universal terminal menu requirement")
    if human_contract.get("terminalMenuPolicy") != "DERIVED_FROM_RESPONSE_CLASS":
        errors.append("MASTER does not derive menu policy from response class")
    if human_contract.get("responseClassificationRef") != "interaction-model.json#responseClassification":
        errors.append("MASTER response classification reference mismatch")
    rc4_classes = conformance_by_id.get("CF-RC4-003", {}).get("applicability", {}).get("responseClass", [])
    if set(rc4_classes) != set(schema_classes):
        errors.append("CF-RC4-003 response classes differ from schema")

    communication = load("v0.14.0/agent-communication-model.json")
    if communication.get("persistenceFailureFallback", {}).get("detailsRef", "missing") is not None:
        errors.append("persistence fallback may not invent detailsRef")

    xor_contract = communication.get("persistenceXorContract", {})
    if xor_contract.get("mutuallyExclusive") is not True:
        errors.append("persistence fallback XOR is not declared mutually exclusive")
    persisted_variant = xor_contract.get("variants", {}).get("PERSISTED_RESPONSE", {})
    failed_variant = xor_contract.get("variants", {}).get("PERSISTENCE_FAILURE", {})
    if persisted_variant.get("persistence") != "MUST_BE_NULL":
        errors.append("persisted response may still carry persistence failure data")
    if failed_variant.get("detailsRef") != "MUST_BE_NULL":
        errors.append("persistence failure may still carry detailsRef")

    chat_schema = load("v0.14.0/schemas/agent-chat-output.schema.json")
    blocked_null = False
    blocked_ref = False
    for clause in chat_schema.get("allOf", []):
        condition = clause.get("if", {}).get("properties", {})
        then_props = clause.get("then", {}).get("properties", {})
        if condition.get("status", {}).get("const") != "BLOCKED":
            continue
        details_type = condition.get("detailsRef", {}).get("type")
        persistence_type = then_props.get("persistence", {}).get("type")
        if details_type == "null" and persistence_type == "object":
            blocked_null = True
        if details_type == "string" and persistence_type == "null":
            blocked_ref = True
    if not blocked_null or not blocked_ref:
        errors.append("agent chat output schema does not enforce BLOCKED persistence XOR")
    activation = load("v0.14.0/agent-activation-model.json").get("atomicClaimContract", {})
    required = [
        "CAS_COMMIT_EXACT_PROPOSED_STATE_AT_EXPECTED_REVISION",
        "PROVIDER_READBACK_FULL_COMMITTED_STATE",
        "VERIFY_CANONICAL_STATE_DIGEST_AND_BINDINGS",
        "MARK_CLAIM_AUTHORITY_FROM_PROVIDER_EVIDENCE",
    ]
    if not all(item in activation.get("authoritativeSequence", []) for item in required):
        errors.append("provider claim sequence incomplete")
    if activation.get("inMemoryConsumptionAuthoritative") is not False:
        errors.append("in-memory GO consumption incorrectly authoritative")
    if activation.get("persistActivationConsumptionInsideCasState") is not True:
        errors.append("GO activation consumption is not persisted inside CAS state")
    if activation.get("proposedStateIsNonAuthoritativeUntilReadback") is not True:
        errors.append("proposed claim state may be treated as authoritative before readback")
    if conformance_by_id.get("CF-RC4-004", {}).get("semanticKey") != "GO_CLAIM_STATE_INTEGRITY":
        errors.append("GO claim state-integrity conformance assertion missing")
    required_claim_evidence = {
        "READBACK_STATE_EQUALS_PROPOSED_STATE",
        "CANONICAL_STATE_DIGEST_MATCH",
        "PROJECT_JOB_AGENT_IDENTITY_CHAT_DISPATCH_BINDINGS_MATCH",
        "ACTIVATION_ID_PRESENT_IN_PERSISTED_CONSUMED_ACTIVATION_IDS",
        "READBACK_REF_PRESENT",
        "READBACK_BLOB_IDENTITY_PRESENT",
    }
    if not required_claim_evidence.issubset(set(activation.get("claimSuccessRequires", []))):
        errors.append("GO claim success evidence is incomplete")

    provider_claim_requirements = {
        "OBSERVED_FULL_STATE_EQUALS_PROPOSED_STATE",
        "OBSERVED_CANONICAL_STATE_DIGEST_MATCHES",
        "PROJECT_JOB_AGENT_IDENTITY_CHAT_DISPATCH_BINDINGS_MATCH",
        "OBSERVED_ACTIVATION_ID_PERSISTED_IN_CONSUMED_ACTIVATION_IDS",
        "READBACK_REFERENCE_PRESENT",
        "OBSERVED_BLOB_IDENTITY_PRESENT",
    }
    for provider_path in (
        "v0.14.0/providers/github/0.6.0/package.json",
        "v0.14.0/providers/gitlab/0.6.0/package.json",
    ):
        provider = load(provider_path).get("model", {}).get("agentClaimProtocol", {})
        if not provider_claim_requirements.issubset(set(provider.get("successRequires", []))):
            errors.append(f"provider claim readback contract incomplete: {provider_path}")
        if provider.get("onReadbackMismatch") != "RECONCILE_REQUIRED":
            errors.append(f"provider claim mismatch is not fail-closed: {provider_path}")

    module_map = bundle_map.get("modulePaths", {})
    recovery = load("v0.14.0/module-self-healing-model.json").get("moduleProfiles", [])
    recovery_keys = {item.get("moduleKey") for item in recovery}
    if set(module_map) != recovery_keys:
        errors.append("module/recovery coverage mismatch")
    if "creationTypeVocabulary" not in module_map:
        errors.append("Creation Type vocabulary not embedded")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    manifest = load("RELEASE-MANIFEST.json")
    if manifest.get("version") != version:
        errors.append("VERSION and manifest differ")
    readiness = (ROOT / "PRODUCT-READINESS.md").read_text(encoding="utf-8")
    expected_count = len(module_map)
    if f"{expected_count}/{expected_count}" not in readiness:
        errors.append(f"PRODUCT-READINESS lacks current module/recovery count {expected_count}/{expected_count}")
    for stale in ("website-delivery@1.1.0", "website-team@1.1.0"):
        if stale in readiness:
            errors.append(f"PRODUCT-READINESS contains stale default {stale}")

    if errors:
        print("SAFOR rc.3 audit remediation: FAIL")
        for error in errors:
            print("-", error)
        raise SystemExit(1)
    print(f"SAFOR rc.3 audit remediation: PASS ({len(module_map)} modules/recovery profiles)")


if __name__ == "__main__":
    validate()
