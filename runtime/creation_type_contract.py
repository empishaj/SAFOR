"""Pure cross-contract checks; this module never converts legacy projects."""
from collections.abc import Mapping
from typing import Any


def validate_creation_type_contract(
    framework: Mapping[str, Any], creation_type: str | None = None
) -> dict[str, Any]:
    """Reject disagreement between project schema and declared creation profiles."""
    errors: list[str] = []
    modules = framework.get("embeddedModules", {})
    if not isinstance(modules, Mapping):
        return {"valid": False, "errors": ["CREATION_TYPE_MODULES_INVALID"]}
    try:
        values = modules["schemaProject"]["content"]["properties"]["creationType"]["enum"]
        catalog = modules["packageCatalog"]["content"]["creationProfiles"]
        runtime = framework["runtimeContract"]["creationProfiles"]
        sets = []
        for items, field in ((values, None), (catalog, "creationType"), (runtime, "id")):
            if not isinstance(items, list) or not items:
                raise ValueError("Missing creation type declaration")
            names = items if field is None else [item[field] for item in items]
            if any(not isinstance(name, str) or not name for name in names):
                raise ValueError("Invalid creation type declaration")
            if len(set(names)) != len(names):
                raise ValueError("Duplicate creation type declaration")
            sets.append(set(names))
    except (KeyError, TypeError, ValueError):
        return {"valid": False, "errors": ["CREATION_TYPE_DECLARATION_INVALID"]}
    if not (sets[0] == sets[1] == sets[2]):
        errors.append("PROJECT_CREATION_TYPE_CONTRACT_MISMATCH")
    if creation_type is not None and not all(creation_type in names for names in sets):
        errors.append("PROJECT_CREATION_TYPE_UNSUPPORTED")
    return {"valid": not errors, "errors": errors}
