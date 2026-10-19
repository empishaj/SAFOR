#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.bootstrap_policy import evaluate_domain_framework_pair, validate_domain_package
from runtime.public_evaluation_access import resolve_public_evaluation_access
from tools.build_domain_framework import build_distribution, validate_distribution

VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
SCHEMA = "0.14.0"
errors = []


def fail(message):
    errors.append(message)


def load(relative):
    try:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{relative}: cannot parse JSON: {exc}")
        return {}


def blob_sha(relative):
    raw = (ROOT / relative).read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
framework = load("SAFOR-FRAMEWORK.json")
versioned_path = f"SAFOR-FRAMEWORK-v{version}.json"
versioned = load(versioned_path)
manifest = load("RELEASE-MANIFEST.json")
config = load("v0.14.0/bundle-module-map.json")

if version != VERSION:
    fail(f"VERSION must be {VERSION}, got {version}")
if framework.get("format") != "SAFOR_FRAMEWORK_SINGLE_FILE":
    fail("Framework format mismatch")
if framework.get("schemaVersion") != SCHEMA:
    fail("Framework schemaVersion must be 0.14.0")
if framework.get("bundleVersion") != VERSION:
    fail("Framework bundleVersion mismatch")
if framework != versioned:
    fail("Versioned Framework must exactly equal SAFOR-FRAMEWORK.json")
if manifest.get("version") != VERSION or manifest.get("sourceRoot") != "v0.14.0":
    fail("Release manifest version/sourceRoot mismatch")
if manifest.get("status") != "RELEASE_CANDIDATE":
    fail("Release status must remain RELEASE_CANDIDATE")
if manifest.get("distributable") != versioned_path:
    fail("Release distributable mismatch")

modules = framework.get("embeddedModules", {})
required_modules = set(config.get("modulePaths", {}))
if set(modules) != required_modules:
    fail(f"Embedded module set mismatch: missing={sorted(required_modules-set(modules))}, extra={sorted(set(modules)-required_modules)}")
profiles = modules.get("moduleSelfHealing", {}).get("content", {}).get("moduleProfiles", [])
profile_by_key = {item.get("moduleKey"): item for item in profiles}
if set(profile_by_key) != set(modules):
    fail(f"Recovery coverage mismatch: missing={sorted(set(modules)-set(profile_by_key))}, extra={sorted(set(profile_by_key)-set(modules))}")

integrity = framework.get("integrityManifest", {})
for key, module in modules.items():
    source = module.get("sourcePath")
    if not isinstance(source, str) or not source.startswith("v0.14.0/"):
        fail(f"{key}: source must be v0.14.0, got {source}")
        continue
    if not (ROOT / source).is_file():
        fail(f"{key}: source missing: {source}")
        continue
    actual_blob = blob_sha(source)
    if module.get("sourceBlobSha") != actual_blob:
        fail(f"{key}: embedded source blob mismatch")
    if integrity.get(key, {}).get("sourceBlobSha") != actual_blob:
        fail(f"{key}: integrity manifest blob mismatch")
    if module.get("selfHealingProfileId") != profile_by_key.get(key, {}).get("profileId"):
        fail(f"{key}: recovery profile binding mismatch")
    if "/packages/factories/" in source or "/packages/operating-models/" in source:
        fail(f"Generic Framework embeds forbidden domain package source: {source}")

for reference, target in framework.get("referenceResolution", {}).items():
    if target not in modules:
        fail(f"Unresolved reference target {reference}->{target}")

kernel = modules.get("kernel", {}).get("content", {})
if kernel != load("v0.14.0/SAFOR-MASTER.json"):
    fail("Embedded kernel differs from canonical v0.14 kernel")
if kernel.get("schemaVersion") != SCHEMA or kernel.get("kernelVersion") != SCHEMA:
    fail("Kernel version mismatch")
for principle in ("structuredHumanGoEvidenceRequired", "atomicAgentClaimRequired", "verifiedResponseReadbackBeforeMasterCompletionClaim", "statusFreshnessDerivedNotAsserted", "partialProductControlWriteReconciliation", "requirementsEvidenceDimensionsSeparated"):
    if kernel.get("kernelPrinciples", {}).get(principle) is not True:
        fail(f"Kernel principle missing: {principle}")

chat = modules.get("chatExecution", {}).get("content", {})
if chat.get("primaryExecutionMode") != "DECLARATIVE_LLM_CHAT" or chat.get("customerInstalledRuntimeRequired") is not False:
    fail("Chat-first/no-customer-runtime boundary invalid")
activation = modules.get("agentActivation", {}).get("content", {}).get("chatAgentActivationContract", {})
if activation.get("activationMode") != "HUMAN_GO_REQUIRED" or activation.get("acceptedHumanMessage") != "GO":
    fail("HUMAN-GO activation contract invalid")
for field in ("backgroundWakeupAssumed", "gitEventActivationAllowed", "pollingActivationAllowed", "automationActivationAllowed", "hostTriggerActivationAllowed", "schedulerMayActivateChat", "masterMayActivateChat", "masterMaySynthesizeHumanGo", "masterMayCreateHumanGoEvidence"):
    if activation.get(field) is not False:
        fail(f"Forbidden activation trigger enabled: {field}")
if activation.get("activationAuthority") != "HUMAN_ONLY":
    fail("Normal chat-agent activation authority must be HUMAN_ONLY")
if activation.get("claimMode") != "ATOMIC_AGENT_STATE_CLAIM_WITH_SINGLE_USE_GO_EVIDENCE":
    fail("Atomic single-use GO claim mode missing")
activation_model = modules.get("agentActivation", {}).get("content", {})
preclaim = set(activation_model.get("onHumanGo", {}).get("preClaimChecks", []))
required_preclaim = {
    "JOB_CONTRACT_POINTER_EXACT_MATCH",
    "AGENT_JOB_SCHEMA_VALID",
    "AGENT_JOB_RUNTIME_CONTRACT_VALID",
    "JOB_CLAIM_AND_RESPONSE_BINDINGS_COMPLETE",
}
missing_preclaim = sorted(required_preclaim - preclaim)
if missing_preclaim:
    fail(f"Agent Job fail-closed preclaim checks missing: {missing_preclaim}")
rearm = activation_model.get("onHumanGo", {}).get("preSelectionAgentStateHandling", {})
if rearm.get("rearmStateOwner") != "AGENT":
    fail("Agent State rearm owner must be AGENT")
if rearm.get("masterMayWriteAgentState") is not False:
    fail("MASTER must not rearm Agent State")
if rearm.get("secondHumanGoRequired") is not False:
    fail("Safe settled-state rearm must continue the same direct HUMAN GO")
if set(rearm.get("settledMasterStatuses", [])) != {
    "REJECTED", "ACCEPTED", "INTEGRATED", "CANCELED", "SUPERSEDED"
}:
    fail("Agent State rearm terminal MASTER status set invalid")
if rearm.get("rearmForbiddenDuringInitialization") is not True:
    fail("Agent State rearm must be forbidden during initialization/reinitialization")
if rearm.get("rearmRequiresSeparateDirectHumanGo") is not True:
    fail("Agent State rearm must require a later separate direct HUMAN GO")
if rearm.get("rearmHumanInputSource") != "DIRECT_HUMAN_INPUT_IN_INITIALIZED_AGENT_CHAT":
    fail("Agent State rearm HUMAN source invalid")
if rearm.get("rearmHumanMessage") != "GO":
    fail("Agent State rearm HUMAN message must be GO")
if rearm.get("rearmStateMustRetainAllRequiredTopLevelFields") is not True:
    fail("Agent State rearm must retain all required top-level fields")
if rearm.get("rearmSessionAndCurrentJobRepresentation") != "EXPLICIT_NULL":
    fail("Agent State rearm must persist session/currentJob as explicit null")
if rearm.get("readyStatusForbiddenIfPersistedStateInvalid") is not True:
    fail("READY must be forbidden for schema-invalid persisted Agent State")

responses = modules.get("agentResponseContract", {}).get("content", {}).get("responseTypes", {})
expected_responses = {"JOB_RESULT", "JOB_ERROR", "CLARIFICATION_REQUEST", "CAPABILITY_MISMATCH", "IMPROVEMENT_PROPOSAL"}
if set(responses) != expected_responses:
    fail("Typed response family mismatch")
communication = modules.get("agentCommunication", {}).get("content", {})
if communication.get("owner") != "SAFOR_PLATFORM":
    fail("Agent communication must be platform-owned")
if communication.get("humanBoundary", {}).get("masterIsOnlyDomainInterface") is not True:
    fail("MASTER-only HUMAN interface missing")
if communication.get("budgets", {}).get("maxLines") != 1 or communication.get("rendering", {}).get("menuForbidden") is not True:
    fail("Minimal single-line no-menu agent chat invalid")
master_status = modules.get("masterStatus", {}).get("content", {})
if master_status.get("principles", {}).get("fullRepositoryScanForRoutineStatusForbidden") is not True:
    fail("MASTER routine full-scan prohibition missing")

identity_schema = modules.get("schemaAgentIdentity", {}).get("content", {})
if not {"agentId", "displayName", "inboxBinding", "activationContract"}.issubset(set(identity_schema.get("required", []))):
    fail("Agent identity required fields incomplete")
job_schema = modules.get("schemaAgentJob", {}).get("content", {})
if not {"domainContext", "responseContracts", "communicationContract"}.issubset(set(job_schema.get("required", []))):
    fail("Agent job contract required fields incomplete")
if not expected_responses.issubset(set(job_schema.get("$defs", {}).get("responseContracts", {}).get("required", []))):
    fail("Agent job does not bind all response types")

catalog = load("v0.14.0/package-catalog.json")
if catalog.get("format") != "SAFOR_PACKAGE_CATALOG" or catalog.get("schemaVersion") != SCHEMA:
    fail("v0.14 package catalog invalid")
profiles_catalog = load("v0.14.0/domain-framework-profiles.json")
for profile in profiles_catalog.get("profiles", []):
    profile_id = profile.get("id")
    factory = load(profile.get("defaultFactory", {}).get("publicPath", ""))
    operating_model = load(profile.get("defaultOperatingModel", {}).get("publicPath", ""))
    creation_type = profile.get("creationType")
    domain_id = profile.get("domainId")
    for package, label in ((factory, "Factory"), (operating_model, "Operating Model")):
        result = validate_domain_package(package, VERSION, creation_type)
        if result.get("valid") is not True:
            fail(f"{profile_id} {label} invalid: {result}")
    pair = evaluate_domain_framework_pair(factory, operating_model, VERSION, creation_type, domain_id)
    if pair.get("compatible") is not True:
        fail(f"{profile_id} package pair incompatible: {pair}")
    built = build_distribution(profile_id)
    validation = validate_distribution(built, profile_id)
    if validation.get("valid") is not True:
        fail(f"{profile_id} distribution invalid: {validation}")
    committed = load(profile.get("distributionFile", ""))
    if committed != built:
        fail(f"{profile_id} committed distribution is not reproducible")
    if committed.get("framework", {}).get("bundleVersion") != VERSION:
        fail(f"{profile_id} does not embed {VERSION}")

for distribution_file, access_file in (("SAFOR-FRAMEWORK-SAAS.json", "SAFOR-TEST-ACCESS-SAAS.json"), ("SAFOR-FRAMEWORK-BOOK-CREATION.json", "SAFOR-TEST-ACCESS-BOOK-CREATION.json")):
    access = load(access_file)
    result = resolve_public_evaluation_access(load(distribution_file), access, catalog, access_file_name=access_file)
    if result.get("outcome") != "PUBLIC_EVALUATION_ACCESS_RESOLVED":
        fail(f"{distribution_file} evaluation access does not resolve: {result}")
    if access.get("restrictions", {}).get("productionAuthorization") is not False:
        fail(f"{access_file} must never authorize production")

conformance = modules.get("conformance", {}).get("content", {})
if conformance.get("schemaVersion") != SCHEMA:
    fail("Conformance model must be 0.14.0")
traceability = load("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
if len(traceability.get("requirements", [])) != 33:
    fail("Traceability must contain exactly 33 requirements")

runpy.run_path(str(ROOT / 'tools/validate_audit_remediation.py'), run_name='__main__')

if errors:
    print("SAFOR validation: FAIL")
    for error in errors:
        print("-", error)
    raise SystemExit(1)
print(f"SAFOR validation: PASS ({len(modules)}/{len(modules)} v0.14 modules and recovery profiles)")
