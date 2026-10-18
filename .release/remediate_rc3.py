#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OLD_VERSION = "0.14.0-rc.2"
NEW_VERSION = "0.14.0-rc.3"
SCHEMA_VERSION = "0.14.0"
BASE_COMMIT = "c1019b6253e5906b315c8eaa31413ff5acca3605"
ACTIVE_CREATION_TYPES = ["WEBSITE", "SOFTWARE_SAAS", "BOOK"]

CURRENT_DOCS = [
    "README.md",
    "ARCHITECTURE.md",
    "SECURITY.md",
    "START-HIER.md",
    "SUPPORT.md",
    "QUICKSTART.md",
    "RELEASE-CHECKLIST.md",
    "PRODUCT-READINESS.md",
    "LICENSE-DECISION.md",
    "ACCEPTANCE-TESTS.md",
    "HUMAN-NOTICE-CONFORMANCE.md",
    "MASTER-SUBAGENT-ORCHESTRATION.md",
    "AGENT-JOB-CONTRACT.md",
    "AGENT-WORKSPACE.md",
    "MULTI-AGENT-SCHEDULER.md",
]

DISTRIBUTABLES = [
    "SAFOR-FRAMEWORK.json",
    f"SAFOR-FRAMEWORK-v{NEW_VERSION}.json",
    "SAFOR-FRAMEWORK-WEBSITE.json",
    "SAFOR-FRAMEWORK-SAAS.json",
    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
    "SAFOR-TEST-ACCESS-SAAS.json",
    "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: str, value: Any) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_text(path: str, old: str, new: str, *, required: bool = False) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if required and old not in text:
        raise RuntimeError(f"Expected text missing in {path}: {old!r}")
    if old in text:
        target.write_text(text.replace(old, new), encoding="utf-8")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if marker not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + content.strip() + "\n"
        target.write_text(text, encoding="utf-8")


def by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for item in items:
        if item.get("id") == item_id:
            return item
    raise RuntimeError(f"Missing object id {item_id}")


def generic_recovery_profile(module_key: str, source_path: str) -> dict[str, Any]:
    profile_id = "MRP-" + re.sub(r"[^A-Z0-9]", "", module_key.upper())
    return {
        "profileId": profile_id,
        "moduleKey": module_key,
        "moduleClass": "POLICY_MODEL",
        "authorityType": "PINNED_CANONICAL_SOURCE",
        "repairability": "RESTORE_FROM_VERIFIED_SOURCE",
        "sourceOfTruth": f"embeddedModules.{module_key} + integrityManifest.{module_key} ({source_path})",
        "failureDetectors": ["MODULE_BLOB_MISMATCH", "MODULE_SCHEMA_OR_CONTRACT_INVALID"],
        "automaticRepairs": ["RELOAD_VERIFIED_EMBEDDED_MODULE", "COMPARE_WITH_PINNED_CANONICAL_SOURCE"],
        "forbiddenRepairs": [
            "INVENT_MISSING_EVIDENCE",
            "EXPAND_AUTHORITY_OR_SCOPE",
            "BYPASS_HUMAN_GATE_OR_REQUIRED_REVIEW",
            "ACCEPT_UNVERIFIED_STATE",
            "AUTOMATICALLY_RECLASSIFY_LEGACY_CREATION_TYPE",
        ],
        "retryBudget": 0,
        "preconditions": [
            "CURRENT_PROVIDER_RIGHTS_PROVEN",
            "PRE_REPAIR_STATE_REFERENCED",
            "SUCCESS_EVIDENCE_DEFINED_BEFORE_MUTATION",
        ],
        "verification": {
            "requiredEvidence": ["AUTHORITATIVE_READBACK", "EXPECTED_STATE_MATCH", "REPAIR_RECORD_PERSISTED"],
            "successPredicate": f"{module_key}_MATCHES_PINNED_RELEASE",
        },
        "escalation": {
            "when": [
                "SOURCE_OF_TRUTH_AMBIGUOUS",
                "AUTHORITATIVE_READBACK_FAILS",
                "REPAIR_WOULD_CHANGE_SEMANTICS_OR_AUTHORITY",
            ],
            "target": "MASTER",
        },
    }


def patch_creation_types() -> None:
    vocabulary = {
        "format": "SAFOR_CREATION_TYPE_VOCABULARY",
        "schemaVersion": SCHEMA_VERSION,
        "id": "SAFOR-CREATION-TYPES-0.14",
        "authority": "CANONICAL_FOR_NEW_V014_PROJECTS",
        "activeCreationTypes": ACTIVE_CREATION_TYPES,
        "rules": [
            "Every new v0.14 project descriptor uses exactly one active Creation Type.",
            "Domain Framework profiles, project schemas, package selection and Factory/Operating Model compatibility use the same active vocabulary.",
            "Legacy Creation Types are never silently rewritten.",
        ],
        "legacyCreationTypes": {
            "SOFTWARE_WEBSITE": {
                "status": "LEGACY_ONLY",
                "migrationMode": "EXPLICIT_CONTEXTUAL_MIGRATION",
                "automaticReplacementForbidden": True,
                "decisionRules": [
                    {
                        "when": "BOUND_FACTORY_FAMILY == safor.factory.website",
                        "targetCreationType": "WEBSITE",
                    },
                    {
                        "when": "BOUND_FACTORY_FAMILY == safor.factory.saas",
                        "targetCreationType": "SOFTWARE_SAAS",
                    },
                    {
                        "when": "DOMAIN_CONTEXT_OR_FACTORY_BINDING_AMBIGUOUS",
                        "outcome": "MIGRATION_DECISION_REQUIRED",
                    },
                ],
            }
        },
    }
    write_json("v0.14.0/creation-type-vocabulary.json", vocabulary)

    schema = load_json("v0.14.0/schemas/project.schema.json")
    schema["properties"]["creationType"] = {
        "enum": ACTIVE_CREATION_TYPES,
        "description": "Canonical v0.14 Creation Type.",
        "x-safor-vocabulary-ref": "creation-type-vocabulary.json#activeCreationTypes",
    }
    write_json("v0.14.0/schemas/project.schema.json", schema)

    migration = load_json("v0.14.0/migration-model.json")
    migration["creationTypeMigration"] = {
        "vocabularyRef": "creation-type-vocabulary.json",
        "legacyValue": "SOFTWARE_WEBSITE",
        "mode": "EXPLICIT_CONTEXTUAL_MIGRATION_ONLY",
        "requirements": [
            "PIN_SOURCE_PROJECT_DESCRIPTOR_AND_BINDINGS",
            "CLASSIFY_FROM_DOMAIN_AND_BOUND_FACTORY",
            "REQUIRE_HUMAN_DECISION_WHEN_AMBIGUOUS",
            "WRITE_NON_DESTRUCTIVE_MIGRATION_MANIFEST",
            "PRESERVE_LEGACY_ARTIFACTS",
            "PROVIDER_READBACK_REQUIRED",
        ],
        "outcomes": ["MIGRATED_TO_WEBSITE", "MIGRATED_TO_SOFTWARE_SAAS", "MIGRATION_DECISION_REQUIRED"],
    }
    write_json("v0.14.0/migration-model.json", migration)


def patch_kernel() -> None:
    kernel = load_json("v0.14.0/SAFOR-MASTER.json")
    principles = kernel["kernelPrinciples"]
    principles["safMemoryAbsolutePrerequisite"] = False
    principles["mandatoryProviderReadWriteBeforeProjectSelection"] = False
    principles["terminalMenuOnEveryHumanResponse"] = False
    principles["controlWorkspaceDiscriminatedByWorkspaceType"] = True
    principles["remoteSaforMemoryRequiredForRemoteGit"] = True
    principles["localMasterControlRootSupportedWithoutRemoteMemory"] = True
    principles["workspaceSpecificCapabilityVerification"] = True
    principles["terminalMenuRequiredForInteractiveResponses"] = True
    principles["canonicalCreationTypeVocabularyRequired"] = True
    principles["providerConfirmedClaimRequired"] = True

    kernel["creationTypeVocabularyRef"] = "creation-type-vocabulary.json"
    kernel["controlWorkspacePolicyRef"] = "repository-policy.json#controlWorkspacePolicy"
    kernel["invariantPolicy"] = {
        "statuses": ["ACTIVE", "SUPERSEDED", "LEGACY_ONLY"],
        "executionRule": "Only ACTIVE invariants participate in current v0.14 execution.",
        "supersessionRule": "SUPERSEDED invariants remain immutable history and require supersededBy references.",
    }

    protocols = {
        "agentActivationProtocol": {
            "modelRef": "agent-activation-model.json",
        },
        "agentChatProtocol": {
            "modelRef": "agent-communication-model.json",
            "schemaRef": "schemas/agent-chat-output.schema.json",
        },
        "masterStatusProtocol": {
            "modelRef": "master-status-model.json",
            "schemaRef": "schemas/project-status-index.schema.json",
        },
        "agentResponseProtocol": {
            "modelRef": "agent-response-contract-model.json",
            "templateCatalogRef": "agent-response-contract-model.json#responseTypes",
            "schemaRef": "schemas/agent-response.schema.json",
        },
    }
    for key, values in protocols.items():
        target = kernel.setdefault(key, {})
        target.update(values)

    schemas = kernel.setdefault("schemas", {})
    for legacy in ("agentResult", "agentBootstrap", "agentChatStatus", "masterStatusIndex"):
        schemas.pop(legacy, None)
    schemas.update(
        {
            "agentResponse": "schemas/agent-response.schema.json",
            "agentInitialization": "schemas/agent-initialization.schema.json",
            "agentChatOutput": "schemas/agent-chat-output.schema.json",
            "projectStatusIndex": "schemas/project-status-index.schema.json",
            "creationTypeVocabulary": "creation-type-vocabulary.json",
        }
    )

    for layer in kernel.get("moduleArchitecture", {}).get("layers", []):
        if layer.get("id") == "HUMAN_INTERACTION_GOVERNANCE":
            layer["responsibility"] = (
                "Phase-aware HUMAN cognitive-load governance, decision gating, decision reuse, terminology abstraction, "
                "content-only informational notices and exactly one terminal menu for interactive HUMAN responses."
            )

    rules = kernel.get("moduleArchitecture", {}).get("dependencyRules", [])
    for index, rule in enumerate(rules):
        if rule.startswith("Every SAFOR-generated HUMAN-facing response must validate"):
            rules[index] = (
                "Every SAFOR-generated HUMAN-facing response validates against the HUMAN response contract. "
                "Informational notices are content-only; interactive checkpoints terminate with exactly one state-derived menu."
            )

    loop = kernel.get("controlPlane", {}).get("interactionLoop", {})
    loop["stableCheckpointBehavior"] = (
        "Platform informational notices are content-only and non-interactive. Interactive checkpoints and genuine decisions "
        "contain exactly one valid state-derived terminal menu, followed by no SAFOR-visible content."
    )
    loop["informationalNoticeMayOmitTerminalMenu"] = True
    loop["informationalNoticeMenuForbidden"] = True
    loop["interactiveResponseRequiresExactlyOneMenu"] = True

    invariants = kernel["invariants"]
    for invariant in invariants:
        invariant.setdefault("status", "ACTIVE")
    superseded = {
        "INV-013": ["INV-234"],
        "INV-037": ["INV-232"],
        "INV-038": ["INV-232"],
        "INV-039": ["INV-231"],
        "INV-054": ["INV-233", "INV-237"],
        "INV-121": ["INV-234"],
        "INV-123": ["INV-234"],
        "INV-217": ["INV-235"],
    }
    for invariant_id, replacements in superseded.items():
        invariant = by_id(invariants, invariant_id)
        invariant["status"] = "SUPERSEDED"
        invariant["supersededBy"] = replacements
        invariant["supersessionReason"] = "Replaced by the active v0.14 rc.3 contract."

    new_invariants = [
        {
            "id": "INV-231",
            "status": "ACTIVE",
            "rule": "New v0.14 projects use exactly one canonical Creation Type from creation-type-vocabulary.json: WEBSITE, SOFTWARE_SAAS or BOOK. Legacy SOFTWARE_WEBSITE requires explicit contextual migration and is never silently rewritten.",
        },
        {
            "id": "INV-232",
            "status": "ACTIVE",
            "rule": "Control workspace policy is discriminated by project workspace type: REMOTE_GIT requires a separate writable HUMAN-controlled safor-memory; LOCAL_GIT requires a Git-tracked MASTER-only .safor/ root and does not require remote memory.",
        },
        {
            "id": "INV-233",
            "status": "ACTIVE",
            "rule": "A normal chat subagent may be activated only by explicit HUMAN GO in its bound chat. Git, polling, automation, another chat and background host events never activate it.",
        },
        {
            "id": "INV-234",
            "status": "ACTIVE",
            "rule": "Informational HUMAN notices contain no menu. Interactive checkpoints and genuine decisions contain exactly one terminal menu and no SAFOR-visible content after it.",
        },
        {
            "id": "INV-235",
            "status": "ACTIVE",
            "rule": "The canonical fail-closed identity status for a chat that cannot prove its binding is REIDENTIFICATION_REQUIRED.",
        },
        {
            "id": "INV-236",
            "status": "ACTIVE",
            "rule": "When a control-response write is unavailable, an agent may emit one local BLOCKED status with persistence.state=FAILED and detailsRef=null; it must not invent a Git reference or repeat an already verified product commit.",
        },
        {
            "id": "INV-237",
            "status": "ACTIVE",
            "rule": "A HUMAN-GO job claim becomes authoritative only after provider compare-and-swap against the expected state revision, provider readback and persisted activation consumption. In-memory consumption alone is never authoritative.",
        },
    ]
    existing_ids = {item["id"] for item in invariants}
    invariants.extend(item for item in new_invariants if item["id"] not in existing_ids)
    write_json("v0.14.0/SAFOR-MASTER.json", kernel)


def patch_initialization_and_interaction() -> None:
    initialization = load_json("v0.14.0/initialization-model.json")
    initialization["creationTypeVocabularyRef"] = "creation-type-vocabulary.json"
    initialization["controlWorkspacePolicyRef"] = "repository-policy.json#controlWorkspacePolicy"
    initialization["agentBootstrapContract"]["modelRef"] = "agent-activation-model.json"
    write_json("v0.14.0/initialization-model.json", initialization)

    interaction = load_json("v0.14.0/interaction-model.json")
    experience = interaction.get("initializationExperience", {})
    for step in experience.get("steps", []):
        step_id = step.get("id")
        if step_id in {"PROVIDER", "ACCESS", "OWNER", "SAFOR_MEMORY", "EXISTING_PROJECT", "NEW_PROJECT"}:
            step["when"] = "PROJECT_WORKSPACE_TYPE == REMOTE_GIT"
        if step_id == "SAFOR_MEMORY":
            step["failureBehavior"] = "WAITING_HUMAN_CONTROL_WORKSPACE"
            step["stopMessage"] = (
                "Für den Remote-Git-Pfad fehlt ein beschreibbares `safor-memory`. "
                "Der lokale Git-Pfad verwendet stattdessen `.safor/`."
            )
        if step_id == "CREATION_TYPE":
            step["options"] = [
                {"label": "Website", "intent": "SELECT_CREATION_TYPE_WEBSITE"},
                {"label": "Software / SaaS", "intent": "SELECT_CREATION_TYPE_SOFTWARE_SAAS"},
                {"label": "Buch", "intent": "SELECT_CREATION_TYPE_BOOK"},
            ]
    rules = experience.setdefault("interactionRules", [])
    rules[:] = [
        rule
        for rule in rules
        if "SAFOR_MEMORY failure" not in rule and "SAFOR_MEMORY" not in rule.upper()
    ]
    for rule in (
        "Remote Git requires verified read/write access to a separate HUMAN-controlled safor-memory.",
        "Local Git requires verified local filesystem/Git rights and a MASTER-only Git-tracked .safor/ root; no remote memory is required.",
        "Creation Type options are WEBSITE, SOFTWARE_SAAS and BOOK unless a domain distribution preselects one.",
    ):
        if rule not in rules:
            rules.append(rule)
    write_json("v0.14.0/interaction-model.json", interaction)


def patch_repository_policy() -> None:
    policy = load_json("v0.14.0/repository-policy.json")
    policy["version"] = SCHEMA_VERSION
    policy["controlWorkspacePolicy"] = {
        "discriminator": "PROJECT_WORKSPACE_TYPE",
        "REMOTE_GIT": {
            "strategy": "REMOTE_SEPARATE_SAFOR_MEMORY",
            "target": "{selectedOwner}/safor-memory",
            "mustPreExist": True,
            "mustBeReadable": True,
            "mustBeWritable": True,
            "autoCreate": False,
            "onMissingOrInsufficientAccess": "WAITING_HUMAN_CONTROL_WORKSPACE",
        },
        "LOCAL_GIT": {
            "strategy": "LOCAL_MASTER_CONTROL_ROOT",
            "target": ".safor/",
            "mustBeGitTracked": True,
            "masterOnly": True,
            "workerWritesForbidden": True,
            "remoteMemoryRequired": False,
            "onMissingCapabilities": "WAITING_HUMAN_LOCAL_HOST_ACCESS",
        },
        "rule": "Exactly one branch applies. Remote and local control prerequisites must never be combined.",
    }
    legacy = policy.get("controlRepositoryRequirement")
    if isinstance(legacy, dict):
        legacy["status"] = "DEPRECATED_NON_EXECUTABLE"
        legacy["supersededBy"] = "controlWorkspacePolicy"
        legacy["rule"] = "Historical compatibility projection only; current execution uses controlWorkspacePolicy."
    write_json("v0.14.0/repository-policy.json", policy)


def patch_communication_and_persistence() -> None:
    model = load_json("v0.14.0/agent-communication-model.json")
    model["persistenceFailureFallback"] = {
        "status": "BLOCKED",
        "authoritative": False,
        "allowedOnlyWhen": "CONTROL_RESPONSE_WRITE_OR_READBACK_UNAVAILABLE",
        "requiredFields": ["jobId", "agentId", "attemptId", "phase", "reasonCode"],
        "detailsRef": None,
        "persistenceState": "FAILED",
        "rules": [
            "Never invent a Git response reference.",
            "Do not repeat an already provider-verified product commit.",
            "After provider recovery, persist only the missing response and reconcile its index.",
            "Keep the chat fallback to one line and route the HUMAN to MASTER.",
        ],
    }
    model["patterns"]["BLOCKED_PERSISTENCE_FAILURE"] = (
        "Job {jobKey} blockiert | Status: BLOCKED | Rückmeldung nicht gespeichert | MASTER-Klärung erforderlich"
    )
    write_json("v0.14.0/agent-communication-model.json", model)

    schema = load_json("v0.14.0/schemas/agent-chat-output.schema.json")
    if "persistence" not in schema["required"]:
        schema["required"].append("persistence")
    schema["properties"]["persistence"] = {
        "type": ["object", "null"],
        "additionalProperties": False,
        "required": ["state", "target", "reasonCode", "authoritativeResponsePersisted", "attemptId", "phase"],
        "properties": {
            "state": {"const": "FAILED"},
            "target": {"const": "CONTROL_REPOSITORY"},
            "reasonCode": {"type": "string", "minLength": 1},
            "authoritativeResponsePersisted": {"const": False},
            "attemptId": {"type": "string", "minLength": 1},
            "phase": {"type": "string", "minLength": 1},
        },
    }
    schema["allOf"] = [
        {
            "if": {
                "properties": {"status": {"const": "BLOCKED"}, "detailsRef": {"type": "null"}},
                "required": ["status", "detailsRef"],
            },
            "then": {"properties": {"persistence": {"type": "object"}}, "required": ["persistence"]},
        },
        {
            "if": {"not": {"properties": {"status": {"const": "BLOCKED"}}, "required": ["status"]}},
            "then": {"properties": {"persistence": {"type": "null"}}},
        },
    ]
    write_json("v0.14.0/schemas/agent-chat-output.schema.json", schema)

    path = ROOT / "runtime/agent_jobs.py"
    text = path.read_text(encoding="utf-8")
    old_signature = "def render_agent_chat_output(*, status: str, project_id: str, agent_id: str, display_name: str, job_key: str | None=None, target_branch: str | None=None, details_ref: str | None=None) -> dict[str, Any]:"
    new_signature = "def render_agent_chat_output(*, status: str, project_id: str, agent_id: str, display_name: str, job_key: str | None=None, target_branch: str | None=None, details_ref: str | None=None, persistence_state: str | None=None, attempt_id: str | None=None, phase: str | None=None, reason_code: str | None=None) -> dict[str, Any]:"
    if old_signature not in text:
        raise RuntimeError("agent chat signature target missing")
    text = text.replace(old_signature, new_signature, 1)
    old_blocked = """    elif status == 'BLOCKED':
        if not job_key or not details_ref:
            raise AgentJobValidationError('BLOCKED_REQUIRES_JOB_AND_DETAILS_REF')
        text = f'Job {job_key} blockiert | Status: BLOCKED | Meldung: {details_ref} | MASTER-Klärung erforderlich'
        terminal = True
"""
    new_blocked = """    elif status == 'BLOCKED':
        if not job_key:
            raise AgentJobValidationError('BLOCKED_REQUIRES_JOB')
        if details_ref:
            text = f'Job {job_key} blockiert | Status: BLOCKED | Meldung: {details_ref} | MASTER-Klärung erforderlich'
            persistence = None
        else:
            if persistence_state != 'FAILED' or not attempt_id or not phase or not reason_code:
                raise AgentJobValidationError('BLOCKED_WITHOUT_DETAILS_REQUIRES_PERSISTENCE_FAILURE_CONTEXT')
            text = f'Job {job_key} blockiert | Status: BLOCKED | Rückmeldung nicht gespeichert | MASTER-Klärung erforderlich'
            persistence = {'state': 'FAILED', 'target': 'CONTROL_REPOSITORY', 'reasonCode': reason_code, 'authoritativeResponsePersisted': False, 'attemptId': attempt_id, 'phase': phase}
        terminal = True
"""
    if old_blocked not in text:
        raise RuntimeError("agent chat blocked target missing")
    text = text.replace(old_blocked, new_blocked, 1)
    text = text.replace(
        "    if '\\n' in text or '\\r' in text:\n",
        "    if status != 'BLOCKED' or details_ref:\n        persistence = None\n    if '\\n' in text or '\\r' in text:\n",
        1,
    )
    old_return = "return {'format': 'SAFOR_AGENT_CHAT_OUTPUT', 'schemaVersion': '0.14.0', 'status': status, 'projectId': project_id, 'agentId': agent_id, 'displayName': display_name, 'jobKey': job_key, 'targetBranch': target_branch, 'detailsRef': details_ref, 'text': text, 'terminal': terminal, 'containsDomainDetail': False}"
    new_return = "return {'format': 'SAFOR_AGENT_CHAT_OUTPUT', 'schemaVersion': '0.14.0', 'status': status, 'projectId': project_id, 'agentId': agent_id, 'displayName': display_name, 'jobKey': job_key, 'targetBranch': target_branch, 'detailsRef': details_ref, 'persistence': persistence, 'text': text, 'terminal': terminal, 'containsDomainDetail': False}"
    if old_return not in text:
        raise RuntimeError("agent chat return target missing")
    path.write_text(text.replace(old_return, new_return, 1), encoding="utf-8")


def patch_claim_protocol() -> None:
    activation = load_json("v0.14.0/agent-activation-model.json")
    activation["atomicClaimContract"].update(
        {
            "authoritativeSequence": [
                "READ_PINNED_JOB_STATE",
                "VALIDATE_GO_EVIDENCE",
                "PREPARE_CLAIM_INTENT",
                "CAS_COMMIT_EXPECTED_REVISION",
                "PROVIDER_READBACK",
                "PERSIST_ACTIVATION_CONSUMPTION",
                "MARK_CLAIM_CONFIRMED",
            ],
            "inMemoryConsumptionAuthoritative": False,
            "claimSuccessRequiresProviderReadback": True,
            "casFailureOutcome": "RECONCILE_REQUIRED",
            "activationConsumptionAuthority": "PERSISTED_JOB_STATE_AFTER_PROVIDER_READBACK",
        }
    )
    write_json("v0.14.0/agent-activation-model.json", activation)

    for provider_path in (
        "v0.14.0/providers/github/0.6.0/package.json",
        "v0.14.0/providers/gitlab/0.6.0/package.json",
    ):
        provider = load_json(provider_path)
        provider.setdefault("model", {})["agentClaimProtocol"] = {
            "requiredOperations": [
                "READ_JOB_STATE_AT_PINNED_REVISION",
                "WRITE_JOB_STATE_WITH_EXPECTED_REVISION",
                "READ_BACK_COMMITTED_JOB_STATE",
            ],
            "successRequires": [
                "COMPARE_AND_SWAP_SUCCEEDED",
                "OBSERVED_REVISION_MATCHES_PROPOSED_REVISION",
                "OBSERVED_LIFECYCLE_STATUS_IS_CLAIMED",
                "OBSERVED_ACTIVATION_ID_MATCHES",
            ],
            "onCasConflict": "RECONCILE_REQUIRED",
            "inMemoryStateNeverAuthoritative": True,
        }
        write_json(provider_path, provider)

    path = ROOT / "runtime/go_evidence.py"
    text = path.read_text(encoding="utf-8")
    start = text.index("def atomically_observe_go_and_claim(")
    replacement = '''def prepare_go_claim(
    *,
    job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_state_revision: int,
    consumed_activation_ids: set[str] | frozenset[str] | None,
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Prepare a non-authoritative provider CAS intent; do not consume GO yet."""
    state = deepcopy(dict(_mapping(job_state, "jobState")))
    if state.get("format") != "SAFOR_AGENT_JOB_STATE":
        raise GoEvidenceValidationError("JOB_STATE_FORMAT_INVALID")
    if state.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("JOB_STATE_SCHEMA_VERSION_INVALID")
    if state.get("lifecycleStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("JOB_NOT_WAITING_HUMAN_GO")
    if state.get("revision") != expected_state_revision:
        raise GoEvidenceValidationError("JOB_STATE_REVISION_CONFLICT")
    expected = {
        "projectId": state.get("projectId"),
        "agentId": state.get("assignedAgentId"),
        "identityRevision": state.get("assignedIdentityRevision"),
        "chatBindingId": state.get("chatBindingId"),
        "targetJobId": state.get("jobId"),
        "targetDispatchRevision": state.get("dispatchRevision"),
    }
    validate_human_go_evidence(
        go_evidence,
        expected=expected,
        consumed_activation_ids=set(consumed_activation_ids or ()),
    )
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(go_evidence_ref.get(field), f"GO_EVIDENCE_REF_{field.upper()}_MISSING")
    activation_id = str(go_evidence["activationId"])
    proposed = deepcopy(state)
    proposed["revision"] = expected_state_revision + 1
    proposed["lifecycleStatus"] = "CLAIMED"
    proposed["claimConfirmationStatus"] = "PENDING_PROVIDER_CAS_READBACK"
    proposed["goEvidenceRef"] = dict(go_evidence_ref)
    proposed.setdefault("transitionHistory", []).extend(
        [
            {"from": "WAITING_HUMAN_GO", "to": "GO_OBSERVED", "at": go_evidence["observedAt"], "actorId": go_evidence["agentId"], "evidenceRefs": [str(go_evidence_ref["path"])]},
            {"from": "GO_OBSERVED", "to": "CLAIMED", "at": go_evidence["observedAt"], "actorId": go_evidence["agentId"], "evidenceRefs": [str(go_evidence_ref["path"])]},
        ]
    )
    proposed["updatedAt"] = go_evidence["observedAt"]
    return {
        "format": "SAFOR_GO_CLAIM_INTENT",
        "schemaVersion": "0.14.0",
        "authoritative": False,
        "activationId": activation_id,
        "expectedRevision": expected_state_revision,
        "proposedRevision": expected_state_revision + 1,
        "requiredProviderSequence": ["CAS_COMMIT_EXPECTED_REVISION", "PROVIDER_READBACK", "PERSIST_ACTIVATION_CONSUMPTION"],
        "proposedState": proposed,
    }


def confirm_go_claim_after_provider_readback(
    *,
    claim_intent: Mapping[str, Any],
    provider_readback: Mapping[str, Any],
    consumed_activation_ids: MutableSet[str],
) -> dict[str, Any]:
    """Confirm authority only after provider CAS and readback prove the claim."""
    intent = _mapping(claim_intent, "claimIntent")
    readback = _mapping(provider_readback, "providerReadback")
    if intent.get("format") != "SAFOR_GO_CLAIM_INTENT" or intent.get("authoritative") is not False:
        raise GoEvidenceValidationError("GO_CLAIM_INTENT_INVALID")
    activation_id = _nonempty(intent.get("activationId"), "GO_ACTIVATION_ID_MISSING")
    if activation_id in consumed_activation_ids:
        raise GoEvidenceValidationError("GO_EVIDENCE_ALREADY_CONSUMED")
    if readback.get("casSucceeded") is not True:
        raise GoEvidenceValidationError("PROVIDER_CAS_NOT_CONFIRMED")
    if readback.get("readbackVerified") is not True:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_READBACK_UNVERIFIED")
    if readback.get("observedRevision") != intent.get("proposedRevision"):
        raise GoEvidenceValidationError("PROVIDER_CLAIM_REVISION_MISMATCH")
    if readback.get("observedLifecycleStatus") != "CLAIMED":
        raise GoEvidenceValidationError("PROVIDER_CLAIM_STATUS_MISMATCH")
    if readback.get("observedActivationId") != activation_id:
        raise GoEvidenceValidationError("PROVIDER_CLAIM_ACTIVATION_MISMATCH")
    state = deepcopy(dict(_mapping(intent.get("proposedState"), "proposedState")))
    consumed_activation_ids.add(activation_id)
    state["consumedActivationIds"] = sorted(set(state.get("consumedActivationIds") or ()) | {activation_id})
    state["claimConfirmationStatus"] = "CONFIRMED_PROVIDER_CAS_READBACK"
    state["claimProviderReadbackRef"] = readback.get("readbackRef")
    return state


def atomically_observe_go_and_claim(
    *,
    job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_state_revision: int,
    consumed_activation_ids: MutableSet[str],
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility alias returning a non-authoritative claim intent.

    Provider CAS and readback remain mandatory; use
    confirm_go_claim_after_provider_readback() before treating CLAIMED as true.
    """
    return prepare_go_claim(
        job_state=job_state,
        go_evidence=go_evidence,
        expected_state_revision=expected_state_revision,
        consumed_activation_ids=set(consumed_activation_ids),
        go_evidence_ref=go_evidence_ref,
    )
'''
    path.write_text(text[:start] + replacement, encoding="utf-8")


def patch_bundle_map_and_recovery() -> None:
    mapping = load_json("v0.14.0/bundle-module-map.json")
    mapping["modulePaths"]["creationTypeVocabulary"] = "v0.14.0/creation-type-vocabulary.json"
    mapping["referenceResolution"]["creation-type-vocabulary.json"] = "creationTypeVocabulary"
    keys = set(mapping.get("v014AuthoritativeKeys", []))
    keys.add("creationTypeVocabulary")
    mapping["v014AuthoritativeKeys"] = sorted(keys)
    write_json("v0.14.0/bundle-module-map.json", mapping)

    recovery = load_json("v0.14.0/module-self-healing-model.json")
    profiles = recovery["moduleProfiles"]
    profiles[:] = [p for p in profiles if p.get("moduleKey") != "creationTypeVocabulary"]
    profiles.append(generic_recovery_profile("creationTypeVocabulary", "v0.14.0/creation-type-vocabulary.json"))
    profiles.sort(key=lambda item: item["moduleKey"])
    write_json("v0.14.0/module-self-healing-model.json", recovery)


def patch_conformance() -> None:
    suite = load_json("v0.14.0/conformance.json")
    assertions = suite["assertions"]
    for assertion in assertions:
        assertion.setdefault("status", "ACTIVE")
        statement = assertion.get("statement", "")
        if "SOFTWARE_WEBSITE or BOOK" in statement:
            assertion["statement"] = "New v0.14 projects use exactly one active Creation Type: WEBSITE, SOFTWARE_SAAS or BOOK; SOFTWARE_WEBSITE is legacy-only and migrates explicitly."
        if "safor-memory" in statement and "absolute" in statement.lower():
            assertion["status"] = "SUPERSEDED"
            assertion["supersededBy"] = ["CF-RC3-004"]
    new_assertions = [
        ("CF-RC3-001", "Every current domain profile Creation Type is accepted by the canonical v0.14 project schema."),
        ("CF-RC3-002", "Every executable model/schema/template reference in kernel and initialization resolves uniquely to an embedded module or allowed pinned external source."),
        ("CF-RC3-003", "Only ACTIVE invariants govern current execution; superseded legacy rules are machine-readable and non-executable."),
        ("CF-RC3-004", "REMOTE_GIT and LOCAL_GIT use mutually exclusive control-workspace prerequisites."),
        ("CF-RC3-005", "A control-response persistence failure produces no invented Git reference and never repeats a verified product commit."),
        ("CF-RC3-006", "A HUMAN-GO claim is authoritative only after provider CAS, provider readback and persisted activation consumption."),
        ("CF-RC3-007", "Current release documentation is checked against VERSION, manifest, module/recovery counts and domain defaults."),
    ]
    existing = {a["id"] for a in assertions}
    for assertion_id, statement in new_assertions:
        if assertion_id not in existing:
            assertions.append({"id": assertion_id, "status": "ACTIVE", "statement": statement, "expected": True})
    write_json("v0.14.0/conformance.json", suite)


def patch_release_metadata() -> None:
    (ROOT / "VERSION").write_text(NEW_VERSION + "\n", encoding="utf-8")
    for path in CURRENT_DOCS:
        if (ROOT / path).exists():
            replace_text(path, OLD_VERSION, NEW_VERSION)
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        replace_text(str(path.relative_to(ROOT)), OLD_VERSION, NEW_VERSION)
    for path in ("tools/validate_safor.py", "tools/build_bundle.py", "tools/build_domain_framework.py"):
        replace_text(path, OLD_VERSION, NEW_VERSION)

    replace_text("PRODUCT-READINESS.md", "75/75", "92/92")
    replace_text("PRODUCT-READINESS.md", "website-delivery@1.1.0", "website-delivery@1.2.0")
    replace_text("PRODUCT-READINESS.md", "website-team@1.1.0", "website-team@1.2.0")
    replace_text("ARCHITECTURE.md", "`SOFTWARE_WEBSITE` is `FREE_PUBLIC`", "`WEBSITE` is `FREE_PUBLIC`")

    manifest = load_json("RELEASE-MANIFEST.json")
    manifest["version"] = NEW_VERSION
    manifest["previousVersion"] = OLD_VERSION
    manifest["distributable"] = f"SAFOR-FRAMEWORK-v{NEW_VERSION}.json"
    manifest["releaseEvidenceRef"] = f"RELEASE-EVIDENCE-{NEW_VERSION}.json"
    manifest["releaseNotesRef"] = f"RELEASE-NOTES-{NEW_VERSION}.md"
    manifest["checksumFile"] = f"SHA256SUMS-{NEW_VERSION}.txt"
    for feature in (
        "CANONICAL_V014_CREATION_TYPE_VOCABULARY",
        "EXPLICIT_LEGACY_CREATION_TYPE_MIGRATION",
        "SEMANTIC_REFERENCE_LINTING",
        "VERSIONED_ACTIVE_INVARIANTS",
        "DISCRIMINATED_CONTROL_WORKSPACE_POLICY",
        "PERSISTENCE_FAILURE_CHAT_FALLBACK",
        "PROVIDER_CONFIRMED_GO_CLAIM_PROTOCOL",
        "RELEASE_DOCUMENTATION_DRIFT_GUARD",
    ):
        if feature not in manifest.setdefault("features", []):
            manifest["features"].append(feature)
    manifest["auditRemediation"] = {
        "sourceRelease": OLD_VERSION,
        "targetRelease": NEW_VERSION,
        "baseCommit": BASE_COMMIT,
        "findings": {
            "AUDIT-RC2-01": "RESOLVED_AUTOMATED_SCHEMA_AND_DOMAIN_TESTS",
            "AUDIT-RC2-02": "RESOLVED_SEMANTIC_REFERENCE_LINTER",
            "AUDIT-RC2-03": "RESOLVED_ACTIVE_SUPERSEDED_INVARIANT_MODEL",
            "AUDIT-RC2-04": "RESOLVED_DISCRIMINATED_CONTROL_WORKSPACE_POLICY",
            "AUDIT-RC2-05": "RESOLVED_AUTOMATED_PERSISTENCE_FAILURE_CONTRACT",
            "AUDIT-RC2-06": "CONTRACT_AND_AUTOMATED_TESTS_RESOLVED_REAL_PROVIDER_E2E_OPEN",
            "AUDIT-RC2-07": "OPEN_REAL_GIT_E2E_AND_REFERENCE_MIGRATION",
            "AUDIT-RC2-08": "RESOLVED_AUTOMATED_DOCUMENTATION_DRIFT_GUARD",
            "AUDIT-RC2-09": "OPEN_EMPIRICAL_CONTEXT_AND_USABILITY_EVIDENCE",
        },
    }
    write_json("RELEASE-MANIFEST.json", manifest)

    notes = f"""# SAFOR {NEW_VERSION} Release Notes

## Purpose

This release candidate remediates the independent rc.2 audit without redesigning SAFOR or adding a mandatory customer runtime.

## Corrected contracts

- Canonical Creation Types are `WEBSITE`, `SOFTWARE_SAAS` and `BOOK` across new project descriptors and domain profiles.
- Legacy `SOFTWARE_WEBSITE` remains historical and requires explicit contextual migration.
- Current kernel model/schema/template references resolve to active v0.14 modules.
- Invariants are machine-classified as `ACTIVE`, `SUPERSEDED` or `LEGACY_ONLY`.
- `REMOTE_GIT` requires separate `safor-memory`; `LOCAL_GIT` uses a MASTER-only Git-tracked `.safor/` root without remote-memory requirement.
- Control-response persistence failure can be reported locally without inventing a Git reference or repeating a verified product commit.
- HUMAN-GO claim success requires provider compare-and-swap, provider readback and persisted activation consumption.
- Current documentation is checked against release facts.

## Distribution files

- `SAFOR-FRAMEWORK-v{NEW_VERSION}.json`
- `SAFOR-FRAMEWORK.json`
- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- public SaaS and Book evaluation access bundles

## Evidence boundary

Automated schema, reference, invariant, policy, failure-injection, reproducibility and regression checks do not constitute a fresh-chat real-Git E2E, cross-host equivalence, `safomwebsite` migration acceptance, empirical cognitive-load evidence or General Availability.
"""
    (ROOT / f"RELEASE-NOTES-{NEW_VERSION}.md").write_text(notes, encoding="utf-8")

    evidence = {
        "format": "SAFOR_RELEASE_EVIDENCE",
        "schemaVersion": SCHEMA_VERSION,
        "product": "SAFOR",
        "version": NEW_VERSION,
        "status": "MATERIALIZATION_PREPARED",
        "createdAt": now(),
        "baseMainCommit": BASE_COMMIT,
        "integrationBranch": os.environ.get("GITHUB_REF_NAME", "safor/audit-remediation-0.14.0-rc.3"),
        "workflow": {
            "repository": os.environ.get("GITHUB_REPOSITORY", "empishaj/SAFOR"),
            "runId": os.environ.get("GITHUB_RUN_ID"),
            "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        },
        "validatedCommands": [
            "python tools/build_bundle.py --check",
            "python tools/build_domain_framework.py --check",
            "python tools/validate_safor.py",
            "python tools/validate_audit_remediation.py",
            "python tools/validate_traceability.py",
            "python -m unittest discover -s tests -v",
            f"sha256sum --check SHA256SUMS-{NEW_VERSION}.txt",
        ],
        "artifacts": [],
        "truthBoundary": [
            "Automated PASS is not a fresh-chat real-Git E2E PASS.",
            "Provider claim semantics require an actual host/provider compare-and-swap and readback.",
            "JSON does not create provider permissions or force a non-conforming host.",
            "Reference-project migration remains deferred until isolated real-Git E2E passes.",
            "Cognitive-load reduction remains an empirical product claim requiring measurement.",
        ],
    }
    write_json(f"RELEASE-EVIDENCE-{NEW_VERSION}.json", evidence)

    append_once(
        "CHANGELOG.md",
        f"## {NEW_VERSION}",
        f"""
## {NEW_VERSION}

- Resolves the rc.2 Creation-Type cross-schema defect with one canonical v0.14 vocabulary and explicit legacy migration.
- Replaces ambiguous current kernel model/schema/template references with active v0.14 references and adds semantic linting.
- Classifies current invariants as active, superseded or legacy-only and removes contradictory active semantics.
- Discriminates REMOTE_GIT and LOCAL_GIT control prerequisites.
- Adds persistence-failure chat fallback without invented Git references.
- Requires provider CAS/readback before a HUMAN-GO claim becomes authoritative.
- Adds documentation-drift validation and rebuilds every Framework distribution reproducibly.
""",
    )


def create_validators_and_tests() -> None:
    validator = r'''#!/usr/bin/env python3
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
'''
    (ROOT / "tools/validate_audit_remediation.py").write_text(validator, encoding="utf-8")

    test = r'''import json
import subprocess
import sys
import unittest
from pathlib import Path

from runtime.agent_jobs import AgentJobValidationError, render_agent_chat_output
from runtime.go_evidence import (
    GoEvidenceValidationError,
    confirm_go_claim_after_provider_readback,
    prepare_go_claim,
)

ROOT = Path(__file__).resolve().parents[1]


class AuditRemediationRc3Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def evidence(self):
        return {
            "format": "SAFOR_HUMAN_GO_EVIDENCE", "schemaVersion": "0.14.0",
            "activationId": "activation-rc3-001", "projectId": "project-001",
            "agentId": "agent-a", "identityRevision": 2,
            "chatBindingId": "binding-a-r2", "sessionId": "session-001",
            "targetJobId": "job-001", "targetDispatchRevision": 3,
            "intent": "GO", "source": "DIRECT_HUMAN_INPUT_IN_BOUND_AGENT_CHAT",
            "observedAt": "2026-10-18T10:00:00Z", "singleUse": True,
            "jobPromptTransported": False,
        }

    def state(self):
        return {
            "format": "SAFOR_AGENT_JOB_STATE", "schemaVersion": "0.14.0",
            "projectId": "project-001", "jobId": "job-001",
            "assignedAgentId": "agent-a", "assignedIdentityRevision": 2,
            "chatBindingId": "binding-a-r2", "dispatchRevision": 3,
            "revision": 7, "lifecycleStatus": "WAITING_HUMAN_GO",
            "goEvidenceRef": None, "consumedActivationIds": [],
            "transitionHistory": [], "updatedAt": "2026-10-18T09:59:00Z",
        }

    def ref(self):
        return {"repository": "example/safor-memory", "ref": "commit123", "path": "projects/example/evidence/go.json", "blobSha": "blob1234"}

    def test_creation_type_contract_is_consistent(self):
        active = ["WEBSITE", "SOFTWARE_SAAS", "BOOK"]
        self.assertEqual(active, self.load("v0.14.0/creation-type-vocabulary.json")["activeCreationTypes"])
        self.assertEqual(active, self.load("v0.14.0/schemas/project.schema.json")["properties"]["creationType"]["enum"])
        self.assertEqual(set(active), {p["creationType"] for p in self.load("v0.14.0/domain-framework-profiles.json")["profiles"]})

    def test_legacy_creation_type_requires_explicit_contextual_migration(self):
        legacy = self.load("v0.14.0/creation-type-vocabulary.json")["legacyCreationTypes"]["SOFTWARE_WEBSITE"]
        self.assertEqual("LEGACY_ONLY", legacy["status"])
        self.assertTrue(legacy["automaticReplacementForbidden"])
        self.assertEqual("EXPLICIT_CONTEXTUAL_MIGRATION", legacy["migrationMode"])

    def test_active_invariants_are_unambiguous(self):
        invariants = self.load("v0.14.0/SAFOR-MASTER.json")["invariants"]
        indexed = {item["id"]: item for item in invariants}
        for legacy_id in ("INV-013", "INV-037", "INV-038", "INV-039", "INV-054", "INV-121", "INV-123", "INV-217"):
            self.assertEqual("SUPERSEDED", indexed[legacy_id]["status"])
            self.assertTrue(indexed[legacy_id]["supersededBy"])
        for active_id in ("INV-231", "INV-232", "INV-233", "INV-234", "INV-235", "INV-236", "INV-237"):
            self.assertEqual("ACTIVE", indexed[active_id]["status"])

    def test_local_and_remote_control_policies_are_mutually_explicit(self):
        policy = self.load("v0.14.0/repository-policy.json")["controlWorkspacePolicy"]
        self.assertEqual("PROJECT_WORKSPACE_TYPE", policy["discriminator"])
        self.assertFalse(policy["LOCAL_GIT"]["remoteMemoryRequired"])
        self.assertEqual("{selectedOwner}/safor-memory", policy["REMOTE_GIT"]["target"])

    def test_persistence_failure_chat_fallback_has_no_fake_reference(self):
        output = render_agent_chat_output(
            status="BLOCKED", project_id="project-001", agent_id="agent-a",
            display_name="Nova Dev", job_key="WP-001", details_ref=None,
            persistence_state="FAILED", attempt_id="attempt-001",
            phase="WRITE_RESPONSE", reason_code="CONTROL_WRITE_UNAVAILABLE",
        )
        self.assertIsNone(output["detailsRef"])
        self.assertEqual("FAILED", output["persistence"]["state"])
        self.assertFalse(output["persistence"]["authoritativeResponsePersisted"])
        self.assertNotIn("http", output["text"])
        with self.assertRaisesRegex(AgentJobValidationError, "PERSISTENCE_FAILURE_CONTEXT"):
            render_agent_chat_output(status="BLOCKED", project_id="project-001", agent_id="agent-a", display_name="Nova Dev", job_key="WP-001")

    def test_go_claim_is_not_authoritative_before_provider_readback(self):
        consumed = set()
        intent = prepare_go_claim(
            job_state=self.state(), go_evidence=self.evidence(),
            expected_state_revision=7, consumed_activation_ids=consumed,
            go_evidence_ref=self.ref(),
        )
        self.assertFalse(intent["authoritative"])
        self.assertEqual(set(), consumed)
        self.assertEqual("PENDING_PROVIDER_CAS_READBACK", intent["proposedState"]["claimConfirmationStatus"])
        with self.assertRaisesRegex(GoEvidenceValidationError, "PROVIDER_CAS_NOT_CONFIRMED"):
            confirm_go_claim_after_provider_readback(
                claim_intent=intent,
                provider_readback={"casSucceeded": False, "readbackVerified": False},
                consumed_activation_ids=consumed,
            )
        self.assertEqual(set(), consumed)
        confirmed = confirm_go_claim_after_provider_readback(
            claim_intent=intent,
            provider_readback={
                "casSucceeded": True, "readbackVerified": True,
                "observedRevision": 8, "observedLifecycleStatus": "CLAIMED",
                "observedActivationId": "activation-rc3-001",
                "readbackRef": "git:commit:claimed",
            },
            consumed_activation_ids=consumed,
        )
        self.assertEqual("CONFIRMED_PROVIDER_CAS_READBACK", confirmed["claimConfirmationStatus"])
        self.assertIn("activation-rc3-001", consumed)

    def test_audit_validator_passes(self):
        subprocess.run([sys.executable, str(ROOT / "tools/validate_audit_remediation.py")], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
'''
    (ROOT / "tests/test_audit_remediation_rc3.py").write_text(test, encoding="utf-8")

    go_test = (ROOT / "tests/test_go_evidence_v014.py").read_text(encoding="utf-8")
    go_test = go_test.replace(
        "from runtime.go_evidence import GoEvidenceValidationError, atomically_observe_go_and_claim, validate_human_go_evidence",
        "from runtime.go_evidence import GoEvidenceValidationError, confirm_go_claim_after_provider_readback, prepare_go_claim, validate_human_go_evidence",
    )
    start = go_test.index("    def test_atomic_claim_uses_expected_revision_and_consumes_activation")
    end = go_test.index("\n\nif __name__ == \"__main__\":")
    replacement = '''    def test_claim_requires_provider_cas_readback_before_consumption(self):
        consumed = set()
        intent = prepare_go_claim(job_state=self.state(), go_evidence=self.evidence(), expected_state_revision=7, consumed_activation_ids=consumed, go_evidence_ref=self.ref())
        self.assertFalse(intent["authoritative"])
        self.assertEqual(set(), consumed)
        claimed = confirm_go_claim_after_provider_readback(
            claim_intent=intent,
            provider_readback={"casSucceeded": True, "readbackVerified": True, "observedRevision": 8, "observedLifecycleStatus": "CLAIMED", "observedActivationId": "activation-001", "readbackRef": "git:claim"},
            consumed_activation_ids=consumed,
        )
        self.assertEqual("CLAIMED", claimed["lifecycleStatus"])
        self.assertEqual(8, claimed["revision"])
        self.assertIn("activation-001", consumed)
        self.assertEqual(["activation-001"], claimed["consumedActivationIds"])

    def test_failed_cas_does_not_consume_or_confirm(self):
        consumed = set()
        intent = prepare_go_claim(job_state=self.state(), go_evidence=self.evidence(), expected_state_revision=7, consumed_activation_ids=consumed, go_evidence_ref=self.ref())
        with self.assertRaisesRegex(GoEvidenceValidationError, "PROVIDER_CAS_NOT_CONFIRMED"):
            confirm_go_claim_after_provider_readback(claim_intent=intent, provider_readback={"casSucceeded": False, "readbackVerified": False}, consumed_activation_ids=consumed)
        self.assertEqual(set(), consumed)

    def test_duplicate_claim_fails_after_persisted_consumption(self):
        with self.assertRaisesRegex(GoEvidenceValidationError, "GO_EVIDENCE_ALREADY_CONSUMED"):
            prepare_go_claim(job_state=self.state(), go_evidence=self.evidence(), expected_state_revision=7, consumed_activation_ids={"activation-001"}, go_evidence_ref=self.ref())
'''
    (ROOT / "tests/test_go_evidence_v014.py").write_text(go_test[:start] + replacement + go_test[end:], encoding="utf-8")


def patch_validator_and_ci() -> None:
    validator_path = ROOT / "tools/validate_safor.py"
    validator = validator_path.read_text(encoding="utf-8")
    marker = "if errors:\n"
    extra = "runpy.run_path(str(ROOT / 'tools/validate_audit_remediation.py'), run_name='__main__')\n\n"
    if "validate_audit_remediation.py" not in validator:
        if "import runpy" not in validator:
            validator = validator.replace("import json\n", "import json\nimport runpy\n", 1)
        if marker not in validator:
            raise RuntimeError("validate_safor insertion target missing")
        validator = validator.replace(marker, extra + marker, 1)
        validator_path.write_text(validator, encoding="utf-8")

    workflow_path = ROOT / ".github/workflows/validate.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    if "Validate audit remediation" not in workflow:
        needle = "      - name: Validate SAFOR distribution\n        run: python tools/validate_safor.py\n"
        replacement = needle + "      - name: Validate audit remediation\n        run: python tools/validate_audit_remediation.py\n      - name: Validate requirements traceability\n        run: python tools/validate_traceability.py\n"
        if needle not in workflow:
            raise RuntimeError("validate workflow insertion target missing")
        workflow_path.write_text(workflow.replace(needle, replacement, 1), encoding="utf-8")


def prepare() -> None:
    patch_creation_types()
    patch_kernel()
    patch_initialization_and_interaction()
    patch_repository_policy()
    patch_communication_and_persistence()
    patch_claim_protocol()
    patch_bundle_map_and_recovery()
    patch_conformance()
    patch_release_metadata()
    create_validators_and_tests()
    patch_validator_and_ci()

    old_bundle = ROOT / f"SAFOR-FRAMEWORK-v{OLD_VERSION}.json"
    if old_bundle.exists():
        old_bundle.unlink()


def finalize() -> None:
    alias = (ROOT / "SAFOR-FRAMEWORK.json").read_bytes()
    versioned = (ROOT / f"SAFOR-FRAMEWORK-v{NEW_VERSION}.json").read_bytes()
    if alias != versioned:
        raise RuntimeError("Generic alias and versioned Framework differ")
    artifacts = []
    lines = []
    for relative in DISTRIBUTABLES:
        raw = (ROOT / relative).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        artifacts.append({"path": relative, "sha256": digest, "bytes": len(raw)})
        lines.append(f"{digest}  {relative}")
    checksum = ROOT / f"SHA256SUMS-{NEW_VERSION}.txt"
    checksum.write_text("\n".join(lines) + "\n", encoding="utf-8")
    evidence_path = f"RELEASE-EVIDENCE-{NEW_VERSION}.json"
    evidence = load_json(evidence_path)
    evidence["status"] = "MATERIALIZED_AWAITING_AUTOMATED_VALIDATION"
    evidence["materializedAt"] = now()
    evidence["artifactCount"] = len(artifacts)
    evidence["artifacts"] = artifacts
    evidence["checksumFile"] = checksum.name
    write_json(evidence_path, evidence)
    manifest = load_json("RELEASE-MANIFEST.json")
    manifest["distributionArtifactCount"] = len(artifacts)
    manifest["embeddedModuleCount"] = len(load_json("v0.14.0/bundle-module-map.json")["modulePaths"])
    write_json("RELEASE-MANIFEST.json", manifest)


def mark_pass() -> None:
    evidence_path = f"RELEASE-EVIDENCE-{NEW_VERSION}.json"
    evidence = load_json(evidence_path)
    evidence["status"] = "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS"
    evidence["automatedValidationCompletedAt"] = now()
    write_json(evidence_path, evidence)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "finalize", "mark-pass"])
    args = parser.parse_args()
    globals()[args.mode.replace("-", "_")]()
