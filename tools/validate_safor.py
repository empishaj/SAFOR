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
master = load_json("v0.5.0/SAFOR-MASTER.json")
memory_model = load_json("v0.5.0/memory-model.json")
init = load_json("v0.5.0/initialization-model.json")
registry = load_json("v0.5.0/package-registry.json")
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

if version != "0.5.0-rc.1":
    fail("VERSION must be 0.5.0-rc.1.")
if manifest.get("version") != version:
    fail("RELEASE-MANIFEST version must match VERSION.")
if manifest.get("status") != "RELEASE_CANDIDATE":
    fail("Release status must be RELEASE_CANDIDATE.")
if bundle.get("format") != "SAFOR_MASTER_COMPLETE_SINGLE_FILE":
    fail("Complete bundle format is invalid.")
if bundle.get("schemaVersion") != "0.5.0":
    fail("Complete bundle schemaVersion must be 0.5.0.")
if bundle.get("bundleVersion") != version:
    fail("Complete bundle version must match VERSION.")

modules = bundle.get("embeddedModules", {})
required_modules = {
    "kernel","initialization","interaction","memoryModel","selfHealing","repositoryPolicy","packageRegistry",
    "providerGithub","providerGitlab","providerGenericGit","providerPlastic",
    "memoryVersionedRepository","memoryHostFilesystem",
    "operatingModelSaas","operatingModelBook","factorySoftwareWebsite","factoryBook",
    "schemaPackageManifest","schemaControlState","schemaValueStreamState","schemaExecutionState","schemaWorkItem",
    "schemaProject","schemaBindings","schemaMemoryBinding","schemaSessionRecord","schemaOutputRecord",
    "schemaDecisionRecord","schemaEvidenceRecord","schemaInteractionMenu","schemaSelfHealingRecord","conformance"
}
missing = sorted(required_modules - set(modules))
if missing:
    fail("Missing embedded modules: " + ", ".join(missing))
if len(modules) != 32:
    fail(f"Expected 32 embedded modules, got {len(modules)}.")

refs = bundle.get("referenceResolution", {})
for ref, target in refs.items():
    if target not in modules:
        fail(f"Unresolved referenceResolution target: {ref}->{target}")

runtime = bundle.get("runtimeContract", {})
if runtime.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Canonical repository must be empishaj/SAFOR.")
if runtime.get("memoryAndWorkProviderIndependent") is not True:
    fail("Memory and work provider must be independent.")
if runtime.get("outputProvenanceRequired") is not True:
    fail("Output provenance must be required.")
if runtime.get("freshSessionResumeFromMemory") is not True:
    fail("Fresh-session resume from Memory must be required.")

memory_req = runtime.get("memoryRequirement", {})
if memory_req.get("providerNeutral") is not True:
    fail("Runtime Memory requirement must be provider-neutral.")
required_memory_caps = {
    "memory.object.read","memory.object.write","memory.revision.read","memory.durability.prove","memory.resume.prove"
}
if set(memory_req.get("mandatoryCapabilities", [])) != required_memory_caps:
    fail("Runtime mandatory Memory capabilities mismatch.")
if memory_req.get("newLocationCreationRequiresExplicitHumanApproval") is not True:
    fail("New Memory location creation must require HUMAN approval.")
if memory_req.get("onNoEligibleMemory") != "STOP":
    fail("No eligible durable Memory must STOP.")

# No universal hard-coded repository requirement.
bundle_text = (ROOT / "SAFOR-MASTER-COMPLETE.json").read_text(encoding="utf-8")
if '"absoluteRuntimePrerequisite"' in bundle_text:
    fail("Legacy absolute repository prerequisite remains in bundle.")
if '"repositoryPattern": "{selectedOwner}/safor-memory"' in bundle_text:
    fail("SAFOR Memory must not be universally bound to {selectedOwner}/safor-memory.")

# Memory model semantics.
if memory_model.get("principles", {}).get("providerNeutral") is not True:
    fail("Memory model must be provider-neutral.")
if memory_model.get("principles", {}).get("noAuthoritativeStateOnlyInChat") is not True:
    fail("Memory model must forbid authoritative chat-only state.")
if memory_model.get("ownership", {}).get("physicalOwner") != "HUMAN_OR_ORGANIZATION":
    fail("Physical Memory ownership must be HUMAN_OR_ORGANIZATION.")
if memory_model.get("ownership", {}).get("logicalOwner") != "SAFOR_PROJECT":
    fail("Logical Memory owner must be SAFOR_PROJECT.")
if memory_model.get("resume", {}).get("chatHistoryRequired") is not False:
    fail("Resume must not require chat history.")
if memory_model.get("provenance", {}).get("perOutputRequired") is not True:
    fail("Per-output provenance must be required.")

# Initialization order and semantics.
expected_init = [
    "DISCOVER_MEMORY_PROVIDER_OPTIONS","SELECT_MEMORY_PROVIDER","VERIFY_MEMORY_PROVIDER",
    "SELECT_MEMORY_OWNER","SELECT_COLLABORATION_MODE","VERIFY_COLLABORATION_SAFETY",
    "BIND_AND_INITIALIZE_MEMORY_ROOT","SELECT_CREATION_TYPE","DISCOVER_AND_SELECT_WORK_PROVIDER",
    "VERIFY_WORK_PROVIDER","SELECT_OR_DEFINE_PROJECT","RESOLVE_AND_CONFIRM_PACKAGES",
    "MATERIALIZE_PROJECT_AND_REGISTER_SESSION"
]
actual_init = [x.get("operation") for x in init.get("sequence", [])]
if actual_init != expected_init:
    fail("Initialization sequence does not match v0.5 Memory-first order.")
if "GitHub or GitLab" in init.get("purpose", ""):
    fail("Initialization purpose remains product-coupled.")
if init.get("stateAuthority", {}).get("chatContext") != "NON_AUTHORITATIVE_CACHE":
    fail("Chat context must be NON_AUTHORITATIVE_CACHE.")

# MASTER invariants.
principles = master.get("kernelPrinciples", {})
for key in ("memoryProviderNeutral","memoryOwnedByHumanOrOrganization","noAuthoritativeStateOnlyInChat",
            "memoryAndWorkProviderIndependent","multiHumanMultiLlm","perOutputProvenance","multiWriterConflictSafe"):
    if principles.get(key) is not True:
        fail(f"Kernel principle missing/false: {key}")

invariants = {x.get("id"): x.get("rule","") for x in master.get("invariants", [])}
for inv in [f"INV-{i:03d}" for i in range(45,55)]:
    if inv not in invariants:
        fail(f"Missing v0.5 invariant {inv}.")

actions = {a.get("id"): a for a in master.get("controlPlane", {}).get("actions", [])}
if actions.get("K01", {}).get("operation") != "DISCOVER_MEMORY_PROVIDER_OPTIONS":
    fail("K01 must discover Memory provider options.")
if actions.get("K09", {}).get("operation") != "DISCOVER_AND_SELECT_WORK_PROVIDER":
    fail("K09 must select work provider independently.")
if actions.get("R01", {}).get("operation") != "LOAD_MEMORY_AND_REHYDRATE_PROJECT":
    fail("R01 must rehydrate from Memory.")
if actions.get("E04", {}).get("operation") != "PERSIST_OUTPUT_PROVENANCE_AND_COLLECT_EVIDENCE":
    fail("E04 must persist output provenance before evaluation.")

# Package system.
package_kinds = set(master.get("packageSystem", {}).get("requiredPackageKinds", []))
if "MEMORY_PROVIDER_ADAPTER" not in package_kinds:
    fail("MEMORY_PROVIDER_ADAPTER must be required.")
if "PROVIDER_ADAPTER" in package_kinds:
    fail("PROVIDER_ADAPTER must not be universally required; work provider is Factory-dependent.")

registry_packages = {p.get("packageId"): p for p in registry.get("packages", [])}
for pkg in (
    "safor.memory.versioned-repository","safor.memory.host-filesystem",
    "safor.provider.git-generic","safor.provider.plastic-scm"
):
    if pkg not in registry_packages:
        fail(f"Registry missing {pkg}.")

# Factory behavior.
software = load_json("v0.5.0/packages/factories/software-delivery/1.0.0/package.json")
book = load_json("v0.5.0/packages/factories/book-production/0.1.0/package.json")
for factory, creation_type, name in ((software,"SOFTWARE_WEBSITE","software"),(book,"BOOK","book")):
    model = factory.get("model", {})
    for contract in ("discoveryContract","planningContract","evidenceContract"):
        if model.get(contract, {}).get("creationType") != creation_type:
            fail(f"{name} {contract} creationType mismatch.")
    if model.get("outputProvenance", {}).get("required") is not True:
        fail(f"{name} Factory must require output provenance.")
if software.get("model", {}).get("workspaceRequirements", {}).get("required") is not True:
    fail("Software/Website must require versioned work provider.")
if book.get("model", {}).get("workspaceRequirements", {}).get("memoryOnlyAllowed") is not True:
    fail("Book must allow Memory-only mode.")

# Provenance/session/state schemas.
output_schema = load_json("v0.5.0/schemas/output-record.schema.json")
out_required = set(output_schema.get("required", []))
for field in ("producer","llm","safor","memoryRevision"):
    if field not in out_required:
        fail(f"Output provenance missing required field: {field}")
llm_required = set(output_schema.get("properties", {}).get("llm", {}).get("required", []))
for field in ("used","observability","provider","model","modelVersion"):
    if field not in llm_required:
        fail(f"Output LLM provenance missing required field: {field}")

session_schema = load_json("v0.5.0/schemas/session-record.schema.json")
for field in ("sessionId","actorId","host","llm","baseMemoryRevision"):
    if field not in set(session_schema.get("required", [])):
        fail(f"Session record missing required field: {field}")

project_schema = load_json("v0.5.0/schemas/project.schema.json")
project_required = set(project_schema.get("required", []))
if "memoryBindingRef" not in project_required or "workspaces" not in project_required:
    fail("Project schema must require memoryBindingRef and workspaces.")
if "controlRepository" in project_schema.get("properties", {}):
    fail("Project schema must not use legacy controlRepository.")

bindings_schema = load_json("v0.5.0/schemas/bindings.schema.json")
bindings_required = set(bindings_schema.get("required", []))
if "memoryProvider" not in bindings_required or "workProviderAdapters" not in bindings_required:
    fail("Bindings must separate memoryProvider and workProviderAdapters.")

evidence_schema = load_json("v0.5.0/schemas/evidence-record.schema.json")
if "provenanceRef" not in set(evidence_schema.get("required", [])):
    fail("Evidence records must require provenanceRef.")

execution_schema = load_json("v0.5.0/schemas/execution-state.schema.json")
exec_required = set(execution_schema.get("required", []))
if "sessions" not in exec_required or "outputRefs" not in exec_required:
    fail("Execution state must persist sessions and outputRefs.")

# Memory adapters.
versioned_mem = load_json("v0.5.0/memory-providers/versioned-repository/1.0.0/package.json")
fs_mem = load_json("v0.5.0/memory-providers/host-filesystem/0.1.0/package.json")
if versioned_mem.get("packageKind") != "MEMORY_PROVIDER_ADAPTER":
    fail("Versioned repository Memory package kind invalid.")
if fs_mem.get("packageKind") != "MEMORY_PROVIDER_ADAPTER":
    fail("Filesystem Memory package kind invalid.")
if "persistence" not in json.dumps(fs_mem.get("model", {}), ensure_ascii=False).lower():
    fail("Filesystem Memory adapter must explicitly address persistence.")

# Work adapters.
git_generic = load_json("v0.5.0/providers/git-generic/0.1.0/package.json")
plastic = load_json("v0.5.0/providers/plastic-scm/0.1.0/package.json")
if git_generic.get("packageId") != "safor.provider.git-generic":
    fail("Generic Git adapter missing.")
if plastic.get("packageId") != "safor.provider.plastic-scm":
    fail("Plastic adapter missing.")
if plastic.get("model", {}).get("runtimeBinding", {}).get("implementedByDefault") is not False:
    fail("Plastic adapter must not claim an implementation by default.")

# Conformance.
conf = load_json("v0.5.0/conformance.json")
assertions = {a.get("id"): a for a in conf.get("assertions", [])}
for cf in [f"CF-{i:03d}" for i in range(56,66)]:
    if assertions.get(cf, {}).get("expected") is not True:
        fail(f"Missing v0.5 conformance assertion {cf}.")

# Product-wide legacy SAF branding scan remains enforced.
legacy_upper = "SA" + "F"
legacy_lower = "sa" + "f"
legacy_patterns = (
    legacy_upper + "-", legacy_upper + "_", legacy_upper + " ", '"' + legacy_upper + '"',
    "urn:" + legacy_lower + ":", legacy_lower + ".", legacy_lower + "-", '"' + legacy_lower + '"',
)
text_extensions = {".json", ".md", ".py", ".yml", ".yaml", ".txt"}
skip_parts = {".git", "__pycache__"}
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
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in legacy_patterns:
        if pattern in content:
            fail(f"Legacy branding remains in file content: {rel} ({pattern})")

if errors:
    print("SAFOR validation: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("SAFOR validation: PASS")
print(f"- version: {version}")
print(f"- embedded modules: {len(modules)}")
print("- provider-neutral Memory: verified")
print("- Memory/work-provider independence: verified")
print("- multi-session/shared concurrency model: verified")
print("- per-output LLM/SAFOR provenance: verified")
print("- Factory-bound Discovery/Planning/Evidence: verified")
