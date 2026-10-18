"""Pure creation-type consistency checks for SAFOR 0.14 Frameworks.

This validates the type contract, not the complete project descriptor, package
entitlement, HUMAN authority or migration state. It never coerces legacy values.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def validate_creation_type_contract(
    framework: Mapping[str, Any], creation_type: str | None = None
) -> dict[str, Any]:
    """Require runtime profiles, schema, initialization and catalog to agree."""
    errors: list[str] = []
    groups: dict[str, set[str]] = {}

    def collect(name: str, values: Any) -> None:
        if (not isinstance(values, list) or not values
                or any(not isinstance(v, str) or not v.strip() for v in values)):
            errors.append(f"{name}_INVALID")
            return
        if len(values) != len(set(values)):
            errors.append(f"{name}_DUPLICATE")
        groups[name] = set(values)
        if "SOFTWARE_WEBSITE" in values:
            errors.append(f"{name}_LEGACY_TYPE_FORBIDDEN")

    try:
        if framework.get("schemaVersion") != "0.14.0":
            errors.append("FRAMEWORK_SCHEMA_VERSION_UNSUPPORTED")
        modules = framework["embeddedModules"]
        collect("RUNTIME_CREATION_TYPES", [
            p["id"] for p in framework["runtimeContract"]["creationProfiles"]
        ])
        collect("PROJECT_SCHEMA_CREATION_TYPES", modules["schemaProject"]["content"]
                ["properties"]["creationType"]["enum"])
        steps = [s for s in modules["initialization"]["content"]["sequence"]
                 if s.get("id") == "INIT-01"]
        if len(steps) != 1:
            errors.append("CREATION_TYPE_INITIALIZATION_STEP_INVALID")
        else:
            collect("INITIALIZATION_CREATION_TYPES", [
                p["id"] for p in steps[0]["menu"]["options"]
            ])
        collect("CATALOG_CREATION_TYPES", [
            p["creationType"] for p in modules["packageCatalog"]["content"]
            ["creationProfiles"]
        ])
    except (KeyError, TypeError, AttributeError):
        errors.append("CREATION_TYPE_CONTRACT_STRUCTURE_INVALID")

    expected = groups.get("RUNTIME_CREATION_TYPES", set())
    for name, values in groups.items():
        if values != expected:
            errors.append(f"{name}_MISMATCH")
    if creation_type is not None and (
        not isinstance(creation_type, str) or creation_type not in expected
    ):
        errors.append("PROJECT_CREATION_TYPE_UNSUPPORTED")
    return {"valid": not errors, "errors": errors,
            "supportedCreationTypes": sorted(expected)}
