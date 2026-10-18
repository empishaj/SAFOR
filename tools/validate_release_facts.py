#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    errors: list[str] = []
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    facts = load("RELEASE-FACTS.json")
    manifest = load("RELEASE-MANIFEST.json")
    trace = load("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
    profiles = load("v0.14.0/domain-framework-profiles.json")
    module_map = load("v0.14.0/bundle-module-map.json")
    recovery = load("v0.14.0/module-self-healing-model.json")
    readiness = (ROOT / "PRODUCT-READINESS.md").read_text(encoding="utf-8")

    if facts.get("format") != "SAFOR_RELEASE_FACTS":
        errors.append("release facts format mismatch")
    if facts.get("targetVersion") != version:
        errors.append("RELEASE-FACTS targetVersion differs from VERSION")
    if manifest.get("version") != version:
        errors.append("manifest version differs from VERSION")
    if trace.get("releaseTarget") != version:
        errors.append("traceability releaseTarget differs from VERSION")
    if f"Current target: **v{version}**" not in readiness:
        errors.append("PRODUCT-READINESS current target differs from VERSION")

    if manifest.get("releaseFactsRef") != "RELEASE-FACTS.json":
        errors.append("manifest does not bind canonical release facts")
    if manifest.get("previousVersion") != facts.get("previousVersion"):
        errors.append("previousVersion differs between manifest and release facts")

    artifacts = facts.get("releaseArtifacts", {})
    expected_refs = {
        "distributable": artifacts.get("distributable"),
        "releaseEvidenceRef": artifacts.get("evidence"),
        "releaseNotesRef": artifacts.get("notes"),
        "checksumFile": artifacts.get("checksums"),
    }
    for field, expected in expected_refs.items():
        if manifest.get(field) != expected:
            errors.append(f"manifest {field} differs from release facts")
    if artifacts.get("state") != "PENDING_WP_A7":
        errors.append("release facts artifact state must remain PENDING_WP_A7 before materialization")
    if manifest.get("releaseArtifactsState") != "PENDING_WP_A7_MATERIALIZATION":
        errors.append("manifest artifact state is not pending WP-A7")
    if "Materialization state: **PENDING WP-A7**" not in readiness:
        errors.append("PRODUCT-READINESS does not disclose pending rc.4 materialization")

    module_count = len(module_map.get("modulePaths", {}))
    recovery_count = len(recovery.get("moduleProfiles", []))
    if facts.get("moduleCount") != module_count:
        errors.append("release facts moduleCount mismatch")
    if facts.get("recoveryProfileCount") != recovery_count:
        errors.append("release facts recoveryProfileCount mismatch")
    if manifest.get("embeddedModuleCount") != module_count:
        errors.append("manifest embeddedModuleCount mismatch")
    if module_count != recovery_count:
        errors.append("module and recovery-profile counts differ")

    by_profile = {item["id"]: item for item in profiles.get("profiles", [])}
    facts_defaults = facts.get("domainDefaults", {})
    for profile_id, profile in by_profile.items():
        expected = {
            "creationType": profile["creationType"],
            "accessMode": profile["accessMode"],
            "factoryPackageId": profile["defaultFactory"]["packageId"],
            "factoryVersion": profile["defaultFactory"]["version"],
            "operatingModelPackageId": profile["defaultOperatingModel"]["packageId"],
            "operatingModelVersion": profile["defaultOperatingModel"]["version"],
            "publicationMode": profile["publicationMode"],
        }
        if facts_defaults.get(profile_id) != expected:
            errors.append(f"release facts domain default mismatch: {profile_id}")

    website = facts_defaults.get("WEBSITE", {})
    free_starter = manifest.get("freeStarterProfile", {})
    if free_starter.get("defaultFactoryVersion") != website.get("factoryVersion"):
        errors.append("manifest Website Factory default differs from release facts")
    if free_starter.get("defaultOperatingModelVersion") != website.get("operatingModelVersion"):
        errors.append("manifest Website Operating Model default differs from release facts")
    if "Website defaults family-aware at 1.2.0" not in readiness:
        errors.append("PRODUCT-READINESS lacks Website 1.2.0 default")
    if "Website defaults family-aware at 1.1.0" in readiness:
        errors.append("PRODUCT-READINESS still contains stale Website 1.1.0 default")

    migration = facts.get("referenceProjectMigration", {})
    historical = migration.get("historicalBaselineMigration", {})
    candidate = migration.get("candidateMigration", {})
    if historical.get("status") != "COMPLETED":
        errors.append("historical reference migration must remain COMPLETED")
    if candidate.get("targetVersion") != version:
        errors.append("candidate migration target differs from VERSION")
    if candidate.get("status") != "NOT_STARTED":
        errors.append("rc.4 candidate migration must remain NOT_STARTED before E2E")
    if "V014_ISOLATED_REAL_GIT_END_TO_END_ACCEPTANCE" not in candidate.get("prerequisites", []):
        errors.append("candidate migration lacks isolated real-Git E2E prerequisite")
    if manifest.get("referenceProjectMigration") != migration:
        errors.append("manifest reference migration differs from release facts")
    if "The rc.4 candidate migration is **NOT_STARTED**" not in readiness:
        errors.append("PRODUCT-READINESS does not distinguish current candidate migration")
    if "V014_REFERENCE_PROJECT_MIGRATION_ACCEPTANCE" not in manifest.get("gaBlockers", []):
        errors.append("current reference-project migration GA blocker was removed prematurely")

    requirements = trace.get("requirements", [])
    if len(requirements) != 33:
        errors.append("traceability must contain 33 requirements")
    pending_tests = sum(1 for item in requirements if item.get("coverage", {}).get("automatedTest") == "PENDING")
    pending_bundles = sum(1 for item in requirements if item.get("coverage", {}).get("bundle") == "PENDING")
    if pending_tests != 33:
        errors.append("all rc.4 requirement automated-test dimensions must be PENDING before WP-A7")
    if pending_bundles != 33:
        errors.append("all rc.4 requirement bundle dimensions must be PENDING before WP-A7")
    if any(item.get("coverage", {}).get("realGitE2E") != "NOT_VERIFIED" for item in requirements):
        errors.append("real-Git E2E must remain NOT_VERIFIED")
    if any(item.get("coverage", {}).get("crossHost") != "NOT_VERIFIED" for item in requirements):
        errors.append("cross-host must remain NOT_VERIFIED")

    summary = trace.get("summary", {})
    if summary.get("automatedTestPass") != 0 or summary.get("automatedTestPendingUntilCI") != 33:
        errors.append("traceability automated-test summary is inconsistent")
    if summary.get("bundlePass") != 0 or summary.get("bundlePendingUntilMaterialization") != 33:
        errors.append("traceability bundle summary is inconsistent")
    if summary.get("percentageClaimForbidden") is not True:
        errors.append("traceability must continue to forbid false percentage claims")

    if errors:
        print("SAFOR release facts validation: FAIL")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print(
        f"SAFOR release facts validation: PASS "
        f"({version}; {module_count}/{recovery_count} modules/recovery; "
        "rc.4 build evidence pending WP-A7)"
    )


if __name__ == "__main__":
    main()
