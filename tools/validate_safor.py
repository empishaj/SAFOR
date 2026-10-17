#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []


def fail(message):
    errors.append(message)


def load_json(path):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{path}: cannot parse JSON: {exc}")
        return {}


framework = load_json("SAFOR-FRAMEWORK.json")
manifest = load_json("RELEASE-MANIFEST.json")
kernel_file = load_json("v0.12.0/SAFOR-MASTER.json")
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

if framework.get("format") != "SAFOR_FRAMEWORK_SINGLE_FILE":
    fail("Framework bundle format must be SAFOR_FRAMEWORK_SINGLE_FILE.")
if framework.get("schemaVersion") != "0.12.0":
    fail("Framework schemaVersion must be 0.12.0.")
if framework.get("bundleVersion") != version:
    fail("Framework bundle version must match VERSION.")
if framework.get("definitionId") != "safor-framework":
    fail("Framework definitionId mismatch.")
if framework.get("distributionMode") != "FRAMEWORK_PLUS_EXTERNAL_DOMAIN_PACKAGES":
    fail("Framework distribution mode mismatch.")

modules = framework.get("embeddedModules", {})
required_modules = {
    "kernel","initialization","interaction","humanDecisionGate","selfHealing","moduleSelfHealing",
    "agentWorkspace","agentJobContract","multiAgentScheduler","repositoryPolicy","packageRegistry",
    "packageDistribution","commercialEntitlement","workspaceModel","packageCatalog",
    "providerGithub","providerGitlab","schemaPackageManifest","schemaControlState",
    "schemaValueStreamState","schemaExecutionState","schemaWorkItem","schemaProject","schemaBindings",
    "schemaDecisionRecord","schemaEvidenceRecord","schemaInteractionMenu","schemaHumanResponse",
    "schemaHumanCognitiveLoadPolicy","schemaHumanDecisionGate","schemaSelfHealingRecord",
    "schemaModuleRecoveryProfile","schemaAgentRegistry","schemaAgentIdentity","schemaAgentInboxIndex",
    "schemaAgentState","schemaAgentJob","schemaAgentJobState","schemaAgentResult",
    "schemaSchedulerState","schemaDispatchWave","schemaResourceLease","deterministicControl",
    "eventModel","predicateRegistry","transitionRegistry","effectModel","acceptanceModel",
    "schemaEvent","schemaPredicate","schemaTransition","schemaEffectIntent","schemaTransitionRecord",
    "schemaStateSnapshot","schemaAcceptanceContract","schemaReviewDecision","schemaAuthorityDecision",
    "schemaPackageCatalog","schemaEntitlement","schemaWorkspaceBinding","conformance"
}
missing = sorted(required_modules - set(modules))
extra = sorted(set(modules) - required_modules)
if missing:
    fail("Missing embedded Framework modules: " + ", ".join(missing))
if extra:
    fail("Unexpected embedded Framework modules: " + ", ".join(extra))
if len(modules) != 61:
    fail(f"Expected exactly 61 embedded Framework modules, got {len(modules)}.")

forbidden_domain_module_keys = {
    "operatingModelSaas","operatingModelBook","factorySoftwareWebsite","factoryBook"
}
leaked_keys = sorted(forbidden_domain_module_keys & set(modules))
if leaked_keys:
    fail("Public Framework embeds forbidden domain-package module keys: " + ", ".join(leaked_keys))
for key, module in modules.items():
    source_path = str(module.get("sourcePath", ""))
    if "/packages/factories/" in source_path or "/packages/operating-models/" in source_path:
        fail(f"Public Framework embeds domain package content via {key}: {source_path}")
    if not source_path.startswith(("v0.10.0/","v0.11.0/","v0.12.0/")):
        fail(f"Embedded module {key} comes from unsupported source baseline: {source_path}")

# Exact recovery-profile coverage.
module_recovery = modules.get("moduleSelfHealing", {}).get("content", {})
profiles = module_recovery.get("moduleProfiles", [])
profile_by_key = {}
profile_ids = set()
for profile in profiles:
    key = profile.get("moduleKey")
    pid = profile.get("profileId")
    if not key or not pid:
        fail("Module recovery profile missing moduleKey/profileId.")
        continue
    if key in profile_by_key:
        fail(f"Duplicate recovery profile for module {key}.")
    if pid in profile_ids:
        fail(f"Duplicate recovery profileId {pid}.")
    profile_by_key[key] = profile
    profile_ids.add(pid)
if set(profile_by_key) != set(modules):
    fail(
        "Recovery profile coverage mismatch: "
        f"missing={sorted(set(modules)-set(profile_by_key))}, "
        f"unknown={sorted(set(profile_by_key)-set(modules))}"
    )
if len(profiles) != 61:
    fail(f"Expected 61 recovery profiles, got {len(profiles)}.")
coverage = module_recovery.get("coverageContract", {})
for field in ("exactCoverageRequired","oneProfilePerEmbeddedModule","noUnprofiledEmbeddedModules","noProfilesForUnknownModuleKeys"):
    if coverage.get(field) is not True:
        fail(f"Module recovery coverage contract {field} must be true.")

valid_repairability = {
    "IMMUTABLE_VALIDATE_ONLY","RESTORE_FROM_VERIFIED_SOURCE",
    "REGENERATE_DERIVED_ONLY","REBIND_EXTERNAL_CAPABILITY"
}
integrity = framework.get("integrityManifest", {})
for key, module in modules.items():
    profile = profile_by_key.get(key, {})
    for field in (
        "profileId","moduleKey","moduleClass","authorityType","repairability",
        "failureDetectors","automaticRepairs","forbiddenRepairs","retryBudget",
        "verification","escalation"
    ):
        if field not in profile:
            fail(f"Recovery profile {key} missing {field}.")
    if profile.get("repairability") not in valid_repairability:
        fail(f"Recovery profile {key} repairability invalid.")
    pid = profile.get("profileId")
    if module.get("selfHealingProfileId") != pid:
        fail(f"Embedded module {key} recovery profile ID mismatch.")
    if integrity.get(key, {}).get("selfHealingProfileId") != pid:
        fail(f"Integrity manifest {key} recovery profile ID mismatch.")
    if integrity.get(key, {}).get("sourceBlobSha") != module.get("sourceBlobSha"):
        fail(f"Integrity manifest {key} blob SHA mismatch.")

refs = framework.get("referenceResolution", {})
for ref, target in refs.items():
    if target not in modules:
        fail(f"Unresolved Framework reference {ref}->{target}.")

# Release artifact integrity.
if manifest.get("version") != version:
    fail("Release manifest version must match VERSION.")
if manifest.get("status") != "RELEASE_CANDIDATE":
    fail("Release status must remain RELEASE_CANDIDATE.")
if manifest.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Release canonical repository mismatch.")
if manifest.get("sourceRoot") != "v0.12.0":
    fail("Release sourceRoot must be v0.12.0.")
expected_versioned = f"SAFOR-FRAMEWORK-v{version}.json"
if manifest.get("distributable") != expected_versioned:
    fail("Release distributable must be the versioned SAFOR Framework.")
if manifest.get("latestAlias") != "SAFOR-FRAMEWORK.json":
    fail("Release latestAlias must be SAFOR-FRAMEWORK.json.")
versioned_framework = load_json(expected_versioned)
if versioned_framework != framework:
    fail("Versioned Framework artifact must exactly match SAFOR-FRAMEWORK.json.")

runtime = framework.get("runtimeContract", {})
if runtime.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Runtime canonical repository mismatch.")
if runtime.get("canonicalBranch") != "main":
    fail("Runtime canonical branch must be main.")
domain_policy = runtime.get("domainPackagePolicy", {})
if domain_policy.get("embeddedDomainPackageContent") is not False:
    fail("Public Framework must declare embeddedDomainPackageContent=false.")
if domain_policy.get("paidPublicResolutionForbidden") is not True:
    fail("Paid public package resolution must be forbidden.")
if domain_policy.get("paidRequiresVerifiedEntitlement") is not True:
    fail("Paid package binding must require verified entitlement.")
if "HUMAN-selected REMOTE_GIT or LOCAL_GIT" not in runtime.get("projectWorkspaceRule", ""):
    fail("Runtime projectWorkspaceRule must require HUMAN-selected remote/local Git.")
if "never grants organizational authority" not in runtime.get("entitlementRule", ""):
    fail("Runtime entitlement rule must separate package access from authority.")
if framework.get("productRepository", {}).get("projectTargetForbidden") is not True:
    fail("Canonical SAFOR product repository must be forbidden as project target.")

control_policy = framework.get("controlWorkspacePolicy", {})
if control_policy.get("REMOTE_GIT", {}).get("strategy") != "REMOTE_SEPARATE_SAFOR_MEMORY":
    fail("REMOTE_GIT control strategy must use separate safor-memory.")
if control_policy.get("LOCAL_GIT", {}).get("strategy") != "LOCAL_MASTER_CONTROL_ROOT":
    fail("LOCAL_GIT control strategy must use local MASTER control root.")
if control_policy.get("LOCAL_GIT", {}).get("root") != ".safor/":
    fail("LOCAL_GIT control root must be .safor/.")

# 0.12 modules must be pinned from 0.12 source.
for key in (
    "kernel","initialization","selfHealing","moduleSelfHealing","repositoryPolicy","packageRegistry",
    "packageDistribution","commercialEntitlement","workspaceModel","packageCatalog",
    "schemaProject","schemaBindings","schemaPackageCatalog","schemaEntitlement",
    "schemaWorkspaceBinding","conformance"
):
    if not str(modules.get(key, {}).get("sourcePath", "")).startswith("v0.12.0/"):
        fail(f"0.12 module {key} must come from v0.12.0 source.")

kernel = modules.get("kernel", {}).get("content", {})
if kernel != kernel_file:
    fail("Embedded kernel must equal v0.12.0/SAFOR-MASTER.json.")
if kernel.get("schemaVersion") != "0.12.0" or kernel.get("kernelVersion") != "0.12.0":
    fail("Kernel version/schemaVersion must be 0.12.0.")
for principle in (
    "modularDomainPackages","paidPackageContentExcludedFromPublicFramework",
    "freeWebsitePackagesPubliclyResolvable","commercialEntitlementRequiredForPaidPackages",
    "entitlementIndependentFromOrganizationalAuthority","humanOwnsProjectWorkspace",
    "localGitWorkspaceSupported","projectWorkspaceSeparateFromPackageSource",
    "frameworkRepositoryNeverProjectTarget"
):
    if kernel.get("kernelPrinciples", {}).get(principle) is not True:
        fail(f"Kernel principle {principle} must be true.")

for ref_field, expected in (
    ("packageDistributionModelRef","package-distribution-model.json"),
    ("commercialEntitlementModelRef","commercial-entitlement-model.json"),
    ("workspaceModelRef","workspace-model.json"),
    ("packageCatalogRef","package-catalog.json"),
    ("repositoryPolicyRef","repository-policy.json"),
    ("initializationModelRef","initialization-model.json"),
):
    if kernel.get(ref_field) != expected:
        fail(f"Kernel {ref_field} mismatch.")

invariants = {x.get("id") for x in kernel.get("invariants", [])}
for n in range(37, 166):
    inv = f"INV-{n:03d}"
    if inv not in invariants:
        fail(f"Missing invariant {inv}.")

# Package catalog/distribution/entitlement.
catalog = modules.get("packageCatalog", {}).get("content", {})
if catalog.get("format") != "SAFOR_PACKAGE_CATALOG" or catalog.get("schemaVersion") != "0.12.0":
    fail("Package catalog format/version mismatch.")
entries = catalog.get("entries", [])
entry_by_id = {}
for entry in entries:
    pid = entry.get("packageId")
    if pid in entry_by_id:
        fail(f"Duplicate package catalog entry {pid}.")
    entry_by_id[pid] = entry

for pid in ("safor.factory.software-delivery","safor.om.saas-engineering"):
    entry = entry_by_id.get(pid, {})
    if entry.get("accessMode") != "FREE_PUBLIC":
        fail(f"{pid} must be FREE_PUBLIC.")
    dist = entry.get("distribution", {})
    if dist.get("sourceClass") != "PUBLIC_CANONICAL_REPOSITORY" or not dist.get("path"):
        fail(f"{pid} must resolve from public canonical repository.")
    package_path = dist.get("path")
    package = load_json(package_path) if package_path else {}
    if package.get("packageId") != pid:
        fail(f"Public free package path for {pid} resolves wrong packageId.")
    if package.get("version") != entry.get("version"):
        fail(f"Public free package version mismatch for {pid}.")

for pid in ("safor.factory.book-production","safor.om.book-authoring"):
    entry = entry_by_id.get(pid, {})
    if entry.get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
        fail(f"{pid} must be PAID_ENTITLEMENT_REQUIRED.")
    dist = entry.get("distribution", {})
    if dist.get("sourceClass") != "ENTITLED_PACKAGE_SOURCE":
        fail(f"{pid} must use ENTITLED_PACKAGE_SOURCE.")
    if dist.get("publicModelPath", "NOT_NULL") is not None:
        fail(f"{pid} must not expose a public model path.")

profiles = {x.get("creationType"): x for x in catalog.get("creationProfiles", [])}
web = profiles.get("SOFTWARE_WEBSITE", {})
book = profiles.get("BOOK", {})
if web.get("accessMode") != "FREE_PUBLIC" or web.get("autoResolveFromPublicFrameworkGit") is not True:
    fail("SOFTWARE_WEBSITE must be FREE_PUBLIC and public-auto-resolvable.")
if book.get("accessMode") != "PAID_ENTITLEMENT_REQUIRED" or book.get("autoResolveFromPublicFrameworkGit") is not False:
    fail("BOOK must require paid entitlement and forbid public auto-resolution.")
if book.get("missingAccessOutcome") != "PACKAGE_ACCESS_REQUIRED":
    fail("BOOK missing access must produce PACKAGE_ACCESS_REQUIRED.")

distribution = modules.get("packageDistribution", {}).get("content", {})
if distribution.get("principles", {}).get("paidContentExcludedFromPublicFramework") is not True:
    fail("Distribution model must exclude paid content from public Framework.")
if distribution.get("sourceClasses", {}).get("PUBLIC_CANONICAL_REPOSITORY", {}).get("allowedAccessModes") != ["FREE_PUBLIC"]:
    fail("Public package source may serve FREE_PUBLIC only.")
if distribution.get("freeStarterProfile", {}).get("creationType") != "SOFTWARE_WEBSITE":
    fail("Free starter profile must be SOFTWARE_WEBSITE.")

entitlement = modules.get("commercialEntitlement", {}).get("content", {})
for field in (
    "paidRequiresVerifiedEntitlement","selfAssertedEntitlementForbidden",
    "packagePossessionAloneIsNotVerifiedEntitlement","entitlementCannotGrantOperatingModelAuthority",
    "entitlementCannotGrantProviderRights","entitlementCannotExpandProjectScope",
    "exactPackageAndVersionCoverageRequired"
):
    if entitlement.get("rules", {}).get(field) is not True:
        fail(f"Commercial entitlement rule {field} must be true.")
allowed_methods = set(entitlement.get("allowedVerificationMethods", []))
if allowed_methods != {"AUTHORIZED_ENTITLEMENT_PROVIDER_READBACK","VERIFIED_OFFLINE_SIGNATURE"}:
    fail("Commercial entitlement verification method set mismatch.")

registry = modules.get("packageRegistry", {}).get("content", {})
if registry.get("catalogRef") != "package-catalog.json":
    fail("Package registry must reference package catalog.")
for package in registry.get("technicalPackages", []):
    if package.get("packageId") in ("safor.factory.book-production","safor.om.book-authoring"):
        fail("Paid book packages must not be public technical package paths.")
for req in registry.get("externalCommercialRequirements", []):
    if req.get("accessMode") != "PAID_ENTITLEMENT_REQUIRED" or req.get("publicContentResolutionForbidden") is not True:
        fail("Commercial package requirement must forbid public content resolution.")

# Technical compatibility of free starter pair.
free_factory = load_json("v0.10.0/packages/factories/software-delivery/1.4.0/package.json")
free_om = load_json("v0.10.0/packages/operating-models/saas-engineering/1.4.0/package.json")
factory_caps = set(free_factory.get("exports", {}).get("capabilities", []))
om_caps = set(free_om.get("exports", {}).get("capabilities", []))
factory_auth = set(free_factory.get("exports", {}).get("authorities", []))
om_auth = set(free_om.get("exports", {}).get("authorities", []))
if not factory_caps.issubset(om_caps):
    fail("Free Website Factory capabilities are not covered by free Operating Model.")
if not factory_auth.issubset(om_auth):
    fail("Free Website Factory authorities are not covered by free Operating Model.")

# Workspace model and repository boundary.
workspace = modules.get("workspaceModel", {}).get("content", {})
types = workspace.get("projectWorkspaceTypes", {})
if set(types) != {"REMOTE_GIT","LOCAL_GIT"}:
    fail("Workspace model must expose exactly REMOTE_GIT and LOCAL_GIT.")
local = types.get("LOCAL_GIT", {})
if local.get("controlRoot") != ".safor/":
    fail("LOCAL_GIT controlRoot must be .safor/.")
if ".safor/" not in local.get("workerProtection", {}).get("forbiddenWritePrefixes", []):
    fail("LOCAL_GIT must forbid worker writes to .safor/.")
if local.get("controlStrategy") != "LOCAL_MASTER_CONTROL_ROOT":
    fail("LOCAL_GIT control strategy mismatch.")
if types.get("REMOTE_GIT", {}).get("controlStrategy") != "REMOTE_SEPARATE_SAFOR_MEMORY":
    fail("REMOTE_GIT control strategy mismatch.")
hard_rules = workspace.get("hardRules", [])
if not any("Canonical SAFOR repository cannot be the project workspace" in x for x in hard_rules):
    fail("Workspace model must forbid canonical SAFOR repository as project target.")
if not any("Commercial package source cannot be the project workspace" in x for x in hard_rules):
    fail("Workspace model must forbid package sources as project targets.")

repo_policy = modules.get("repositoryPolicy", {}).get("content", {})
if repo_policy.get("principles", {}).get("humanOwnsProjectWorkspace") is not True:
    fail("Repository policy must require HUMAN-owned project workspace.")
control_req = repo_policy.get("controlRepositoryRequirement", {})
if control_req.get("mandatoryWhen") != "PROJECT_WORKSPACE_TYPE == REMOTE_GIT":
    fail("safor-memory must be conditional on REMOTE_GIT.")
if control_req.get("localAlternative", {}).get("root") != ".safor/":
    fail("Repository policy local control alternative must be .safor/.")
if ".safor/" not in repo_policy.get("repositoryClasses", {}).get("LOCAL_GIT_WORKSPACE", {}).get("workerForbiddenPrefixes", []):
    fail("Repository policy must protect local .safor/ from workers.")

# Schemas carry the new workspace/package boundaries.
project_schema = modules.get("schemaProject", {}).get("content", {})
if project_schema.get("properties", {}).get("schemaVersion", {}).get("const") != "0.12.0":
    fail("Project schema must be 0.12.0.")
for field in ("workspaceBindingRef","bindingsRef"):
    if field not in project_schema.get("required", []):
        fail(f"Project schema missing {field}.")
bindings_schema = modules.get("schemaBindings", {}).get("content", {})
if bindings_schema.get("properties", {}).get("schemaVersion", {}).get("const") != "0.12.0":
    fail("Bindings schema must be 0.12.0.")
for field in ("operatingModel","factory","workspaceBindingRef"):
    if field not in bindings_schema.get("required", []):
        fail(f"Bindings schema missing {field}.")
workspace_schema = modules.get("schemaWorkspaceBinding", {}).get("content", {})
for field in ("projectWorkspace","controlWorkspace","ownership"):
    if field not in workspace_schema.get("required", []):
        fail(f"Workspace binding schema missing {field}.")
entitlement_schema = modules.get("schemaEntitlement", {}).get("content", {})
for field in ("entitlementId","subject","grant","validity","issuer","verification"):
    if field not in entitlement_schema.get("required", []):
        fail(f"Entitlement schema missing {field}.")
catalog_schema = modules.get("schemaPackageCatalog", {}).get("content", {})
for field in ("entries","creationProfiles"):
    if field not in catalog_schema.get("required", []):
        fail(f"Package catalog schema missing {field}.")

# Initialization order: package access before project location.
initialization = modules.get("initialization", {}).get("content", {})
sequence = initialization.get("sequence", [])
ids = [x.get("id") for x in sequence]
expected_prefix = ["INIT-00","INIT-00A","INIT-01","INIT-02","INIT-03","INIT-04","INIT-05","INIT-06"]
if ids[:len(expected_prefix)] != expected_prefix:
    fail(f"Initialization prefix mismatch: {ids[:len(expected_prefix)]}")
if initialization.get("entryBehavior", {}).get("firstHumanSurface") != "CREATION_TYPE_SELECTION_MENU":
    fail("Creation type must be the first HUMAN bootstrap surface after preflight.")
if ids.index("INIT-05") > ids.index("INIT-06"):
    fail("Factory/OM compatibility must be verified before project workspace selection.")
if initialization.get("workspaceModelRef") != "workspace-model.json":
    fail("Initialization must reference workspace model.")

actions = {a.get("id"): a for a in kernel.get("controlPlane", {}).get("actions", [])}
if kernel.get("controlPlane", {}).get("startActionId") != "K00":
    fail("Kernel must start at K00.")
if actions.get("K00", {}).get("modelRef") != "module-self-healing-model.json":
    fail("K00 must bind module-self-healing model.")
if actions.get("K00A", {}).get("modelRef") != "deterministic-control-model.json":
    fail("K00A must bind deterministic-control model.")
for action_id in ("K01","K06","K08","K11"):
    action = actions.get(action_id, {})
    if not action.get("humanDecision"):
        fail(f"{action_id} must be an explicit HUMAN decision.")
    contract = action.get("humanInteractionContract", {})
    for field in ("gateRef","phase","reason","targetLoad","maxNewDecisionContexts","technicalDetailExposure","deriveBeforeAsk","reuseUnchangedDecision"):
        if field not in contract:
            fail(f"{action_id} HUMAN interaction contract missing {field}.")
    if contract.get("gateRef") != "human-decision-gate-model.json":
        fail(f"{action_id} must use HUMAN Decision Gate.")
    if contract.get("maxNewDecisionContexts") != 1:
        fail(f"{action_id} must show one decision context at a time.")
if actions.get("K02", {}).get("modelRef") != "package-distribution-model.json":
    fail("K02 must bind package distribution model.")
if actions.get("K04", {}).get("modelRef") != "commercial-entitlement-model.json":
    fail("K04 must bind commercial entitlement model.")
if actions.get("K06", {}).get("modelRef") != "workspace-model.json":
    fail("K06 must bind workspace model.")

# Existing Factory execution semantics remain package-bound.
if actions.get("D01", {}).get("modelRef") != "BOUND_FACTORY.model.discoveryContract":
    fail("D01 must bind resolved Factory discoveryContract.")
if actions.get("P01", {}).get("modelRef") != "BOUND_FACTORY.model.planningContract":
    fail("P01 must bind resolved Factory planningContract.")
if actions.get("E04", {}).get("modelRef") != "BOUND_FACTORY.model.evidenceContract":
    fail("E04 must bind resolved Factory evidenceContract.")
if actions.get("E05", {}).get("modelRef") != "acceptance-model.json":
    fail("E05 must bind deterministic acceptance model.")
if actions.get("E05", {}).get("factoryEvidenceContractRef") != "BOUND_FACTORY.model.evidenceContract":
    fail("E05 must retain Factory evidence contract as domain input.")

# Human communication/decision governance retained.
gate = modules.get("humanDecisionGate", {}).get("content", {})
if gate.get("defaultDecision") != "DO_NOT_ASK":
    fail("HUMAN Decision Gate default must be DO_NOT_ASK.")
if gate.get("decisionReusePolicy", {}).get("unchangedApprovalRepetitionForbidden") is not True:
    fail("Unchanged HUMAN decisions must not be re-requested.")
interaction = modules.get("interaction", {}).get("content", {})
terminal = interaction.get("terminalMenuContract", {})
for field in ("exactlyOne","mustBeFinalRenderedElement","contentAfterMenuForbidden","stopRenderingAfterMenu","menuPresenceDoesNotImplyHumanDecision"):
    if terminal.get(field) is not True:
        fail(f"Terminal menu contract {field} must be true.")
human_response_schema = modules.get("schemaHumanResponse", {}).get("content", {})
if "terminalMenu" not in human_response_schema.get("required", []):
    fail("HUMAN response schema must require terminal menu.")

# Agent/job/scheduler boundaries retained.
agent = modules.get("agentWorkspace", {}).get("content", {})
if agent.get("resultProtocol", {}).get("notAcceptance") != "Agent result is a claim of work performed, never authoritative acceptance.":
    fail("Agent result must not self-accept.")
if agent.get("activationContract", {}).get("backgroundWakeupAssumed") is not False:
    fail("Agent workspace must not assume background wakeup.")
job = modules.get("agentJobContract", {}).get("content", {})
if job.get("authorizationSemantics", {}).get("jobPermissionIsUpperBound") is not True:
    fail("Agent Job permissions must remain upper bounds.")
if job.get("humanProjectionContract", {}).get("providerReadbackRequiredBeforeReady") is not True:
    fail("Agent Job HUMAN projection must be read back before READY.")
scheduler = modules.get("multiAgentScheduler", {}).get("content", {})
if scheduler.get("principles", {}).get("mutationConflictsBlockParallelDispatch") is not True:
    fail("Scheduler must block mutation conflicts.")
if scheduler.get("conflictModel", {}).get("safeDefault") != "Any ambiguity is treated as conflict and the jobs are serialized.":
    fail("Scheduler safe conflict default changed unexpectedly.")

# Deterministic Control / Acceptance retained.
deterministic = modules.get("deterministicControl", {}).get("content", {})
pure = deterministic.get("pureReducerContract", {})
for field in (
    "sameCanonicalInputsSameLogicalOutput","inputMutationForbidden","providerIoForbidden",
    "llmInvocationForbidden","wallClockReadForbidden","randomnessForbidden",
    "arbitraryCodeFromJsonForbidden"
):
    if pure.get(field) is not True:
        fail(f"Deterministic reducer contract {field} must be true.")
predicate_registry = modules.get("predicateRegistry", {}).get("content", {})
allowed_predicates = {p.get("id") for p in predicate_registry.get("predicates", [])}
if predicate_registry.get("executionPolicy", {}).get("closedRegistry") is not True:
    fail("Predicate registry must remain closed.")
transition_registry = modules.get("transitionRegistry", {}).get("content", {})
allowed_effect_ops = set(modules.get("effectModel", {}).get("content", {}).get("stateEffectOperations", []))


def walk_guard(expr):
    if not isinstance(expr, dict):
        fail("Transition guard must be an object.")
        return
    if "predicate" in expr:
        if expr.get("predicate") not in allowed_predicates:
            fail(f"Transition references unknown predicate {expr.get('predicate')}.")
        return
    for op in ("all","any"):
        if op in expr:
            for child in expr.get(op, []):
                walk_guard(child)
            return
    if "not" in expr:
        walk_guard(expr["not"])
        return
    fail("Transition guard uses unsupported form.")


for transition in transition_registry.get("transitions", []):
    walk_guard(transition.get("guards", {}))
    for effect in transition.get("effects", []):
        if effect.get("op") not in allowed_effect_ops:
            fail(f"Transition {transition.get('transitionId')} uses unknown effect op {effect.get('op')}.")

acceptance = modules.get("acceptanceModel", {}).get("content", {})
for principle in (
    "acceptanceOwnedByDeterministicKernel",
    "qualitativeJudgmentMustBecomeExplicitReviewOrAuthorityDecision",
    "agentSelfCheckIsNotAcceptanceEvidence","contractImmutableAfterApproval",
    "reviewIndependenceEnforced","authorityIdMustMatchExactly","rejectedAuthorityBlocksAcceptance"
):
    if acceptance.get("principles", {}).get(principle) is not True:
        fail(f"Acceptance principle {principle} must be true.")

# Self-healing taxonomy includes all current failure classes.
self_healing = modules.get("selfHealing", {}).get("content", {})
failure_classes = {x.get("id") for x in self_healing.get("failureClasses", [])}
for n in range(10, 24):
    cid = f"SH-{n:02d}"
    if cid not in failure_classes:
        fail(f"Missing Self-Healing failure class {cid}.")
for forbidden in (
    "INVENT_COMMERCIAL_ENTITLEMENT","RESOLVE_PAID_PACKAGE_FROM_PUBLIC_CANONICAL_REPOSITORY",
    "USE_SAFOR_PRODUCT_REPOSITORY_AS_PROJECT_TARGET","BYPASS_LOCAL_GIT_REQUIREMENT",
    "ALLOW_WORKER_WRITE_TO_LOCAL_SAFOR_CONTROL_ROOT"
):
    if forbidden not in self_healing.get("forbiddenAutomaticRepairs", []):
        fail(f"Self-Healing missing forbidden repair {forbidden}.")

# Conformance must include the entire current required range.
conformance = modules.get("conformance", {}).get("content", {})
assertions = {x.get("id"): x for x in conformance.get("assertions", [])}
for n in range(46, 217):
    cid = f"CF-{n:03d}"
    if assertions.get(cid, {}).get("expected") is not True:
        fail(f"Missing passing conformance assertion {cid}.")

# Product-wide legacy branding scan retained.
legacy_upper = "SA" + "F"
legacy_lower = "sa" + "f"
legacy_patterns = (
    legacy_upper + "-", legacy_upper + "_", legacy_upper + " ",
    '"' + legacy_upper + '"', "urn:" + legacy_lower + ":",
    legacy_lower + ".", legacy_lower + "-", '"' + legacy_lower + '"',
)
text_extensions = {".json",".md",".py",".yml",".yaml",".txt"}
skip_parts = {".git","__pycache__"}
for path in ROOT.rglob("*"):
    if any(part in skip_parts for part in path.parts):
        continue
    rel = path.relative_to(ROOT)
    for pattern in legacy_patterns:
        if pattern in str(rel):
            fail(f"Legacy branding remains in filename: {rel} ({pattern})")
    if not path.is_file() or path.suffix.lower() not in text_extensions:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in legacy_patterns:
        if pattern in text:
            fail(f"Legacy branding remains in file content: {rel} ({pattern})")

if errors:
    print("SAFOR validation: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("SAFOR validation: PASS")
print(f"- Framework version: {version}")
print(f"- embedded Framework modules: {len(modules)}")
print("- public paid domain content: excluded")
print("- free Website Factory/OM: public-resolvable and compatible")
print("- paid Book Factory/OM: entitlement-gated, no public model path")
print("- HUMAN project workspace: REMOTE_GIT or LOCAL_GIT")
print("- REMOTE_GIT control: separate safor-memory")
print("- LOCAL_GIT control: MASTER-only .safor/")
print("- deterministic control/acceptance: retained")
print("- module-wide Self-Healing: exact 61/61 coverage")
