#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OLD_VERSION = "0.13.0-rc.8"
NEW_VERSION = "0.13.0-rc.9"
SAFOR_BASE_COMMIT = "086aae928e255bb099b94c507c405e8b82ad03ab"
MEMORY_MIGRATION_COMMIT = "85e08eab15b18a86868090d7b18573b9e2484aea"
PRODUCT_REPOSITORY_HEAD_AT_MIGRATION = "1026ff2176d739aeedc506e5970b48528aa8ad23"
CURRENT_STATE_BLOB = "8e0d00bb8e7f1aedf70043be761f6378eb924f81"
REGISTRY_BLOB = "466dcdb608cb22592d97a575b9687c8c513beb7f"
MIGRATION_AUDIT_BLOB = "bc18643d0c23d60094cd5c350bba68f0607d27a8"

CURRENT_VERSION_TEXT_FILES = [
    "README.md",
    "SECURITY.md",
    "START-HIER.md",
    "SUPPORT.md",
    "QUICKSTART.md",
    "RELEASE-CHECKLIST.md",
    "PRODUCT-READINESS.md",
    "LICENSE-DECISION.md",
    "ACCEPTANCE-TESTS.md",
    "HUMAN-NOTICE-CONFORMANCE.md",
    "tools/validate_safor.py",
]

DISTRIBUTABLES = [
    "SAFOR-FRAMEWORK.json",
    f"SAFOR-FRAMEWORK-v{NEW_VERSION}.json",
    "SAFOR-FRAMEWORK-WEBSITE.json",
    "SAFOR-FRAMEWORK-SAAS.json",
    "SAFOR-FRAMEWORK-BOOK-CREATION.json",
    "SAFOR-TEST-ACCESS-SAAS.json",
    "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
]


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: str, value: Any) -> None:
    (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def replace_text(path: str, old: str, new: str, *, require_old: bool = False) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if require_old and old not in text:
        raise RuntimeError(f"Expected text not found in {path}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if marker not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + content.strip() + "\n"
        target.write_text(text, encoding="utf-8")


def prepare() -> None:
    (ROOT / "VERSION").write_text(NEW_VERSION + "\n", encoding="utf-8")

    for path in CURRENT_VERSION_TEXT_FILES:
        replace_text(path, OLD_VERSION, NEW_VERSION, require_old=True)

    for test_file in sorted((ROOT / "tests").glob("test_*.py")):
        text = test_file.read_text(encoding="utf-8")
        if OLD_VERSION in text:
            test_file.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")

    # Correct a pre-existing onboarding mismatch: the SaaS Framework requires
    # the SaaS evaluation-access file, never the Book access file.
    replace_text(
        "START-HIER.md",
        "`SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-BOOK-CREATION.json`",
        "`SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-SAAS.json`",
    )

    manifest = load_json("RELEASE-MANIFEST.json")
    manifest["version"] = NEW_VERSION
    manifest["distributable"] = f"SAFOR-FRAMEWORK-v{NEW_VERSION}.json"
    manifest["previousVersion"] = OLD_VERSION
    manifest["releaseEvidenceRef"] = f"RELEASE-EVIDENCE-{NEW_VERSION}.json"
    manifest["releaseNotesRef"] = f"RELEASE-NOTES-{NEW_VERSION}.md"
    manifest["checksumFile"] = f"SHA256SUMS-{NEW_VERSION}.txt"

    additions = [
        "REFERENCE_PROJECT_RC8_MIGRATION_COMPLETED",
        "REFERENCE_PROJECT_CURRENT_STATE_POINTER",
        "COMPLETE_NINE_AGENT_REFERENCE_REGISTRY",
        "REFERENCE_PROJECT_MIGRATION_PROVIDER_READBACK",
        "VERSIONED_RELEASE_EVIDENCE",
        "DISTRIBUTION_SHA256_CHECKSUMS",
    ]
    features = manifest.setdefault("features", [])
    for feature in additions:
        if feature not in features:
            features.append(feature)

    manifest["gaBlockers"] = [
        blocker
        for blocker in manifest.get("gaBlockers", [])
        if blocker != "REFERENCE_PROJECT_RC8_MIGRATION_ACCEPTANCE"
    ]
    manifest["referenceProjectMigration"] = {
        "status": "COMPLETED",
        "projectId": "67454821-9325-41f3-ac41-d72121cfec5f",
        "projectSlug": "safomwebsite",
        "controlRepository": "empishaj/safor-memory",
        "mergeCommit": MEMORY_MIGRATION_COMMIT,
        "pullRequest": 4,
        "currentStateRef": "projects/safomwebsite/state/current.json",
        "currentStateBlobSha": CURRENT_STATE_BLOB,
        "agentRegistryRef": "projects/safomwebsite/agents/index.json",
        "agentRegistryBlobSha": REGISTRY_BLOB,
        "migrationAuditRef": "projects/safomwebsite/audit/rc8-migration-validation.json",
        "migrationAuditBlobSha": MIGRATION_AUDIT_BLOB,
        "agentCount": 9,
        "typedResponseTemplateCount": 5,
        "historicalArtifactsPreserved": True,
        "productRepository": "empishaj/safomwebsite",
        "productRepositoryHeadUnchangedAtMigration": PRODUCT_REPOSITORY_HEAD_AT_MIGRATION,
    }
    write_json("RELEASE-MANIFEST.json", manifest)

    conformance_path = ROOT / "HUMAN-NOTICE-CONFORMANCE.md"
    conformance = conformance_path.read_text(encoding="utf-8")
    old_section = (
        "## Reference-project migration\n\n"
        "The product release is complete only after `safomwebsite` receives a non-destructive rc.8 migration: current binding, complete agent registry, active identity overlays, response templates, MASTER status index and one authoritative current-state pointer. Historical jobs, AWC objects and evidence remain immutable read-only history."
    )
    new_section = (
        "## Reference-project migration\n\n"
        "The non-destructive `safomwebsite` migration is complete in `empishaj/safor-memory` at merge commit "
        f"`{MEMORY_MIGRATION_COMMIT}` (PR #4). The authoritative projection is "
        "`projects/safomwebsite/state/current.json`; the complete nine-agent registry, HUMAN-GO identity overlays, response-template binding and compact MASTER status index are present. Historical jobs, AWC objects, legacy identities and evidence remain read-only history.\n\n"
        "This closes the reference-project migration acceptance item for rc.9. It does not close cross-host, provider, commercial-delivery or General Availability acceptance items."
    )
    if old_section not in conformance:
        raise RuntimeError("Reference-project migration section changed unexpectedly")
    conformance_path.write_text(conformance.replace(old_section, new_section), encoding="utf-8")

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    section = f"""## {NEW_VERSION}

- Publishes a fresh generic SAFOR Framework and all three domain Framework distributions after the non-destructive `safomwebsite` reference migration completed.
- Adds a versioned release-evidence record, SHA-256 distribution checksums and dedicated release notes.
- Records the complete nine-agent reference registry, authoritative current-state pointer and provider-readback evidence without embedding project-specific state in the generic Framework.
- Removes `REFERENCE_PROJECT_RC8_MIGRATION_ACCEPTANCE` from the GA blocker list while retaining all unrelated cross-host, provider, commercial and governance blockers.
- Corrects the SaaS onboarding instruction to pair `SAFOR-FRAMEWORK-SAAS.json` with `SAFOR-TEST-ACCESS-SAAS.json`.
- Rebuilds and revalidates the generic, Website, SaaS-evaluation and Book-evaluation Framework files from canonical sources.

"""
    if f"## {NEW_VERSION}\n" not in changelog:
        if not changelog.startswith("# Changelog\n"):
            raise RuntimeError("Unexpected CHANGELOG heading")
        changelog = changelog.replace("# Changelog\n\n", "# Changelog\n\n" + section, 1)
        changelog_path.write_text(changelog, encoding="utf-8")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    evidence_bullet = f"- `RELEASE-EVIDENCE-{NEW_VERSION}.json` — versioned release, migration and validation evidence.\n"
    version_bullet = f"- `SAFOR-FRAMEWORK-v{NEW_VERSION}.json` — versioned generic Framework release candidate.\n"
    if evidence_bullet not in readme and version_bullet in readme:
        readme = readme.replace(version_bullet, version_bullet + evidence_bullet, 1)
        readme_path.write_text(readme, encoding="utf-8")

    append_once(
        "PRODUCT-READINESS.md",
        "## rc.9 reference-project evidence",
        f"""
## rc.9 reference-project evidence

The `safomwebsite` control plane migration is provider-verified at `empishaj/safor-memory@{MEMORY_MIGRATION_COMMIT}`. It contributes a complete nine-agent registry, HUMAN-GO-only identity overlays, personal inbox/response indexes, typed response bindings, a compact MASTER status index and an authoritative current-state pointer. The product repository remained unchanged during this control-plane migration.

This closes only the reference-project migration blocker. General Availability still depends on the remaining provider, cross-host, commercial-delivery, governance and end-to-end acceptance items in `RELEASE-MANIFEST.json`.
""",
    )

    append_once(
        "RELEASE-CHECKLIST.md",
        f"`RELEASE-EVIDENCE-{NEW_VERSION}.json`",
        f"""
## {NEW_VERSION} consolidation checks

- [x] `RELEASE-EVIDENCE-{NEW_VERSION}.json` binds the release to the verified reference-project migration.
- [x] `SHA256SUMS-{NEW_VERSION}.txt` covers every distributed Framework and evaluation-access artifact.
- [x] The prior versioned root Framework file is removed; its immutable history remains in Git.
- [x] The reference-project migration blocker is closed without claiming unrelated GA acceptance.
""",
    )

    release_notes = f"""# SAFOR {NEW_VERSION} Release Notes

## Purpose

This release candidate republishes the complete SAFOR Framework set after the `safomwebsite` reference control plane was migrated non-destructively to the HUMAN-GO agent contracts introduced in rc.8.

## User-facing files

- `SAFOR-FRAMEWORK-WEBSITE.json` — free public Website Framework.
- `SAFOR-FRAMEWORK-SAAS.json` plus `SAFOR-TEST-ACCESS-SAAS.json` — public SaaS evaluation path; not a commercial production license.
- `SAFOR-FRAMEWORK-BOOK-CREATION.json` plus `SAFOR-TEST-ACCESS-BOOK-CREATION.json` — public Book evaluation path; not a commercial production license.
- `SAFOR-FRAMEWORK-v{NEW_VERSION}.json` — generic engineering distribution.
- `SAFOR-FRAMEWORK.json` — byte-identical current generic alias.

## Evidence added in rc.9

- Reference migration merge: `empishaj/safor-memory@{MEMORY_MIGRATION_COMMIT}`.
- Reference migration PR: `empishaj/safor-memory#4`.
- Authoritative project pointer: `projects/safomwebsite/state/current.json`.
- Complete reference agent registry: nine agents with distinct display names and fail-closed `REBIND_REQUIRED` state until one-time chat binding.
- Migration audit: 16 checks passed, 45 materialized project paths, zero unexpected paths and zero deleted historical paths.
- Product repository head at migration remained `{PRODUCT_REPOSITORY_HEAD_AT_MIGRATION}`.

## Compatibility and limits

The schema and kernel baseline remain `0.13.0`. rc.9 does not turn public SaaS or Book evaluation bytes into commercial production packages. It also does not claim that JSON can create provider rights or force a non-conforming LLM host. Remaining GA blockers stay explicit in `RELEASE-MANIFEST.json`.

## Validation

The release is accepted only when bundle reproducibility, all domain distribution checks, `tools/validate_safor.py` and the complete unit/regression suite pass on the final branch head and again on `main` after merge.
"""
    (ROOT / f"RELEASE-NOTES-{NEW_VERSION}.md").write_text(release_notes, encoding="utf-8")

    evidence = {
        "format": "SAFOR_RELEASE_EVIDENCE",
        "schemaVersion": "1.0",
        "product": "SAFOR",
        "version": NEW_VERSION,
        "status": "MATERIALIZED_AND_AWAITING_BRANCH_CI",
        "createdAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "releaseBranch": os.environ.get("GITHUB_REF_NAME", "safor/framework-0.13.0-rc.9"),
        "materializationRun": {
            "repository": os.environ.get("GITHUB_REPOSITORY", "empishaj/SAFOR"),
            "runId": os.environ.get("GITHUB_RUN_ID"),
            "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        },
        "source": {
            "baseVersion": OLD_VERSION,
            "baseCommit": SAFOR_BASE_COMMIT,
            "sourceRoot": "v0.13.0",
        },
        "referenceProjectMigration": manifest["referenceProjectMigration"],
        "validationCommands": [
            "python tools/build_bundle.py --check",
            "python tools/build_domain_framework.py --check",
            "python tools/validate_safor.py",
            "python -m unittest discover -s tests -v",
        ],
        "artifacts": [],
        "truthBoundary": [
            "The Framework is declarative JSON and does not create provider permissions.",
            "Reference-project evidence proves the recorded repository state, not universal cross-host behavior.",
            "Public paid-domain evaluation bytes do not grant commercial production authorization.",
        ],
    }
    write_json(f"RELEASE-EVIDENCE-{NEW_VERSION}.json", evidence)

    test_content = f'''import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "{NEW_VERSION}"


class Rc9ReleaseTests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_version_and_manifest_are_aligned(self):
        self.assertEqual(VERSION, (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        manifest = self.load("RELEASE-MANIFEST.json")
        self.assertEqual(VERSION, manifest["version"])
        self.assertEqual(f"SAFOR-FRAMEWORK-v{{VERSION}}.json", manifest["distributable"])
        self.assertEqual("{OLD_VERSION}", manifest["previousVersion"])

    def test_reference_project_migration_is_closed_with_evidence(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        migration = manifest["referenceProjectMigration"]
        self.assertEqual("COMPLETED", migration["status"])
        self.assertEqual(9, migration["agentCount"])
        self.assertEqual(5, migration["typedResponseTemplateCount"])
        self.assertNotIn("REFERENCE_PROJECT_RC8_MIGRATION_ACCEPTANCE", manifest["gaBlockers"])

    def test_release_evidence_matches_manifest(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        evidence = self.load(manifest["releaseEvidenceRef"])
        self.assertEqual(VERSION, evidence["version"])
        self.assertEqual("{MEMORY_MIGRATION_COMMIT}", evidence["referenceProjectMigration"]["mergeCommit"])
        self.assertEqual("{MIGRATION_AUDIT_BLOB}", evidence["referenceProjectMigration"]["migrationAuditBlobSha"])

    def test_current_generic_alias_equals_versioned_file(self):
        alias = (ROOT / "SAFOR-FRAMEWORK.json").read_bytes()
        versioned = (ROOT / f"SAFOR-FRAMEWORK-v{{VERSION}}.json").read_bytes()
        self.assertEqual(alias, versioned)
        self.assertFalse((ROOT / "SAFOR-FRAMEWORK-v{OLD_VERSION}.json").exists())

    def test_checksum_file_covers_all_declared_artifacts(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        evidence = self.load(manifest["releaseEvidenceRef"])
        checksums = {{
            line.split("  ", 1)[1]: line.split("  ", 1)[0]
            for line in (ROOT / manifest["checksumFile"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        }}
        for artifact in evidence["artifacts"]:
            path = artifact["path"]
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            self.assertEqual(actual, artifact["sha256"])
            self.assertEqual(actual, checksums[path])

    def test_saas_onboarding_uses_matching_access_bundle(self):
        text = (ROOT / "START-HIER.md").read_text(encoding="utf-8")
        self.assertIn("`SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-SAAS.json`", text)
        self.assertNotIn("`SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-BOOK-CREATION.json`", text)

    def test_current_docs_use_rc9_and_plan_remains_historical(self):
        for path in ("README.md", "QUICKSTART.md", "PRODUCT-READINESS.md", "SUPPORT.md"):
            with self.subTest(path=path):
                self.assertIn(VERSION, (ROOT / path).read_text(encoding="utf-8"))
        plan = (ROOT / "HUMAN-NOTICE-IMPLEMENTATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("{OLD_VERSION}", plan)


if __name__ == "__main__":
    unittest.main()
'''
    (ROOT / "tests/test_rc9_release.py").write_text(test_content, encoding="utf-8")

    old_framework = ROOT / f"SAFOR-FRAMEWORK-v{OLD_VERSION}.json"
    if old_framework.exists():
        old_framework.unlink()


def finalize() -> None:
    generic_alias = (ROOT / "SAFOR-FRAMEWORK.json").read_bytes()
    generic_versioned = (ROOT / f"SAFOR-FRAMEWORK-v{NEW_VERSION}.json").read_bytes()
    if generic_alias != generic_versioned:
        raise RuntimeError("Generic Framework alias is not byte-identical to versioned artifact")

    artifacts = []
    checksum_lines = []
    for relative in DISTRIBUTABLES:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"Missing distributable: {relative}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        artifacts.append({"path": relative, "sha256": digest, "bytes": len(raw)})
        checksum_lines.append(f"{digest}  {relative}")

    checksum_path = ROOT / f"SHA256SUMS-{NEW_VERSION}.txt"
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    evidence_path = f"RELEASE-EVIDENCE-{NEW_VERSION}.json"
    evidence = load_json(evidence_path)
    evidence["status"] = "MATERIALIZED_AND_LOCALLY_VALIDATED"
    evidence["artifacts"] = artifacts
    evidence["artifactCount"] = len(artifacts)
    evidence["checksumFile"] = checksum_path.name
    evidence["materializedAt"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_json(evidence_path, evidence)

    manifest = load_json("RELEASE-MANIFEST.json")
    manifest["distributionArtifactCount"] = len(artifacts)
    write_json("RELEASE-MANIFEST.json", manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "finalize"])
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        finalize()
