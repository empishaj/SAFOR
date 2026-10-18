#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.14.0-rc.2"


def replace(relative: str, old: str, new: str, *, required: bool = False) -> None:
    target = ROOT / relative
    text = target.read_text(encoding="utf-8")
    if required and old not in text:
        raise RuntimeError(f"Expected text not found in {relative}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def write(relative: str, content: str) -> None:
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


# Make the shared commercial/domain resolver explicitly support both the
# retained 0.13 compatibility baseline and the new 0.14 product contracts.
replace(
    "runtime/bootstrap_policy.py",
    'entitlement.get("schemaVersion") != "0.13.0"',
    'entitlement.get("schemaVersion") not in {"0.13.0", "0.14.0"}',
    required=True,
)
replace(
    "runtime/bootstrap_policy.py",
    'delivery_evidence.get("schemaVersion") != "0.13.0"',
    'delivery_evidence.get("schemaVersion") not in {"0.13.0", "0.14.0"}',
    required=True,
)
replace(
    "runtime/bootstrap_policy.py",
    'catalog.get("schemaVersion") != "0.13.0"',
    'catalog.get("schemaVersion") not in {"0.13.0", "0.14.0"}',
    required=True,
)
replace(
    "runtime/bootstrap_policy.py",
    'package.get("schemaVersion") not in {"0.12.0", "0.13.0"}',
    'package.get("schemaVersion") not in {"0.12.0", "0.13.0", "0.14.0"}',
)

# Migrate all tests that exercise the current public-evaluation route to the
# new catalog. Historical tests may continue to use pinned older catalogs.
replace(
    "tests/test_domain_framework_distributions.py",
    'load_json("v0.13.0/package-catalog.json")',
    'load_json("v0.14.0/package-catalog.json")',
    required=True,
)
replace(
    "tests/test_public_evaluation_access.py",
    'load_json("v0.13.0/package-catalog.json")',
    'load_json("v0.14.0/package-catalog.json")',
    required=True,
)

# Repository hygiene now retains v0.14 as the active source tree and keeps
# v0.10-v0.13 only as explicit compatibility/audit baselines.
replace(
    "tests/test_repository_hygiene.py",
    '{"v0.10.0", "v0.11.0", "v0.12.0", "v0.13.0"}',
    '{"v0.10.0", "v0.11.0", "v0.12.0", "v0.13.0", "v0.14.0"}',
    required=True,
)
replace(
    "tests/test_repository_hygiene.py",
    "# The rc.6 bundle resolves authoritative modules only from these source\n        # baselines. Earlier versions remain recoverable through Git history.",
    "# v0.14 is the active source tree. v0.10-v0.13 remain explicit\n        # compatibility and audit baselines; earlier versions are Git history.",
)

# Remove the obsolete assertion that production chat use requires a host
# runtime. Stronger host enforcement remains optional, not an end-user install.
replace(
    "tests/test_user_onboarding.py",
    '        self.assertIn("Production use therefore requires an integrated SAFOR host/runtime boundary", self.readme)\n',
    '        self.assertIn("Optional host integration can provide stronger machine enforcement", self.readme)\n        self.assertIn("does not require a separately installed customer runtime", self.readme)\n        self.assertNotIn("Production use therefore requires an integrated SAFOR host/runtime boundary", self.readme)\n',
    required=True,
)

# Keep the README aligned with the actually materialized v0.14 packages.
for old, new in (
    ("safor.factory.website-delivery@1.1.0", "safor.factory.website-delivery@1.2.0"),
    ("safor.om.website-team@1.1.0", "safor.om.website-team@1.2.0"),
    ("safor.factory.software-delivery@1.7.0-test.1", "safor.factory.software-delivery@1.8.0-test.1"),
    ("safor.om.saas-engineering@1.7.0-test.1", "safor.om.saas-engineering@1.8.0-test.1"),
    ("safor.factory.book-production@1.0.0-test.1", "safor.factory.book-production@1.1.0-test.1"),
    ("safor.om.book-authoring@1.0.0-test.1", "safor.om.book-authoring@1.1.0-test.1"),
    ("v0.13.0/packages/factories/website-delivery/1.1.0/package.json", "v0.14.0/packages/factories/website-delivery/1.2.0/package.json"),
    ("v0.13.0/packages/operating-models/website-team/1.1.0/package.json", "v0.14.0/packages/operating-models/website-team/1.2.0/package.json"),
    ("The rc.6 SaaS and Book distributions", "The current SaaS and Book distributions"),
    ("Paid package access in rc.6", "Paid package access in the current release candidate"),
    ("The Framework/package/licensing boundary and public evaluation reference bridge are machine-tested.", "The Framework/package/licensing boundary and public evaluation reference bridge are machine-tested; the new v0.14 real-Git E2E remains an explicit blocker."),
):
    replace("README.md", old, new)
replace(
    "README.md",
    "The retained source baselines are exactly `v0.10.0`, `v0.11.0`, `v0.12.0` and `v0.13.0`, because the executable rc.6 bundle resolves modules from those four trees. Earlier product evolution remains auditable through commits and merged pull requests.",
    "The active source tree is `v0.14.0`. `v0.10.0` through `v0.13.0` remain explicit compatibility and audit baselines; earlier product evolution remains auditable through Git history.",
)

# Enrich the communication contract with the platform-owned rendering fields
# used by the integrated v0.14 validator.
communication_path = ROOT / "v0.14.0/agent-communication-model.json"
communication = json.loads(communication_path.read_text(encoding="utf-8"))
communication["owner"] = "SAFOR_PLATFORM"
for forbidden in ("MENU", "FACTORY_PRESENTATION_OVERRIDE", "OPERATING_MODEL_PRESENTATION_OVERRIDE"):
    if forbidden not in communication["forbiddenContent"]:
        communication["forbiddenContent"].append(forbidden)
communication["rendering"] = {
    "singleLine": True,
    "menuForbidden": True,
    "substantiveContentStoredInGit": True,
}
communication_path.write_text(json.dumps(communication, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Replace the rc.8-specific integration test with one that validates the
# canonical v0.14 contracts and module names actually shipped to users.
write(
    "tests/test_human_notice_conformance.py",
    '''import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.14.0-rc.2"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class HumanNoticeConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.framework = load("SAFOR-FRAMEWORK.json")
        cls.modules = cls.framework["embeddedModules"]
        cls.kernel = cls.modules["kernel"]["content"]

    def test_ordinary_chat_is_primary_and_runtime_install_is_not_required(self):
        model = self.modules["chatExecution"]["content"]
        self.assertEqual("DECLARATIVE_LLM_CHAT", model["primaryExecutionMode"])
        self.assertFalse(model["customerInstalledRuntimeRequired"])
        self.assertFalse(model["referenceImplementations"]["requiredForNormalChatUse"])

    def test_human_go_is_the_only_agent_activation(self):
        activation = self.modules["agentActivation"]["content"]["chatAgentActivationContract"]
        self.assertEqual("HUMAN_GO_REQUIRED", activation["activationMode"])
        self.assertEqual("GO", activation["acceptedHumanMessage"])
        for field in ("backgroundWakeupAssumed", "gitEventActivationAllowed", "pollingActivationAllowed", "automationActivationAllowed", "hostTriggerActivationAllowed", "schedulerMayActivateChat"):
            self.assertFalse(activation[field])
        self.assertEqual("ATOMIC_COMPARE_AND_SWAP_WITH_SINGLE_USE_GO_EVIDENCE", activation["claimMode"])
        self.assertTrue(activation["stringSubstringEvidenceForbidden"])

    def test_agent_identity_requires_display_name_binding_and_fail_closed_rebind(self):
        schema = self.modules["schemaAgentIdentity"]["content"]
        required = set(schema["required"])
        self.assertTrue({"agentId", "displayName", "chatBinding", "activationContract", "communicationContractRef"}.issubset(required))
        chat_binding = schema["$defs"]["chatBinding"]
        self.assertIn("onUncertain", chat_binding["required"])
        activation = schema["allOf"][0]["then"]["properties"]["activationContract"]["allOf"][0]["properties"]
        self.assertEqual("HUMAN_GO_REQUIRED", activation["activationMode"]["const"])
        self.assertFalse(activation["automationActivationAllowed"]["const"])

    def test_job_requires_domain_all_response_and_chat_contracts(self):
        schema = self.modules["schemaAgentJob"]["content"]
        self.assertTrue({"domainContext", "responseContracts", "communicationContract"}.issubset(schema["required"]))
        required_responses = set(schema["$defs"]["responseContracts"]["required"])
        self.assertTrue({"JOB_RESULT", "JOB_ERROR", "CLARIFICATION_REQUEST", "CAPABILITY_MISMATCH", "IMPROVEMENT_PROPOSAL"}.issubset(required_responses))

    def test_response_contract_has_exact_five_types(self):
        model = self.modules["agentResponseContract"]["content"]
        self.assertEqual({"JOB_RESULT", "JOB_ERROR", "CLARIFICATION_REQUEST", "CAPABILITY_MISMATCH", "IMPROVEMENT_PROPOSAL"}, set(model["responseTypes"]))
        for response_type, contract in model["responseTypes"].items():
            self.assertTrue(contract["templateRef"].startswith("templates/responses/"), response_type)

    def test_agent_chat_is_platform_owned_single_line_and_non_domain(self):
        model = self.modules["agentCommunication"]["content"]
        self.assertEqual("SAFOR_PLATFORM", model["owner"])
        self.assertTrue(model["humanBoundary"]["masterIsOnlyDomainInterface"])
        self.assertFalse(model["humanBoundary"]["agentMayAskHumanDomainQuestions"])
        self.assertEqual(1, model["budgets"]["maxLines"])
        self.assertTrue(model["rendering"]["singleLine"])
        self.assertTrue(model["rendering"]["menuForbidden"])
        self.assertIn("MENU", model["forbiddenContent"])

    def test_master_status_forbids_full_scan_and_requires_git_references(self):
        model = self.modules["masterStatus"]["content"]
        self.assertTrue(model["principles"]["fullRepositoryScanForRoutineStatusForbidden"])
        self.assertTrue(model["principles"]["allReportedResultsRequireGitReference"])
        self.assertTrue(model["principles"]["staleProjectionMustBeDisclosed"])

    def test_all_domain_distributions_embed_integrated_v014_contracts(self):
        required = {"chatExecution", "agentActivation", "agentResponseContract", "agentCommunication", "masterStatus", "schemaHumanGoEvidence", "schemaAgentResponse", "schemaAgentChatOutput", "executionAttempt"}
        for file_name in ("SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json", "SAFOR-FRAMEWORK-BOOK-CREATION.json"):
            distribution = load(file_name)
            framework = distribution["framework"]
            self.assertEqual(VERSION, framework["bundleVersion"])
            self.assertEqual("0.14.0", framework["schemaVersion"])
            self.assertTrue(required.issubset(framework["embeddedModules"]))

    def test_platform_not_factory_or_operating_model_owns_human_communication(self):
        self.assertTrue(self.kernel["kernelPrinciples"]["platformOwnsHumanVisibleCommunication"])
        self.assertTrue(self.kernel["kernelPrinciples"]["minimalSubagentChatStatusOnly"])
        for file_name in ("SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json", "SAFOR-FRAMEWORK-BOOK-CREATION.json"):
            distribution = load(file_name)
            for package in distribution["embeddedDomainModules"].values():
                serialized = json.dumps(package)
                self.assertNotIn("humanGoActivationOverride", serialized)
                self.assertNotIn("agentChatResponseLength", serialized)


if __name__ == "__main__":
    unittest.main()
''',
)

# The integrated validator validates the uploaded product, not an old source
# generation beside it.
write(
    "tools/validate_safor.py",
    '''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.bootstrap_policy import evaluate_domain_framework_pair, validate_domain_package
from runtime.public_evaluation_access import resolve_public_evaluation_access
from tools.build_domain_framework import build_distribution, validate_distribution

VERSION = "0.14.0-rc.2"
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
    return hashlib.sha1(f"blob {len(raw)}\\0".encode("utf-8") + raw).hexdigest()


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
for field in ("backgroundWakeupAssumed", "gitEventActivationAllowed", "pollingActivationAllowed", "automationActivationAllowed", "hostTriggerActivationAllowed", "schedulerMayActivateChat"):
    if activation.get(field) is not False:
        fail(f"Forbidden activation trigger enabled: {field}")
if activation.get("claimMode") != "ATOMIC_COMPARE_AND_SWAP_WITH_SINGLE_USE_GO_EVIDENCE":
    fail("Atomic single-use GO claim mode missing")

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
if not {"agentId", "displayName", "chatBinding", "activationContract"}.issubset(set(identity_schema.get("required", []))):
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
    committed = load(profile.get("outputFile", ""))
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

if errors:
    print("SAFOR validation: FAIL")
    for error in errors:
        print("-", error)
    raise SystemExit(1)
print(f"SAFOR validation: PASS ({len(modules)}/{len(modules)} v0.14 modules and recovery profiles)")
''',
)

print("SAFOR v0.14 bundle compatibility patch applied")
