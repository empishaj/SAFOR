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
modular_master = load_json("v0.8.0/SAFOR-MASTER.json")
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

if bundle.get("format") != "SAFOR_MASTER_COMPLETE_SINGLE_FILE":
    fail("Complete bundle format is invalid.")

modules = bundle.get("embeddedModules", {})
required_modules = {
    "kernel","initialization","interaction","selfHealing","repositoryPolicy","packageRegistry",
    "providerGithub","providerGitlab","operatingModelSaas","operatingModelBook",
    "factorySoftwareWebsite","factoryBook","schemaPackageManifest","schemaControlState",
    "schemaValueStreamState","schemaExecutionState","schemaWorkItem","schemaProject",
    "schemaBindings","schemaDecisionRecord","schemaEvidenceRecord","schemaInteractionMenu",
    "schemaSelfHealingRecord","agentWorkspace","schemaAgentRegistry","schemaAgentIdentity",
    "schemaAgentState","schemaAgentInboxIndex","schemaAgentJob","schemaAgentJobState","schemaAgentResult",
    "agentJobContract","multiAgentScheduler","schemaSchedulerState","schemaDispatchWave","schemaResourceLease","conformance"
}
missing = sorted(required_modules - set(modules))
if missing:
    fail("Missing embedded modules: " + ", ".join(missing))

refs = bundle.get("referenceResolution", {})
bad_refs = sorted(f"{ref}->{target}" for ref, target in refs.items() if target not in modules)
if bad_refs:
    fail("Unresolved embedded references: " + ", ".join(bad_refs))

runtime = bundle.get("runtimeContract", {})
if runtime.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Canonical product repository must be empishaj/SAFOR.")
if runtime.get("canonicalBranch") != "main":
    fail("Canonical product branch must be main.")

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
if actions.get("D01", {}).get("modelRef") != "BOUND_FACTORY.model.discoveryContract":
    fail("D01 must bind Factory discoveryContract.")
if actions.get("P01", {}).get("modelRef") != "BOUND_FACTORY.model.planningContract":
    fail("P01 must bind Factory planningContract.")
for action_id in ("E04","E05"):
    if actions.get(action_id, {}).get("modelRef") != "BOUND_FACTORY.model.evidenceContract":
        fail(f"{action_id} must bind Factory evidenceContract.")

invariants = {x.get("id") for x in kernel.get("invariants", [])}
for inv in tuple(f"INV-{n:03d}" for n in range(37, 87)):
    if inv not in invariants:
        fail(f"Missing required invariant {inv}.")

conformance = modules.get("conformance", {}).get("content", {})
assertions = {x.get("id"): x for x in conformance.get("assertions", [])}
for cf in tuple(f"CF-{n:03d}" for n in range(46, 111)):
    if assertions.get(cf, {}).get("expected") is not True:
        fail(f"Missing/passing conformance assertion {cf}.")


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
if manifest.get("sourceRoot") != "v0.8.0":
    fail("Release manifest source root must be v0.8.0.")
if bundle.get("schemaVersion") != "0.8.0":
    fail("Complete bundle schemaVersion must be 0.8.0.")
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
