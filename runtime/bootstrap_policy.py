"""Pure SAFOR 0.12/0.13 bootstrap policy reference implementation.

This module evaluates package-access and HUMAN-workspace boundary rules only.
It performs no provider I/O, filesystem I/O, purchases, entitlement issuance,
or organizational-authority changes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

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
    if entitlement.get("schemaVersion") not in {"0.12.0", "0.13.0"}:
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


DOMAIN_CONTRACT_FIELDS_V1 = (
    "packageId",
    "packageKind",
    "version",
    "commercial",
    "compatibility",
    "exports",
    "dependencies",
    "model",
)

DOMAIN_CONTRACT_FIELDS_V2 = (
    "packageId",
    "packageFamily",
    "packageKind",
    "version",
    "commercial",
    "compatibility",
    "exports",
    "dependencies",
    "model",
)


def _semver_core(version: str) -> tuple[int, int, int]:
    core = str(version).split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Unsupported semantic version: {version}")
    return tuple(int(part) for part in parts)


def canonical_domain_contract(package: Mapping[str, Any]) -> str:
    canonicalization = package.get("integrity", {}).get(
        "canonicalization", "SAFOR_CANONICAL_JSON_V1"
    )
    fields = (
        DOMAIN_CONTRACT_FIELDS_V2
        if canonicalization == "SAFOR_CANONICAL_JSON_V2"
        else DOMAIN_CONTRACT_FIELDS_V1
    )
    projection = {field: package.get(field) for field in fields}
    return json.dumps(
        projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_domain_package_digest(package: Mapping[str, Any]) -> str:
    payload = canonical_domain_contract(package).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate_domain_package(
    package: Mapping[str, Any],
    framework_version: str,
    creation_type: str,
) -> Dict[str, Any]:
    errors: List[str] = []
    package_id = str(package.get("packageId", ""))
    package_kind = package.get("packageKind")

    if package.get("format") != "SAFOR_DOMAIN_PACKAGE":
        errors.append("DOMAIN_PACKAGE_FORMAT_INVALID")
    if package.get("schemaVersion") != "0.13.0":
        errors.append("DOMAIN_PACKAGE_SCHEMA_VERSION_INVALID")
    if package_kind not in {"FACTORY", "OPERATING_MODEL"}:
        errors.append("DOMAIN_PACKAGE_KIND_INVALID")
    if package_kind == "FACTORY" and not package_id.startswith("safor.factory."):
        errors.append("DOMAIN_PACKAGE_ID_KIND_MISMATCH")
    if package_kind == "OPERATING_MODEL" and not package_id.startswith("safor.om."):
        errors.append("DOMAIN_PACKAGE_ID_KIND_MISMATCH")

    commercial = package.get("commercial", {})
    access_mode = commercial.get("accessMode")
    if access_mode == "FREE_PUBLIC":
        if commercial.get("entitlementRequired") is not False:
            errors.append("FREE_PACKAGE_ENTITLEMENT_FLAG_INVALID")
    elif access_mode == "PAID_ENTITLEMENT_REQUIRED":
        if commercial.get("entitlementRequired") is not True:
            errors.append("PAID_PACKAGE_ENTITLEMENT_FLAG_INVALID")
    else:
        errors.append("DOMAIN_PACKAGE_ACCESS_MODE_INVALID")
    if commercial.get("entitlementEvidenceMode") != "EXTERNAL_ONLY":
        errors.append("DOMAIN_PACKAGE_ENTITLEMENT_MUST_BE_EXTERNAL")

    integrity = package.get("integrity", {})
    if integrity.get("canonicalization") not in {
        "SAFOR_CANONICAL_JSON_V1",
        "SAFOR_CANONICAL_JSON_V2",
    }:
        errors.append("DOMAIN_PACKAGE_CANONICALIZATION_INVALID")
    if integrity.get("digestAlgorithm") != "SHA-256":
        errors.append("DOMAIN_PACKAGE_DIGEST_ALGORITHM_INVALID")
    if integrity.get("digestScope") != "DECLARED_DOMAIN_CONTRACT":
        errors.append("DOMAIN_PACKAGE_DIGEST_SCOPE_INVALID")
    expected_digest = compute_domain_package_digest(package)
    if integrity.get("contentDigest") != expected_digest:
        errors.append("DOMAIN_PACKAGE_INTEGRITY_MISMATCH")
    verification_mode = integrity.get("verificationMode")
    if verification_mode not in {
        "CANONICAL_REPOSITORY_READBACK",
        "TRUSTED_PACKAGE_SOURCE_READBACK",
        "SIGNED_ARTIFACT",
    }:
        errors.append("DOMAIN_PACKAGE_VERIFICATION_MODE_INVALID")
    if verification_mode == "SIGNED_ARTIFACT" and not integrity.get("signature"):
        errors.append("DOMAIN_PACKAGE_SIGNATURE_MISSING")

    compatibility = package.get("compatibility", {})
    supported = compatibility.get("supportedCreationTypes", [])
    if creation_type not in supported:
        errors.append("DOMAIN_PACKAGE_CREATION_TYPE_UNSUPPORTED")
    framework = compatibility.get("framework", {})
    try:
        actual = _semver_core(framework_version)
        minimum = _semver_core(framework.get("minimum", ""))
        maximum_exclusive = _semver_core(framework.get("maximumExclusive", ""))
        if not (minimum <= actual < maximum_exclusive):
            errors.append("DOMAIN_PACKAGE_FRAMEWORK_INCOMPATIBLE")
    except ValueError:
        errors.append("DOMAIN_PACKAGE_FRAMEWORK_RANGE_INVALID")

    return {
        "valid": not errors,
        "errors": errors,
        "contentDigest": expected_digest,
    }



def _evaluate_counterpart_contract(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> Dict[str, Any]:
    counterpart = source.get("compatibility", {}).get("counterpart", {})
    target_exports = target.get("exports", {})
    missing_capabilities = sorted(
        set(counterpart.get("requiredCapabilities", []))
        - set(target_exports.get("capabilities", []))
    )
    missing_authorities = sorted(
        set(counterpart.get("requiredAuthorities", []))
        - set(target_exports.get("authorities", []))
    )
    missing_work_item_types = sorted(
        set(counterpart.get("requiredWorkItemTypes", []))
        - set(target_exports.get("workItemTypes", []))
    )
    missing_artifact_types = sorted(
        set(counterpart.get("requiredArtifactTypes", []))
        - set(target_exports.get("artifactTypes", []))
    )
    allowed_ids = set(counterpart.get("allowedPackageIds", []))
    allowed_families = set(counterpart.get("allowedPackageFamilies", []))
    id_allowed = not allowed_ids or target.get("packageId") in allowed_ids
    family_allowed = (
        not allowed_families
        or target.get("packageFamily") in allowed_families
    )
    kind_allowed = (
        not counterpart.get("requiredKind")
        or target.get("packageKind") == counterpart.get("requiredKind")
    )
    return {
        "compatible": (
            kind_allowed
            and id_allowed
            and family_allowed
            and not missing_capabilities
            and not missing_authorities
            and not missing_work_item_types
            and not missing_artifact_types
        ),
        "kindAllowed": kind_allowed,
        "idAllowed": id_allowed,
        "familyAllowed": family_allowed,
        "missingCapabilities": missing_capabilities,
        "missingAuthorities": missing_authorities,
        "missingWorkItemTypes": missing_work_item_types,
        "missingArtifactTypes": missing_artifact_types,
    }


def evaluate_domain_framework_pair(
    factory: Mapping[str, Any],
    operating_model: Mapping[str, Any],
    framework_version: str,
    creation_type: str,
    domain_id: str,
) -> Dict[str, Any]:
    """Strict compatibility for domain-specific SAFOR Framework distributions."""
    base = evaluate_domain_package_pair(
        factory, operating_model, framework_version, creation_type
    )
    factory_domains = set(factory.get("compatibility", {}).get("domainIds", []))
    om_domains = set(operating_model.get("compatibility", {}).get("domainIds", []))
    family_presence = bool(factory.get("packageFamily")) and bool(
        operating_model.get("packageFamily")
    )
    domain_match = domain_id in factory_domains and domain_id in om_domains

    errors = []
    if not family_presence:
        errors.append("DOMAIN_PACKAGE_FAMILY_REQUIRED")
    if not domain_match:
        errors.append("DOMAIN_FRAMEWORK_DOMAIN_MISMATCH")

    return {
        **base,
        "compatible": base["compatible"] and family_presence and domain_match,
        "domainId": domain_id,
        "domainMatch": domain_match,
        "packageFamiliesPresent": family_presence,
        "domainErrors": errors,
    }

def evaluate_domain_package_pair(
    factory: Mapping[str, Any],
    operating_model: Mapping[str, Any],
    framework_version: str,
    creation_type: str,
) -> Dict[str, Any]:
    factory_validation = validate_domain_package(factory, framework_version, creation_type)
    om_validation = validate_domain_package(operating_model, framework_version, creation_type)

    checks = {
        "factoryKind": factory.get("packageKind") == "FACTORY",
        "operatingModelKind": operating_model.get("packageKind") == "OPERATING_MODEL",
        "frameworkRange": (
            "DOMAIN_PACKAGE_FRAMEWORK_INCOMPATIBLE" not in factory_validation["errors"]
            and "DOMAIN_PACKAGE_FRAMEWORK_INCOMPATIBLE" not in om_validation["errors"]
            and "DOMAIN_PACKAGE_FRAMEWORK_RANGE_INVALID" not in factory_validation["errors"]
            and "DOMAIN_PACKAGE_FRAMEWORK_RANGE_INVALID" not in om_validation["errors"]
        ),
        "creationTypeSupport": (
            "DOMAIN_PACKAGE_CREATION_TYPE_UNSUPPORTED" not in factory_validation["errors"]
            and "DOMAIN_PACKAGE_CREATION_TYPE_UNSUPPORTED" not in om_validation["errors"]
        ),
        "capabilityCoverage": False,
        "authorityCoverage": False,
        "dependencyCoverage": True,
    }

    factory_to_om = _evaluate_counterpart_contract(factory, operating_model)
    om_to_factory = _evaluate_counterpart_contract(operating_model, factory)

    missing_capabilities = factory_to_om["missingCapabilities"]
    missing_authorities = factory_to_om["missingAuthorities"]
    checks["capabilityCoverage"] = not missing_capabilities
    checks["authorityCoverage"] = not missing_authorities
    checks["dependencyCoverage"] = (
        factory_to_om["compatible"] and om_to_factory["compatible"]
    )

    compatible = (
        factory_validation["valid"]
        and om_validation["valid"]
        and all(checks.values())
    )
    return {
        "compatible": compatible,
        "checks": checks,
        "missingCapabilities": missing_capabilities,
        "missingAuthorities": missing_authorities,
        "factoryErrors": factory_validation["errors"],
        "operatingModelErrors": om_validation["errors"],
        "factoryToOperatingModel": factory_to_om,
        "operatingModelToFactory": om_to_factory,
    }



def evaluate_active_conditional_requirements(
    factory: Mapping[str, Any],
    operating_model: Mapping[str, Any],
    active_conditions: Iterable[str],
) -> Dict[str, Any]:
    """Evaluate Factory requirements that become mandatory only for active conditions.

    Base package compatibility intentionally checks only unconditional counterpart
    requirements. This function fails closed when an event/risk condition activates
    a capability or authority that the selected Operating Model cannot supply.
    """
    conditions = set(active_conditions)
    contract = factory.get("model", {}).get("compatibilityContract", {})
    om_exports = operating_model.get("exports", {})
    available_capabilities = set(om_exports.get("capabilities", []))
    available_authorities = set(om_exports.get("authorities", []))

    required_capabilities = {
        item.get("capabilityId")
        for item in contract.get("conditionalCapabilities", [])
        if item.get("when") in conditions and item.get("capabilityId")
    }
    required_authorities = {
        item.get("authorityId")
        for item in contract.get("conditionalAuthorities", [])
        if item.get("when") in conditions and item.get("authorityId")
    }
    missing_capabilities = sorted(required_capabilities - available_capabilities)
    missing_authorities = sorted(required_authorities - available_authorities)
    return {
        "satisfied": not missing_capabilities and not missing_authorities,
        "activeConditions": sorted(conditions),
        "requiredCapabilities": sorted(required_capabilities),
        "requiredAuthorities": sorted(required_authorities),
        "missingCapabilities": missing_capabilities,
        "missingAuthorities": missing_authorities,
    }


def validate_factory_contract_consistency(factory: Mapping[str, Any]) -> Dict[str, Any]:
    """Check internal consistency of a SAFOR Factory's declared requirements."""
    errors: List[str] = []
    if factory.get("packageKind") != "FACTORY":
        errors.append("NOT_A_FACTORY")
        return {"valid": False, "errors": errors}

    compatibility = factory.get("compatibility", {}).get("counterpart", {})
    contract = factory.get("model", {}).get("compatibilityContract", {})
    exports = factory.get("exports", {})
    exported_capabilities = set(exports.get("capabilities", []))
    exported_authorities = set(exports.get("authorities", []))

    counterpart_capabilities = set(compatibility.get("requiredCapabilities", []))
    counterpart_authorities = set(compatibility.get("requiredAuthorities", []))
    mandatory_capabilities = set(contract.get("mandatoryCapabilities", []))
    mandatory_authorities = set(contract.get("mandatoryAuthorities", []))

    if counterpart_capabilities != mandatory_capabilities:
        errors.append("MANDATORY_CAPABILITY_CONTRACT_MISMATCH")
    if counterpart_authorities != mandatory_authorities:
        errors.append("MANDATORY_AUTHORITY_CONTRACT_MISMATCH")
    if not mandatory_capabilities.issubset(exported_capabilities):
        errors.append("MANDATORY_CAPABILITY_NOT_EXPORTED")
    if not mandatory_authorities.issubset(exported_authorities):
        errors.append("MANDATORY_AUTHORITY_NOT_EXPORTED")

    conditional_capabilities = {
        item.get("capabilityId")
        for item in contract.get("conditionalCapabilities", [])
        if item.get("capabilityId")
    }
    conditional_authorities = {
        item.get("authorityId")
        for item in contract.get("conditionalAuthorities", [])
        if item.get("authorityId")
    }
    if not conditional_capabilities.issubset(exported_capabilities):
        errors.append("CONDITIONAL_CAPABILITY_NOT_EXPORTED")
    if not conditional_authorities.issubset(exported_authorities):
        errors.append("CONDITIONAL_AUTHORITY_NOT_EXPORTED")

    nodes = factory.get("model", {}).get("flowGraph", {}).get("nodes", [])
    for node in nodes:
        for capability in node.get("requiresCapabilities", []):
            if capability not in exported_capabilities:
                errors.append(f"FLOW_CAPABILITY_NOT_EXPORTED:{node.get('id')}:{capability}")
        for authority in node.get("requiredAuthorities", []):
            if authority not in exported_authorities:
                errors.append(f"FLOW_AUTHORITY_NOT_EXPORTED:{node.get('id')}:{authority}")
        for item in node.get("conditionalAuthorities", []):
            authority = item.get("authorityId")
            if authority and authority not in exported_authorities:
                errors.append(f"FLOW_CONDITIONAL_AUTHORITY_NOT_EXPORTED:{node.get('id')}:{authority}")

    return {"valid": not errors, "errors": errors}

def _loaded_package_record(
    loaded_packages: Sequence[Mapping[str, Any]],
    package_id: str,
) -> Optional[Mapping[str, Any]]:
    matches = []
    for record in loaded_packages:
        artifact = record.get("artifact") if isinstance(record.get("artifact"), Mapping) else record
        if artifact.get("packageId") == package_id:
            matches.append(record)
    if len(matches) > 1:
        raise ValueError(f"Multiple loaded package candidates for {package_id}")
    return matches[0] if matches else None



def _parse_timestamp(value: str) -> datetime:
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def validate_commercial_entitlement(
    entitlement: Mapping[str, Any],
    package_id: str,
    version: str,
    verification_context: Mapping[str, Any],
) -> Dict[str, Any]:
    """Strict rc.4 commercial entitlement verification.

    Time, subject and trust are supplied explicitly so this policy function stays
    pure and never reads the wall clock or invents trusted identities.
    """
    if entitlement.get("format") != "SAFOR_COMMERCIAL_ENTITLEMENT" or entitlement.get("schemaVersion") != "0.13.0":
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_UNVERIFIED"}

    if entitlement.get("status") != "ACTIVE":
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_STATUS_INVALID"}

    grant = entitlement.get("grant", {})
    if grant.get("packageId") != package_id or not _version_grant_matches(str(grant.get("versionRange", "")), version):
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_SCOPE_MISMATCH"}

    expected_subject = verification_context.get("subjectRef")
    subject = entitlement.get("subject", {})
    if not expected_subject or subject.get("subjectRef") != expected_subject:
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_SUBJECT_MISMATCH"}

    issuer = entitlement.get("issuer", {})
    trusted_issuers = set(verification_context.get("trustedIssuerIds", []))
    if not trusted_issuers or issuer.get("issuerId") not in trusted_issuers:
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_ISSUER_UNTRUSTED"}

    verification = entitlement.get("verification", {})
    trusted_verifiers = set(verification_context.get("trustedEntitlementVerifierIds", []))
    if verification.get("method") not in ALLOWED_ENTITLEMENT_VERIFIERS:
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_UNVERIFIED"}
    if verification.get("result") != "VERIFIED":
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_UNVERIFIED"}
    if not trusted_verifiers or verification.get("verifierId") not in trusted_verifiers:
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_VERIFIER_UNTRUSTED"}
    if not verification.get("evidenceRef"):
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_UNVERIFIED"}

    basis = entitlement.get("commercialBasis", {})
    if (
        basis.get("basisType") not in {"PURCHASE", "SUBSCRIPTION", "CONTRACT", "MANUAL_GRANT"}
        or not basis.get("evidenceRef")
        or basis.get("sku") != grant.get("sku")
    ):
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_COMMERCIAL_BASIS_INVALID"}

    evaluated_at_raw = verification_context.get("evaluatedAt")
    try:
        evaluated_at = _parse_timestamp(str(evaluated_at_raw))
        valid_from = _parse_timestamp(str(entitlement.get("validity", {}).get("validFrom")))
        valid_until_raw = entitlement.get("validity", {}).get("validUntil")
        verified_at = _parse_timestamp(str(verification.get("verifiedAt")))
        if evaluated_at < valid_from:
            return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_NOT_YET_VALID"}
        if valid_until_raw is not None and evaluated_at >= _parse_timestamp(str(valid_until_raw)):
            return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_EXPIRED"}
        if verified_at > evaluated_at:
            return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_VERIFICATION_TIME_INVALID"}
    except (TypeError, ValueError):
        return {"valid": False, "outcome": "PACKAGE_ENTITLEMENT_TIME_INVALID"}

    return {
        "valid": True,
        "outcome": "PACKAGE_ENTITLEMENT_VERIFIED",
        "entitlementId": entitlement.get("entitlementId"),
        "issuerId": issuer.get("issuerId"),
        "verifierId": verification.get("verifierId"),
    }


def validate_commercial_delivery_evidence(
    delivery_evidence: Mapping[str, Any],
    artifact: Mapping[str, Any],
    entitlement: Mapping[str, Any],
    verification_context: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate evidence produced by an entitled/private package delivery source."""
    if delivery_evidence.get("format") != "SAFOR_COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE":
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE_INVALID"}
    if delivery_evidence.get("schemaVersion") != "0.13.0":
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE_INVALID"}
    if delivery_evidence.get("result") != "VERIFIED":
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE_INVALID"}
    if delivery_evidence.get("entitlementId") != entitlement.get("entitlementId"):
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_ENTITLEMENT_MISMATCH"}
    if delivery_evidence.get("packageId") != artifact.get("packageId"):
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_PACKAGE_MISMATCH"}
    if delivery_evidence.get("version") != artifact.get("version"):
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_PACKAGE_MISMATCH"}

    artifact_digest = compute_domain_package_digest(artifact)
    if artifact.get("integrity", {}).get("contentDigest") != artifact_digest:
        return {"valid": False, "outcome": "DOMAIN_PACKAGE_INTEGRITY_MISMATCH"}
    if delivery_evidence.get("artifactDigest") != artifact_digest:
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_DIGEST_MISMATCH"}

    verifier_id = delivery_evidence.get("verifierId")
    trusted_delivery_verifiers = set(verification_context.get("trustedDeliveryVerifierIds", []))
    if not trusted_delivery_verifiers or verifier_id not in trusted_delivery_verifiers:
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_VERIFIER_UNTRUSTED"}
    if not delivery_evidence.get("sourceRef") or not delivery_evidence.get("deliveryId"):
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE_INVALID"}

    try:
        evaluated_at = _parse_timestamp(str(verification_context.get("evaluatedAt")))
        issued_at = _parse_timestamp(str(delivery_evidence.get("issuedAt")))
        expires_at = _parse_timestamp(str(delivery_evidence.get("expiresAt")))
        if issued_at > evaluated_at:
            return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_TIME_INVALID"}
        if evaluated_at >= expires_at:
            return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_EXPIRED"}
    except (TypeError, ValueError):
        return {"valid": False, "outcome": "COMMERCIAL_PACKAGE_DELIVERY_TIME_INVALID"}

    return {
        "valid": True,
        "outcome": "COMMERCIAL_PACKAGE_DELIVERY_VERIFIED",
        "deliveryId": delivery_evidence.get("deliveryId"),
        "artifactDigest": artifact_digest,
        "verifierId": verifier_id,
    }

def resolve_composable_creation_packages(
    creation_type: str,
    catalog: Mapping[str, Any],
    loaded_packages: Sequence[Mapping[str, Any]],
    entitlements: Sequence[Mapping[str, Any]],
    selection: Optional[Mapping[str, str]] = None,
    verification_context: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if catalog.get("schemaVersion") != "0.13.0":
        return {"outcome": "PACKAGE_CATALOG_SCHEMA_UNSUPPORTED", "packages": []}

    profile = _creation_profile(catalog, creation_type)
    policy = profile.get("selectionPolicy", {})
    verification_context = verification_context or {}
    selection = selection or {}
    factory_id = selection.get("factoryPackageId", profile.get("defaultFactoryPackageId"))
    om_id = selection.get("operatingModelPackageId", profile.get("defaultOperatingModelPackageId"))

    if factory_id != profile.get("defaultFactoryPackageId") and policy.get("factoryOverrideAllowed") is not True:
        return {"outcome": "FACTORY_OVERRIDE_FORBIDDEN", "packages": []}
    if om_id != profile.get("defaultOperatingModelPackageId") and policy.get("operatingModelOverrideAllowed") is not True:
        return {"outcome": "OPERATING_MODEL_OVERRIDE_FORBIDDEN", "packages": []}

    requested = [("FACTORY", factory_id), ("OPERATING_MODEL", om_id)]
    resolutions: List[Dict[str, Any]] = []
    access_modes: Set[str] = set()

    for expected_kind, package_id in requested:
        try:
            entry = _catalog_entry(catalog, str(package_id))
        except ValueError:
            return {"outcome": "PACKAGE_NOT_IN_CATALOG", "packageId": package_id, "packages": []}

        if entry.get("kind") != expected_kind:
            return {"outcome": "PACKAGE_KIND_MISMATCH", "packageId": package_id, "packages": []}
        if creation_type not in entry.get("supportedCreationTypes", []):
            return {
                "outcome": "DOMAIN_PACKAGE_CREATION_TYPE_UNSUPPORTED",
                "packageId": package_id,
                "packages": [],
            }

        access_mode = entry.get("accessMode")
        access_policy = profile.get("selectedPackageAccessPolicy", "ANY_COMPATIBLE_ACCESS")
        if (
            access_policy == "BOTH_PAID_ENTITLEMENT_REQUIRED"
            and access_mode != "PAID_ENTITLEMENT_REQUIRED"
        ):
            return {
                "outcome": "CREATION_PROFILE_REQUIRES_BOTH_PAID_PACKAGES",
                "creationType": creation_type,
                "packageId": package_id,
                "packages": [],
            }
        access_modes.add(str(access_mode))
        loaded = _loaded_package_record(loaded_packages, str(package_id))

        if access_mode == "FREE_PUBLIC":
            if loaded is not None:
                artifact = loaded.get("artifact") if isinstance(loaded.get("artifact"), Mapping) else loaded
                source_class = loaded.get("sourceClass", "HUMAN_LOADED_PACKAGE")
                if source_class not in {"HUMAN_LOADED_PACKAGE", "PUBLIC_CANONICAL_REPOSITORY"}:
                    return {"outcome": "INVALID_FREE_PACKAGE_SOURCE", "packageId": package_id, "packages": []}
                resolutions.append({
                    "packageId": package_id,
                    "kind": expected_kind,
                    "mode": "USE_LOADED_PACKAGE",
                    "sourceClass": source_class,
                    "version": artifact.get("version"),
                })
            else:
                distribution = entry.get("distribution", {})
                if distribution.get("sourceClass") != "PUBLIC_CANONICAL_REPOSITORY" or not distribution.get("path"):
                    return {"outcome": "FREE_PUBLIC_SOURCE_INVALID", "packageId": package_id, "packages": []}
                resolutions.append({
                    "packageId": package_id,
                    "kind": expected_kind,
                    "mode": "RESOLVE_PUBLIC_FREE",
                    "sourceClass": "PUBLIC_CANONICAL_REPOSITORY",
                    "path": distribution["path"],
                    "version": entry.get("version"),
                    "requiresImmutableReadback": True,
                })
            continue

        if access_mode == "PAID_ENTITLEMENT_REQUIRED":
            if loaded is None:
                return {"outcome": "PACKAGE_ACCESS_REQUIRED", "missingPackageId": package_id, "packages": []}
            artifact = loaded.get("artifact") if isinstance(loaded.get("artifact"), Mapping) else loaded
            source_class = loaded.get("sourceClass", "HUMAN_LOADED_PACKAGE")
            if source_class not in {"HUMAN_LOADED_PACKAGE", "ENTITLED_PACKAGE_SOURCE"}:
                return {"outcome": "PAID_PUBLIC_RESOLUTION_FORBIDDEN", "packageId": package_id, "packages": []}
            version = str(artifact.get("version", loaded.get("version", "")))
            if not version:
                return {"outcome": "PACKAGE_VERSION_MISSING", "packageId": package_id, "packages": []}
            candidates = [
                e for e in entitlements
                if e.get("grant", {}).get("packageId") == str(package_id)
                and _version_grant_matches(str(e.get("grant", {}).get("versionRange", "")), version)
            ]
            if not candidates:
                return {"outcome": "PACKAGE_ENTITLEMENT_UNVERIFIED", "packageId": package_id, "packages": []}

            verified = []
            failures = []
            for candidate in candidates:
                decision = validate_commercial_entitlement(
                    candidate, str(package_id), version, verification_context
                )
                if decision["valid"]:
                    verified.append((candidate, decision))
                else:
                    failures.append(decision["outcome"])
            if len(verified) != 1:
                outcome = failures[0] if failures else "PACKAGE_ENTITLEMENT_UNVERIFIED"
                return {"outcome": outcome, "packageId": package_id, "packages": []}

            matched_entitlement, entitlement_decision = verified[0]
            delivery_decision = None
            if source_class == "ENTITLED_PACKAGE_SOURCE":
                delivery_evidence = loaded.get("deliveryEvidence")
                if not isinstance(delivery_evidence, Mapping):
                    return {
                        "outcome": "COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE_REQUIRED",
                        "packageId": package_id,
                        "packages": [],
                    }
                delivery_decision = validate_commercial_delivery_evidence(
                    delivery_evidence,
                    artifact,
                    matched_entitlement,
                    verification_context,
                )
                if not delivery_decision["valid"]:
                    return {
                        "outcome": delivery_decision["outcome"],
                        "packageId": package_id,
                        "packages": [],
                    }

            resolution = {
                "packageId": package_id,
                "kind": expected_kind,
                "mode": "USE_ENTITLED_PACKAGE",
                "sourceClass": source_class,
                "version": version,
                "entitlementId": matched_entitlement.get("entitlementId"),
                "entitlementVerifierId": entitlement_decision.get("verifierId"),
            }
            if delivery_decision is not None:
                resolution["deliveryId"] = delivery_decision.get("deliveryId")
                resolution["deliveryArtifactDigest"] = delivery_decision.get("artifactDigest")
                resolution["deliveryVerifierId"] = delivery_decision.get("verifierId")
            resolutions.append(resolution)
            continue

        return {"outcome": "UNKNOWN_ACCESS_MODE", "packageId": package_id, "packages": []}

    return {
        "outcome": "PACKAGE_ACCESS_RESOLVED",
        "creationType": creation_type,
        "selectedFactoryPackageId": factory_id,
        "selectedOperatingModelPackageId": om_id,
        "mixedAccessModes": len(access_modes) > 1,
        "packages": resolutions,
    }
