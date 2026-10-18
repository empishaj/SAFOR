#!/usr/bin/env python3
"""Build SAFOR domain-specific single-file distributions.

Public Website distribution can be reproduced from this repository.
Commercial SaaS/Book distributions require protected Factory/Operating Model
inputs and are intentionally not committed to the public repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]

import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_domain_framework_pair,
    validate_domain_package,
)

from runtime.creation_type_contract import validate_creation_type_contract

PROFILE_CATALOG = ROOT / "v0.14.0/domain-framework-profiles.json"
BASE_FRAMEWORK = ROOT / "SAFOR-FRAMEWORK.json"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def distribution_digest(distribution: Mapping[str, Any]) -> str:
    projection = {k: v for k, v in distribution.items() if k != "integrity"}
    return "sha256:" + hashlib.sha256(canonical(projection).encode("utf-8")).hexdigest()


def profile_by_id(profile_id: str) -> Dict[str, Any]:
    catalog = load_json(PROFILE_CATALOG)
    matches = [p for p in catalog["profiles"] if p["id"] == profile_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one domain framework profile for {profile_id}")
    return matches[0]


def resolve_package_path(
    package_ref: Mapping[str, Any],
    explicit_path: Optional[str],
    public_artifact: bool,
) -> Path:
    if explicit_path:
        path = Path(explicit_path)
        if not path.is_absolute():
            path = ROOT / path
        return path
    public_path = package_ref.get("publicPath")
    if public_artifact and public_path:
        return ROOT / str(public_path)
    raise ValueError(
        f"Protected package input required for {package_ref['packageId']}; "
        "provide --factory-file/--operating-model-file from the licensed package channel."
    )


def build_distribution(
    profile_id: str,
    factory_file: Optional[str] = None,
    operating_model_file: Optional[str] = None,
) -> Dict[str, Any]:
    profile = profile_by_id(profile_id)
    framework = load_json(BASE_FRAMEWORK)
    type_decision = validate_creation_type_contract(framework, profile["creationType"])
    if not type_decision["valid"]:
        raise ValueError(f"Creation-type contract invalid: {type_decision['errors']}")
    factory_path = resolve_package_path(
        profile["defaultFactory"], factory_file, profile["publicArtifactCommitted"]
    )
    om_path = resolve_package_path(
        profile["defaultOperatingModel"], operating_model_file, profile["publicArtifactCommitted"]
    )
    factory = load_json(factory_path)
    operating_model = load_json(om_path)

    expected_factory = profile["defaultFactory"]
    expected_om = profile["defaultOperatingModel"]
    for artifact, expected, kind in (
        (factory, expected_factory, "FACTORY"),
        (operating_model, expected_om, "OPERATING_MODEL"),
    ):
        if artifact.get("packageId") != expected["packageId"]:
            raise ValueError(
                f"{kind} packageId mismatch: {artifact.get('packageId')} != {expected['packageId']}"
            )
        if artifact.get("packageFamily") != expected["packageFamily"]:
            raise ValueError(
                f"{kind} packageFamily mismatch: {artifact.get('packageFamily')} != {expected['packageFamily']}"
            )
        if expected.get("version") and artifact.get("version") != expected["version"]:
            raise ValueError(
                f"{kind} version mismatch: {artifact.get('version')} != {expected['version']}"
            )
        if artifact.get("commercial", {}).get("accessMode") != profile["accessMode"]:
            raise ValueError(f"{kind} access mode does not match domain framework profile.")

        validation = validate_domain_package(
            artifact, framework["bundleVersion"], profile["creationType"]
        )
        if not validation["valid"]:
            raise ValueError(f"{kind} package invalid: {validation['errors']}")

    pair = evaluate_domain_framework_pair(
        factory,
        operating_model,
        framework["bundleVersion"],
        profile["creationType"],
        profile["domainId"],
    )
    if not pair["compatible"]:
        raise ValueError(f"Domain Factory/Operating Model pair incompatible: {pair}")

    distribution: Dict[str, Any] = {
        "format": "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION",
        "schemaVersion": "0.14.0",
        "distributionVersion": framework["bundleVersion"],
        "distributionId": profile["distributionId"],
        "fileName": profile["distributionFile"],
        "publicationMode": profile["publicationMode"],
        "evaluationNotice": (
            "Public test/evaluation artifact. Embedded paid-mode modules are public test bytes "
            "and are not the protected commercial production package source."
            if profile["publicationMode"] == "PUBLIC_TEST_EVALUATION"
            else None
        ),
        "evaluationAccess": (
            {
                "mode": "EXTERNAL_TEST_ACCESS_BUNDLE",
                "file": profile["evaluationAccessFile"],
                "embeddedModulesSourceClass": "HUMAN_LOADED_PACKAGE",
                "productionAuthorization": False,
            }
            if profile["publicationMode"] == "PUBLIC_TEST_EVALUATION"
            else None
        ),
        "domain": {
            "domainId": profile["domainId"],
            "creationType": profile["creationType"],
            "accessMode": profile["accessMode"],
        },
        "framework": framework,
        "embeddedDomainModules": {
            "factory": factory,
            "operatingModel": operating_model,
        },
        "defaultBinding": {
            "factory": {
                "packageId": factory["packageId"],
                "packageFamily": factory["packageFamily"],
                "version": factory["version"],
                "contentDigest": compute_domain_package_digest(factory),
            },
            "operatingModel": {
                "packageId": operating_model["packageId"],
                "packageFamily": operating_model["packageFamily"],
                "version": operating_model["version"],
                "contentDigest": compute_domain_package_digest(operating_model),
            },
            "compatibility": "COMPATIBLE",
            "domainId": profile["domainId"],
        },
        "replacementPolicy": profile["replacementPolicy"],
        "replacementContract": {
            "rule": (
                "A replacement Factory or Operating Model is adopted only after access/integrity "
                "verification and evaluate_domain_framework_pair confirms the active domain, both "
                "package-family constraints and both counterpart contracts. Cross-domain pairs fail closed."
            ),
            "factoryReplacementAllowed": True,
            "operatingModelReplacementAllowed": True,
            "requiresSameDomain": True,
            "requiresBidirectionalCompatibility": True,
            "requiresPackageFamilyCompatibility": True,
        },
    }
    distribution["integrity"] = {
        "canonicalization": "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION_V1",
        "digestAlgorithm": "SHA-256",
        "digestScope": "DISTRIBUTION_EXCLUDING_INTEGRITY",
        "contentDigest": distribution_digest(distribution),
    }
    return distribution


def validate_distribution(
    distribution: Mapping[str, Any],
    profile_id: str,
) -> Dict[str, Any]:
    profile = profile_by_id(profile_id)
    errors = []
    if distribution.get("format") != "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION":
        errors.append("DOMAIN_FRAMEWORK_FORMAT_INVALID")
    if distribution.get("distributionId") != profile["distributionId"]:
        errors.append("DOMAIN_FRAMEWORK_PROFILE_MISMATCH")
    if distribution.get("fileName") != profile["distributionFile"]:
        errors.append("DOMAIN_FRAMEWORK_FILENAME_MISMATCH")
    if distribution.get("publicationMode") != profile["publicationMode"]:
        errors.append("DOMAIN_FRAMEWORK_PUBLICATION_MODE_MISMATCH")
    if profile["publicationMode"] == "PUBLIC_TEST_EVALUATION":
        access = distribution.get("evaluationAccess", {})
        if access.get("file") != profile.get("evaluationAccessFile"):
            errors.append("DOMAIN_FRAMEWORK_EVALUATION_ACCESS_MISMATCH")
        if access.get("embeddedModulesSourceClass") != "HUMAN_LOADED_PACKAGE":
            errors.append("DOMAIN_FRAMEWORK_EVALUATION_SOURCE_CLASS_INVALID")
        if access.get("productionAuthorization") is not False:
            errors.append("DOMAIN_FRAMEWORK_EVALUATION_PRODUCTION_AUTHORIZATION_INVALID")
    domain = distribution.get("domain", {})
    if domain.get("domainId") != profile["domainId"]:
        errors.append("DOMAIN_FRAMEWORK_DOMAIN_MISMATCH")
    if domain.get("creationType") != profile["creationType"]:
        errors.append("DOMAIN_FRAMEWORK_CREATION_TYPE_MISMATCH")

    framework = distribution.get("framework", {})
    type_decision = validate_creation_type_contract(framework, profile["creationType"])
    errors.extend(type_decision["errors"])
    modules = distribution.get("embeddedDomainModules", {})
    factory = modules.get("factory", {})
    operating_model = modules.get("operatingModel", {})
    pair = evaluate_domain_framework_pair(
        factory,
        operating_model,
        str(framework.get("bundleVersion", "")),
        profile["creationType"],
        profile["domainId"],
    )
    if not pair["compatible"]:
        errors.append("DOMAIN_FRAMEWORK_PAIR_INCOMPATIBLE")

    expected_digest = distribution_digest(distribution)
    if distribution.get("integrity", {}).get("contentDigest") != expected_digest:
        errors.append("DOMAIN_FRAMEWORK_INTEGRITY_MISMATCH")

    return {"valid": not errors, "errors": errors, "pair": pair}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["WEBSITE", "SAAS", "BOOK_CREATION"])
    parser.add_argument("--factory-file")
    parser.add_argument("--operating-model-file")
    parser.add_argument("--output")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Rebuild and compare every public committed domain distribution.",
    )
    args = parser.parse_args()

    if args.check:
        catalog = load_json(PROFILE_CATALOG)
        for profile in catalog["profiles"]:
            if not profile["publicArtifactCommitted"]:
                continue
            built = build_distribution(profile["id"])
            output = ROOT / profile["distributionFile"]
            if not output.exists():
                raise SystemExit(
                    f"SAFOR domain distribution reproducibility: FAIL (missing {output.name})"
                )
            committed = load_json(output)
            if canonical(committed) != canonical(built):
                raise SystemExit(
                    f"SAFOR domain distribution reproducibility: FAIL ({output.name})"
                )
            decision = validate_distribution(committed, profile["id"])
            if not decision["valid"]:
                raise SystemExit(
                    f"SAFOR domain distribution validation: FAIL ({output.name}: {decision['errors']})"
                )
        print("SAFOR domain distribution reproducibility: PASS")
        return

    if not args.profile:
        parser.error("--profile is required unless --check is used")

    built = build_distribution(
        args.profile,
        factory_file=args.factory_file,
        operating_model_file=args.operating_model_file,
    )
    profile = profile_by_id(args.profile)
    output = Path(args.output) if args.output else ROOT / profile["distributionFile"]
    if not output.is_absolute():
        output = ROOT / output
    output.write_text(json.dumps(built, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
