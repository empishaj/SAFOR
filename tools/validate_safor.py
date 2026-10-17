#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_domain_package_pair,
    validate_domain_package,
)

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


def git_blob_sha(path):
    raw = (ROOT / path).read_bytes()
    header = f"blob {len(raw)}\0".encode("utf-8")
    return hashlib.sha1(header + raw).hexdigest()


version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
framework = load_json("SAFOR-FRAMEWORK.json")
manifest = load_json("RELEASE-MANIFEST.json")
kernel_file = load_json("v0.13.0/SAFOR-MASTER.json")

# Framework identity and release artifact.
if version != "0.13.0-rc.1":
    fail(f"VERSION must be 0.13.0-rc.1, got {version}.")
if framework.get("format") != "SAFOR_FRAMEWORK_SINGLE_FILE":
    fail("Framework bundle format must be SAFOR_FRAMEWORK_SINGLE_FILE.")
if framework.get("schemaVersion") != "0.13.0":
    fail("Framework schemaVersion must be 0.13.0.")
if framework.get("bundleVersion") != version:
    fail("Framework bundle version must match VERSION.")
if framework.get("definitionId") != "safor-framework":
    fail("Framework definitionId mismatch.")
if framework.get("distributionMode") != "FRAMEWORK_PLUS_EXTERNAL_DOMAIN_PACKAGES":
    fail("Framework distribution mode mismatch.")

expected_versioned = f"SAFOR-FRAMEWORK-v{version}.json"
versioned_framework = load_json(expected_versioned)
if versioned_framework != framework:
    fail("Versioned Framework artifact must exactly match SAFOR-FRAMEWORK.json.")

if manifest.get("version") != version:
    fail("Release manifest version must match VERSION.")
if manifest.get("status") != "RELEASE_CANDIDATE":
    fail("Release status must remain RELEASE_CANDIDATE.")
if manifest.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Release canonical repository mismatch.")
if manifest.get("sourceRoot") != "v0.13.0":
    fail("Release sourceRoot must be v0.13.0.")
if manifest.get("distributable") != expected_versioned:
    fail("Release distributable must point to the versioned 0.13 Framework.")
if manifest.get("latestAlias") != "SAFOR-FRAMEWORK.json":
    fail("Release latestAlias mismatch.")

# Exact embedded module/recovery coverage.
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
    "schemaPackageCatalog","schemaEntitlement","schemaWorkspaceBinding","conformance",
    "composablePackageModel","schemaDomainPackage","schemaPackageSelection",
    "schemaPackageCompatibilityDecision",
}
missing = sorted(required_modules - set(modules))
extra = sorted(set(modules) - required_modules)
if missing:
    fail("Missing embedded Framework modules: " + ", ".join(missing))
if extra:
    fail("Unexpected embedded Framework modules: " + ", ".join(extra))
if len(modules) != 65:
    fail(f"Expected exactly 65 embedded Framework modules, got {len(modules)}.")

profiles = modules.get("moduleSelfHealing", {}).get("content", {}).get("moduleProfiles", [])
profile_by_key = {p.get("moduleKey"): p for p in profiles}
if len(profiles) != len(profile_by_key):
    fail("Duplicate module self-healing profile key.")
if set(profile_by_key) != set(modules):
    fail(
        "Module recovery coverage mismatch: "
        f"missing={sorted(set(modules)-set(profile_by_key))}, "
        f"extra={sorted(set(profile_by_key)-set(modules))}"
    )

integrity = framework.get("integrityManifest", {})
for key, module in modules.items():
    source_path = module.get("sourcePath")
    if not source_path or not (ROOT / source_path).exists():
        fail(f"Embedded module {key} source path is missing: {source_path}")
        continue
    actual_blob = git_blob_sha(source_path)
    if module.get("sourceBlobSha") != actual_blob:
        fail(f"Embedded module {key} source blob SHA mismatch.")
    if integrity.get(key, {}).get("sourceBlobSha") != actual_blob:
        fail(f"Integrity manifest {key} source blob SHA mismatch.")
    profile = profile_by_key.get(key, {})
    if module.get("selfHealingProfileId") != profile.get("profileId"):
        fail(f"Embedded module {key} self-healing profile mismatch.")
    if integrity.get(key, {}).get("selfHealingProfileId") != profile.get("profileId"):
        fail(f"Integrity manifest {key} self-healing profile mismatch.")

# Domain packages must remain external to Framework.
for key, module in modules.items():
    source_path = str(module.get("sourcePath", ""))
    if "/packages/factories/" in source_path or "/packages/operating-models/" in source_path:
        fail(f"Public Framework embeds forbidden domain package module {key}: {source_path}")

refs = framework.get("referenceResolution", {})
for ref, target in refs.items():
    if target not in modules:
        fail(f"Unresolved Framework reference {ref}->{target}.")

for ref, target in {
    "composable-package-model.json": "composablePackageModel",
    "schemas/domain-package.schema.json": "schemaDomainPackage",
    "schemas/package-selection.schema.json": "schemaPackageSelection",
    "schemas/package-compatibility-decision.schema.json": "schemaPackageCompatibilityDecision",
}.items():
    if refs.get(ref) != target:
        fail(f"Required 0.13 reference resolution missing: {ref}->{target}.")

# 0.13 authoritative sources.
for key in (
    "kernel","initialization","moduleSelfHealing","packageRegistry","packageDistribution",
    "commercialEntitlement","packageCatalog","schemaBindings","schemaPackageCatalog",
    "schemaEntitlement","composablePackageModel","schemaDomainPackage",
    "schemaPackageSelection","schemaPackageCompatibilityDecision",
):
    if not str(modules.get(key, {}).get("sourcePath", "")).startswith("v0.13.0/"):
        fail(f"0.13 module {key} must come from v0.13.0 source.")

# Kernel contract.
kernel = modules.get("kernel", {}).get("content", {})
if kernel != kernel_file:
    fail("Embedded kernel must equal v0.13.0/SAFOR-MASTER.json.")
if kernel.get("schemaVersion") != "0.13.0" or kernel.get("kernelVersion") != "0.13.0":
    fail("Kernel version/schemaVersion must be 0.13.0.")

required_principles = (
    "modularDomainPackages",
    "paidPackageContentExcludedFromPublicFramework",
    "freeWebsitePackagesPubliclyResolvable",
    "commercialEntitlementRequiredForPaidPackages",
    "entitlementIndependentFromOrganizationalAuthority",
    "humanOwnsProjectWorkspace",
    "localGitWorkspaceSupported",
    "projectWorkspaceSeparateFromPackageSource",
    "frameworkRepositoryNeverProjectTarget",
    "domainPackagesAreChatLoadableJson",
    "factoryAndOperatingModelIndependentlySelectable",
    "creationProfilesDefineDefaultsNotLockedPairs",
    "packageAccessResolvedPerSelectedPackage",
    "mixedFreeAndPaidPackagePairsAllowed",
    "domainPackageEntitlementEvidenceExternal",
    "domainPackageIntegrityRequired",
    "packageSelectionRequiresCompatibilityDecision",
)
for principle in required_principles:
    if kernel.get("kernelPrinciples", {}).get(principle) is not True:
        fail(f"Kernel principle {principle} must be true.")

invariants = {x.get("id") for x in kernel.get("invariants", [])}
for n in range(37, 176):
    inv = f"INV-{n:03d}"
    if inv not in invariants:
        fail(f"Missing invariant {inv}.")

package_system = kernel.get("packageSystem", {})
if package_system.get("domainPackageSchemaRef") != "schemas/domain-package.schema.json":
    fail("Kernel must bind domain-package schema.")
if package_system.get("selectionSchemaRef") != "schemas/package-selection.schema.json":
    fail("Kernel must bind package-selection schema.")
if package_system.get("compatibilityDecisionSchemaRef") != "schemas/package-compatibility-decision.schema.json":
    fail("Kernel must bind package compatibility-decision schema.")
for rule in (
    "creationProfileDefinesDefaultPackageIds",
    "factoryOverrideAllowed",
    "operatingModelOverrideAllowed",
    "packageAccessResolvedPerSelectedPackage",
    "mixedFreeAndPaidPackagePairsAllowed",
    "domainPackageEntitlementEvidenceExternal",
    "domainPackageContractDigestRequired",
    "packagePairCompatibilityDecisionRequired",
):
    if package_system.get("rules", {}).get(rule) is not True:
        fail(f"Kernel package rule {rule} must be true.")

runtime = framework.get("runtimeContract", {})
domain_policy = runtime.get("domainPackagePolicy", {})
for rule in (
    "accessEvaluatedPerSelectedPackage",
    "independentFactoryOverrideAllowed",
    "independentOperatingModelOverrideAllowed",
    "mixedFreeAndPaidPairAllowed",
    "entitlementEvidenceExternal",
    "declaredContractDigestRequired",
    "compatibilityDecisionRequiredBeforeBinding",
):
    if domain_policy.get(rule) is not True:
        fail(f"Runtime domain package policy {rule} must be true.")
if domain_policy.get("embeddedDomainPackageContent") is not False:
    fail("Public Framework must declare embeddedDomainPackageContent=false.")
if domain_policy.get("paidPublicResolutionForbidden") is not True:
    fail("Paid public package resolution must be forbidden.")
if domain_policy.get("paidRequiresVerifiedEntitlement") is not True:
    fail("Paid selected package must require verified entitlement.")

# Package catalog: defaults and independently purchasable entries.
catalog = modules.get("packageCatalog", {}).get("content", {})
if catalog.get("format") != "SAFOR_PACKAGE_CATALOG" or catalog.get("schemaVersion") != "0.13.0":
    fail("Package catalog format/version mismatch.")

entries = catalog.get("entries", [])
entry_by_id = {}
for entry in entries:
    pid = entry.get("packageId")
    if pid in entry_by_id:
        fail(f"Duplicate package catalog entry {pid}.")
    entry_by_id[pid] = entry
    if entry.get("kind") not in {"FACTORY", "OPERATING_MODEL"}:
        fail(f"Catalog entry {pid} has invalid package kind.")
    if not entry.get("supportedCreationTypes"):
        fail(f"Catalog entry {pid} must declare supportedCreationTypes.")

free_ids = ("safor.factory.software-delivery", "safor.om.saas-engineering")
for pid in free_ids:
    entry = entry_by_id.get(pid, {})
    if entry.get("accessMode") != "FREE_PUBLIC":
        fail(f"{pid} must be FREE_PUBLIC.")
    dist = entry.get("distribution", {})
    if dist.get("sourceClass") != "PUBLIC_CANONICAL_REPOSITORY" or not dist.get("path"):
        fail(f"{pid} must resolve from public canonical repository.")
        continue
    package = load_json(dist["path"])
    if package.get("format") != "SAFOR_DOMAIN_PACKAGE":
        fail(f"{pid} must use SAFOR_DOMAIN_PACKAGE format.")
    if package.get("schemaVersion") != "0.13.0":
        fail(f"{pid} domain package schemaVersion must be 0.13.0.")
    if package.get("packageId") != pid:
        fail(f"Public free package path for {pid} resolves wrong packageId.")
    if package.get("version") != entry.get("version"):
        fail(f"Public free package version mismatch for {pid}.")
    if package.get("integrity", {}).get("contentDigest") != compute_domain_package_digest(package):
        fail(f"Public free package digest mismatch for {pid}.")

for pid in ("safor.factory.book-production", "safor.om.book-authoring"):
    entry = entry_by_id.get(pid, {})
    if entry.get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
        fail(f"{pid} must be PAID_ENTITLEMENT_REQUIRED.")
    dist = entry.get("distribution", {})
    if dist.get("sourceClass") != "ENTITLED_PACKAGE_SOURCE":
        fail(f"{pid} must use ENTITLED_PACKAGE_SOURCE.")
    if dist.get("publicModelPath", "NOT_NULL") is not None:
        fail(f"{pid} must expose no public model path.")

profiles_by_type = {x.get("creationType"): x for x in catalog.get("creationProfiles", [])}
web = profiles_by_type.get("SOFTWARE_WEBSITE", {})
book = profiles_by_type.get("BOOK", {})
if web.get("defaultFactoryPackageId") != "safor.factory.software-delivery":
    fail("Website default Factory mismatch.")
if web.get("defaultOperatingModelPackageId") != "safor.om.saas-engineering":
    fail("Website default Operating Model mismatch.")
if web.get("autoResolveDefaultsFromPublicFrameworkGit") is not True:
    fail("Website defaults must be public-auto-resolvable.")
if book.get("defaultFactoryPackageId") != "safor.factory.book-production":
    fail("Book default Factory mismatch.")
if book.get("defaultOperatingModelPackageId") != "safor.om.book-authoring":
    fail("Book default Operating Model mismatch.")
if book.get("autoResolveDefaultsFromPublicFrameworkGit") is not False:
    fail("Book defaults must not public-auto-resolve.")
for creation_type, profile in profiles_by_type.items():
    policy = profile.get("selectionPolicy", {})
    for rule in (
        "factoryOverrideAllowed",
        "operatingModelOverrideAllowed",
        "requireExplicitHumanApprovalForPaidOverride",
        "requirePairCompatibility",
        "resolveEachPackageAccessIndependently",
    ):
        if policy.get(rule) is not True:
            fail(f"{creation_type} selection policy {rule} must be true.")

# Free starter artifacts must be valid for 0.13 and mutually compatible.
free_factory = load_json("v0.13.0/packages/factories/software-delivery/1.5.0/package.json")
free_om = load_json("v0.13.0/packages/operating-models/saas-engineering/1.5.0/package.json")
for package in (free_factory, free_om):
    result = validate_domain_package(package, version, "SOFTWARE_WEBSITE")
    if not result["valid"]:
        fail(f"Free domain package invalid: {package.get('packageId')}: {result['errors']}")
pair = evaluate_domain_package_pair(free_factory, free_om, version, "SOFTWARE_WEBSITE")
if not pair["compatible"]:
    fail(f"Free Website Factory/Operating Model pair is incompatible: {pair}")

# Distribution / entitlement semantics.
distribution = modules.get("packageDistribution", {}).get("content", {})
for principle in (
    "factoryAndOperatingModelIndependentlySelectable",
    "creationProfilesProvideDefaultsOnly",
    "accessEvaluatedPerSelectedPackage",
    "mixedFreeAndPaidPairAllowed",
    "entitlementEvidenceExternalToPackageArtifact",
    "domainPackageIntegrityRequired",
    "compatibilityDecisionRequiredBeforeBinding",
):
    if distribution.get("principles", {}).get(principle) is not True:
        fail(f"Distribution principle {principle} must be true.")

entitlement = modules.get("commercialEntitlement", {}).get("content", {})
for rule in (
    "paidRequiresVerifiedEntitlement",
    "selfAssertedEntitlementForbidden",
    "packagePossessionAloneIsNotVerifiedEntitlement",
    "entitlementCannotGrantOperatingModelAuthority",
    "entitlementCannotGrantProviderRights",
    "entitlementCannotExpandProjectScope",
    "exactPackageAndVersionCoverageRequired",
    "entitlementEvaluatedPerSelectedPackage",
    "mixedPairRequiresOnlyPaidPackageEntitlements",
    "entitlementEvidenceExternalToPackageArtifact",
    "packageSelectionDoesNotTransferEntitlement",
):
    if entitlement.get("rules", {}).get(rule) is not True:
        fail(f"Commercial entitlement rule {rule} must be true.")

# Workspace boundaries retained.
workspace = modules.get("workspaceModel", {}).get("content", {})
types = workspace.get("projectWorkspaceTypes", {})
if set(types) != {"REMOTE_GIT", "LOCAL_GIT"}:
    fail("Workspace model must expose exactly REMOTE_GIT and LOCAL_GIT.")
if types.get("LOCAL_GIT", {}).get("controlRoot") != ".safor/":
    fail("LOCAL_GIT controlRoot must be .safor/.")
if types.get("REMOTE_GIT", {}).get("controlStrategy") != "REMOTE_SEPARATE_SAFOR_MEMORY":
    fail("REMOTE_GIT control strategy mismatch.")
if framework.get("productRepository", {}).get("projectTargetForbidden") is not True:
    fail("Canonical SAFOR product repository must be forbidden as project target.")

# Binding schema must persist package audit chain.
bindings_schema = modules.get("schemaBindings", {}).get("content", {})
required_binding_fields = set(bindings_schema.get("required", []))
for field in ("packageSelectionRef", "compatibilityDecisionRef", "factory", "operatingModel"):
    if field not in required_binding_fields:
        fail(f"Project bindings schema must require {field}.")
domain_required = set(bindings_schema.get("$defs", {}).get("domainBinding", {}).get("required", []))
for field in ("artifactFormat", "artifactSchemaVersion", "contentDigest", "accessMode", "entitlementEvidenceRef", "selectionOrigin", "integrityVerificationRef"):
    if field not in domain_required:
        fail(f"Domain binding must require {field}.")

# Initialization must resolve independent packages before workspace selection.
initialization = modules.get("initialization", {}).get("content", {})
ops = [x.get("operation") for x in initialization.get("sequence", [])]
required_order = [
    "SELECT_CREATION_TYPE",
    "RESOLVE_PACKAGE_SELECTION_PROFILE",
    "RESOLVE_SELECTED_FACTORY_AND_OPERATING_MODEL_ACCESS",
    "VERIFY_PACKAGE_INTEGRITY_AND_ACCESS",
    "VERIFY_FACTORY_OPERATING_MODEL_COMPATIBILITY",
    "MATERIALIZE_PACKAGE_SELECTION_AND_COMPATIBILITY_DECISION",
    "SELECT_PROJECT_WORKSPACE_TYPE",
]
positions = []
for op in required_order:
    if op not in ops:
        fail(f"Initialization operation missing: {op}.")
    else:
        positions.append(ops.index(op))
if positions and positions != sorted(positions):
    fail("Composable package initialization order is invalid.")

if errors:
    print("SAFOR validation: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("SAFOR validation: PASS")
print(f"Framework: {version}")
print(f"Embedded modules/recovery profiles: {len(modules)}/{len(profile_by_key)}")
print("Free Website starter: independently selectable FREE_PUBLIC Factory + Operating Model")
print("Commercial access: per selected package, external verified entitlement")
print("Domain package integrity: SHA-256 declared-contract verification")
print("Project workspace: HUMAN-owned REMOTE_GIT or LOCAL_GIT")
