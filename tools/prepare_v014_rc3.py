#!/usr/bin/env python3
"""Explicit, bounded rc.2 -> rc.3 source correction; never migrates a project.

Run only on a dedicated review branch. This release-preparation utility refuses
unexpected input bytes and retains every historical/versioned artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OLD = "0.14.0-rc.2"
NEW = "0.14.0-rc.3"
BASE = "c1019b6253e5906b315c8eaa31413ff5acca3605"
PINS = {
    "v0.14.0/schemas/project.schema.json": "5f43cf57c7acfbe17e8d4a88a4c7ab7097980a0a",
    "v0.14.0/SAFOR-MASTER.json": "f067b7239fb59c55bcd9a6511dba8ecd19b5cd27",
    "v0.14.0/interaction-model.json": "d36d73dc085777fb6029d83393daad6a9a1c04bf",
    "v0.14.0/conformance.json": "6e83be4e02399100cdcffc9de18dc49e6fc14a2e",
    "tools/build_bundle.py": "9c601a2a79d1b26a9e720756bda014c611f1a72e",
    "tools/build_domain_framework.py": "5a8f5ee5bd2457c7191c408025c53bb639522da3",
    "tools/validate_safor.py": "dd29dba2e550ca27d67d012a68b0e4da17c0912c",
}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(path, value):
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one source anchor: {old[:90]!r}")
    return text.replace(old, new, 1)


def apply():
    if (ROOT / "VERSION").read_text().strip() != OLD:
        raise ValueError("Apply requires the unmodified rc.2 version; never silently reapply.")
    for name, expected in PINS.items():
        raw = (ROOT / name).read_bytes()
        actual = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if actual != expected:
            raise ValueError(f"Unexpected source bytes: {name}: {actual} != {expected}")

    schema = load("v0.14.0/schemas/project.schema.json")
    schema["properties"]["creationType"]["enum"] = ["WEBSITE", "SOFTWARE_SAAS", "BOOK"]
    write("v0.14.0/schemas/project.schema.json", schema)

    kernel = load("v0.14.0/SAFOR-MASTER.json")
    rules = {x["id"]: x for x in kernel["invariants"]}
    rules["INV-039"]["rule"] = (
        "Exactly one active creation type is required: WEBSITE, SOFTWARE_SAAS or BOOK. "
        "A generic Framework requires explicit HUMAN selection; a domain distribution "
        "supplies its declared type without a redundant question. Repository contents "
        "never select the creation type."
    )
    rules["INV-040"]["rule"] = (
        "Creation type fixes the domain and default Factory/Operating Model candidates, "
        "not a non-replaceable pair. Each selected package remains independently "
        "replaceable through explicit HUMAN selection, verified access/integrity and "
        "same-domain bidirectional compatibility."
    )
    old_rule = "After safor-memory verification, ask exactly one mandatory creation-type question: Software / Website or Buch."
    behaviors = kernel["humanCommunication"]["requiredBehavior"]
    if behaviors.count(old_rule) != 1:
        raise ValueError("Legacy creation-type communication anchor changed.")
    behaviors[behaviors.index(old_rule)] = (
        "For a generic Framework, ask one creation-type question with Website, Software / "
        "SaaS and Buch. For a domain distribution, reuse its declared type without asking again."
    )
    write("v0.14.0/SAFOR-MASTER.json", kernel)

    interaction = load("v0.14.0/interaction-model.json")
    step = next(s for s in interaction["initializationExperience"]["steps"]
                if s["id"] == "CREATION_TYPE")
    step["options"] = [
        {"label": "Website", "intent": "SELECT_CREATION_TYPE_WEBSITE"},
        {"label": "Software / SaaS", "intent": "SELECT_CREATION_TYPE_SOFTWARE_SAAS"},
        {"label": "Buch", "intent": "SELECT_CREATION_TYPE_BOOK"},
    ]
    step["skipWhen"] = "CONTAINER_FORMAT == SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION"
    step["preselectedOutcome"] = "DOMAIN_AND_CREATION_TYPE_PRESELECTED"
    write("v0.14.0/interaction-model.json", interaction)

    conformance = load("v0.14.0/conformance.json")
    assertion = next(a for a in conformance["assertions"] if a["id"] == "CF-195")
    assertion["statement"] = replace_once(assertion["statement"], "SOFTWARE_WEBSITE", "WEBSITE")
    write("v0.14.0/conformance.json", conformance)

    path = ROOT / "tools/build_bundle.py"
    text = path.read_text()
    text = replace_once(text, "ROOT = Path(__file__).resolve().parents[1]\n",
        "ROOT = Path(__file__).resolve().parents[1]\n\nimport sys\n"
        "if str(ROOT) not in sys.path:\n    sys.path.insert(0, str(ROOT))\n\n"
        "from runtime.creation_type_contract import validate_creation_type_contract\n")
    text = replace_once(text,
        '    return {\n        "format": "SAFOR_FRAMEWORK_SINGLE_FILE",',
        '    bundle = {\n        "format": "SAFOR_FRAMEWORK_SINGLE_FILE",')
    text = replace_once(text, '\n\ndef canonical(obj):',
        '\n    decision = validate_creation_type_contract(bundle)\n'
        '    if not decision["valid"]:\n'
        '        raise ValueError(f"Creation-type contract invalid: {decision[\'errors\']}")\n'
        '    return bundle\n\n\ndef canonical(obj):')
    path.write_text(text)

    path = ROOT / "tools/build_domain_framework.py"
    text = path.read_text()
    text = replace_once(text, 'PROFILE_CATALOG = ROOT /',
        'from runtime.creation_type_contract import validate_creation_type_contract\n\n'
        'PROFILE_CATALOG = ROOT /')
    text = replace_once(text, '    framework = load_json(BASE_FRAMEWORK)\n',
        '    framework = load_json(BASE_FRAMEWORK)\n'
        '    type_decision = validate_creation_type_contract(framework, profile["creationType"])\n'
        '    if not type_decision["valid"]:\n'
        '        raise ValueError(f"Creation-type contract invalid: {type_decision[\'errors\']}")\n')
    text = replace_once(text, '    framework = distribution.get("framework", {})\n',
        '    framework = distribution.get("framework", {})\n'
        '    type_decision = validate_creation_type_contract(framework, profile["creationType"])\n'
        '    errors.extend(type_decision["errors"])\n')
    path.write_text(text)

    path = ROOT / "tools/validate_safor.py"
    text = path.read_text()
    text = replace_once(text, f'VERSION = "{OLD}"', f'VERSION = "{NEW}"')
    text = replace_once(text, 'from runtime.public_evaluation_access import',
        'from runtime.creation_type_contract import validate_creation_type_contract\n'
        'from runtime.public_evaluation_access import')
    text = replace_once(text, 'framework = load("SAFOR-FRAMEWORK.json")\n',
        'framework = load("SAFOR-FRAMEWORK.json")\n'
        'creation_type_decision = validate_creation_type_contract(framework)\n'
        'if not creation_type_decision["valid"]:\n'
        '    fail(f"Creation-type contract invalid: {creation_type_decision[\'errors\']}")\n')
    path.write_text(text)

    (ROOT / "VERSION").write_text(NEW + "\n")
    manifest = load("RELEASE-MANIFEST.json")
    manifest.update(version=NEW, previousVersion=OLD,
                    distributable=f"SAFOR-FRAMEWORK-v{NEW}.json",
                    releaseEvidenceRef=f"RELEASE-EVIDENCE-{NEW}.json",
                    releaseNotesRef=f"RELEASE-NOTES-{NEW}.md",
                    checksumFile=f"SHA256SUMS-{NEW}.txt")
    manifest["features"].append("CREATION_TYPE_CONTRACT_BUILD_GUARD_AND_REGRESSION_TESTS")
    write("RELEASE-MANIFEST.json", manifest)
    readme = ROOT / "README.md"
    readme.write_text(readme.read_text().replace(OLD, NEW))
    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text()
    title, rest = text.split("\n", 1)
    entry = (
        f"\n## {NEW} — Creation-type contract correction\n\n"
        "- Aligns the active project schema, kernel selection rules, interaction choices "
        "and free-Website conformance statement with WEBSITE, SOFTWARE_SAAS and BOOK.\n"
        "- Rejects the ambiguous legacy SOFTWARE_WEBSITE value for new active 0.14 descriptors; "
        "historical schemas and artifacts remain unchanged.\n"
        "- Fails bundle/domain builds and validation when schema, initialization, runtime "
        "profiles and catalog types disagree. Adds 15 regression tests.\n"
        "- Rebuilds all three domain distributions, the generic/versioned Framework and "
        "integrity evidence. Does not migrate a project or authorize publishing.\n"
    )
    changelog.write_text(title + "\n" + entry + rest)
    (ROOT / f"RELEASE-NOTES-{NEW}.md").write_text(
        f"# SAFOR {NEW}\n\n"
        "## Corrected contract\n\n"
        "The project descriptor now accepts exactly WEBSITE, SOFTWARE_SAAS and BOOK. "
        "The old SOFTWARE_WEBSITE enum could not satisfy the Website/SaaS package contracts. "
        "Active selection rules and the derived menu use the same vocabulary; domain "
        "distributions continue to suppress redundant creation-type questions.\n\n"
        "## Regression protection and integrity\n\n"
        "A pure type-contract validator is called by both builders and the distribution "
        "validator. The regression suite checks all domains, legacy/unknown values, missing "
        "or duplicate records, source/embedded schema agreement, source blob identities "
        "and distribution digests. A deliberately reintroduced schema conflict is rejected "
        "even after recomputing the distribution digest.\n\n"
        "## Migration boundary\n\n"
        "Historical versioned bundles and pre-0.14 sources remain unchanged. This candidate "
        "does not rewrite existing projects, select a domain for ambiguous legacy records, "
        "activate agents or authorize deployment. An existing project still needs its "
        "explicit, non-destructive migration and provider readback. Existing GA blockers "
        "and commercial entitlement policies remain in force.\n"
    )
    print("Applied bounded creation-type correction; rebuild and verification still required.")


def evidence(log_directory):
    directory = Path(log_directory)
    logs = {name: (directory / f"{name}.log").read_text()
            for name in ("baseline", "bundle", "domains", "validate", "tests")}
    match = re.search(r"Ran (\d+) tests", logs["tests"])
    if not match or not re.search(r"^OK\s*$", logs["tests"], re.MULTILINE):
        raise ValueError("Full unittest PASS evidence missing.")
    for name, marker in (("bundle", "SAFOR Framework reproducibility: PASS"),
                         ("domains", "SAFOR domain distribution reproducibility: PASS"),
                         ("validate", "SAFOR validation: PASS")):
        if marker not in logs[name]:
            raise ValueError(f"Missing successful verification: {name}")
    if "FAILED" not in logs["baseline"]:
        raise ValueError("Expected pre-fix regression failure evidence missing.")
    artifacts = ["SAFOR-FRAMEWORK.json", f"SAFOR-FRAMEWORK-v{NEW}.json",
                 "SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json",
                 "SAFOR-FRAMEWORK-BOOK-CREATION.json", "SAFOR-TEST-ACCESS-SAAS.json",
                 "SAFOR-TEST-ACCESS-BOOK-CREATION.json"]
    sums = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in artifacts}
    (ROOT / f"SHA256SUMS-{NEW}.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sums.items()))
    write(f"RELEASE-EVIDENCE-{NEW}.json", {
        "format": "SAFOR_RELEASE_EVIDENCE", "schemaVersion": "1.0", "version": NEW,
        "status": "VERIFIED_CANDIDATE_NOT_MERGED", "sourceBaselineCommit": BASE,
        "evaluatedAt": datetime.now(timezone.utc).isoformat(),
        "executionEnvironment": "GITHUB_ACTIONS",
        "runRef": f"https://github.com/empishaj/SAFOR/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
        "recipeCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "automatedTests": {"result": "PASS", "testsRun": int(match.group(1)),
                           "newRegressionTests": 15, "preFixRegression": "EXPECTED_FAIL"},
        "bundleReproducibility": "PASS", "domainReproducibility": "PASS",
        "distributionValidation": "PASS", "artifactSha256": sums,
        "logSha256": {name: hashlib.sha256(content.encode()).hexdigest()
                      for name, content in logs.items()},
        "projectMigration": "NOT_PERFORMED", "agentsActivated": False,
        "productionDeployment": "NOT_PERFORMED", "independentReview": "NOT_CLAIMED",
        "realGitProjectE2E": "NOT_PERFORMED", "crossHostEvidence": "NOT_PERFORMED",
        "historicalArtifacts": "PRESERVED_BY_ADDITIVE_VERSIONED_OUTPUTS",
        "scope": "Creation-type contract correction and distribution regeneration only."
    })
    print(f"Wrote verified release-candidate evidence: {match.group(1)} tests and seven artifact checksums.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--evidence", metavar="LOG_DIRECTORY")
    args = parser.parse_args()
    if args.apply:
        apply()
    else:
        evidence(args.evidence)
