"""Pure SAFOR 0.12 bootstrap policy reference implementation.

This module evaluates package-access and HUMAN-workspace boundary rules only.
It performs no provider I/O, filesystem I/O, purchases, entitlement issuance,
or organizational-authority changes.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

ALLOWED_ENTITLEMENT_VERIFIERS = {
    "AUTHORIZED_ENTITLEMENT_PROVIDER_READBACK",
    "VERIFIED_OFFLINE_SIGNATURE",
}

LOCAL_REQUIRED_CAPABILITIES = {
    "workspace.local.read",
    "workspace.local.write",
    "workspace.git.repository.read",
    "workspace.git.history.read",
    "workspace.git.branch.read",
    "workspace.git.branch.write",
    "workspace.git.commit.write",
}

REMOTE_REQUIRED_CAPABILITIES = {
    "workspace.project.read",
    "workspace.project.write",
    "workspace.git.history.read",
    "workspace.git.branch.read",
    "workspace.git.branch.write",
}


def _creation_profile(catalog: Mapping[str, Any], creation_type: str) -> Mapping[str, Any]:
    matches = [x for x in catalog.get("creationProfiles", []) if x.get("creationType") == creation_type]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one creation profile for {creation_type}, found {len(matches)}")
    return matches[0]


def _catalog_entry(catalog: Mapping[str, Any], package_id: str) -> Mapping[str, Any]:
    matches = [x for x in catalog.get("entries", []) if x.get("packageId") == package_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one catalog entry for {package_id}, found {len(matches)}")
    return matches[0]


def _loaded_package(loaded_packages: Sequence[Mapping[str, Any]], package_id: str) -> Optional[Mapping[str, Any]]:
    matches = [x for x in loaded_packages if x.get("packageId") == package_id]
    if len(matches) > 1:
        raise ValueError(f"Multiple loaded package candidates for {package_id}")
    return matches[0] if matches else None


def _version_grant_matches(version_range: str, version: str) -> bool:
    # rc.1 deliberately supports only exact version or wildcard grants.
    return version_range == "*" or version_range == version


def entitlement_covers(
    entitlement: Mapping[str, Any],
    package_id: str,
    version: str,
) -> bool:
    if entitlement.get("format") != "SAFOR_COMMERCIAL_ENTITLEMENT":
        return False
    if entitlement.get("schemaVersion") != "0.12.0":
        return False
    grant = entitlement.get("grant", {})
    if grant.get("packageId") != package_id:
        return False
    if not _version_grant_matches(str(grant.get("versionRange", "")), version):
        return False
    verification = entitlement.get("verification", {})
    if verification.get("method") not in ALLOWED_ENTITLEMENT_VERIFIERS:
        return False
    if not verification.get("verifierId") or not verification.get("evidenceRef") or not verification.get("verifiedAt"):
        return False
    issuer = entitlement.get("issuer", {})
    if not issuer.get("issuerId"):
        return False
    return True


def resolve_creation_packages(
    creation_type: str,
    catalog: Mapping[str, Any],
    loaded_packages: Sequence[Mapping[str, Any]],
    entitlements: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    profile = _creation_profile(catalog, creation_type)
    required_ids = [profile["factoryPackageId"], profile["operatingModelPackageId"]]
    access_mode = profile["accessMode"]
    resolutions: List[Dict[str, Any]] = []

    for package_id in required_ids:
        entry = _catalog_entry(catalog, package_id)
        if entry.get("accessMode") != access_mode:
            return {"outcome": "CATALOG_ACCESS_MODE_MISMATCH", "packages": []}

        loaded = _loaded_package(loaded_packages, package_id)

        if access_mode == "FREE_PUBLIC":
            if loaded is not None:
                source_class = loaded.get("sourceClass")
                if source_class not in {"HUMAN_LOADED_PACKAGE", "PUBLIC_CANONICAL_REPOSITORY"}:
                    return {"outcome": "INVALID_FREE_PACKAGE_SOURCE", "packages": []}
                resolutions.append({
                    "packageId": package_id,
                    "mode": "USE_LOADED_PACKAGE",
                    "sourceClass": source_class,
                    "version": loaded.get("version"),
                })
            else:
                distribution = entry.get("distribution", {})
                if distribution.get("sourceClass") != "PUBLIC_CANONICAL_REPOSITORY" or not distribution.get("path"):
                    return {"outcome": "FREE_PUBLIC_SOURCE_INVALID", "packages": []}
                resolutions.append({
                    "packageId": package_id,
                    "mode": "RESOLVE_PUBLIC_FREE",
                    "sourceClass": "PUBLIC_CANONICAL_REPOSITORY",
                    "path": distribution["path"],
                    "requiresImmutableReadback": True,
                })
            continue

        if access_mode == "PAID_ENTITLEMENT_REQUIRED":
            if loaded is None:
                return {"outcome": "PACKAGE_ACCESS_REQUIRED", "missingPackageId": package_id, "packages": []}
            if loaded.get("sourceClass") not in {"HUMAN_LOADED_PACKAGE", "ENTITLED_PACKAGE_SOURCE"}:
                return {"outcome": "PAID_PUBLIC_RESOLUTION_FORBIDDEN", "packageId": package_id, "packages": []}
            version = str(loaded.get("version", ""))
            if not version:
                return {"outcome": "PACKAGE_VERSION_MISSING", "packageId": package_id, "packages": []}
            matching = [e for e in entitlements if entitlement_covers(e, package_id, version)]
            if len(matching) != 1:
                return {"outcome": "PACKAGE_ENTITLEMENT_UNVERIFIED", "packageId": package_id, "packages": []}
            resolutions.append({
                "packageId": package_id,
                "mode": "USE_ENTITLED_PACKAGE",
                "sourceClass": loaded["sourceClass"],
                "version": version,
                "entitlementId": matching[0].get("entitlementId"),
            })
            continue

        return {"outcome": "UNKNOWN_ACCESS_MODE", "packages": []}

    return {
        "outcome": "PACKAGE_ACCESS_RESOLVED",
        "creationType": creation_type,
        "accessMode": access_mode,
        "packages": resolutions,
    }


def factory_operating_model_compatible(
    factory_manifest: Mapping[str, Any],
    operating_model_manifest: Mapping[str, Any],
) -> Dict[str, Any]:
    factory_exports = factory_manifest.get("exports", {})
    om_exports = operating_model_manifest.get("exports", {})
    required_capabilities = set(factory_exports.get("capabilities", []))
    available_capabilities = set(om_exports.get("capabilities", []))
    required_authorities = set(factory_exports.get("authorities", []))
    available_authorities = set(om_exports.get("authorities", []))
    missing_capabilities = sorted(required_capabilities - available_capabilities)
    missing_authorities = sorted(required_authorities - available_authorities)
    return {
        "compatible": not missing_capabilities and not missing_authorities,
        "missingCapabilities": missing_capabilities,
        "missingAuthorities": missing_authorities,
    }


def validate_workspace_binding(
    binding: Mapping[str, Any],
    actual_capabilities: Iterable[str],
    canonical_framework_repository: str,
    package_source_repositories: Iterable[str] = (),
) -> Dict[str, Any]:
    errors: List[str] = []
    caps: Set[str] = set(actual_capabilities)
    ownership = binding.get("ownership", {})
    if ownership.get("humanControlled") is not True:
        errors.append("WORKSPACE_NOT_HUMAN_CONTROLLED")

    project = binding.get("projectWorkspace", {})
    control = binding.get("controlWorkspace", {})
    workspace_type = project.get("type")
    forbidden_repos = {canonical_framework_repository, *package_source_repositories}

    if workspace_type == "REMOTE_GIT":
        missing = sorted(REMOTE_REQUIRED_CAPABILITIES - caps)
        if missing:
            errors.append("REMOTE_CAPABILITIES_MISSING:" + ",".join(missing))
        repository = project.get("repository")
        if repository in forbidden_repos:
            errors.append("PROJECT_TARGET_IS_PRODUCT_OR_PACKAGE_SOURCE")
        if control.get("strategy") != "REMOTE_SEPARATE_SAFOR_MEMORY":
            errors.append("REMOTE_CONTROL_STRATEGY_INVALID")
        control_repo = control.get("repository")
        if not control_repo or not str(control_repo).endswith("/safor-memory"):
            errors.append("REMOTE_SAFOR_MEMORY_INVALID")
        if control_repo == repository:
            errors.append("CONTROL_REPOSITORY_EQUALS_PROJECT_REPOSITORY")

    elif workspace_type == "LOCAL_GIT":
        missing = sorted(LOCAL_REQUIRED_CAPABILITIES - caps)
        if missing:
            errors.append("LOCAL_GIT_CAPABILITIES_MISSING:" + ",".join(missing))
        if not project.get("path") or not project.get("gitRoot"):
            errors.append("LOCAL_GIT_PATH_INVALID")
        if control.get("strategy") != "LOCAL_MASTER_CONTROL_ROOT":
            errors.append("LOCAL_CONTROL_STRATEGY_INVALID")
        if control.get("root") != ".safor/" or control.get("masterOnly") is not True or control.get("gitTracked") is not True:
            errors.append("LOCAL_CONTROL_ROOT_INVALID")
    else:
        errors.append("UNKNOWN_PROJECT_WORKSPACE_TYPE")

    return {"valid": not errors, "errors": errors}
