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

    policy = load("v0.14.0/repository-policy.json").get("controlWorkspacePolicy", {})
    if policy.get("discriminator") != "PROJECT_WORKSPACE_TYPE":
        errors.append("control workspace policy has no discriminator")
    if policy.get("LOCAL_GIT", {}).get("remoteMemoryRequired") is not False:
        errors.append("LOCAL_GIT still requires remote memory")
    if policy.get("REMOTE_GIT", {}).get("target") != "{selectedOwner}/safor-memory":
        errors.append("REMOTE_GIT memory target mismatch")

    communication = load("v0.14.0/agent-communication-model.json")
    if communication.get("persistenceFailureFallback", {}).get("detailsRef", "missing") is not None:
        errors.append("persistence fallback may not invent detailsRef")
    activation = load("v0.14.0/agent-activation-model.json").get("atomicClaimContract", {})
    required = ["CAS_COMMIT_EXPECTED_REVISION", "PROVIDER_READBACK", "PERSIST_ACTIVATION_CONSUMPTION"]
    if not all(item in activation.get("authoritativeSequence", []) for item in required):
        errors.append("provider claim sequence incomplete")
    if activation.get("inMemoryConsumptionAuthoritative") is not False:
        errors.append("in-memory GO consumption incorrectly authoritative")

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
