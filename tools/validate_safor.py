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
modular_master = load_json("v0.4.0/SAFOR-MASTER.json")
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

if bundle.get("format") != "SAF_MASTER_COMPLETE_SINGLE_FILE":
    fail("Complete bundle format is invalid.")

modules = bundle.get("embeddedModules", {})
required_modules = {
    "kernel","initialization","interaction","selfHealing","repositoryPolicy","packageRegistry",
    "providerGithub","providerGitlab","operatingModelSaas","operatingModelBook",
    "factorySoftwareWebsite","factoryBook","schemaPackageManifest","schemaControlState",
    "schemaValueStreamState","schemaExecutionState","schemaWorkItem","schemaProject",
    "schemaBindings","schemaDecisionRecord","schemaEvidenceRecord","schemaInteractionMenu",
    "schemaSelfHealingRecord","conformance"
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
for inv in ("INV-037","INV-038","INV-039","INV-040","INV-041","INV-042","INV-043","INV-044"):
    if inv not in invariants:
        fail(f"Missing required invariant {inv}.")

conformance = modules.get("conformance", {}).get("content", {})
assertions = {x.get("id"): x for x in conformance.get("assertions", [])}
for cf in ("CF-046","CF-047","CF-048","CF-049","CF-050","CF-051","CF-052","CF-053","CF-054","CF-055"):
    if assertions.get(cf, {}).get("expected") is not True:
        fail(f"Missing/passing conformance assertion {cf}.")

if manifest.get("version") != version:
    fail("RELEASE-MANIFEST.json version must match VERSION.")
if bundle.get("bundleVersion") != version:
    fail("Complete bundle version must match VERSION.")
if manifest.get("status") != "RELEASE_CANDIDATE":
    fail("v0.4.0-rc.1 must declare RELEASE_CANDIDATE status.")
if manifest.get("canonicalRepository") != "empishaj/SAFOR":
    fail("Release manifest canonical repository mismatch.")
if manifest.get("distributable") != "SAFOR-MASTER-COMPLETE.json":
    fail("Release manifest distributable mismatch.")

if modular_master.get("distribution", {}).get("canonicalSource", {}).get("repository") != "empishaj/SAFOR":
    fail("Modular master canonical repository mismatch.")

complete_text = (ROOT / "SAFOR-MASTER-COMPLETE.json").read_text(encoding="utf-8")
for forbidden in ("empishaj/SAFOR.", "empishaj/saf-memory", "{selectedOwner}/saf-memory"):
    if forbidden in complete_text:
        fail(f"Forbidden legacy reference remains in complete bundle: {forbidden}")

# Product-wide legacy branding scan.
legacy_token = "SAF" + "-"
text_extensions = {".json", ".md", ".py", ".yml", ".yaml", ".txt"}
skip_parts = {".git", "__pycache__"}
for path in ROOT.rglob("*"):
    if any(part in skip_parts for part in path.parts):
        continue
    rel = path.relative_to(ROOT)
    if legacy_token in str(rel):
        fail(f"Legacy branding remains in filename: {rel}")
    if not path.is_file() or path.suffix.lower() not in text_extensions:
        continue
    try:
        text_content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if legacy_token in text_content:
        fail(f"Legacy branding remains in file content: {rel}")

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
