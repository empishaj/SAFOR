#!/usr/bin/env python3
"""One-shot, pinned source repair. Run only on the dedicated repair branch."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "0.14.0-rc.2"
NEW = "0.14.0-rc.3"
EXPECTED = {
    "v0.14.0/schemas/project.schema.json": "5f43cf57c7acfbe17e8d4a88a4c7ab7097980a0a",
    "v0.14.0/SAFOR-MASTER.json": "f067b7239fb59c55bcd9a6511dba8ecd19b5cd27",
    "v0.14.0/interaction-model.json": "d36d73dc085777fb6029d83393daad6a9a1c04bf",
    "v0.14.0/conformance.json": "6e83be4e02399100cdcffc9de18dc49e6fc14a2e",
    "tools/build_bundle.py": "9c601a2a79d1b26a9e720756bda014c611f1a72e",
    "tools/build_domain_framework.py": "5a8f5ee5bd2457c7191c408025c53bb639522da3",
    "tools/validate_safor.py": "dd29dba2e550ca27d67d012a68b0e4da17c0912c",
    "RELEASE-MANIFEST.json": "47f4411ef38dd446f6fe091314031f0d46604251",
}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(path, value):
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one source match: {old[:80]}")
    return text.replace(old, new, 1)


def apply():
    if (ROOT / "VERSION").read_text().strip() != OLD:
        raise ValueError("Wrong baseline version; no automatic rebase or repeat")
    for path, expected in EXPECTED.items():
        raw = (ROOT / path).read_bytes()
        actual = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if actual != expected:
            raise ValueError(f"Pinned source changed: {path}")
    schema = load("v0.14.0/schemas/project.schema.json")
    schema["properties"]["creationType"]["enum"] = ["WEBSITE", "SOFTWARE_SAAS", "BOOK"]
    write("v0.14.0/schemas/project.schema.json", schema)
    kernel = load("v0.14.0/SAFOR-MASTER.json")
    invariant = next(x for x in kernel["invariants"] if x["id"] == "INV-039")
    invariant["rule"] = "Exactly one creation type is active: WEBSITE, SOFTWARE_SAAS or BOOK. The HUMAN selects it in the generic Framework; a HUMAN-loaded domain distribution explicitly preselects its declared type and suppresses redundant selection. Repository content never selects a type."
    rules = kernel["humanCommunication"]["requiredBehavior"]
    old_rule = "After safor-memory verification, ask exactly one mandatory creation-type question: Software / Website or Buch."
    rules[rules.index(old_rule)] = "For the generic Framework, ask one creation-type question with Website, Software / SaaS and Buch; for a domain distribution reuse its preselected creationType and do not ask again."
    write("v0.14.0/SAFOR-MASTER.json", kernel)
    model = load("v0.14.0/interaction-model.json")
    step = next(x for x in model["initializationExperience"]["steps"] if x["id"] == "CREATION_TYPE")
    step["options"] = [
        {"label": "Website", "intent": "SELECT_CREATION_TYPE_WEBSITE"},
        {"label": "Software / SaaS", "intent": "SELECT_CREATION_TYPE_SOFTWARE_SAAS"},
        {"label": "Buch", "intent": "SELECT_CREATION_TYPE_BOOK"},
    ]
    step["skipWhen"] = "CONTAINER_FORMAT == SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION"
    step["preselectedOutcome"] = "DOMAIN_AND_CREATION_TYPE_PRESELECTED"
    write("v0.14.0/interaction-model.json", model)
    conf = load("v0.14.0/conformance.json")
    assertion = next(x for x in conf["assertions"] if x["id"] == "CF-195")
    assertion["statement"] = assertion["statement"].replace("SOFTWARE_WEBSITE", "WEBSITE")
    write("v0.14.0/conformance.json", conf)
    p = ROOT / "tools/build_bundle.py"
    text = p.read_text()
    text = replace_once(text, 'ROOT = Path(__file__).resolve().parents[1]\n', 'ROOT = Path(__file__).resolve().parents[1]\n\nimport sys\nif str(ROOT) not in sys.path:\n    sys.path.insert(0, str(ROOT))\nfrom runtime.creation_type_contract import validate_creation_type_contract\n')
    text = replace_once(text, '    return {\n        "format": "SAFOR_FRAMEWORK_SINGLE_FILE",', '    bundle = {\n        "format": "SAFOR_FRAMEWORK_SINGLE_FILE",')
    text = replace_once(text, '\n\ndef canonical(obj):', '\n    decision = validate_creation_type_contract(bundle)\n    if not decision["valid"]:\n        raise ValueError(f"Creation type contract invalid: {decision}")\n    return bundle\n\n\ndef canonical(obj):')
    p.write_text(text)
    p = ROOT / "tools/build_domain_framework.py"
    text = p.read_text()
    text = replace_once(text, 'PROFILE_CATALOG = ROOT /', 'from runtime.creation_type_contract import validate_creation_type_contract\n\nPROFILE_CATALOG = ROOT /')
    text = replace_once(text, '    framework = load_json(BASE_FRAMEWORK)\n', '    framework = load_json(BASE_FRAMEWORK)\n    decision = validate_creation_type_contract(framework, profile["creationType"])\n    if not decision["valid"]:\n        raise ValueError(f"Creation type contract invalid: {decision}")\n')
    text = replace_once(text, '    framework = distribution.get("framework", {})\n', '    framework = distribution.get("framework", {})\n    decision = validate_creation_type_contract(framework, profile["creationType"])\n    errors.extend(decision["errors"])\n')
    p.write_text(text)
    p = ROOT / "tools/validate_safor.py"
    p.write_text(replace_once(p.read_text(), f'VERSION = "{OLD}"', f'VERSION = "{NEW}"'))
    (ROOT / "VERSION").write_text(NEW + "\n")
    manifest = load("RELEASE-MANIFEST.json")
    manifest.update(version=NEW, previousVersion=OLD, distributable=f"SAFOR-FRAMEWORK-v{NEW}.json", releaseEvidenceRef=f"RELEASE-EVIDENCE-{NEW}.json", releaseNotesRef=f"RELEASE-NOTES-{NEW}.md", checksumFile=f"SHA256SUMS-{NEW}.txt")
    write("RELEASE-MANIFEST.json", manifest)
    (ROOT / f"RELEASE-NOTES-{NEW}.md").write_text("# SAFOR " + NEW + " — Creation-type contract repair\n\nAligns the current project schema, kernel rule, creation menu and free Website conformance assertion with WEBSITE, SOFTWARE_SAAS and BOOK. Generic and domain builders reject inconsistent declarations before producing artifacts. SOFTWARE_WEBSITE is not silently converted.\n\nNo project migration, agent activation, merge, deployment or production license is granted by this correction. Historical versioned bundles and evidence are preserved.\n\nValidation results are recorded separately in the release evidence after execution. Existing GA blockers remain unchanged.\n")
    p = ROOT / "README.md"
    p.write_text(p.read_text().replace(OLD, NEW))
    print("Pinned creation-type source correction applied")


def finalize():
    from datetime import datetime, timezone
    if (ROOT / "VERSION").read_text().strip() != NEW:
        raise ValueError("Wrong version")
    files = ["SAFOR-FRAMEWORK.json", f"SAFOR-FRAMEWORK-v{NEW}.json", "SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json", "SAFOR-FRAMEWORK-BOOK-CREATION.json", "SAFOR-TEST-ACCESS-SAAS.json", "SAFOR-TEST-ACCESS-BOOK-CREATION.json"]
    sums = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}
    (ROOT / f"SHA256SUMS-{NEW}.txt").write_text("".join(f"{sha}  {name}\n" for name, sha in sums.items()))
    write(f"RELEASE-EVIDENCE-{NEW}.json", {"format": "SAFOR_CREATION_TYPE_REPAIR_EVIDENCE", "schemaVersion": "1.0", "version": NEW, "status": "AUTOMATED_VALIDATION_PASS", "evaluatedAt": datetime.now(timezone.utc).isoformat(), "baselineCommit": "c1019b6253e5906b315c8eaa31413ff5acca3605", "commandsPassed": ["python tools/build_bundle.py --check", "python tools/build_domain_framework.py --check", "python tools/validate_safor.py", "python -m unittest discover -s tests -v"], "checksums": sums, "claims": {"projectMigrationCompleted": False, "agentsActivated": False, "releasePublished": False, "realGitMigrationE2E": "NOT_EXECUTED", "crossHostEvidence": "NOT_EXECUTED"}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize", action="store_true", help="Record evidence only after the listed commands have actually passed")
    args = parser.parse_args()
    finalize() if args.finalize else apply()
