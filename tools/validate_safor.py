#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_active_conditional_requirements,
    evaluate_domain_package_pair,
    evaluate_domain_framework_pair,
    validate_domain_package,
    validate_factory_contract_consistency,
)

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
if version != "0.13.0-rc.6":
    fail(f"VERSION must be 0.13.0-rc.6, got {version}.")
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
    "kernel","initialization","selfHealing","moduleSelfHealing","packageRegistry","packageDistribution",
    "commercialEntitlement","packageCatalog","schemaBindings","schemaPackageCatalog",
    "schemaEntitlement","conformance","composablePackageModel","schemaDomainPackage",
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
    "softwareSaasRequiresPaidFactoryAndOperatingModel",
    "creationProfileAccessPolicyEnforced",
    "commercialEntitlementStatusTimeSubjectAndTrustRequired",
    "commercialBasisEvidenceRequired",
    "entitledSourceDeliveryEvidenceRequired",
    "commercialDeliveryDigestBindingRequired",
    "domainSpecificFrameworkDistributions",
    "sameKernelAcrossDomainDistributions",
    "domainDistributionPreselectsDomainAndDefaults",
    "embeddedDomainDefaultsRemainReplaceable",
    "replacementRequiresSameDomain",
    "replacementRequiresBidirectionalCompatibility",
    "packageFamilyCompatibilityRequiredForV2Packages",
    "crossDomainPackageReplacementForbidden",
    "publicPaidDomainEvaluationArtifactsAllowedForTesting",
    "publicEvaluationDoesNotAuthorizePaidUse",
)
for principle in required_principles:
    if kernel.get("kernelPrinciples", {}).get(principle) is not True:
        fail(f"Kernel principle {principle} must be true.")

invariants = {x.get("id") for x in kernel.get("invariants", [])}
for n in range(37, 201):
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
    "softwareSaasRequiresPaidFactoryAndOperatingModel",
    "creationProfileSelectedAccessPolicyRequired",
    "entitlementStatusTimeSubjectAndTrustRequired",
    "commercialBasisEvidenceRequired",
    "entitledPackageSourceDeliveryEvidenceRequired",
    "deliveryEvidenceMustBindEntitlementPackageVersionAndDigest",
    "humanLoadedPaidPackageStillRequiresEntitlement",
    "domainFrameworkProfileCatalogRequired",
    "domainDistributionPreselectsDomain",
    "replacementSameDomainRequired",
    "replacementBidirectionalCounterpartRequired",
    "replacementPackageFamilyConstraintsEnforced",
    "crossDomainReplacementForbidden",
    "publicEvaluationPaidBytesNotProductionSource",
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
    "creationProfileAccessPolicyEnforced",
    "softwareSaasRequiresPaidFactoryAndOperatingModel",
    "strictEntitlementVerificationRequired",
    "entitledSourceDeliveryEvidenceRequired",
    "deliveryDigestBindingRequired",
):
    if domain_policy.get(rule) is not True:
        fail(f"Runtime domain package policy {rule} must be true.")
if domain_policy.get("embeddedDomainPackageContent") is not False:
    fail("Public Framework must declare embeddedDomainPackageContent=false.")
if domain_policy.get("paidPublicResolutionForbidden") is not True:
    fail("Paid public package resolution must be forbidden.")
if domain_policy.get("paidRequiresVerifiedEntitlement") is not True:
    fail("Paid selected package must require verified entitlement.")

domain_distribution_policy = runtime.get("domainFrameworkDistributionPolicy", {})
for rule in (
    "domainPreselectedByDistribution",
    "embeddedDefaultFactoryAndOperatingModel",
    "creationTypeQuestionSuppressedForDomainDistribution",
    "factoryReplacementAllowed",
    "operatingModelReplacementAllowed",
    "replacementRequiresSameDomain",
    "replacementRequiresBidirectionalCompatibility",
    "replacementRequiresPackageFamilyCompatibility",
    "crossDomainPairForbidden",
):
    if domain_distribution_policy.get(rule) is not True:
        fail(f"Runtime domain distribution policy {rule} must be true.")
if set(domain_distribution_policy.get("publicDistributions", [])) != {
    "SAFOR-FRAMEWORK-WEBSITE.json",
    "SAFOR-FRAMEWORK-SAAS.json",
    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
}:
    fail("All three domain Framework artifacts must be present for rc.6 testing.")
if set(domain_distribution_policy.get("publicTestEvaluationDistributions", [])) != {
    "SAFOR-FRAMEWORK-SAAS.json",
    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
}:
    fail("SaaS and Book must be marked public test/evaluation distributions.")
if set(domain_distribution_policy.get("commercialProductionDistributions", [])) != {
    "SAFOR-FRAMEWORK-SAAS.json",
    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
}:
    fail("Commercial production distribution names mismatch.")
if domain_distribution_policy.get("publicTestBytesDoNotDefineCommercialProductionSource") is not True:
    fail("Public test bytes must not define the commercial production source.")

# Package catalog: distinct free Website and commercial Software/SaaS/Book paths.
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
    if not entry.get("packageFamily"):
        fail(f"Catalog entry {pid} must declare packageFamily.")

free_ids = ("safor.factory.website-delivery", "safor.om.website-team")
for pid in free_ids:
    entry = entry_by_id.get(pid, {})
    if entry.get("accessMode") != "FREE_PUBLIC":
        fail(f"{pid} must be FREE_PUBLIC.")
    if entry.get("supportedCreationTypes") != ["WEBSITE"]:
        fail(f"{pid} must support WEBSITE only.")
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

commercial_ids = (
    "safor.factory.software-delivery",
    "safor.om.saas-engineering",
    "safor.factory.book-production",
    "safor.om.book-authoring",
)
for pid in commercial_ids:
    entry = entry_by_id.get(pid, {})
    if entry.get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
        fail(f"{pid} must be PAID_ENTITLEMENT_REQUIRED.")
    dist = entry.get("distribution", {})
    if dist.get("sourceClass") != "ENTITLED_PACKAGE_SOURCE":
        fail(f"{pid} must use ENTITLED_PACKAGE_SOURCE.")
    if dist.get("publicModelPath", "NOT_NULL") is not None:
        fail(f"{pid} must expose no public model path.")

if entry_by_id.get("safor.factory.software-delivery", {}).get("supportedCreationTypes") != ["SOFTWARE_SAAS"]:
    fail("Software Factory catalog entry must support SOFTWARE_SAAS only.")
if entry_by_id.get("safor.om.saas-engineering", {}).get("supportedCreationTypes") != ["SOFTWARE_SAAS"]:
    fail("SaaS Engineering OM catalog entry must support SOFTWARE_SAAS only.")

profiles_by_type = {x.get("creationType"): x for x in catalog.get("creationProfiles", [])}
if set(profiles_by_type) != {"WEBSITE", "SOFTWARE_SAAS", "BOOK"}:
    fail("Creation profiles must be exactly WEBSITE, SOFTWARE_SAAS and BOOK.")

web = profiles_by_type.get("WEBSITE", {})
software = profiles_by_type.get("SOFTWARE_SAAS", {})
book = profiles_by_type.get("BOOK", {})
if web.get("domainId") != "WEBSITE_CREATION":
    fail("Website creation profile domainId mismatch.")
if software.get("domainId") != "SAAS_ENGINEERING":
    fail("Software/SaaS creation profile domainId mismatch.")
if book.get("domainId") != "BOOK_CREATION":
    fail("Book creation profile domainId mismatch.")
if web.get("defaultFactoryPackageId") != "safor.factory.website-delivery":
    fail("Website default Factory mismatch.")
if web.get("defaultOperatingModelPackageId") != "safor.om.website-team":
    fail("Website default Operating Model mismatch.")
if web.get("selectedPackageAccessPolicy") != "ANY_COMPATIBLE_ACCESS":
    fail("Website selected package access policy mismatch.")
if web.get("autoResolveDefaultsFromPublicFrameworkGit") is not True:
    fail("Website defaults must be public-auto-resolvable.")

if software.get("defaultFactoryPackageId") != "safor.factory.software-delivery":
    fail("Software/SaaS default Factory mismatch.")
if software.get("defaultOperatingModelPackageId") != "safor.om.saas-engineering":
    fail("Software/SaaS default Operating Model mismatch.")
if software.get("selectedPackageAccessPolicy") != "BOTH_PAID_ENTITLEMENT_REQUIRED":
    fail("Software/SaaS must require both selected packages to be paid.")
if software.get("autoResolveDefaultsFromPublicFrameworkGit") is not False:
    fail("Software/SaaS commercial defaults must not public-auto-resolve.")

if book.get("selectedPackageAccessPolicy") != "BOTH_PAID_ENTITLEMENT_REQUIRED":
    fail("Book must require both selected packages to be paid.")
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

# Free Website starter artifacts must be valid for 0.13 and mutually compatible.
free_factory = load_json("v0.13.0/packages/factories/website-delivery/1.1.0/package.json")
free_om = load_json("v0.13.0/packages/operating-models/website-team/1.1.0/package.json")
for package in (free_factory, free_om):
    result = validate_domain_package(package, version, "WEBSITE")
    if not result["valid"]:
        fail(f"Free Website package invalid: {package.get('packageId')}: {result['errors']}")
pair = evaluate_domain_framework_pair(
    free_factory, free_om, version, "WEBSITE", "WEBSITE_CREATION"
)
if not pair["compatible"]:
    fail(f"Free Website Factory/Operating Model pair is domain-incompatible: {pair}")

factory_consistency = validate_factory_contract_consistency(free_factory)
if not factory_consistency["valid"]:
    fail(f"Website Factory 1.1 contract is internally inconsistent: {factory_consistency['errors']}")

if free_factory.get("version") != "1.1.0" or free_om.get("version") != "1.1.0":
    fail("Free Website Factory/Operating Model defaults must both be 1.1.0.")
if free_factory.get("packageFamily") != "safor.factory.website":
    fail("Website Factory packageFamily mismatch.")
if free_om.get("packageFamily") != "safor.om.website":
    fail("Website Operating Model packageFamily mismatch.")
if free_factory.get("compatibility", {}).get("domainIds") != ["WEBSITE_CREATION"]:
    fail("Website Factory domainIds mismatch.")
if free_om.get("compatibility", {}).get("domainIds") != ["WEBSITE_CREATION"]:
    fail("Website Operating Model domainIds mismatch.")
if free_factory.get("integrity", {}).get("canonicalization") != "SAFOR_CANONICAL_JSON_V2":
    fail("Website Factory 1.1 must use SAFOR_CANONICAL_JSON_V2.")
if free_om.get("integrity", {}).get("canonicalization") != "SAFOR_CANONICAL_JSON_V2":
    fail("Website Operating Model 1.1 must use SAFOR_CANONICAL_JSON_V2.")
scope = free_factory.get("model", {}).get("scopeBoundary", {})
for excluded in (
    "GENERAL_SAAS_PRODUCT_ENGINEERING",
    "SERVICE_OPERATIONS",
    "INCIDENT_RESPONSE",
    "SOFTWARE_SUPPLY_CHAIN_GOVERNANCE",
):
    if excluded not in scope.get("excluded", []):
        fail(f"Website Factory must explicitly exclude {excluded}.")
boundary = free_factory.get("model", {}).get("discoveryContract", {}).get("boundaryCheck", {})
if boundary.get("targetCreationType") != "SOFTWARE_SAAS":
    fail("Website Factory must escalate application/SaaS scope to SOFTWARE_SAAS.")

nodes = {
    node.get("id"): node
    for node in free_factory.get("model", {}).get("flowGraph", {}).get("nodes", [])
}
expected_types = {
    "WEB-01": "WEBSITE_DEFINITION",
    "WEB-02": "CONTENT_INFORMATION_ARCHITECTURE",
    "WEB-03": "EXPERIENCE_DESIGN",
    "WEB-04": "WEBSITE_IMPLEMENTATION",
    "WEB-05": "WEBSITE_VERIFICATION",
    "WEB-06": "PUBLISH",
    "WEB-07": "POST_PUBLISH_OBSERVATION",
    "WEB-08": "WEBSITE_OUTCOME_ASSESSMENT",
}
for node_id, expected_type in expected_types.items():
    if nodes.get(node_id, {}).get("workItemType") != expected_type:
        fail(f"Website Factory {node_id} must be {expected_type}.")

quality = free_factory.get("model", {}).get("webQualityContract", {})
if quality.get("accessibility", {}).get("defaultStandard") != "WCAG_2_2":
    fail("Website Factory default accessibility standard must be WCAG 2.2.")
if quality.get("accessibility", {}).get("defaultTargetLevel") != "AA":
    fail("Website Factory default accessibility target must be AA.")
if quality.get("responsiveVerificationRequired") is not True:
    fail("Website Factory must require responsive verification.")
if quality.get("performanceEvidenceRequired") is not True:
    fail("Website Factory must require performance evidence.")

conditional = free_factory.get("model", {}).get("compatibilityContract", {}).get("conditionalCapabilities", [])
if {x.get("capabilityId") for x in conditional} != {"search_visibility_verification"}:
    fail("Website Factory search visibility must be the only conditional capability in the starter.")

outcome = free_factory.get("model", {}).get("outcomeModel", {}).get("measurementContract", {})
required_measurement_fields = {
    "metric", "baselineOrBaselineResolution", "targetOrDecisionThreshold",
    "observationWindow", "dataSource", "decisionRule",
}
if not required_measurement_fields.issubset(set(outcome.get("requiredFields", []))):
    fail("Website Factory outcome measurement contract is incomplete.")
if "INCONCLUSIVE" not in outcome.get("allowedDecisions", []):
    fail("Website Factory outcome model must permit INCONCLUSIVE.")

# Publicly disclosed Software/SaaS 1.6 artifacts are historical only and must not be catalog-resolvable.
for legacy_path in (
    "v0.13.0/packages/factories/software-delivery/1.6.0/package.json",
    "v0.13.0/packages/operating-models/saas-engineering/1.6.0/package.json",
):
    if not (ROOT / legacy_path).exists():
        fail(f"Expected historical disclosure artifact missing: {legacy_path}")
for pid in ("safor.factory.software-delivery", "safor.om.saas-engineering"):
    entry = entry_by_id.get(pid, {})
    if entry.get("distribution", {}).get("path"):
        fail(f"Commercial Software/SaaS catalog entry {pid} must not expose a public path.")
    if not entry.get("legacyDisclosure"):
        fail(f"Commercial Software/SaaS catalog entry {pid} must record legacy disclosure.")

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
    "websiteStarterIsFreePublic",
    "softwareSaasRequiresPaidFactoryAndOperatingModel",
    "creationProfileMayConstrainSelectedAccessModes",
    "commercialDeliveryEvidenceRequiredForEntitledSource",
    "deliveryArtifactDigestMustMatchPackageIntegrity",
    "trustedDeliveryVerifierRequired",
    "deliveryEvidenceExternalToPackageArtifact",
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
    "creationProfileAccessPolicyMustBeSatisfiedBeforeBinding",
    "softwareSaasRequiresFactoryEntitlement",
    "softwareSaasRequiresOperatingModelEntitlement",
    "freeWebsiteDefaultsRequireNoEntitlement",
    "entitlementStatusMustBeActive",
    "entitlementValidityEvaluatedAtExplicitTimestamp",
    "entitlementSubjectMustMatchActiveHumanOrOrganization",
    "entitlementIssuerMustBeTrusted",
    "entitlementVerifierMustBeTrusted",
    "commercialBasisEvidenceRequired",
    "commercialBasisSkuMustMatchGrant",
    "entitledPackageSourceRequiresDeliveryEvidence",
    "deliveryEvidenceMustBindEntitlementPackageVersionAndDigest",
    "deliveryVerifierMustBeTrusted",
    "deliveryEvidenceMustBeTimeValid",
    "humanLoadedPaidPackageMayBypassDeliveryChannelButNeverEntitlement",
):
    if entitlement.get("rules", {}).get(rule) is not True:
        fail(f"Commercial entitlement rule {rule} must be true.")

# Domain Framework profiles and public single-file distribution.
domain_profiles = load_json("v0.13.0/domain-framework-profiles.json")
if domain_profiles.get("format") != "SAFOR_DOMAIN_FRAMEWORK_PROFILE_CATALOG":
    fail("Domain framework profile catalog format mismatch.")
profile_by_id = {x.get("id"): x for x in domain_profiles.get("profiles", [])}
if set(profile_by_id) != {"WEBSITE", "SAAS", "BOOK_CREATION"}:
    fail("Domain framework profiles must be exactly WEBSITE, SAAS and BOOK_CREATION.")
expected_domain_profiles = {
    "WEBSITE": ("WEBSITE_CREATION", "WEBSITE", "SAFOR-FRAMEWORK-WEBSITE.json", True, "PUBLIC_PRODUCTION"),
    "SAAS": ("SAAS_ENGINEERING", "SOFTWARE_SAAS", "SAFOR-FRAMEWORK-SAAS.json", True, "PUBLIC_TEST_EVALUATION"),
    "BOOK_CREATION": ("BOOK_CREATION", "BOOK", "SAFOR-FRAMEWORK-BOOK-CREATION.json", True, "PUBLIC_TEST_EVALUATION"),
}
for pid, (domain_id, creation_type, filename, public_artifact, publication_mode) in expected_domain_profiles.items():
    profile = profile_by_id.get(pid, {})
    if profile.get("domainId") != domain_id:
        fail(f"Domain framework profile {pid} domainId mismatch.")
    if profile.get("creationType") != creation_type:
        fail(f"Domain framework profile {pid} creationType mismatch.")
    if profile.get("distributionFile") != filename:
        fail(f"Domain framework profile {pid} filename mismatch.")
    if profile.get("publicArtifactCommitted") is not public_artifact:
        fail(f"Domain framework profile {pid} public artifact policy mismatch.")
    if profile.get("publicationMode") != publication_mode:
        fail(f"Domain framework profile {pid} publicationMode mismatch.")
    replacement = profile.get("replacementPolicy", {})
    for flag in (
        "factoryReplaceable",
        "operatingModelReplaceable",
        "sameDomainRequired",
        "bidirectionalCounterpartRequired",
        "packageFamilyConstraintsEnforced",
        "crossDomainPairForbidden",
    ):
        if replacement.get(flag) is not True:
            fail(f"Domain framework profile {pid} replacement policy {flag} must be true.")

website_distribution = load_json("SAFOR-FRAMEWORK-WEBSITE.json")
if website_distribution.get("format") != "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION":
    fail("Website domain Framework distribution format mismatch.")
if website_distribution.get("distributionId") != "safor.framework.website":
    fail("Website domain Framework distributionId mismatch.")
if website_distribution.get("distributionVersion") != version:
    fail("Website domain Framework distribution version mismatch.")
if website_distribution.get("domain", {}).get("domainId") != "WEBSITE_CREATION":
    fail("Website domain Framework domainId mismatch.")
if website_distribution.get("framework") != framework:
    fail("Website domain Framework must embed the exact current SAFOR base Framework.")
embedded_defaults = website_distribution.get("embeddedDomainModules", {})
if embedded_defaults.get("factory") != free_factory:
    fail("Website domain Framework embedded Factory mismatch.")
if embedded_defaults.get("operatingModel") != free_om:
    fail("Website domain Framework embedded Operating Model mismatch.")
website_pair = evaluate_domain_framework_pair(
    embedded_defaults.get("factory", {}),
    embedded_defaults.get("operatingModel", {}),
    version,
    "WEBSITE",
    "WEBSITE_CREATION",
)
if not website_pair["compatible"]:
    fail(f"Website domain Framework embedded pair incompatible: {website_pair}")

for profile_id, filename, domain_id, creation_type, expected_factory_family, expected_om_family in (
    ("SAAS", "SAFOR-FRAMEWORK-SAAS.json", "SAAS_ENGINEERING", "SOFTWARE_SAAS", "safor.factory.saas", "safor.om.saas"),
    ("BOOK_CREATION", "SAFOR-FRAMEWORK-BOOK-CREATION.json", "BOOK_CREATION", "BOOK", "safor.factory.book", "safor.om.book"),
):
    distribution_artifact = load_json(filename)
    if distribution_artifact.get("format") != "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION":
        fail(f"{profile_id} domain Framework format mismatch.")
        continue
    if distribution_artifact.get("publicationMode") != "PUBLIC_TEST_EVALUATION":
        fail(f"{profile_id} must be marked PUBLIC_TEST_EVALUATION.")
    if not distribution_artifact.get("evaluationNotice"):
        fail(f"{profile_id} public evaluation notice is required.")
    if distribution_artifact.get("distributionVersion") != version:
        fail(f"{profile_id} domain Framework version mismatch.")
    if distribution_artifact.get("framework") != framework:
        fail(f"{profile_id} domain Framework must embed exact current base Framework.")
    if distribution_artifact.get("domain", {}).get("domainId") != domain_id:
        fail(f"{profile_id} domainId mismatch.")
    if distribution_artifact.get("domain", {}).get("creationType") != creation_type:
        fail(f"{profile_id} creationType mismatch.")
    if distribution_artifact.get("domain", {}).get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
        fail(f"{profile_id} test Framework must retain paid access mode.")

    embedded = distribution_artifact.get("embeddedDomainModules", {})
    test_factory = embedded.get("factory", {})
    test_om = embedded.get("operatingModel", {})
    if test_factory.get("packageFamily") != expected_factory_family:
        fail(f"{profile_id} Factory family mismatch.")
    if test_om.get("packageFamily") != expected_om_family:
        fail(f"{profile_id} Operating Model family mismatch.")
    if test_factory.get("commercial", {}).get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
        fail(f"{profile_id} embedded Factory must remain PAID_ENTITLEMENT_REQUIRED.")
    if test_om.get("commercial", {}).get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
        fail(f"{profile_id} embedded Operating Model must remain PAID_ENTITLEMENT_REQUIRED.")
    if "PUBLIC_TEST_EVALUATION" not in test_factory.get("provenance", {}).get("sourceRef", ""):
        fail(f"{profile_id} Factory must be explicitly marked public test/evaluation.")
    if "PUBLIC_TEST_EVALUATION" not in test_om.get("provenance", {}).get("sourceRef", ""):
        fail(f"{profile_id} Operating Model must be explicitly marked public test/evaluation.")
    test_pair = evaluate_domain_framework_pair(
        test_factory, test_om, version, creation_type, domain_id
    )
    if not test_pair["compatible"]:
        fail(f"{profile_id} embedded test pair incompatible: {test_pair}")

# Public evaluation bytes must not become production catalog delivery paths.
for paid_id in (
    "safor.factory.software-delivery",
    "safor.om.saas-engineering",
    "safor.factory.book-production",
    "safor.om.book-authoring",
):
    paid_entry = entry_by_id.get(paid_id, {})
    if paid_entry.get("distribution", {}).get("sourceClass") != "ENTITLED_PACKAGE_SOURCE":
        fail(f"{paid_id} production catalog source must remain ENTITLED_PACKAGE_SOURCE.")
    if paid_entry.get("distribution", {}).get("publicModelPath", "NOT_NULL") is not None:
        fail(f"{paid_id} production catalog must still expose no public model path.")

# Strict entitlement schema and commercial delivery contracts.
entitlement_schema = modules.get("schemaEntitlement", {}).get("content", {})
for field in ("status", "commercialBasis", "subject", "grant", "validity", "issuer", "verification"):
    if field not in entitlement_schema.get("required", []):
        fail(f"Entitlement schema must require {field}.")
verification_required = set(
    entitlement_schema.get("properties", {}).get("verification", {}).get("required", [])
)
if "result" not in verification_required:
    fail("Entitlement verification must require result=VERIFIED.")
basis_required = set(
    entitlement_schema.get("properties", {}).get("commercialBasis", {}).get("required", [])
)
if basis_required != {"basisType", "evidenceRef", "sku"}:
    fail("Commercial basis must require basisType, evidenceRef and sku.")

delivery_contract = distribution.get("commercialDeliveryContract", {})
for flag in (
    "noPublicFallback",
    "noDeliveryWithoutEntitlement",
    "noBindingFromExpiredDeliveryEvidence",
    "noDigestSubstitution",
    "humanLoadedLicensedArtifactSupported",
):
    if delivery_contract.get(flag) is not True:
        fail(f"Commercial delivery contract {flag} must be true.")

trust_contract = entitlement.get("trustContract", {})
required_context = set(trust_contract.get("requiredVerificationContext", []))
for field in (
    "evaluatedAt", "subjectRef", "trustedIssuerIds",
    "trustedEntitlementVerifierIds", "trustedDeliveryVerifierIds",
):
    if field not in required_context:
        fail(f"Commercial trust context must require {field}.")
if trust_contract.get("noWallClockInPurePolicy") is not True:
    fail("Commercial policy must not read wall clock.")
if trust_contract.get("noSelfDeclaredTrust") is not True:
    fail("Commercial trust must not be self-declared.")

# 0.13 conformance and self-healing coverage.
self_healing = modules.get("selfHealing", {}).get("content", {})
failure_classes = {x.get("id"): x for x in self_healing.get("failureClasses", [])}
if "SH-24" not in failure_classes:
    fail("Self-Healing must define SH-24 COMPOSABLE_DOMAIN_PACKAGE_FAILURE.")
for forbidden in (
    "INVENT_PACKAGE_ENTITLEMENT",
    "REWRITE_DOMAIN_PACKAGE_TO_MATCH_EXPECTED_DIGEST",
    "SILENTLY_CHANGE_SELECTED_FACTORY_OR_OPERATING_MODEL",
    "FORCE_PACKAGE_COMPATIBILITY_RESULT_TO_PASS",
    "INVENT_COMMERCIAL_BASIS_EVIDENCE",
    "TREAT_REVOKED_SUSPENDED_OR_EXPIRED_ENTITLEMENT_AS_ACTIVE",
    "TRUST_ENTITLEMENT_ISSUER_FROM_SELF_DECLARED_RECORD",
    "TRUST_ENTITLEMENT_OR_DELIVERY_VERIFIER_FROM_SELF_DECLARED_RECORD",
    "INVENT_COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE",
    "IGNORE_COMMERCIAL_DELIVERY_EXPIRY",
    "REWRITE_DELIVERY_DIGEST_TO_MATCH_PACKAGE",
    "SILENTLY_CHANGE_ACTIVE_DOMAIN_TO_FIT_REPLACEMENT",
    "AUTO_REPLACE_COUNTERPART_TO_MAKE_NEW_PACKAGE_COMPATIBLE",
    "IGNORE_PACKAGE_FAMILY_MISMATCH",
    "DOWNGRADE_BIDIRECTIONAL_COMPATIBILITY_TO_ONE_WAY",
):
    if forbidden not in self_healing.get("forbiddenAutomaticRepairs", []):
        fail(f"Self-Healing must forbid {forbidden}.")

conformance = modules.get("conformance", {}).get("content", {})
if conformance.get("schemaVersion") != "0.13.0":
    fail("Conformance model must be 0.13.0.")
assertion_ids = {x.get("id") for x in conformance.get("assertions", [])}
for n in range(217, 261):
    assertion = f"CF-{n:03d}"
    if assertion not in assertion_ids:
        fail(f"Missing composable-package conformance assertion {assertion}.")

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
print("Free Website starter: website-delivery + website-team, FREE_PUBLIC")
print("Software/SaaS: paid Factory + paid Operating Model, two independent entitlements")
print("Commercial access: per selected package, external verified entitlement")
print("Domain package integrity: SHA-256 declared-contract verification")
print("Domain Frameworks: WEBSITE public single-file; SAAS/BOOK commercial build profiles")
print("Replacement compatibility: same-domain + package-family + bidirectional counterpart checks")
print("Project workspace: HUMAN-owned REMOTE_GIT or LOCAL_GIT")
