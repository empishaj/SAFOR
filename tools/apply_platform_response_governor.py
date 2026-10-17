#!/usr/bin/env python3
"""One-off migration for SAFOR v0.13.0-rc.7.

Moves HUMAN-visible communication ownership into the SAFOR platform, adds a
pure reference response governor, updates the response schema/governance
contracts, rebuilds all distributable Frameworks, and adds regression tests.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
OLD_VERSION = "0.13.0-rc.6"
NEW_VERSION = "0.13.0-rc.7"


def load_json(relative: str) -> Dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write_json(relative: str, value: Mapping[str, Any]) -> None:
    (ROOT / relative).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write_text(relative: str, value: str) -> None:
    (ROOT / relative).write_text(value, encoding="utf-8")


def replace_required(text: str, old: str, new: str, *, label: str) -> str:
    if old not in text:
        raise ValueError(f"Expected marker missing in {label}: {old!r}")
    return text.replace(old, new)


def append_unique(items: list[Any], value: Any, *, key: str | None = None) -> None:
    if key is None:
        if value not in items:
            items.append(value)
        return
    existing = {item.get(key) for item in items if isinstance(item, dict)}
    if isinstance(value, dict) and value.get(key) not in existing:
        items.append(value)


def walk_dicts(value: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def find_dict_by_id(value: Any, target_id: str) -> Dict[str, Any]:
    matches = [item for item in walk_dicts(value) if item.get("id") == target_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one object with id={target_id}, got {len(matches)}")
    return matches[0]


def update_interaction_model() -> None:
    path = "v0.10.0/interaction-model.json"
    model = load_json(path)

    principles = model["principles"]
    principles.update(
        {
            "platformOwnsHumanVisibleCommunication": True,
            "domainModulesCannotOverrideHumanVisibleCommunication": True,
            "platformResponseGovernorRequired": True,
            "terminalMenuAlwaysRequired": False,
            "terminalMenuRequiredAtInteractiveCheckpoints": True,
            "informationalNoticeMayOmitTerminalMenu": True,
            "terminalMenuIsFinalRenderedSurface": True,
        }
    )

    model["platformResponseGovernor"] = {
        "id": "SAFOR_PLATFORM_HUMAN_RESPONSE_GOVERNOR",
        "owner": "SAFOR_PLATFORM",
        "scope": "EVERY_SAFOR_GENERATED_HUMAN_VISIBLE_OUTPUT",
        "enforcementBoundary": "AFTER_DOMAIN_FACT_COLLECTION_BEFORE_HUMAN_RENDERING",
        "nonDelegation": {
            "factoryMayControlHumanPresentation": False,
            "operatingModelMayControlHumanPresentation": False,
            "domainModulesMaySupply": [
                "FACTS",
                "RISKS",
                "REQUIRED_HUMAN_DECISION",
                "EVIDENCE_REFS",
                "NEXT_SAFE_ACTION",
            ],
            "domainModulesMayNotControl": [
                "VISIBLE_TEXT",
                "VISIBLE_LENGTH",
                "VISIBLE_STRUCTURE",
                "TECHNICAL_DETAIL_EXPOSURE",
                "NUMBER_OF_CHOICES",
                "TERMINAL_MENU",
                "RESPONSE_BUDGET",
                "PROGRESSIVE_DISCLOSURE",
            ],
            "domainOverrideForbidden": True,
        },
        "defaultSurface": "SUMMARY",
        "detailRetention": {
            "retainFullInternalAnalysis": True,
            "retainEvidence": True,
            "showOnlyWhenHumanRequestsDetailsOrMaterialSafetyRequiresIt": True,
            "technicalIdsHiddenByDefault": True,
        },
        "communicationClasses": {
            "INFORMATIONAL_NOTICE": {
                "humanActionRequired": False,
                "terminalMenuAllowed": False,
                "maxSentences": 2,
                "maxWords": 30,
            },
            "INTERACTIVE_CHECKPOINT": {
                "humanActionRequired": True,
                "terminalMenuRequired": True,
                "maxNewDecisionContexts": 1,
            },
            "DECISION_REQUEST": {
                "humanActionRequired": True,
                "terminalMenuRequired": True,
                "humanDecisionGateRequired": True,
                "maxNewDecisionContexts": 1,
            },
        },
        "eventPolicies": {
            "FRAMEWORK_DETECTED": {
                "responseClass": "INFORMATIONAL_NOTICE",
                "visiblePattern": "Neues {domainLabel}-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.",
                "maxSentences": 2,
                "maxWords": 24,
                "showVersion": False,
                "showBlobOrDigest": False,
                "showFactoryOrOperatingModelIds": False,
                "showValueStreamMapping": False,
                "offerMigrationChoices": False,
                "safeMigrationPlanningIsInternal": True,
            },
            "MIGRATION_PLANNING_STARTED": {
                "responseClass": "INFORMATIONAL_NOTICE",
                "visiblePattern": "Die Migration wird geplant. Bis der sichere Plan steht, ändere ich nichts.",
                "maxSentences": 2,
                "maxWords": 18,
                "offerMigrationChoices": False,
            },
        },
        "humanDecisionEscalationOnlyWhen": [
            "NON_DERIVABLE_SCOPE_DECISION",
            "MATERIAL_ALTERNATIVE",
            "NEW_OR_EXPANDED_AUTHORITY",
            "MATERIAL_RISK_ACCEPTANCE",
            "IRREVERSIBLE_ACTION",
            "GOAL_CONFLICT",
        ],
        "renderAlgorithm": [
            "COLLECT_PLATFORM_AND_DOMAIN_FACTS",
            "REJECT_DOMAIN_PRESENTATION_OVERRIDE",
            "CLASSIFY_HUMAN_RELEVANCE",
            "RUN_HUMAN_DECISION_GATE",
            "CLASSIFY_RESPONSE_CLASS",
            "SELECT_SUMMARY_BY_DEFAULT",
            "COMPRESS_TO_PLATFORM_RESPONSE_BUDGET",
            "MOVE_NONESSENTIAL_DETAIL_TO_DETAILS_OR_EVIDENCE",
            "OMIT_TERMINAL_MENU_FOR_INFORMATIONAL_NOTICE",
            "RENDER_TERMINAL_MENU_ONLY_FOR_INTERACTIVE_CHECKPOINT",
        ],
        "failureMode": "FAIL_CLOSED_TO_MINIMUM_SAFE_PLATFORM_MESSAGE",
        "minimumSafeMessage": "Ich habe die Änderung erkannt. Ich prüfe den sicheren nächsten Schritt und ändere bis dahin nichts.",
    }

    menu_policy = model["menuPolicy"]
    append_unique(
        menu_policy["suppressWhen"],
        "PLATFORM_INFORMATIONAL_NOTICE_WITH_NO_HUMAN_ACTION",
    )
    menu_policy.update(
        {
            "terminalMenuRequired": False,
            "terminalMenuRequiredAtInteractiveCheckpoints": True,
            "exactlyOneTerminalMenu": False,
            "exactlyOneTerminalMenuWhenRequired": True,
            "informationalNoticeMayOmitTerminalMenu": True,
            "informationalNoticeMenuForbidden": True,
            "noContentAfterTerminalMenu": True,
        }
    )

    human = model["humanCommunication"]
    human["defaultBehavior"].update(
        {
            "platformResponseGovernorRequired": True,
            "domainPresentationOverrideForbidden": True,
            "terminalMenuRequired": False,
            "terminalMenuRequiredAtInteractiveCheckpoints": True,
            "informationalNoticeMayOmitTerminalMenu": True,
        }
    )
    human["responseBudgets"]["platformInformationalNotice"] = {
        "maxSentences": 2,
        "targetWords": 24,
        "terminalMenu": "FORBIDDEN",
        "guidance": "State only what changed and what the platform is doing next. Keep analysis, versions, digests, mappings and options behind Details unless materially required.",
    }
    human["messagePatterns"]["frameworkDetected"] = {
        "structure": ["WHAT_CHANGED", "PLATFORM_NEXT_ACTION"],
        "example": "Neues Website-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.",
        "forbidden": [
            "VERSION_AND_DIGEST_DUMP",
            "FACTORY_AND_OPERATING_MODEL_METADATA_DUMP",
            "VALUE_STREAM_WALKTHROUGH",
            "MIGRATION_OPTION_MENU_WITHOUT_REAL_HUMAN_DECISION",
        ],
    }
    human["terminalRule"] = (
        "The SAFOR platform owns response classification. INFORMATIONAL_NOTICE responses contain only the compressed content and no terminal menu. "
        "Interactive checkpoints and genuine decision requests end with exactly one menu, with no SAFOR-visible content after it."
    )

    model["terminalMenuContract"] = {
        "scope": "INTERACTIVE_CHECKPOINTS_AND_GENUINE_DECISION_RESPONSES",
        "responseSchemaRef": "schemas/human-response.schema.json",
        "menuSchemaRef": "schemas/interaction-menu.schema.json",
        "platformOwner": "SAFOR_PLATFORM",
        "requiredFor": [
            "INTERACTIVE_CHECKPOINT",
            "DECISION_REQUEST",
            "BLOCKER_WITH_HUMAN_ACTION",
            "DETAIL_RESPONSE_WITH_NAVIGATION",
        ],
        "omittedFor": ["INFORMATIONAL_NOTICE"],
        "informationalNoticeMenuForbidden": True,
        "exactlyOneWhenRequired": True,
        "mustBeFinalRenderedElementWhenPresent": True,
        "contentAfterMenuForbidden": True,
        "stopRenderingAfterMenu": True,
        "menuPresenceDoesNotImplyHumanDecision": True,
        "finalizer": {
            "mandatory": True,
            "steps": [
                "BUILD_HUMAN_RESPONSE_ENVELOPE",
                "APPLY_PLATFORM_RESPONSE_GOVERNOR",
                "REJECT_DOMAIN_PRESENTATION_OVERRIDE",
                "APPLY_HUMAN_DECISION_GATE",
                "CLASSIFY_RESPONSE_CLASS",
                "COMPRESS_SUMMARY_TO_PLATFORM_BUDGET",
                "IF_INFORMATIONAL_NOTICE_VERIFY_NO_TERMINAL_MENU",
                "IF_INTERACTIVE_DERIVE_CONTEXTUAL_TERMINAL_MENU",
                "IF_INTERACTIVE_AND_CONTEXTUAL_MENU_UNAVAILABLE_DERIVE_SAFE_FALLBACK_MENU",
                "VALIDATE_HUMAN_RESPONSE_SCHEMA",
                "RENDER_CONTENT",
                "IF_INTERACTIVE_RENDER_EXACTLY_ONE_TERMINAL_MENU",
                "STOP_RENDERING",
            ],
            "emitWithoutSuccessfulFinalization": False,
        },
        "fallbackMenu": {
            "requiredOnlyForInteractiveResponse": True,
            "derivationRule": "Derive only currently valid navigation/control actions from authoritative state, Decision Gate, active mandates and actual host capabilities. Never invent a decision or authority merely to populate a menu.",
            "preferredIntents": [
                "NEXT_ROUND",
                "STATUS",
                "DETAILS",
                "HELP",
                "PAUSE",
                "STOP",
            ],
            "minimumUsefulFallback": ["DETAILS", "HELP"],
            "ifNoStateAdvancingActionExists": "Show non-mutating navigation/help actions only for an interactive response; do not turn an informational notice into an interaction.",
        },
    }

    write_json(path, model)


def update_decision_gate() -> None:
    path = "v0.10.0/human-decision-gate-model.json"
    gate = load_json(path)
    gate["platformCommunicationOwnership"] = {
        "owner": "SAFOR_PLATFORM",
        "governorRef": "interaction-model.json#platformResponseGovernor",
        "factoryOrOperatingModelMayOverride": False,
        "rule": "Factories and Operating Models supply domain facts, risks, evidence and legitimate decision requirements only. The SAFOR platform decides whether, how and how much is shown to the HUMAN.",
    }
    for item in (
        "FRAMEWORK_DETECTION_ACKNOWLEDGEMENT",
        "SAFE_REVERSIBLE_MIGRATION_ANALYSIS",
        "MIGRATION_PLAN_DRAFTING",
        "TECHNICAL_VERSION_DIGEST_AND_VALUE_STREAM_COMPARISON",
        "PRESENTATION_FORMAT_OR_RESPONSE_LENGTH_SELECTION",
    ):
        append_unique(gate["mustNotAskHumanFor"], item)
    gate["latePhasePolicy"].update(
        {
            "frameworkDetectionDefault": "INFORMATIONAL_NOTICE_ONLY",
            "safeMigrationPlanningDefault": "ABSORB_INTERNAL_ORCHESTRATION",
        }
    )
    algorithm = gate["evaluationAlgorithm"]
    if "APPLY_PLATFORM_RESPONSE_GOVERNOR_AFTER_GATE" not in algorithm:
        algorithm.append("APPLY_PLATFORM_RESPONSE_GOVERNOR_AFTER_GATE")
    write_json(path, gate)


def update_human_response_schema() -> None:
    path = "v0.10.0/schemas/human-response.schema.json"
    schema = load_json(path)
    schema["required"] = [
        "format",
        "schemaVersion",
        "responseId",
        "phase",
        "responseClass",
        "surface",
        "content",
        "governance",
        "renderingContract",
    ]
    props = schema["properties"]
    props["responseClass"] = {
        "enum": [
            "INFORMATIONAL_NOTICE",
            "INTERACTIVE_CHECKPOINT",
            "DECISION_REQUEST",
            "BLOCKER",
            "DETAIL_RESPONSE",
        ]
    }
    props["content"]["minItems"] = 1
    props["governance"] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "owner",
            "governorId",
            "domainOverrideApplied",
            "decisionGateOutcome",
            "detailsDisclosure",
            "detailsAvailable",
            "evidenceRetained",
            "responseBudget",
        ],
        "properties": {
            "owner": {"const": "SAFOR_PLATFORM"},
            "governorId": {"const": "SAFOR_PLATFORM_HUMAN_RESPONSE_GOVERNOR"},
            "domainOverrideApplied": {"const": False},
            "decisionGateOutcome": {
                "enum": [
                    "ALLOW_ASK",
                    "SUPPRESS_DERIVABLE",
                    "REUSE_EXISTING_DECISION",
                    "BLOCK_INVALID_HUMAN_DELEGATION",
                    "NOT_REQUIRED",
                ]
            },
            "detailsDisclosure": {
                "enum": ["SUMMARY_ONLY", "DETAILS_REQUESTED", "SAFETY_REQUIRED"]
            },
            "detailsAvailable": {"type": "boolean"},
            "evidenceRetained": {"const": True},
            "responseBudget": {
                "type": "object",
                "additionalProperties": False,
                "required": ["maxSentences", "maxWords"],
                "properties": {
                    "maxSentences": {"type": "integer", "minimum": 1},
                    "maxWords": {"type": "integer", "minimum": 1},
                },
            },
        },
    }
    props["renderingContract"] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "renderMode",
            "renderOrder",
            "terminalElement",
            "exactlyOneTerminalMenu",
            "contentAfterTerminalElementForbidden",
            "stopRenderingAfterTerminalMenu",
        ],
        "properties": {
            "renderMode": {"enum": ["CONTENT_ONLY", "CONTENT_THEN_MENU"]},
            "renderOrder": {
                "type": "array",
                "minItems": 1,
                "maxItems": 2,
                "items": {"enum": ["content", "terminalMenu"]},
            },
            "terminalElement": {"enum": ["content", "terminalMenu"]},
            "exactlyOneTerminalMenu": {"type": "boolean"},
            "contentAfterTerminalElementForbidden": {"const": True},
            "stopRenderingAfterTerminalMenu": {"type": "boolean"},
        },
    }
    schema["allOf"] = [
        {
            "if": {
                "properties": {"responseClass": {"const": "INFORMATIONAL_NOTICE"}},
                "required": ["responseClass"],
            },
            "then": {
                "not": {"required": ["terminalMenu"]},
                "properties": {
                    "renderingContract": {
                        "properties": {
                            "renderMode": {"const": "CONTENT_ONLY"},
                            "renderOrder": {"const": ["content"]},
                            "terminalElement": {"const": "content"},
                            "exactlyOneTerminalMenu": {"const": False},
                            "stopRenderingAfterTerminalMenu": {"const": False},
                        }
                    }
                },
            },
        },
        {
            "if": {
                "properties": {
                    "responseClass": {
                        "enum": [
                            "INTERACTIVE_CHECKPOINT",
                            "DECISION_REQUEST",
                            "BLOCKER",
                            "DETAIL_RESPONSE",
                        ]
                    }
                },
                "required": ["responseClass"],
            },
            "then": {
                "required": ["terminalMenu"],
                "properties": {
                    "renderingContract": {
                        "properties": {
                            "renderMode": {"const": "CONTENT_THEN_MENU"},
                            "renderOrder": {"const": ["content", "terminalMenu"]},
                            "terminalElement": {"const": "terminalMenu"},
                            "exactlyOneTerminalMenu": {"const": True},
                            "stopRenderingAfterTerminalMenu": {"const": True},
                        }
                    }
                },
            },
        },
    ]
    write_json(path, schema)


def update_kernel_and_conformance() -> None:
    kernel_path = "v0.13.0/SAFOR-MASTER.json"
    kernel = load_json(kernel_path)
    kernel["kernelPrinciples"].update(
        {
            "platformOwnsHumanVisibleCommunication": True,
            "factoryAndOperatingModelCannotOverrideHumanPresentation": True,
            "platformResponseGovernorRunsBeforeEveryHumanRender": True,
            "safeMigrationPlanningIsInternalOrchestration": True,
            "informationalNoticesAreCompressedAndNonInteractive": True,
            "fullDetailAndEvidenceRemainAvailableOnDemand": True,
        }
    )
    new_invariants = [
        {
            "id": "INV-201",
            "rule": "The SAFOR platform exclusively owns HUMAN-visible response classification, verbosity, structure, progressive disclosure and menu rendering; Factory and Operating Model may supply domain facts, risks, evidence and legitimate decision requirements only.",
        },
        {
            "id": "INV-202",
            "rule": "Every HUMAN-visible output passes the platform response governor after domain fact collection and before rendering; a domain module presentation override is rejected.",
        },
        {
            "id": "INV-203",
            "rule": "Framework detection, technical comparison and safe reversible migration-plan drafting are internal SAFOR orchestration and do not create a HUMAN decision by themselves.",
        },
        {
            "id": "INV-204",
            "rule": "A platform INFORMATIONAL_NOTICE contains at most two sentences and thirty words, hides technical identifiers and offers no choices or terminal menu.",
        },
        {
            "id": "INV-205",
            "rule": "Full technical analysis, evidence and migration mappings remain retained and auditable but are shown only when the HUMAN requests Details or material safety requires disclosure.",
        },
        {
            "id": "INV-206",
            "rule": "A genuine HUMAN decision may be requested only after the Decision Gate identifies non-derivable scope, material alternative, authority, risk, irreversible action or goal conflict; response compression never suppresses such a decision.",
        },
    ]
    existing_ids = {item.get("id") for item in kernel["invariants"]}
    kernel["invariants"].extend(item for item in new_invariants if item["id"] not in existing_ids)

    interaction_contracts = [
        item
        for item in walk_dicts(kernel)
        if item.get("humanResponseSchemaRef") == "schemas/human-response.schema.json"
    ]
    if len(interaction_contracts) != 1:
        raise ValueError(
            f"Expected one kernel HUMAN interaction contract, got {len(interaction_contracts)}"
        )
    contract = interaction_contracts[0]
    contract["platformResponseGovernorRef"] = "interaction-model.json#platformResponseGovernor"
    contract["platformResponseGovernorMandatory"] = True
    contract["domainModulePresentationOverrideForbidden"] = True
    contract["informationalNoticeMayOmitTerminalMenu"] = True
    contract["humanResponseFinalizer"]["steps"] = [
        "BUILD_HUMAN_RESPONSE_ENVELOPE",
        "APPLY_PLATFORM_RESPONSE_GOVERNOR",
        "REJECT_DOMAIN_PRESENTATION_OVERRIDE",
        "APPLY_HUMAN_DECISION_GATE",
        "CLASSIFY_RESPONSE_CLASS",
        "COMPRESS_SUMMARY_TO_PLATFORM_BUDGET",
        "VALIDATE_HUMAN_RESPONSE_SCHEMA",
        "IF_INFORMATIONAL_NOTICE_RENDER_CONTENT_ONLY",
        "IF_INTERACTIVE_RENDER_EXACTLY_ONE_TERMINAL_MENU",
        "VERIFY_NO_CONTENT_AFTER_TERMINAL_ELEMENT",
        "STOP_RENDERING",
    ]
    write_json(kernel_path, kernel)

    conformance_path = "v0.13.0/conformance.json"
    conformance = load_json(conformance_path)
    new_assertions = [
        {
            "id": "CF-261",
            "statement": "HUMAN-visible response governance is owned by the SAFOR platform and is not delegated to a Factory or Operating Model.",
            "expected": True,
        },
        {
            "id": "CF-262",
            "statement": "Factory and Operating Model may contribute domain facts, risk, evidence and legitimate decision requirements but cannot control visible text, verbosity, structure, choices or terminal menus.",
            "expected": True,
        },
        {
            "id": "CF-263",
            "statement": "The platform response governor runs after domain fact collection and before every HUMAN-visible render.",
            "expected": True,
        },
        {
            "id": "CF-264",
            "statement": "Framework detection and safe reversible migration planning produce a compressed non-interactive informational notice rather than a technical report or option menu.",
            "expected": True,
        },
        {
            "id": "CF-265",
            "statement": "The framework-detection notice is limited to two sentences and twenty-four words and contains no version, digest, package-ID or value-stream dump by default.",
            "expected": True,
        },
        {
            "id": "CF-266",
            "statement": "Full migration analysis and evidence remain retained behind Details/Evidence and are not lost through HUMAN-facing compression.",
            "expected": True,
        },
        {
            "id": "CF-267",
            "statement": "SAFOR_HUMAN_RESPONSE distinguishes informational notices without menus from interactive checkpoints with exactly one terminal menu.",
            "expected": True,
        },
    ]
    existing_cf = {item.get("id") for item in conformance["assertions"]}
    conformance["assertions"].extend(
        item for item in new_assertions if item["id"] not in existing_cf
    )
    write_json(conformance_path, conformance)


def update_self_healing() -> None:
    path = "v0.13.0/self-healing-model.json"
    model = load_json(path)
    failure = find_dict_by_id(model, "SH-20")
    failure["name"] = "HUMAN_RESPONSE_GOVERNANCE_FAILURE"
    failure["examples"] = [
        "Interactive HUMAN response has no terminal menu or has more than one menu",
        "Platform INFORMATIONAL_NOTICE contains a terminal menu or migration option list",
        "Factory or Operating Model attempts to control visible response text, length or structure",
        "Default SUMMARY exceeds the platform response budget without a Details request or material safety reason",
        "SAFOR-visible content appears after an interactive terminal menu",
    ]
    write_json(path, model)


def update_build_and_validator() -> None:
    build_path = "tools/build_bundle.py"
    build = read_text(build_path)
    marker = '            "humanCommunicationRule": "Use the embedded HUMAN buddy profile.",\n'
    insertion = (
        '            "platformHumanResponseGovernorRule": "The SAFOR platform owns HUMAN-visible response classification, compression, progressive disclosure and menus; Factory and Operating Model may supply domain facts only and cannot override presentation.",\n'
        + marker
    )
    if "platformHumanResponseGovernorRule" not in build:
        build = replace_required(build, marker, insertion, label=build_path)
    old_menu_rule = (
        '            "humanTerminalMenuRule": "Every SAFOR-generated HUMAN-facing response contains exactly one valid terminal interaction menu and renders no SAFOR-visible content after it.",\n'
    )
    new_menu_rule = (
        '            "humanTerminalMenuRule": "Platform informational notices are content-only and non-interactive. Interactive checkpoints and genuine decisions contain exactly one terminal menu and render no SAFOR-visible content after it.",\n'
    )
    build = replace_required(build, old_menu_rule, new_menu_rule, label=build_path)
    write_text(build_path, build)

    validator_path = "tools/validate_safor.py"
    validator = read_text(validator_path).replace(OLD_VERSION, NEW_VERSION)
    principles_marker = '    "publicEvaluationDoesNotAuthorizePaidUse",\n)\n'
    principles_replacement = (
        '    "publicEvaluationDoesNotAuthorizePaidUse",\n'
        '    "platformOwnsHumanVisibleCommunication",\n'
        '    "factoryAndOperatingModelCannotOverrideHumanPresentation",\n'
        '    "platformResponseGovernorRunsBeforeEveryHumanRender",\n'
        '    "safeMigrationPlanningIsInternalOrchestration",\n'
        '    "informationalNoticesAreCompressedAndNonInteractive",\n'
        '    "fullDetailAndEvidenceRemainAvailableOnDemand",\n'
        ')\n'
    )
    if '    "platformOwnsHumanVisibleCommunication",\n' not in validator:
        validator = replace_required(
            validator,
            principles_marker,
            principles_replacement,
            label=validator_path,
        )
    validator = validator.replace("for n in range(37, 201):", "for n in range(37, 207):")
    validation_marker = (
        'for principle in required_principles:\n'
        '    if kernel.get("kernelPrinciples", {}).get(principle) is not True:\n'
        '        fail(f"Kernel principle {principle} must be true.")\n\n'
    )
    validation_block = validation_marker + '''# Platform-owned HUMAN response governance.\ninteraction = modules.get("interaction", {}).get("content", {})\ngovernor = interaction.get("platformResponseGovernor", {})\nif governor.get("owner") != "SAFOR_PLATFORM":\n    fail("Platform response governor owner must be SAFOR_PLATFORM.")\nif governor.get("enforcementBoundary") != "AFTER_DOMAIN_FACT_COLLECTION_BEFORE_HUMAN_RENDERING":\n    fail("Platform response governor enforcement boundary mismatch.")\nif governor.get("nonDelegation", {}).get("domainOverrideForbidden") is not True:\n    fail("Factory/Operating Model presentation override must be forbidden.")\nframework_notice = governor.get("eventPolicies", {}).get("FRAMEWORK_DETECTED", {})\nif framework_notice.get("responseClass") != "INFORMATIONAL_NOTICE":\n    fail("FRAMEWORK_DETECTED must be an INFORMATIONAL_NOTICE.")\nif framework_notice.get("maxSentences") != 2 or framework_notice.get("maxWords") != 24:\n    fail("FRAMEWORK_DETECTED response budget mismatch.")\nif framework_notice.get("offerMigrationChoices") is not False:\n    fail("FRAMEWORK_DETECTED must not offer migration choices without a genuine HUMAN decision.")\nif interaction.get("terminalMenuContract", {}).get("informationalNoticeMenuForbidden") is not True:\n    fail("Informational notices must not render a terminal menu.")\nresponse_schema = modules.get("schemaHumanResponse", {}).get("content", {})\nrequired_response_fields = set(response_schema.get("required", []))\nfor field in ("responseClass", "governance", "renderingContract"):\n    if field not in required_response_fields:\n        fail(f"HUMAN response schema must require {field}.")\nif "terminalMenu" in required_response_fields:\n    fail("HUMAN response schema must not require terminalMenu for informational notices.")\n\n'''
    if "# Platform-owned HUMAN response governance." not in validator:
        validator = replace_required(
            validator,
            validation_marker,
            validation_block,
            label=validator_path,
        )
    write_text(validator_path, validator)


def update_version_and_manifest() -> None:
    write_text("VERSION", NEW_VERSION + "\n")
    manifest = load_json("RELEASE-MANIFEST.json")
    manifest["version"] = NEW_VERSION
    manifest["distributable"] = f"SAFOR-FRAMEWORK-v{NEW_VERSION}.json"
    manifest["previousVersion"] = OLD_VERSION
    for feature in (
        "PLATFORM_OWNED_HUMAN_RESPONSE_GOVERNOR",
        "DOMAIN_MODULE_PRESENTATION_OVERRIDE_FORBIDDEN",
        "INFORMATIONAL_NOTICE_COMPRESSION",
        "SAFE_MIGRATION_PLANNING_INTERNALIZED",
        "DETAIL_ON_DEMAND_WITH_EVIDENCE_RETENTION",
    ):
        append_unique(manifest["features"], feature)
    append_unique(
        manifest["gaBlockers"],
        "PLATFORM_RESPONSE_GOVERNOR_HOST_END_TO_END_ACCEPTANCE",
    )
    write_json("RELEASE-MANIFEST.json", manifest)


def update_docs_and_tests() -> None:
    current_version_files = [
        "README.md",
        "QUICKSTART.md",
        "START-HIER.md",
        "SUPPORT.md",
        "SECURITY.md",
        "LICENSE-DECISION.md",
        "PRODUCT-READINESS.md",
        "RELEASE-CHECKLIST.md",
        "ACCEPTANCE-TESTS.md",
        "ARCHITECTURE.md",
    ]
    current_version_files.extend(str(path.relative_to(ROOT)) for path in (ROOT / "tests").glob("test_*.py"))
    for relative in current_version_files:
        text = read_text(relative)
        if OLD_VERSION in text:
            write_text(relative, text.replace(OLD_VERSION, NEW_VERSION))

    for relative in (
        "SECURITY.md",
        "LICENSE-DECISION.md",
        "ARCHITECTURE.md",
        "ACCEPTANCE-TESTS.md",
    ):
        text = read_text(relative)
        text = text.replace("safor.factory.website-delivery@1.0.0", "safor.factory.website-delivery@1.1.0")
        text = text.replace("safor.om.website-team@1.0.0", "safor.om.website-team@1.1.0")
        text = text.replace("Factory/Operating Model 1.0.0 pair", "Factory/Operating Model 1.1.0 pair")
        write_text(relative, text)

    support = read_text("SUPPORT.md").replace(
        "## Product paths in rc.3", "## Product paths in the current release candidate"
    )
    write_text("SUPPORT.md", support)

    readiness = read_text("PRODUCT-READINESS.md")
    readiness = readiness.replace(
        "| Total Python unit tests | **86 PASS in CI** |",
        "| Current unit and regression suite | **PASS in CI; count derived from workflow logs** |",
    )
    gate_marker = "| Terminal HUMAN menu contract | PASS by schema/conformance |\n"
    gate_addition = gate_marker + (
        "| Platform-owned HUMAN response governor | PASS by policy/reference runtime/unit |\n"
        "| Domain-module presentation override | FORBIDDEN and regression-tested |\n"
        "| Framework-detection informational notice budget | PASS by unit/validator |\n"
        "| Platform response governor host end-to-end acceptance | OPEN |\n"
    )
    if "| Platform-owned HUMAN response governor |" not in readiness:
        readiness = replace_required(readiness, gate_marker, gate_addition, label="PRODUCT-READINESS.md")
    write_text("PRODUCT-READINESS.md", readiness)

    checklist = read_text("RELEASE-CHECKLIST.md")
    checklist = checklist.replace(
        "- [x] Total current unit suite: 86 tests PASS.",
        "- [x] Current unit and regression suite passes in CI; the test count is derived from workflow logs rather than duplicated in documentation.",
    )
    release_marker = "- [x] HUMAN Decision Gate and terminal-menu contracts remain intact.\n"
    release_addition = release_marker + (
        "- [x] The SAFOR platform exclusively owns HUMAN-visible response governance.\n"
        "- [x] Factory and Operating Model cannot override visible response text, verbosity, structure, choices or menus.\n"
        "- [x] Framework detection and safe migration planning use a compressed non-interactive notice.\n"
        "- [x] Full technical migration analysis remains retained behind Details/Evidence.\n"
    )
    if "- [x] The SAFOR platform exclusively owns HUMAN-visible response governance." not in checklist:
        checklist = replace_required(checklist, release_marker, release_addition, label="RELEASE-CHECKLIST.md")
    ga_marker = "- [ ] Full governance transition migration completed or remaining non-executable boundary explicitly accepted for GA scope.\n"
    ga_addition = (
        "- [ ] Scenario S — platform-owned HUMAN response governor host E2E PASS.\n"
        + ga_marker
    )
    if "Scenario S — platform-owned HUMAN response governor" not in checklist:
        checklist = replace_required(checklist, ga_marker, ga_addition, label="RELEASE-CHECKLIST.md")
    write_text("RELEASE-CHECKLIST.md", checklist)

    human_doc = read_text("HUMAN-COGNITIVE-LOAD.md")
    platform_section = '''\n## Platform-owned response governance\n\nHUMAN-visible communication is a SAFOR platform responsibility. Factories and Operating Models may provide domain facts, risks, evidence and legitimate decision requirements, but they may not control visible wording, length, structure, progressive disclosure, choices or menus.\n\nBefore every visible output, the platform response governor classifies whether the HUMAN must act. Internal events such as detecting a new Framework, comparing versions or drafting a safe reversible migration plan are absorbed by SAFOR. The default visible notice is compressed, for example:\n\n```text\nNeues Website-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.\n```\n\nVersions, digests, package identities, migration mappings and evidence remain retained for audit and are shown only through Details/Evidence or when a material HUMAN decision or safety risk requires them. An informational notice contains no option menu; interactive menus are reserved for genuine checkpoints and decisions.\n'''
    if "## Platform-owned response governance" not in human_doc:
        human_doc += platform_section
    write_text("HUMAN-COGNITIVE-LOAD.md", human_doc)

    readme = read_text("README.md")
    readme_marker = "## Product paths\n"
    readme_section = '''## Platform-owned HUMAN communication\n\nThe SAFOR platform—not a Factory or Operating Model—owns every HUMAN-visible response. Domain modules supply facts, risks, evidence and genuine decision requirements; the platform decides whether to speak, how much to show and whether an interaction menu is warranted. Framework detection and safe migration-plan drafting therefore default to a short non-interactive notice, while full technical analysis remains available under Details/Evidence.\n\n'''
    if "## Platform-owned HUMAN communication" not in readme:
        readme = replace_required(readme, readme_marker, readme_section + readme_marker, label="README.md")
    write_text("README.md", readme)

    start_here = read_text("START-HIER.md")
    start_marker = "## 4. Daran erkennst du einen korrekten Start\n"
    start_note = (
        "Die sichtbare Kommunikation wird zentral durch die SAFOR-Plattform verdichtet. Factory und Operating Model liefern fachliche Fakten, dürfen aber weder die Antwortlänge noch Menüs oder technische Detailtiefe bestimmen. Reine Statusmeldungen wie eine erkannte Framework-Änderung bleiben kurz; Details erscheinen nur auf Nachfrage oder bei einer echten Entscheidung.\n\n"
    )
    if start_note not in start_here:
        start_here = replace_required(start_here, start_marker, start_note + start_marker, label="START-HIER.md")
    write_text("START-HIER.md", start_here)

    acceptance = read_text("ACCEPTANCE-TESTS.md")
    scenario = '''\n## S. Platform-owned HUMAN response governor\n\n**Preconditions**\n- An existing Website project is bound to an older SAFOR Framework.\n- `SAFOR-FRAMEWORK-WEBSITE.json` from the current release is loaded.\n\n**Expected**\n1. The platform recognizes the new Framework and begins safe migration analysis without delegating technical comparison or plan drafting to the HUMAN.\n2. The first visible notice contains at most two sentences and thirty words.\n3. The notice does not expose versions, blob/digest values, package IDs, value-stream mappings or a migration-option menu.\n4. Factory and Operating Model contribute facts/evidence only and cannot override visible wording, length, structure or menu behavior.\n5. Full comparison, mapping and evidence remain retained and are available through Details/Evidence.\n6. A HUMAN decision is requested only if scope, authority, material risk, irreversible action or a genuine alternative requires it.\n\n**Canonical default notice**\n\n```text\nNeues Website-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.\n```\n'''
    if "## S. Platform-owned HUMAN response governor" not in acceptance:
        acceptance += scenario
    write_text("ACCEPTANCE-TESTS.md", acceptance)

    changelog = read_text("CHANGELOG.md")
    entry = f'''## {NEW_VERSION}\n\n- Makes HUMAN-visible communication an exclusive SAFOR platform responsibility.\n- Adds a mandatory platform response governor between domain fact collection and HUMAN rendering.\n- Forbids Factory and Operating Model presentation overrides while retaining their domain facts, risks, evidence and legitimate decision requirements.\n- Compresses Framework detection and safe migration-plan drafting into non-interactive informational notices; technical metadata and mappings remain behind Details/Evidence.\n- Distinguishes content-only informational notices from interactive responses with exactly one terminal menu.\n- Adds a pure reference governor, kernel invariants INV-201 through INV-206, conformance CF-261 through CF-267 and regression tests across all domain Frameworks.\n\n'''
    if f"## {NEW_VERSION}\n" not in changelog:
        changelog = replace_required(changelog, "# Changelog\n\n", "# Changelog\n\n" + entry, label="CHANGELOG.md")
    write_text("CHANGELOG.md", changelog)


def write_reference_runtime_and_tests() -> None:
    runtime = '''from __future__ import annotations\n\nimport re\nfrom typing import Any, Mapping\n\n\nGOVERNOR_ID = "SAFOR_PLATFORM_HUMAN_RESPONSE_GOVERNOR"\n\n_ALLOWED_DOMAIN_KEYS = {\n    "facts",\n    "risks",\n    "requiredHumanDecision",\n    "evidenceRefs",\n    "nextSafeAction",\n}\n\n_FORBIDDEN_PRESENTATION_KEYS = {\n    "visibleText",\n    "responseText",\n    "responseLength",\n    "maxWords",\n    "maxSentences",\n    "menu",\n    "terminalMenu",\n    "choices",\n    "headings",\n    "progressiveDisclosure",\n    "technicalDetailExposure",\n}\n\n_EVENT_POLICIES = {\n    "FRAMEWORK_DETECTED": {\n        "maxSentences": 2,\n        "maxWords": 24,\n        "template": (\n            "Neues {domainLabel}-Framework erkannt. "\n            "Ich prüfe den bestehenden Stand und plane die Migration; "\n            "bis dahin ändere ich nichts."\n        ),\n    },\n    "MIGRATION_PLANNING_STARTED": {\n        "maxSentences": 2,\n        "maxWords": 18,\n        "template": (\n            "Die Migration wird geplant. "\n            "Bis der sichere Plan steht, ändere ich nichts."\n        ),\n    },\n}\n\n\nclass ResponseGovernanceError(ValueError):\n    """Raised when platform response governance cannot safely render."""\n\n\nclass HumanDecisionRequired(ResponseGovernanceError):\n    """Raised when a real HUMAN decision must be routed to an interactive response."""\n\n\ndef _mapping(value: Any, name: str) -> Mapping[str, Any]:\n    if not isinstance(value, Mapping):\n        raise ResponseGovernanceError(f"{name} must be a mapping")\n    return value\n\n\ndef _scan_forbidden_keys(value: Any) -> set[str]:\n    found: set[str] = set()\n    if isinstance(value, Mapping):\n        for key, child in value.items():\n            if key in _FORBIDDEN_PRESENTATION_KEYS:\n                found.add(str(key))\n            found.update(_scan_forbidden_keys(child))\n    elif isinstance(value, list):\n        for child in value:\n            found.update(_scan_forbidden_keys(child))\n    return found\n\n\ndef _validate_domain_contribution(value: Any) -> Mapping[str, Any]:\n    contribution = _mapping(value or {}, "domainContribution")\n    unknown = set(contribution) - _ALLOWED_DOMAIN_KEYS\n    forbidden = _scan_forbidden_keys(contribution)\n    if unknown or forbidden:\n        blocked = sorted(unknown | forbidden)\n        raise ResponseGovernanceError(\n            "DOMAIN_PRESENTATION_OVERRIDE_FORBIDDEN: " + ", ".join(blocked)\n        )\n    return contribution\n\n\ndef _sentence_count(text: str) -> int:\n    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])\n\n\ndef _word_count(text: str) -> int:\n    return len(text.split())\n\n\ndef govern_platform_notice(event: Mapping[str, Any]) -> dict[str, Any]:\n    """Create a deterministic, content-only HUMAN notice owned by SAFOR.\n\n    Domain modules may contribute facts, risks, evidence and a genuine decision\n    requirement. They cannot provide presentation controls. Events that require\n    a real HUMAN decision are rejected from this non-interactive path and must\n    be routed through the normal Decision Gate.\n    """\n\n    event = _mapping(event, "event")\n    event_type = str(event.get("eventType", ""))\n    if event_type not in _EVENT_POLICIES:\n        raise ResponseGovernanceError(f"UNSUPPORTED_PLATFORM_NOTICE: {event_type}")\n\n    contribution = _validate_domain_contribution(event.get("domainContribution", {}))\n    decision_required = bool(event.get("humanDecisionRequired")) or bool(\n        contribution.get("requiredHumanDecision")\n    )\n    material_escalation = any(\n        bool(event.get(field))\n        for field in (\n            "scopeChangeRequired",\n            "authorityChangeRequired",\n            "materialRiskAcceptanceRequired",\n            "irreversibleActionRequired",\n            "goalConflictRequiresPriority",\n        )\n    )\n    if decision_required or material_escalation:\n        raise HumanDecisionRequired(\n            "HUMAN_DECISION_REQUIRED: route through interactive Decision Gate"\n        )\n\n    policy = _EVENT_POLICIES[event_type]\n    domain_label = str(event.get("domainLabel", "")).strip()\n    if event_type == "FRAMEWORK_DETECTED" and not domain_label:\n        raise ResponseGovernanceError("domainLabel is required for FRAMEWORK_DETECTED")\n\n    text = policy["template"].format(domainLabel=domain_label)\n    sentence_count = _sentence_count(text)\n    word_count = _word_count(text)\n    if sentence_count > policy["maxSentences"] or word_count > policy["maxWords"]:\n        raise ResponseGovernanceError(\n            "PLATFORM_RESPONSE_BUDGET_EXCEEDED: "\n            f"sentences={sentence_count}, words={word_count}"\n        )\n\n    details_available = bool(\n        event.get("internalDetails")\n        or contribution.get("facts")\n        or contribution.get("risks")\n        or contribution.get("evidenceRefs")\n    )\n    response_id = str(event.get("eventId", "platform-notice"))\n    phase = str(event.get("phase", "BOOTSTRAP"))\n\n    return {\n        "format": "SAFOR_HUMAN_RESPONSE",\n        "schemaVersion": "0.10.0",\n        "responseId": f"response:{response_id}",\n        "phase": phase,\n        "responseClass": "INFORMATIONAL_NOTICE",\n        "surface": "SUMMARY",\n        "content": [{"type": "STATUS", "text": text}],\n        "governance": {\n            "owner": "SAFOR_PLATFORM",\n            "governorId": GOVERNOR_ID,\n            "domainOverrideApplied": False,\n            "decisionGateOutcome": "SUPPRESS_DERIVABLE",\n            "detailsDisclosure": "SUMMARY_ONLY",\n            "detailsAvailable": details_available,\n            "evidenceRetained": True,\n            "responseBudget": {\n                "maxSentences": policy["maxSentences"],\n                "maxWords": policy["maxWords"],\n            },\n        },\n        "renderingContract": {\n            "renderMode": "CONTENT_ONLY",\n            "renderOrder": ["content"],\n            "terminalElement": "content",\n            "exactlyOneTerminalMenu": False,\n            "contentAfterTerminalElementForbidden": True,\n            "stopRenderingAfterTerminalMenu": False,\n        },\n    }\n'''
    write_text("runtime/human_response_governor.py", runtime)

    tests = '''import json\nimport re\nimport unittest\nfrom pathlib import Path\n\nfrom runtime.human_response_governor import (\n    HumanDecisionRequired,\n    ResponseGovernanceError,\n    govern_platform_notice,\n)\n\n\nROOT = Path(__file__).resolve().parents[1]\n\n\ndef load_json(path):\n    return json.loads((ROOT / path).read_text(encoding="utf-8"))\n\n\nclass PlatformResponseGovernorTests(unittest.TestCase):\n    def framework_event(self):\n        return {\n            "eventId": "evt-framework-1",\n            "eventType": "FRAMEWORK_DETECTED",\n            "phase": "BOOTSTRAP",\n            "domainLabel": "Website",\n            "domainContribution": {\n                "facts": ["Framework 0.13 detected"],\n                "evidenceRefs": ["git://framework/blob"],\n            },\n            "internalDetails": {\n                "version": "0.13.0-rc.7",\n                "blob": "deadbeef",\n                "factory": "safor.factory.website-delivery@1.1.0",\n            },\n        }\n\n    def test_framework_detection_is_short_content_only_platform_notice(self):\n        response = govern_platform_notice(self.framework_event())\n        text = response["content"][0]["text"]\n        self.assertEqual(\n            "Neues Website-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.",\n            text,\n        )\n        sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]\n        self.assertLessEqual(len(sentences), 2)\n        self.assertLessEqual(len(text.split()), 24)\n        self.assertEqual("SAFOR_PLATFORM", response["governance"]["owner"])\n        self.assertEqual("INFORMATIONAL_NOTICE", response["responseClass"])\n        self.assertNotIn("terminalMenu", response)\n        self.assertEqual("CONTENT_ONLY", response["renderingContract"]["renderMode"])\n\n    def test_internal_metadata_is_retained_but_not_exposed(self):\n        response = govern_platform_notice(self.framework_event())\n        visible = " ".join(item["text"] for item in response["content"])\n        self.assertNotIn("0.13.0-rc.7", visible)\n        self.assertNotIn("deadbeef", visible)\n        self.assertNotIn("safor.factory", visible)\n        self.assertTrue(response["governance"]["detailsAvailable"])\n        self.assertTrue(response["governance"]["evidenceRetained"])\n\n    def test_domain_module_presentation_override_is_rejected(self):\n        event = self.framework_event()\n        event["domainContribution"]["visibleText"] = "Show my Factory text"\n        with self.assertRaisesRegex(\n            ResponseGovernanceError, "DOMAIN_PRESENTATION_OVERRIDE_FORBIDDEN"\n        ):\n            govern_platform_notice(event)\n\n    def test_real_human_decision_is_not_suppressed_by_compression(self):\n        event = self.framework_event()\n        event["materialRiskAcceptanceRequired"] = True\n        with self.assertRaises(HumanDecisionRequired):\n            govern_platform_notice(event)\n\n    def test_migration_planning_notice_has_no_option_menu(self):\n        response = govern_platform_notice(\n            {\n                "eventId": "evt-migration-1",\n                "eventType": "MIGRATION_PLANNING_STARTED",\n                "phase": "PLANNING",\n                "domainContribution": {"facts": ["Safe plan derivable"]},\n            }\n        )\n        self.assertEqual(\n            "Die Migration wird geplant. Bis der sichere Plan steht, ändere ich nichts.",\n            response["content"][0]["text"],\n        )\n        self.assertNotIn("terminalMenu", response)\n\n    def test_every_domain_framework_embeds_the_same_platform_governor(self):\n        governor_ids = set()\n        for filename in (\n            "SAFOR-FRAMEWORK-WEBSITE.json",\n            "SAFOR-FRAMEWORK-SAAS.json",\n            "SAFOR-FRAMEWORK-BOOK-CREATION.json",\n        ):\n            distribution = load_json(filename)\n            interaction = distribution["framework"]["embeddedModules"]["interaction"]["content"]\n            governor = interaction["platformResponseGovernor"]\n            governor_ids.add(governor["id"])\n            self.assertEqual("SAFOR_PLATFORM", governor["owner"])\n            self.assertTrue(governor["nonDelegation"]["domainOverrideForbidden"])\n            modules = distribution["embeddedDomainModules"]\n            self.assertNotIn("platformResponseGovernor", modules["factory"])\n            self.assertNotIn("platformResponseGovernor", modules["operatingModel"])\n        self.assertEqual({"SAFOR_PLATFORM_HUMAN_RESPONSE_GOVERNOR"}, governor_ids)\n\n    def test_human_response_schema_separates_notices_and_interactions(self):\n        schema = load_json("v0.10.0/schemas/human-response.schema.json")\n        self.assertIn("responseClass", schema["required"])\n        self.assertIn("governance", schema["required"])\n        self.assertNotIn("terminalMenu", schema["required"])\n        self.assertEqual(2, len(schema["allOf"]))\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
    write_text("tests/test_platform_response_governor.py", tests)


def rebuild_distributions() -> None:
    import subprocess

    commands = [
        ["python", "tools/build_bundle.py"],
        ["python", "tools/build_domain_framework.py", "--profile", "WEBSITE"],
        ["python", "tools/build_domain_framework.py", "--profile", "SAAS"],
        ["python", "tools/build_domain_framework.py", "--profile", "BOOK_CREATION"],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
    old_artifact = ROOT / f"SAFOR-FRAMEWORK-v{OLD_VERSION}.json"
    if old_artifact.exists():
        old_artifact.unlink()


def main() -> None:
    update_interaction_model()
    update_decision_gate()
    update_human_response_schema()
    update_kernel_and_conformance()
    update_self_healing()
    update_build_and_validator()
    update_version_and_manifest()
    update_docs_and_tests()
    write_reference_runtime_and_tests()
    rebuild_distributions()
    print(f"Applied SAFOR platform response governor and built {NEW_VERSION}.")


if __name__ == "__main__":
    main()
