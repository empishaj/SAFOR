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

bundle = load_json("SAFOR-MASTER-COMPLETE.json")
manifest = load_json("RELEASE-MANIFEST.json")
modular_master = load_json("v0.11.0/SAFOR-MASTER.json")
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

if bundle.get("format") != "SAFOR_MASTER_COMPLETE_SINGLE_FILE":
    fail("Complete bundle format is invalid.")

modules = bundle.get("embeddedModules", {})
required_modules = {
    "kernel","initialization","interaction","selfHealing","repositoryPolicy","packageRegistry",
    "providerGithub","providerGitlab","operatingModelSaas","operatingModelBook",
    "factorySoftwareWebsite","factoryBook","schemaPackageManifest","schemaControlState",
    "schemaValueStreamState","schemaExecutionState","schemaWorkItem","schemaProject",
    "schemaBindings","schemaDecisionRecord","schemaEvidenceRecord","schemaInteractionMenu","schemaHumanResponse",
    "humanDecisionGate","schemaHumanCognitiveLoadPolicy","schemaHumanDecisionGate","schemaSelfHealingRecord","schemaModuleRecoveryProfile","moduleSelfHealing","agentWorkspace","schemaAgentRegistry","schemaAgentIdentity",
    "schemaAgentState","schemaAgentInboxIndex","schemaAgentJob","schemaAgentJobState","schemaAgentResult",
    "agentJobContract","multiAgentScheduler","schemaSchedulerState","schemaDispatchWave","schemaResourceLease",
    "deterministicControl","eventModel","predicateRegistry","transitionRegistry","effectModel",
    "schemaEvent","schemaPredicate","schemaTransition","schemaEffectIntent","schemaTransitionRecord","schemaStateSnapshot","conformance"
}
missing = sorted(required_modules - set(modules))
if missing:
    fail("Missing embedded modules: " + ", ".join(missing))

module_recovery_model = modules.get("moduleSelfHealing", {}).get("content", {})
profiles = module_recovery_model.get("moduleProfiles", [])
profile_by_key = {}
profile_ids = set()
for profile in profiles:
    key = profile.get("moduleKey")
    pid = profile.get("profileId")
    if not key or not pid:
        fail("Module recovery profile missing moduleKey/profileId.")
        continue
    if key in profile_by_key:
        fail(f"Duplicate module recovery profile for {key}.")
    if pid in profile_ids:
        fail(f"Duplicate module recovery profileId {pid}.")
    profile_by_key[key] = profile
    profile_ids.add(pid)

module_keys = set(modules)
profile_keys = set(profile_by_key)
if module_keys != profile_keys:
    missing_profiles = sorted(module_keys - profile_keys)
    unknown_profiles = sorted(profile_keys - module_keys)
    if missing_profiles:
        fail("Embedded modules missing recovery profiles: " + ", ".join(missing_profiles))
    if unknown_profiles:
        fail("Recovery profiles target unknown module keys: " + ", ".join(unknown_profiles))

coverage = module_recovery_model.get("coverageContract", {})
for field in ("exactCoverageRequired","oneProfilePerEmbeddedModule","noUnprofiledEmbeddedModules","noProfilesForUnknownModuleKeys"):
    if coverage.get(field) is not True:
        fail(f"Module recovery coverage contract {field} must be true.")

profile_required_fields = (
    "profileId","moduleKey","moduleClass","authorityType","repairability",
    "failureDetectors","automaticRepairs","forbiddenRepairs","retryBudget",
    "verification","escalation"
)
valid_repairability = {
    "IMMUTABLE_VALIDATE_ONLY","RESTORE_FROM_VERIFIED_SOURCE",
    "REGENERATE_DERIVED_ONLY","REBIND_EXTERNAL_CAPABILITY"
}
integrity_manifest = bundle.get("integrityManifest", {})
for key, module in modules.items():
    profile = profile_by_key.get(key, {})
    for field in profile_required_fields:
        if field not in profile:
            fail(f"Recovery profile {key} missing {field}.")
    if profile.get("repairability") not in valid_repairability:
        fail(f"Recovery profile {key} has invalid repairability.")
    if not profile.get("failureDetectors"):
        fail(f"Recovery profile {key} needs failure detectors.")
    if not profile.get("automaticRepairs"):
        fail(f"Recovery profile {key} needs automatic repair policy.")
    if not profile.get("forbiddenRepairs"):
        fail(f"Recovery profile {key} needs forbidden repair policy.")
    expected_pid = profile.get("profileId")
    if module.get("selfHealingProfileId") != expected_pid:
        fail(f"Embedded module {key} selfHealingProfileId mismatch.")
    manifest_entry = integrity_manifest.get(key, {})
    if manifest_entry.get("selfHealingProfileId") != expected_pid:
        fail(f"Integrity manifest {key} selfHealingProfileId mismatch.")
    if not str(module.get("sourcePath","")).startswith(("v0.10.0/","v0.11.0/")):
        fail(f"Embedded module {key} must come from an allowed 0.10/0.11 source baseline.")

recovery_schema = modules.get("schemaModuleRecoveryProfile", {}).get("content", {})
schema_required = set(recovery_schema.get("required", []))
for field in profile_required_fields:
    if field not in schema_required:
        fail(f"Module recovery profile schema missing required field {field}.")

refs = bundle.get("referenceResolution", {})
bad_refs = sorted(f"{ref}->{target}" for ref, target in refs.items() if target not in modules)
if bad_refs:
    fail("Unresolved embedded references: " + ", ".join(bad_refs))

runtime = bundle.get("runtimeContract", {})
if runtime.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Canonical product repository must be empishaj/SAFOR.")
if runtime.get("canonicalBranch") != "main":
    fail("Canonical product branch must be main.")
if "exactly one interaction menu" not in runtime.get("humanTerminalMenuRule", ""):
    fail("Runtime contract must require exactly one terminal HUMAN interaction menu.")

memory = runtime.get("absoluteRuntimePrerequisite", {})
if memory.get("repositoryPattern") != "{selectedOwner}/safor-memory":
    fail("Runtime memory must be {selectedOwner}/safor-memory.")
for key in ("mustPreExist","mustBeReadable","mustBeWritable"):
    if memory.get(key) is not True:
        fail(f"Runtime memory prerequisite {key} must be true.")
if memory.get("autoCreate") is not False:
    fail("safor-memory must never be auto-created.")
if memory.get("onFailure") != "STOP":
    fail("Missing/insufficient safor-memory must STOP.")

creation_types = runtime.get("mandatoryCreationTypes", [])
ids = [x.get("id") for x in creation_types]
if ids != ["SOFTWARE_WEBSITE","BOOK"]:
    fail("Mandatory creation types must be SOFTWARE_WEBSITE and BOOK in that order.")

factory_expectations = {
    "factorySoftwareWebsite": "SOFTWARE_WEBSITE",
    "factoryBook": "BOOK",
}
for module_name, expected_type in factory_expectations.items():
    model = modules.get(module_name, {}).get("content", {}).get("model", {})
    for contract in ("discoveryContract","planningContract","evidenceContract"):
        value = model.get(contract)
        if not isinstance(value, dict):
            fail(f"{module_name} missing {contract}.")
        elif value.get("creationType") != expected_type:
            fail(f"{module_name}.{contract} creationType mismatch.")

kernel = modules.get("kernel", {}).get("content", {})
actions = {a.get("id"): a for a in kernel.get("controlPlane", {}).get("actions", [])}
if kernel.get("controlPlane", {}).get("startActionId") != "K00":
    fail("Kernel startActionId must be K00 module-recovery preflight.")
if actions.get("K00", {}).get("modelRef") != "module-self-healing-model.json":
    fail("K00 must bind module-self-healing-model.json.")
if actions.get("K00A", {}).get("modelRef") != "deterministic-control-model.json":
    fail("K00A must bind deterministic-control-model.json.")
initialization = modules.get("initialization", {}).get("content", {})
sequence = initialization.get("sequence", [])
if not sequence or sequence[0].get("id") != "INIT-00":
    fail("Initialization must begin with INIT-00 module-recovery preflight.")
if sequence and sequence[0].get("failOutcome") != "STOP":
    fail("INIT-00 recovery preflight must fail closed to STOP.")
if len(sequence) < 2 or sequence[1].get("id") != "INIT-00A":
    fail("Initialization second step must be INIT-00A deterministic-control preflight.")
if len(sequence) >= 2 and sequence[1].get("failOutcome") != "STOP":
    fail("INIT-00A deterministic-control preflight must fail closed to STOP.")
if actions.get("D01", {}).get("modelRef") != "BOUND_FACTORY.model.discoveryContract":
    fail("D01 must bind Factory discoveryContract.")
if actions.get("P01", {}).get("modelRef") != "BOUND_FACTORY.model.planningContract":
    fail("P01 must bind Factory planningContract.")
for action_id in ("E04","E05"):
    if actions.get(action_id, {}).get("modelRef") != "BOUND_FACTORY.model.evidenceContract":
        fail(f"{action_id} must bind Factory evidenceContract.")

if actions.get("H01", {}).get("modelRef") != "module-self-healing-model.json":
    fail("H01 must bind module-self-healing-model.json.")
if actions.get("H02", {}).get("modelRef") != "self-healing-model.json":
    fail("H02 must bind self-healing-model.json.")
for action_id in ("H03","H04"):
    if actions.get(action_id, {}).get("modelRef") != "module-self-healing-model.json":
        fail(f"{action_id} must bind module-self-healing-model.json.")
if kernel.get("moduleSelfHealingModelRef") != "module-self-healing-model.json":
    fail("Kernel must reference module-self-healing-model.json.")
if kernel.get("schemas", {}).get("moduleRecoveryProfile") != "schemas/module-recovery-profile.schema.json":
    fail("Kernel must reference module recovery profile schema.")

invariants = {x.get("id") for x in kernel.get("invariants", [])}
for inv in tuple(f"INV-{n:03d}" for n in range(37, 136)):
    if inv not in invariants:
        fail(f"Missing required invariant {inv}.")

conformance = modules.get("conformance", {}).get("content", {})
assertions = {x.get("id"): x for x in conformance.get("assertions", [])}
for cf in tuple(f"CF-{n:03d}" for n in range(46, 176)):
    if assertions.get(cf, {}).get("expected") is not True:
        fail(f"Missing/passing conformance assertion {cf}.")



self_healing = modules.get("selfHealing", {}).get("content", {})
if self_healing.get("moduleRecoveryModelRef") != "module-self-healing-model.json":
    fail("Self-healing model must reference module recovery model.")
for principle in ("moduleProfileRequired","exactModuleCoverageRequired","failClosedOnRecoveryControlFailure","derivedOnlyRegeneration","noSemanticAutoRewrite"):
    if self_healing.get("principles", {}).get(principle) is not True:
        fail(f"Self-healing principle {principle} must be true.")
failure_classes = {x.get("id"): x for x in self_healing.get("failureClasses", [])}
for n in range(10, 22):
    cid = f"SH-{n:02d}"
    if cid not in failure_classes:
        fail(f"Missing module-aware self-healing failure class {cid}.")
if self_healing.get("moduleRecoveryDispatch", {}).get("noMatch") != "STOP_AND_ESCALATE":
    fail("Unknown module recovery target must STOP_AND_ESCALATE.")
if self_healing.get("moduleRecoveryDispatch", {}).get("multipleMatches") != "STOP_AND_ESCALATE":
    fail("Ambiguous module recovery target must STOP_AND_ESCALATE.")

repair_schema = modules.get("schemaSelfHealingRecord", {}).get("content", {})
repair_required = set(repair_schema.get("required", []))
for field in ("moduleKey","moduleProfileId","moduleAuthorityType","moduleRepairability","moduleSourceRef","profileDecision"):
    if field not in repair_required:
        fail(f"Self-healing record schema missing module-aware field {field}.")
agent_model = modules.get("agentWorkspace", {}).get("content", {})
agent_job_model = modules.get("agentJobContract", {}).get("content", {})
if agent_job_model.get("authority", {}).get("authoritativeArtifact") != "agents/{agentId}/inbox/{jobId}.json":
    fail("Canonical job model authoritative path mismatch.")
if agent_job_model.get("authority", {}).get("humanProjection") != "agents/{agentId}/inbox/{jobId}.md":
    fail("Canonical job model HUMAN projection path mismatch.")
if agent_job_model.get("authorizationSemantics", {}).get("jobPermissionIsUpperBound") is not True:
    fail("Canonical job permissions must be an upper bound only.")
if "must not invent" not in agent_job_model.get("roleAndSkillContract", {}).get("skillSourceRule", "").lower():
    fail("Canonical job model must forbid invented skill provenance.")
if agent_job_model.get("humanProjectionContract", {}).get("providerReadbackRequiredBeforeReady") is not True:
    fail("Canonical job Markdown must be read back before READY.")
if agent_model.get("topology", {}).get("inboxIndex") != "agents/{agentId}/inbox/index.json":
    fail("Agent Workspace inbox index path mismatch.")
if agent_model.get("topology", {}).get("jobHumanReadableProjection") != "agents/{agentId}/inbox/{jobId}.md":
    fail("Agent Workspace HUMAN job path mismatch.")
discovery = agent_model.get("discoveryProtocol", {})
if discovery.get("noDirectoryEnumerationRequired") is not True:
    fail("Agent Workspace discovery must not require directory enumeration.")
if discovery.get("authority") != "NON_AUTHORITATIVE_DISCOVERABILITY_PROJECTION":
    fail("Agent inbox index must be a non-authoritative discovery projection.")
if agent_model.get("activationContract", {}).get("backgroundWakeupAssumed") is not False:
    fail("Agent Workspace must not assume background wakeup.")
if "copy" not in agent_model.get("activationContract", {}).get("promptTransportRule", "").lower():
    fail("Agent Workspace must explicitly forbid HUMAN job-prompt transport as authority.")
ownership = agent_model.get("ownership", {})
if "master/jobs/{jobId}.json" not in ownership.get("MASTER_ONLY", []):
    fail("MASTER must own authoritative agent job lifecycle.")
if "agents/{agentId}/state.json" not in ownership.get("AGENT_ONLY", []):
    fail("Agent must own only its local runtime state.")
if agent_model.get("resultProtocol", {}).get("notAcceptance") != "Agent result is a claim of work performed, never authoritative acceptance.":
    fail("Agent result must not be authoritative acceptance.")
for action_id in ("A01","A03","A04","A05"):
    if actions.get(action_id, {}).get("modelRef") != "agent-workspace-model.json":
        fail(f"{action_id} must bind agent-workspace-model.json.")
if actions.get("A02", {}).get("modelRef") != "agent-job-contract-model.json":
    fail("A02 must bind agent-job-contract-model.json.")
if actions.get("E03", {}).get("modelRef") != "agent-job-contract-model.json":
    fail("E03 must bind agent-job-contract-model.json.")
execution_schema = modules.get("schemaExecutionState", {}).get("content", {})
if "agentJobStateRefs" not in execution_schema.get("required", []):
    fail("Execution state must reference agent job states.")
job_state_schema = modules.get("schemaAgentJobState", {}).get("content", {})
if job_state_schema.get("properties", {}).get("owner", {}).get("const") != "MASTER":
    fail("Agent job state must be MASTER-owned.")
job_schema = modules.get("schemaAgentJob", {}).get("content", {})
job_required = job_schema.get("required", [])
for field in ("identity","lineage","provenance","assignment","roleContract","skills","task","dependencies","inputs","authorization","workspace","scheduling","outputContract","verificationContract","constraints","humanReadableProjection"):
    if field not in job_required:
        fail(f"Canonical agent job missing top-level contract area {field}.")

defs = job_schema.get("$defs", {})
job_identity = defs.get("jobIdentity", {})
if job_identity.get("properties", {}).get("immutableAfterDispatch", {}).get("const") is not True:
    fail("Agent job must be immutable after dispatch.")
job_id_pattern = job_identity.get("properties", {}).get("jobId", {}).get("pattern", "")
if "-7" not in job_id_pattern:
    fail("Agent jobId must require UUIDv7.")

lineage_required = defs.get("lineage", {}).get("required", [])
for field in ("packageId","packageSequence","workItemId","sequence","supersedesJobId"):
    if field not in lineage_required:
        fail(f"Agent job lineage missing {field}.")
sequence_required = defs.get("sequence", {}).get("required", [])
for field in ("planSequence","dispatchSequence","attempt","reworkCycle"):
    if field not in sequence_required:
        fail(f"Agent job sequence missing {field}.")

provenance_required = defs.get("provenance", {}).get("required", [])
for field in ("createdAt","issuedAt","createdBy","planningRef","executionStateRef","mandateRef"):
    if field not in provenance_required:
        fail(f"Agent job provenance missing {field}.")
master_prov_required = defs.get("masterProvenance", {}).get("required", [])
for field in ("masterId","masterVersion","masterRunId","masterStateRevision"):
    if field not in master_prov_required:
        fail(f"Agent job MASTER provenance missing {field}.")

assignment_required = defs.get("assignment", {}).get("required", [])
for field in ("agentId","agentName","identityRevision","identityRef","assignmentReason"):
    if field not in assignment_required:
        fail(f"Agent job assignment missing {field}.")

role_required = defs.get("roleContract", {}).get("required", [])
for field in ("roleId","roleName","roleDefinitionRef","roleDefinitionBlobSha","mission","responsibilities","mustNotActAs","decisionRights","authorityExpansionAllowed"):
    if field not in role_required:
        fail(f"Agent job role contract missing {field}.")
if defs.get("roleContract", {}).get("properties", {}).get("authorityExpansionAllowed", {}).get("const") is not False:
    fail("Job role contract must forbid authority expansion.")

skill_required = defs.get("skill", {}).get("required", [])
for field in ("skillId","skillVersion","mandatory","description","executionInstructions","useFor","skillRef","skillBlobSha","requiredLevel"):
    if field not in skill_required:
        fail(f"Agent job skill contract missing {field}.")
if job_schema.get("properties", {}).get("skills", {}).get("minItems") != 1:
    fail("Every agent job must declare at least one explicit skill.")

input_props = defs.get("input", {}).get("properties", {})
if input_props.get("mode", {}).get("const") != "READ_ONLY":
    fail("All canonical job inputs must be READ_ONLY.")
for field in ("commitSha","blobSha"):
    if field not in input_props:
        fail(f"Agent job input missing immutable reference field {field}.")

authorization_required = defs.get("authorization", {}).get("required", [])
for field in ("authorityBasis","actualProviderRightsMustBeVerified","providerCapabilities","repositoryPermissions","explicitlyForbidden"):
    if field not in authorization_required:
        fail(f"Agent job authorization missing {field}.")
if defs.get("authorization", {}).get("properties", {}).get("actualProviderRightsMustBeVerified", {}).get("const") is not True:
    fail("Agent job must require actual provider-right verification.")
repo_permission_required = defs.get("repositoryPermission", {}).get("required", [])
for field in ("repository","read","write","branchCreate","commit","push","changeRequestCreate","merge","deploy"):
    if field not in repo_permission_required:
        fail(f"Repository permission contract missing {field}.")

workspace_required = defs.get("workspace", {}).get("required", [])
for field in ("resourceAccessSource","readSet","writeSet","exclusiveKeys","gitWorkspaces"):
    if field not in workspace_required:
        fail(f"Agent job workspace missing {field}.")
branch_pattern = defs.get("gitWorkspace", {}).get("properties", {}).get("branch", {}).get("pattern")
if branch_pattern != "^safor/job/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$":
    fail("Agent job branch pattern must use Git-ref-safe job/agent keys.")
if defs.get("gitWorkspace", {}).get("properties", {}).get("directDefaultBranchWrite", {}).get("const") is not False:
    fail("Agent job must forbid direct default-branch writes.")

scheduling_required = defs.get("scheduling", {}).get("required", [])
for field in ("dispatchRevision","dispatchState","dispatchWaveRef","resourceLeaseRefs","claimPolicy","claimWindow"):
    if field not in scheduling_required:
        fail(f"Agent job scheduling missing {field}.")
if defs.get("claimWindow", {}).get("properties", {}).get("onExpired", {}).get("const") != "RECONCILE_WITH_MASTER":
    fail("Expired job claim windows must reconcile with MASTER.")

output_required = defs.get("outputContract", {}).get("required", [])
for field in ("machineResult","humanReadableResult","evidenceRoot","auditRoot","requiredOutputs","gitTraceRequired"):
    if field not in output_required:
        fail(f"Agent job output contract missing {field}.")

verify_required = defs.get("verificationContract", {}).get("required", [])
for field in ("acceptanceCriteria","evidenceRequirements","review","selfAcceptanceAllowed","acceptanceAuthority"):
    if field not in verify_required:
        fail(f"Agent job verification contract missing {field}.")
if defs.get("verificationContract", {}).get("properties", {}).get("selfAcceptanceAllowed", {}).get("const") is not False:
    fail("Agent job must forbid self acceptance.")
if defs.get("verificationContract", {}).get("properties", {}).get("acceptanceAuthority", {}).get("const") != "MASTER":
    fail("MASTER must own job acceptance authority.")

constraints = defs.get("constraints", {}).get("properties", {})
for field in ("mayExpandScope","mayModifyMasterState","mayModifyJobContract","mayModifyAgentIdentity","mayModifyInboxIndex","mayModifySchedulerState","mayModifyResourceLease","mayChangeRole","mayDelegate"):
    if constraints.get(field, {}).get("const") is not False:
        fail(f"Agent job constraint {field} must be false.")

projection = defs.get("humanReadableProjection", {})
projection_required = projection.get("required", [])
for field in ("repository","ref","format","blobSha","authoritative","generatedFromJson","requiredSections","readbackRequiredBeforeReady"):
    if field not in projection_required:
        fail(f"Agent job HUMAN projection missing {field}.")
projection_props = projection.get("properties", {})
if projection_props.get("authoritative", {}).get("const") is not False:
    fail("HUMAN job projection must be non-authoritative.")
if projection_props.get("generatedFromJson", {}).get("const") is not True:
    fail("HUMAN job projection must be generated from JSON.")
if projection_props.get("readbackRequiredBeforeReady", {}).get("const") is not True:
    fail("HUMAN job projection must be read back before READY.")
projection_sections = defs.get("jobProjectionSections", {})
if projection_sections.get("minItems") != 14 or projection_sections.get("maxItems") != 14:
    fail("HUMAN job projection must contain all fourteen required sections.")
inbox_index_schema = modules.get("schemaAgentInboxIndex", {}).get("content", {})
if inbox_index_schema.get("properties", {}).get("authoritativeLifecycle", {}).get("const") is not False:
    fail("Agent inbox index schema must be non-authoritative.")
if inbox_index_schema.get("properties", {}).get("verificationRule", {}).get("const") != "READ_MASTER_JOB_STATE_BEFORE_CLAIM":
    fail("Agent inbox index must require MASTER job-state verification before claim.")
identity_schema = modules.get("schemaAgentIdentity", {}).get("content", {})
activation_enums = identity_schema.get("properties", {}).get("activationContract", {}).get("properties", {}).get("onActivation", {}).get("items", {}).get("enum", [])
if "LOAD_INBOX_INDEX" not in activation_enums or "READ_MASTER_JOB_STATE" not in activation_enums:
    fail("Agent identity activation must load the inbox index and MASTER job state.")
if "SCAN_INBOX" in activation_enums:
    fail("Agent identity activation must not depend on repository inbox scanning.")
result_schema = modules.get("schemaAgentResult", {}).get("content", {})
if "completionStatus" not in result_schema.get("required", []):
    fail("Agent result schema missing completionStatus.")

scheduler = modules.get("multiAgentScheduler", {}).get("content", {})
if scheduler.get("capacityModel", {}).get("agentDefaultMaxConcurrentJobs") != 1:
    fail("Default chat-agent scheduler capacity must be one job.")
if scheduler.get("capacityModel", {}).get("defaultProjectMaxParallelJobs") != "AUTO":
    fail("Default project parallelism ceiling must be AUTO.")
if scheduler.get("conflictModel", {}).get("safeDefault") != "Any ambiguity is treated as conflict and the jobs are serialized.":
    fail("Unknown scheduler conflicts must serialize.")
if scheduler.get("gitIsolation", {}).get("directMainWriteForbidden") is not True:
    fail("Agent mutating jobs must forbid direct default-branch writes.")
if "acyclic directed graph" not in scheduler.get("workDecomposition", {}).get("dependencyGraphRule", ""):
    fail("Multi-agent scheduler must require an acyclic dependency graph.")
if "RECONCILE_REQUIRED" not in scheduler.get("leaseProtocol", {}).get("expiryRule", ""):
    fail("Lease expiry must require reconciliation before reassignment.")
for action_id in ("S01","S02","S03","S04","S05","S06","S07"):
    if actions.get(action_id, {}).get("modelRef") != "multi-agent-scheduler-model.json":
        fail(f"{action_id} must bind multi-agent-scheduler-model.json.")

work_schema = modules.get("schemaWorkItem", {}).get("content", {})
if "execution" not in work_schema.get("required", []):
    fail("Work items must include execution scheduling metadata.")
execution_props = work_schema.get("properties", {}).get("execution", {}).get("properties", {})
if execution_props.get("unit", {}).get("enum") != ["ATOMIC","COMPOSITE"]:
    fail("Work item execution unit must support ATOMIC and COMPOSITE.")
if "resourceAccess" not in execution_props:
    fail("Work items must declare scheduling resource access.")
parallel_decision = execution_props.get("parallelizationDecision", {})
if not parallel_decision:
    fail("Work items must declare an evidence-backed parallelizationDecision.")
class_enum = parallel_decision.get("properties", {}).get("classification", {}).get("enum", [])
if class_enum != ["PARALLEL_CANDIDATE","SERIAL_ONLY","COMPOSITE_CONTAINER"]:
    fail("Work-item parallelization classification contract mismatch.")
if len(work_schema.get("allOf", [])) < 2:
    fail("Work-item schema must constrain ATOMIC and COMPOSITE execution forms.")

registry_schema = modules.get("schemaAgentRegistry", {}).get("content", {})
agent_entry = registry_schema.get("$defs", {}).get("agentEntry", {})
if "scheduling" not in agent_entry.get("required", []):
    fail("Agent registry must declare scheduling capacity.")
sched_props = agent_entry.get("properties", {}).get("scheduling", {}).get("properties", {})
if "dispatchEnabled" not in sched_props or "maxConcurrentJobs" not in sched_props:
    fail("Agent registry scheduling requires dispatchEnabled and maxConcurrentJobs.")

for field in ("schedulerStateRef","activeDispatchWaveRefs","resourceLeaseRefs"):
    if field not in execution_schema.get("required", []):
        fail(f"Execution state missing scheduler reference {field}.")

for field in ("humanReadableReport","gitTrace"):
    if field not in result_schema.get("required", []):
        fail(f"Agent result schema missing {field}.")
human_report = result_schema.get("properties", {}).get("humanReadableReport", {})
human_report_required = human_report.get("required", [])
for field in ("repository","ref","commitSha","blobSha","format","requiredSections"):
    if field not in human_report_required:
        fail(f"HUMAN-readable result report missing {field}.")
sections = human_report.get("properties", {}).get("requiredSections", {})
if sections.get("minItems") != 8 or sections.get("maxItems") != 8:
    fail("HUMAN-readable result requiredSections must contain all eight required sections.")
git_trace_entry = result_schema.get("$defs", {}).get("gitTraceEntry", {}).get("required", [])
for field in ("repository","branch","baseCommitSha","headCommitSha","commitShas","changedPaths","providerReadbackRef"):
    if field not in git_trace_entry:
        fail(f"Git trace entry missing {field}.")

if agent_model.get("topology", {}).get("agentHumanReadableResult") != "agents/{agentId}/outbox/{jobId}.result.md":
    fail("Agent Workspace must define the HUMAN-readable result path.")
if "agents/{agentId}/outbox/{jobId}.result.md" not in ownership.get("AGENT_ONLY", []):
    fail("Agent must own its HUMAN-readable result report path.")

for module_name in ("factorySoftwareWebsite","factoryBook"):
    model = modules.get(module_name, {}).get("content", {}).get("model", {})
    sched_contract = model.get("schedulingContract", {})
    if sched_contract.get("atomicDispatchOnly") is not True:
        fail(f"{module_name} must require atomic dispatch.")
    if sched_contract.get("resourceAccessRequired") is not True:
        fail(f"{module_name} must require resource access declarations.")
    req = model.get("planningContract", {}).get("requiredForEachWorkItem", [])
    for field in ("execution","execution.resourceAccess","execution.parallelizationDecision"):
        if field not in req:
            fail(f"{module_name} planning contract missing {field}.")
    if "acyclic directed graph" not in sched_contract.get("dependencyGraphRule", ""):
        fail(f"{module_name} scheduling contract must require an acyclic dependency graph.")

interaction = modules.get("interaction", {}).get("content", {})
if "multiAgentStatusExperience" not in interaction:
    fail("Interaction model must expose multi-agent utilization/status.")

cognitive = interaction.get("humanCognitiveLoadPolicy", {})
if cognitive.get("schemaRef") != "schemas/human-cognitive-load-policy.schema.json":
    fail("Interaction model must bind the HUMAN cognitive-load schema.")
principles = cognitive.get("principles", {})
for key in ("highLoadAllowedWhenHumanKnowledgeIsRequired","extraneousTechnicalLoadAlwaysMinimized","loadMustDecreaseAsContextBecomesKnown","humanIsDecisionMakerNotWorkflowOperator","progressiveDisclosureRequired","oneDecisionContextAtATime","deriveBeforeAsk","noRepeatedUnchangedApproval","domainLanguageFirst"):
    if principles.get(key) is not True:
        fail(f"Cognitive-load principle {key} must be true.")
phase_profiles = cognitive.get("phaseProfiles", {})
expected_phase_loads = {
    "BOOTSTRAP":"MEDIUM","DISCOVERY":"HIGH","PLANNING":"MEDIUM","SCHEDULING":"VERY_LOW",
    "AGENT_COORDINATION":"VERY_LOW","EXECUTION":"LOW","RECOVERY":"LOW","OUTCOME":"MEDIUM","CLOSING":"LOW"
}
for phase, expected_load in expected_phase_loads.items():
    profile = phase_profiles.get(phase, {})
    if profile.get("targetLoad") != expected_load:
        fail(f"{phase} cognitive-load target must be {expected_load}.")
    if profile.get("maxNewDecisionsPerTurn") != 1:
        fail(f"{phase} must limit new HUMAN decision contexts to one per turn.")
    if profile.get("technicalDetailDefault") != "HIDDEN":
        fail(f"{phase} must hide technical detail by default.")
if phase_profiles.get("DISCOVERY", {}).get("allowDeepQuestions") is not True:
    fail("DISCOVERY must explicitly allow deep sequential questions.")
if phase_profiles.get("SCHEDULING", {}).get("humanInteractionDefault") != "NONE":
    fail("SCHEDULING HUMAN interaction default must be NONE.")
if phase_profiles.get("AGENT_COORDINATION", {}).get("humanInteractionDefault") != "NONE":
    fail("AGENT_COORDINATION HUMAN interaction default must be NONE.")
if phase_profiles.get("EXECUTION", {}).get("humanInteractionDefault") != "EXCEPTION_ONLY":
    fail("EXECUTION HUMAN interaction default must be EXCEPTION_ONLY.")
if phase_profiles.get("RECOVERY", {}).get("humanInteractionDefault") != "ESCALATION_ONLY":
    fail("RECOVERY HUMAN interaction default must be ESCALATION_ONLY.")

heuristic = cognitive.get("heuristicLoadEstimate", {})
if heuristic.get("notPsychometricMeasure") is not True:
    fail("Cognitive-load estimate must explicitly be non-psychometric.")
factor_sum = sum(v.get("maxPoints", 0) for v in heuristic.get("factors", {}).values() if isinstance(v, dict))
if factor_sum != 100:
    fail("Cognitive-load heuristic factor maxima must sum to 100.")
phase_max = heuristic.get("phaseMaximumWithoutExplicitEscalation", {})
for phase in expected_phase_loads:
    if phase not in phase_max:
        fail(f"Cognitive-load heuristic missing phase maximum for {phase}.")

question_policy = cognitive.get("questionPolicy", {})
for key in ("askOnlyMinimumNecessaryQuestion","decisionReasonMustBeRecorded","noQuestionWhenAnswerSafelyDerivable","noQuestionWhenUnchangedDecisionReusable"):
    if question_policy.get(key) is not True:
        fail(f"Cognitive question policy {key} must be true.")
if question_policy.get("maxNewDecisionContextsPerTurn") != 1:
    fail("Cognitive question policy must allow one new decision context per turn.")

language = interaction.get("humanLanguagePolicy", {})
if language.get("defaultVocabulary") != "HUMAN_DOMAIN_LANGUAGE":
    fail("Default HUMAN vocabulary must be HUMAN_DOMAIN_LANGUAGE.")
if language.get("technicalIdsHiddenByDefault") is not True:
    fail("Technical IDs must be hidden by default.")
for term in ("DISPATCH_WAVE","RESOURCE_LEASE","PROVIDER_READBACK","EXECUTION_MANDATE"):
    if term not in language.get("internalTermsHiddenByDefault", []):
        fail(f"HUMAN language policy must hide internal term {term}.")
if language.get("humanTerms", {}).get("WORK_ITEM") != "Aufgabe":
    fail("WORK_ITEM must map to HUMAN term Aufgabe.")

primary = interaction.get("primaryActionPolicy", {})
if primary.get("labelMode") != "DOMAIN_SPECIFIC_DYNAMIC":
    fail("Primary actions must use domain-specific dynamic labels.")
if primary.get("fallbackLabel") != "Weiter":
    fail("Primary action fallback label must be Weiter.")
if "NEXT_ROUND" not in primary.get("forbiddenDefaultLabels", []):
    fail("NEXT_ROUND must be forbidden as a default HUMAN label.")

gate = modules.get("humanDecisionGate", {}).get("content", {})
if gate.get("defaultDecision") != "DO_NOT_ASK":
    fail("HUMAN Decision Gate must default to DO_NOT_ASK.")
legit = [x.get("id") for x in gate.get("legitimateReasons", [])]
if len(set(legit)) != 12:
    fail("HUMAN Decision Gate must define exactly 12 unique legitimate reasons.")
for item in ("JOB_ID_GENERATION","RESOURCE_LEASE_MANAGEMENT","DISPATCH_WAVE_PLANNING","READBACK_VERIFICATION","INTERNAL_STATE_TRANSITIONS","FACTORY_OR_OPERATING_MODEL_BINDING_WHEN_DETERMINISTIC_FROM_APPROVED_CREATION_TYPE"):
    if item not in gate.get("mustNotAskHumanFor", []):
        fail(f"HUMAN Decision Gate must forbid delegation of {item}.")
if gate.get("decisionReusePolicy", {}).get("unchangedApprovalRepetitionForbidden") is not True:
    fail("Unchanged HUMAN approval repetition must be forbidden.")
if gate.get("latePhasePolicy", {}).get("schedulingDefault") != "NO_HUMAN_INTERACTION":
    fail("Decision Gate scheduling default must be NO_HUMAN_INTERACTION.")
if gate.get("latePhasePolicy", {}).get("executionDefault") != "EXCEPTION_ONLY":
    fail("Decision Gate execution default must be EXCEPTION_ONLY.")
if gate.get("latePhasePolicy", {}).get("recoveryDefault") != "ESCALATION_ONLY":
    fail("Decision Gate recovery default must be ESCALATION_ONLY.")

if kernel.get("humanDecisionGateModelRef") != "human-decision-gate-model.json":
    fail("Kernel must bind human-decision-gate-model.json.")
if kernel.get("schemas", {}).get("humanCognitiveLoadPolicy") != "schemas/human-cognitive-load-policy.schema.json":
    fail("Kernel must bind HUMAN cognitive-load schema.")
if kernel.get("schemas", {}).get("humanDecisionGate") != "schemas/human-decision-gate.schema.json":
    fail("Kernel must bind HUMAN decision-gate schema.")
guard = kernel.get("controlPlane", {}).get("crossCuttingGuards", {}).get("humanDecisionGate", {})
if guard.get("defaultOutcome") != "DO_NOT_ASK" or guard.get("appliesBefore") != "EVERY_HUMAN_QUESTION_APPROVAL_OR_CHOICE":
    fail("Kernel cross-cutting HUMAN Decision Gate contract is invalid.")

if actions.get("K10", {}).get("humanDecision") is not None:
    fail("K10 deterministic creation-profile binding must not require unconditional HUMAN approval.")
if actions.get("K10", {}).get("humanDecisionWhen") != "ONLY_IF_NON_STANDARD_CHANGED_OR_CONFLICTING_BINDING_REQUIRES_HUMAN_CHOICE":
    fail("K10 must declare the exceptional HUMAN-decision condition.")
if actions.get("K10A", {}).get("humanDecision") != "PACKAGE_BINDING_APPROVAL":
    fail("K10A must carry exceptional PACKAGE_BINDING_APPROVAL.")
bootstrap_actions = next((p.get("actions", []) for p in kernel.get("controlPlane", {}).get("phases", []) if p.get("id") == "BOOTSTRAP"), [])
if "K10" not in bootstrap_actions or "K10A" not in bootstrap_actions or bootstrap_actions.index("K10A") != bootstrap_actions.index("K10") + 1:
    fail("BOOTSTRAP must place exceptional K10A immediately after deterministic K10.")

for action in kernel.get("controlPlane", {}).get("actions", []):
    if action.get("humanDecision"):
        contract = action.get("humanInteractionContract", {})
        for field in ("gateRef","phase","reason","targetLoad","maxNewDecisionContexts","technicalDetailExposure","deriveBeforeAsk","reuseUnchangedDecision"):
            if field not in contract:
                fail(f"{action.get('id')} HUMAN decision action missing interaction contract field {field}.")
        if contract.get("gateRef") != "human-decision-gate-model.json":
            fail(f"{action.get('id')} must bind HUMAN Decision Gate.")
        if contract.get("maxNewDecisionContexts") != 1:
            fail(f"{action.get('id')} must limit HUMAN interaction to one decision context.")
        if contract.get("deriveBeforeAsk") is not True or contract.get("reuseUnchangedDecision") is not True:
            fail(f"{action.get('id')} must derive/reuse before asking.")
        if contract.get("reason") not in legit:
            fail(f"{action.get('id')} uses an invalid HUMAN interaction reason.")

for action_id in ("D01","O01"):
    contract = actions.get(action_id, {}).get("humanInteractionContract", {})
    if contract.get("gateRef") != "human-decision-gate-model.json":
        fail(f"{action_id} dynamic HUMAN interaction must be Decision-Gate governed.")
if actions.get("D01", {}).get("humanInteractionContract", {}).get("targetLoad") != "HIGH":
    fail("D01 DISCOVERY target HUMAN load must be HIGH.")

human_response_schema = modules.get("schemaHumanResponse", {}).get("content", {})
for field in ("format","schemaVersion","responseId","phase","surface","content","terminalMenu","renderingContract"):
    if field not in human_response_schema.get("required", []):
        fail(f"HUMAN response schema missing required field {field}.")
terminal_menu_ref = human_response_schema.get("properties", {}).get("terminalMenu", {}).get("$ref")
if terminal_menu_ref != "interaction-menu.schema.json":
    fail("HUMAN response schema terminalMenu must reference interaction-menu.schema.json.")
render_contract = human_response_schema.get("properties", {}).get("renderingContract", {}).get("properties", {})
for field, expected in (
    ("terminalElement", "terminalMenu"),
    ("exactlyOneTerminalMenu", True),
    ("contentAfterTerminalElementForbidden", True),
    ("stopRenderingAfterTerminalMenu", True),
):
    node = render_contract.get(field, {})
    if node.get("const") != expected:
        fail(f"HUMAN response rendering contract {field} mismatch.")

interaction = modules.get("interaction", {}).get("content", {})
terminal_contract = interaction.get("terminalMenuContract", {})
for field in ("exactlyOne","mustBeFinalRenderedElement","contentAfterMenuForbidden","stopRenderingAfterMenu","menuPresenceDoesNotImplyHumanDecision"):
    if terminal_contract.get(field) is not True:
        fail(f"Interaction terminalMenuContract {field} must be true.")
if terminal_contract.get("responseSchemaRef") != "schemas/human-response.schema.json":
    fail("Interaction terminalMenuContract must reference HUMAN response schema.")
if terminal_contract.get("finalizer", {}).get("emitWithoutSuccessfulFinalization") is not False:
    fail("HUMAN response finalizer must fail closed.")

interaction_menu_schema = modules.get("schemaInteractionMenu", {}).get("content", {})
context_required = interaction_menu_schema.get("properties", {}).get("context", {}).get("required", [])
for field in ("phase","cognitiveLoadTarget","interactionReason","decisionRequired","technicalDetailExposure","decisionGateOutcome","heuristicLoadEstimate","reusedDecisionRef"):
    if field not in context_required:
        fail(f"Interaction menu context missing HUMAN governance field {field}.")

cognitive_schema = modules.get("schemaHumanCognitiveLoadPolicy", {}).get("content", {})
for field in ("objective","schemaRef","principles","loadLevels","phaseProfiles","adaptiveLoadRules","heuristicLoadEstimate","questionPolicy"):
    if field not in cognitive_schema.get("required", []):
        fail(f"HUMAN cognitive-load schema missing required field {field}.")
gate_schema = modules.get("schemaHumanDecisionGate", {}).get("content", {})
for field in ("defaultDecision","legitimateReasons","mustNotAskHumanFor","evaluationAlgorithm","decisionReusePolicy","latePhasePolicy"):
    if field not in gate_schema.get("required", []):
        fail(f"HUMAN decision-gate schema missing required field {field}.")

if "SH-19" not in failure_classes:
    fail("Self-healing failure taxonomy must include SH-19 HUMAN interaction governance failure.")
interaction_profile = profile_by_key.get("interaction", {})
for detector in ("TERMINAL_MENU_MISSING","TERMINAL_MENU_NOT_LAST","MULTIPLE_TERMINAL_MENUS","TERMINAL_MENU_INVALID","POST_MENU_CONTENT_DETECTED"):
    if detector not in interaction_profile.get("failureDetectors", []):
        fail(f"Terminal-menu interaction recovery detector missing {detector}.")
if "schemaHumanResponse" not in profile_by_key:
    fail("Module self-healing missing HUMAN response schema recovery profile.")

for module_key in ("humanDecisionGate","schemaHumanCognitiveLoadPolicy","schemaHumanDecisionGate"):
    if module_key not in profile_by_key:
        fail(f"Module self-healing missing HUMAN governance recovery profile {module_key}.")

for schema_name in ("schemaSchedulerState","schemaDispatchWave","schemaResourceLease"):
    if not modules.get(schema_name, {}).get("content"):
        fail(f"Missing scheduler schema module {schema_name}.")

if manifest.get("version") != version:
    fail("RELEASE-MANIFEST.json version must match VERSION.")
if bundle.get("bundleVersion") != version:
    fail("Complete bundle version must match VERSION.")
if manifest.get("status") != "RELEASE_CANDIDATE":
    fail("The current release candidate must declare RELEASE_CANDIDATE status.")
if manifest.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Release manifest canonical repository mismatch.")
expected_versioned = f"SAFOR-MASTER-COMPLETE-v{version}.json"
if manifest.get("distributable") != expected_versioned:
    fail("Release manifest distributable mismatch.")
if manifest.get("latestAlias") != "SAFOR-MASTER-COMPLETE.json":
    fail("Release manifest latest alias mismatch.")
if manifest.get("sourceRoot") != "v0.11.0":
    fail("Release manifest source root must be v0.11.0.")
if bundle.get("schemaVersion") != "0.11.0":
    fail("Complete bundle schemaVersion must be 0.11.0.")
versioned_bundle = load_json(expected_versioned)
if versioned_bundle != bundle:
    fail("Versioned release artifact must exactly match SAFOR-MASTER-COMPLETE.json.")

if modular_master.get("distribution", {}).get("canonicalSource", {}).get("repository") != "empishaj/SAFOR":
    fail("Modular master canonical repository mismatch.")

complete_text = (ROOT / "SAFOR-MASTER-COMPLETE.json").read_text(encoding="utf-8")
old_product_repo = "empishaj/SAFOR" + "."
legacy_lower_for_refs = "sa" + "f"
old_memory_repo = "empishaj/" + legacy_lower_for_refs + "-memory"
old_memory_pattern = "{selectedOwner}/" + legacy_lower_for_refs + "-memory"
for forbidden in (old_product_repo, old_memory_repo, old_memory_pattern):
    if forbidden in complete_text:
        fail(f"Forbidden legacy reference remains in complete bundle: {forbidden}")

# Product-wide legacy branding scan.
legacy_upper = "SA" + "F"
legacy_lower = "sa" + "f"
legacy_patterns = (
    legacy_upper + "-",
    legacy_upper + "_",
    legacy_upper + " ",
    '"' + legacy_upper + '"',
    "urn:" + legacy_lower + ":",
    legacy_lower + ".",
    legacy_lower + "-",
    '"' + legacy_lower + '"',
)
text_extensions = {".json", ".md", ".py", ".yml", ".yaml", ".txt"}
skip_parts = {".git", "__pycache__"}
for path in ROOT.rglob("*"):
    if any(part in skip_parts for part in path.parts):
        continue
    rel = path.relative_to(ROOT)
    rel_text = str(rel)
    for pattern in legacy_patterns:
        if pattern in rel_text:
            fail(f"Legacy branding remains in filename: {rel} ({pattern})")
    if not path.is_file() or path.suffix.lower() not in text_extensions:
        continue
    try:
        text_content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in legacy_patterns:
        if pattern in text_content:
            fail(f"Legacy branding remains in file content: {rel} ({pattern})")


# SAFOR 0.11 deterministic-control validation
required_v011_modules = {
    "kernel","initialization","selfHealing","moduleSelfHealing","conformance",
    "deterministicControl","eventModel","predicateRegistry","transitionRegistry","effectModel",
    "schemaEvent","schemaPredicate","schemaTransition","schemaEffectIntent","schemaTransitionRecord","schemaStateSnapshot"
}
for key in required_v011_modules:
    if not str(modules.get(key, {}).get("sourcePath", "")).startswith("v0.11.0/"):
        fail(f"Deterministic-control module {key} must be sourced from v0.11.0.")

deterministic = modules.get("deterministicControl", {}).get("content", {})
pure = deterministic.get("pureReducerContract", {})
for field in ("sameCanonicalInputsSameLogicalOutput","inputMutationForbidden","providerIoForbidden","llmInvocationForbidden","wallClockReadForbidden","randomnessForbidden","arbitraryCodeFromJsonForbidden"):
    if pure.get(field) is not True:
        fail(f"Deterministic reducer contract {field} must be true.")
if deterministic.get("principle") != "PROBABILISTIC_WORK_DETERMINISTIC_GOVERNANCE":
    fail("Deterministic control principle mismatch.")

predicate_registry = modules.get("predicateRegistry", {}).get("content", {})
allowed_predicates = {p.get("id") for p in predicate_registry.get("predicates", [])}
if not predicate_registry.get("executionPolicy", {}).get("closedRegistry"):
    fail("Predicate registry must be closed.")
transition_registry = modules.get("transitionRegistry", {}).get("content", {})
allowed_effect_ops = set(modules.get("effectModel", {}).get("content", {}).get("stateEffectOperations", []))
required_transitions = {
    "WORK_ITEM_BECOMES_READY",
    "CONTROL_PROJECT_PAUSED",
    "CONTROL_PROJECT_RESUMED_FROM_PAUSE",
    "CONTROL_PROJECT_STOPPED",
    "CONTROL_RESUME_FROM_STOP_REQUIRES_AUTHORIZATION",
    "CONTROL_RECONCILE_UNKNOWN_EXTERNAL_MUTATION",
}
actual_transitions = {t.get("transitionId") for t in transition_registry.get("transitions", [])}
if not required_transitions.issubset(actual_transitions):
    fail("Transition registry missing rc.1 deterministic transitions.")

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
    fail("Transition guard uses unsupported expression form.")

for transition in transition_registry.get("transitions", []):
    walk_guard(transition.get("guards", {}))
    for effect in transition.get("effects", []):
        if effect.get("op") not in allowed_effect_ops:
            fail(f"Transition {transition.get('transitionId')} uses unknown effect op {effect.get('op')}.")

if kernel.get("deterministicControlModelRef") != "deterministic-control-model.json":
    fail("Kernel must reference deterministic-control-model.json.")
if kernel.get("controlPlane", {}).get("crossCuttingGuards", {}).get("deterministicControlKernel", {}).get("appliesBefore") != "EVERY_AUTHORITATIVE_STATE_TRANSITION_IN_MIGRATED_EXECUTABLE_SLICE":
    fail("Kernel deterministic transition guard scope mismatch.")
if runtime.get("deterministicControlRule") is None:
    fail("Complete bundle runtime contract missing deterministicControlRule.")

if errors:
    print("SAFOR validation: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("SAFOR validation: PASS")
print(f"- embedded modules: {len(modules)}")
print("- canonical product repo: empishaj/SAFOR")
print("- runtime memory: {selectedOwner}/safor-memory")
print("- creation types: SOFTWARE_WEBSITE, BOOK")
print("- Factory-bound Discovery/Planning/Evidence: verified")
print("- Multi-agent conflict-aware scheduling: verified")
print("- Git-isolated agent mutations: verified")
print("- HUMAN-readable agent results + Git trace: verified")
print("- Canonical explicit agent jobs: package/sequence/provenance/role/skills/rights/return routes verified")
print("- HUMAN-readable agent job projection: verified")
print("- Module-wide self-healing coverage: verified for every embedded module")
print("- Profile-constrained recovery / fail-closed recovery control: verified")
print("- Phase-aware HUMAN cognitive-load governance: verified")
print("- Derive-before-ask / unchanged-decision reuse: verified")
print("- HUMAN Decision Gate and domain-language abstraction: verified")
