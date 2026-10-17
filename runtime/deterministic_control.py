"""SAFOR deterministic control reference kernel (0.11.0-rc.1).

The reducer in this module is intentionally pure with respect to external systems:
it does not call providers, LLMs, clocks, random sources, or mutate its input.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

MODEL_VERSION = "0.11.0-rc.1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: Any) -> str:
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def event_hash(event: Mapping[str, Any]) -> str:
    return canonical_hash(event)


def state_hash(snapshot: Mapping[str, Any]) -> str:
    material = copy.deepcopy(dict(snapshot))
    material.pop("stateHash", None)
    return canonical_hash(material)


def initialize_state_hash(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(dict(snapshot))
    result["stateHash"] = state_hash(result)
    return result


def _get_event_path(event: Mapping[str, Any], path: str) -> Any:
    current: Any = event
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise KeyError(f"Event path not found: {path}")
        current = current[part]
    return current


def _aggregate_key(name: str) -> str:
    mapping = {"CONTROL": "control", "VALUE_STREAM": "valueStream", "EXECUTION": "execution"}
    if name not in mapping:
        raise ValueError(f"Unknown aggregate: {name}")
    return mapping[name]


def _find_work_items(snapshot: Mapping[str, Any], work_item_id: str) -> List[Mapping[str, Any]]:
    items = snapshot.get("valueStream", {}).get("workItems", [])
    return [item for item in items if item.get("id") == work_item_id]


def _find_work_item(snapshot: Mapping[str, Any], event: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    subject = event.get("subject", {})
    if subject.get("type") != "WORK_ITEM":
        return None
    matches = _find_work_items(snapshot, subject.get("ref", ""))
    if len(matches) != 1:
        return None
    return matches[0]


def _find_mutable_work_item(snapshot: MutableMapping[str, Any], event: Mapping[str, Any]) -> MutableMapping[str, Any]:
    subject = event.get("subject", {})
    ref = subject.get("ref")
    items = snapshot.get("valueStream", {}).get("workItems", [])
    matches = [item for item in items if item.get("id") == ref]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one subject work item, found {len(matches)} for {ref}")
    return matches[0]


def _resolve_read_path(
    path: str,
    snapshot: Mapping[str, Any],
    aggregate_name: str,
    event: Mapping[str, Any],
) -> Any:
    if path.startswith("$aggregate."):
        current: Any = snapshot[_aggregate_key(aggregate_name)]
        parts = path[len("$aggregate."):].split(".")
    elif path.startswith("$subject."):
        subject = _find_work_item(snapshot, event)
        if subject is None:
            raise KeyError("Subject work item not found")
        current = subject
        parts = path[len("$subject."):].split(".")
    elif path.startswith("$control."):
        current = snapshot["control"]
        parts = path[len("$control."):].split(".")
    elif path.startswith("$valueStream."):
        current = snapshot["valueStream"]
        parts = path[len("$valueStream."):].split(".")
    elif path.startswith("$execution."):
        current = snapshot["execution"]
        parts = path[len("$execution."):].split(".")
    else:
        raise KeyError(f"Unsupported state path: {path}")
    for part in parts:
        if not isinstance(current, Mapping) or part not in current:
            raise KeyError(f"State path not found: {path}")
        current = current[part]
    return current


def _resolve_mutable_parent(
    path: str,
    snapshot: MutableMapping[str, Any],
    aggregate_name: str,
    event: Mapping[str, Any],
) -> Tuple[MutableMapping[str, Any], str]:
    if path.startswith("$aggregate."):
        current: MutableMapping[str, Any] = snapshot[_aggregate_key(aggregate_name)]
        parts = path[len("$aggregate."):].split(".")
    elif path.startswith("$subject."):
        current = _find_mutable_work_item(snapshot, event)
        parts = path[len("$subject."):].split(".")
    else:
        raise KeyError(f"Effects may mutate only $aggregate or $subject paths: {path}")
    if not parts:
        raise KeyError(f"Invalid mutation path: {path}")
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, MutableMapping):
            raise KeyError(f"State path not mutable object: {path}")
        current = next_value
    return current, parts[-1]


def _subject_status(snapshot: Mapping[str, Any], transition: Mapping[str, Any], event: Mapping[str, Any]) -> Optional[str]:
    if transition["subjectType"] == "WORK_ITEM":
        subject = _find_work_item(snapshot, event)
        return None if subject is None else subject.get("status")
    aggregate = snapshot[_aggregate_key(transition["aggregate"])]
    return aggregate.get("status")


def _predicate_all_dependencies_accepted(snapshot: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    item = _find_work_item(snapshot, event)
    if item is None:
        return False
    for dep_id in item.get("dependencies", []):
        matches = _find_work_items(snapshot, dep_id)
        if len(matches) != 1 or matches[0].get("status") != "ACCEPTED":
            return False
    return True


def _predicate_active_mandate_covers(snapshot: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    item = _find_work_item(snapshot, event)
    if item is None:
        return False
    work_item_id = item.get("id")
    required_capabilities = set(item.get("requiredCapabilities", []))
    for mandate in snapshot.get("control", {}).get("mandates", []):
        if mandate.get("active") is not True or mandate.get("revokedAt") is not None:
            continue
        scope = mandate.get("scope", {})
        if work_item_id not in set(scope.get("workItemIds", [])):
            continue
        if required_capabilities.issubset(set(scope.get("capabilities", []))):
            return True
    return False


def _predicate_inputs_resolvable(snapshot: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    item = _find_work_item(snapshot, event)
    if item is None:
        return False
    objects = snapshot.get("valueStream", {}).get("objects", [])
    by_id: Dict[str, List[Mapping[str, Any]]] = {}
    for obj in objects:
        by_id.setdefault(obj.get("id"), []).append(obj)
    for input_ref in item.get("inputs", []):
        ref = input_ref.get("ref")
        matches = by_id.get(ref, [])
        if len(matches) != 1 or matches[0].get("artifactRef") is None:
            return False
    return True


def _predicate_resource_declaration_complete(snapshot: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    item = _find_work_item(snapshot, event)
    if item is None:
        return False
    resource = item.get("execution", {}).get("resourceAccess")
    if not isinstance(resource, Mapping):
        return False
    return all(isinstance(resource.get(key), list) for key in ("readSet", "writeSet", "exclusiveKeys"))


def _evaluate_predicate(
    predicate_id: str,
    args: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    transition: Mapping[str, Any],
    event: Mapping[str, Any],
) -> Tuple[bool, Optional[str]]:
    if predicate_id == "EVENT_SEQUENCE_CONTIGUOUS":
        expected = snapshot.get("lastAppliedEventSequence", -1) + 1
        actual = event.get("sequence")
        return actual == expected, f"expected={expected},actual={actual}"
    if predicate_id == "SUBJECT_WORK_ITEM_EXISTS":
        matches = _find_work_items(snapshot, event.get("subject", {}).get("ref", ""))
        return len(matches) == 1, f"matches={len(matches)}"
    if predicate_id == "ALL_DEPENDENCIES_ACCEPTED":
        return _predicate_all_dependencies_accepted(snapshot, event), None
    if predicate_id == "ACTIVE_MANDATE_COVERS_WORK_ITEM":
        return _predicate_active_mandate_covers(snapshot, event), None
    if predicate_id == "REQUIRED_INPUTS_RESOLVABLE":
        return _predicate_inputs_resolvable(snapshot, event), None
    if predicate_id == "RESOURCE_DECLARATION_COMPLETE":
        return _predicate_resource_declaration_complete(snapshot, event), None
    if predicate_id == "FIELD_EQUALS":
        value = _resolve_read_path(args["path"], snapshot, transition["aggregate"], event)
        return value == args.get("value"), f"actual={value!r}"
    if predicate_id == "FIELD_IN":
        value = _resolve_read_path(args["path"], snapshot, transition["aggregate"], event)
        return value in args.get("values", []), f"actual={value!r}"
    if predicate_id == "EVENT_TYPE_IS":
        return event.get("eventType") == args.get("value"), None
    raise ValueError(f"Unknown predicate: {predicate_id}")


def _evaluate_guard(
    expr: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    transition: Mapping[str, Any],
    event: Mapping[str, Any],
    allowed_predicates: set[str],
    results: List[Dict[str, Any]],
) -> bool:
    if "predicate" in expr:
        predicate_id = expr["predicate"]
        if predicate_id not in allowed_predicates:
            raise ValueError(f"Predicate not pinned in registry: {predicate_id}")
        ok, detail = _evaluate_predicate(predicate_id, expr.get("args", {}), snapshot, transition, event)
        results.append({"predicate": predicate_id, "result": bool(ok), "detail": detail})
        return bool(ok)
    if "all" in expr:
        values = [_evaluate_guard(x, snapshot, transition, event, allowed_predicates, results) for x in expr["all"]]
        return all(values)
    if "any" in expr:
        values = [_evaluate_guard(x, snapshot, transition, event, allowed_predicates, results) for x in expr["any"]]
        return any(values)
    if "not" in expr:
        return not _evaluate_guard(expr["not"], snapshot, transition, event, allowed_predicates, results)
    raise ValueError("Invalid guard expression")


def _apply_effect(
    effect: Mapping[str, Any],
    snapshot: MutableMapping[str, Any],
    transition: Mapping[str, Any],
    event: Mapping[str, Any],
) -> None:
    op = effect["op"]
    parent, key = _resolve_mutable_parent(effect["path"], snapshot, transition["aggregate"], event)
    if op == "SET":
        parent[key] = copy.deepcopy(effect.get("value"))
    elif op == "SET_FROM_EVENT":
        parent[key] = copy.deepcopy(_get_event_path(event, effect["eventPath"]))
    elif op == "SET_FROM_STATE":
        parent[key] = copy.deepcopy(_resolve_read_path(effect["statePath"], snapshot, transition["aggregate"], event))
    elif op == "INCREMENT":
        current = parent.get(key)
        if not isinstance(current, (int, float)):
            raise ValueError(f"INCREMENT target is not numeric: {effect['path']}")
        parent[key] = current + effect["by"]
    elif op == "APPEND_UNIQUE":
        current = parent.get(key)
        if not isinstance(current, list):
            raise ValueError(f"APPEND_UNIQUE target is not a list: {effect['path']}")
        value = copy.deepcopy(effect.get("value"))
        if value not in current:
            current.append(value)
    elif op == "REMOVE_MATCHING":
        current = parent.get(key)
        if not isinstance(current, list):
            raise ValueError(f"REMOVE_MATCHING target is not a list: {effect['path']}")
        match = effect["match"]
        parent[key] = [item for item in current if not (isinstance(item, Mapping) and all(item.get(k) == v for k, v in match.items()))]
    elif op == "REVOKE_ACTIVE_MANDATES":
        current = parent.get(key)
        if not isinstance(current, list):
            raise ValueError("Mandates target must be a list")
        revoked_at = _get_event_path(event, effect["eventPath"])
        for mandate in current:
            if mandate.get("active") is True and mandate.get("revokedAt") is None:
                mandate["active"] = False
                mandate["revokedAt"] = revoked_at
    else:
        raise ValueError(f"Unknown state effect op: {op}")


def _make_effect_intents(transition: Mapping[str, Any], event: Mapping[str, Any]) -> List[Dict[str, Any]]:
    result = []
    for index, template in enumerate(transition.get("effectIntents", [])):
        raw_id = f"{transition['transitionId']}|{event['eventId']}|{index}"
        effect_id = "eff-" + hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24]
        result.append({
            "format": "SAFOR_EFFECT_INTENT",
            "schemaVersion": "0.11.0",
            "effectIntentId": effect_id,
            "effectType": template["effectType"],
            "reason": template["reason"],
            "sourceTransitionId": transition["transitionId"],
            "sourceEventId": event["eventId"],
            "payload": copy.deepcopy(template.get("payload", {})),
        })
    return result


def _record(
    transition_id: str,
    event_id: str,
    pre_hash: str,
    post_hash: str,
    guard_results: List[Dict[str, Any]],
    effect_intents: List[Dict[str, Any]],
    model_revision: str,
    outcome: str,
) -> Dict[str, Any]:
    raw = f"{transition_id}|{event_id}|{pre_hash}|{post_hash}|{outcome}"
    record_id = "tr-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return {
        "format": "SAFOR_TRANSITION_RECORD",
        "schemaVersion": "0.11.0",
        "transitionRecordId": record_id,
        "transitionId": transition_id,
        "eventId": event_id,
        "preStateHash": pre_hash,
        "postStateHash": post_hash,
        "guardResults": guard_results,
        "effectIntents": effect_intents,
        "modelRevision": model_revision,
        "outcome": outcome,
    }


def reduce(
    projection_set: Mapping[str, Any],
    event: Mapping[str, Any],
    pinned_models: Mapping[str, Any],
) -> Dict[str, Any]:
    """Apply at most one authoritative deterministic transition."""
    original = copy.deepcopy(dict(projection_set))
    pre_hash = state_hash(original)
    declared_hash = original.get("stateHash")
    if declared_hash is not None and declared_hash != pre_hash:
        record = _record("STATE_HASH_VALIDATION", event.get("eventId", "UNKNOWN"), pre_hash, pre_hash, [], [], original.get("modelRevision", ""), "INTEGRITY_FAILURE")
        return {"outcome": "INTEGRITY_FAILURE", "state": original, "transitionRecord": record, "effectIntents": []}

    model_revision = pinned_models.get("modelRevision")
    if model_revision != original.get("modelRevision"):
        record = _record("MODEL_REVISION_VALIDATION", event.get("eventId", "UNKNOWN"), pre_hash, pre_hash, [], [], str(model_revision), "CONTROL_FAILURE")
        return {"outcome": "CONTROL_FAILURE", "state": original, "transitionRecord": record, "effectIntents": []}

    event_id = event.get("eventId")
    if not event_id:
        record = _record("EVENT_VALIDATION", "UNKNOWN", pre_hash, pre_hash, [], [], str(model_revision), "CONTROL_FAILURE")
        return {"outcome": "CONTROL_FAILURE", "state": original, "transitionRecord": record, "effectIntents": []}

    processed = original.get("processedEvents", {})
    incoming_hash = event_hash(event)
    if event_id in processed:
        if processed[event_id] == incoming_hash:
            record = _record("IDEMPOTENT_EVENT", event_id, pre_hash, pre_hash, [], [], str(model_revision), "IDEMPOTENT_NO_OP")
            return {"outcome": "IDEMPOTENT_NO_OP", "state": original, "transitionRecord": record, "effectIntents": []}
        record = _record("DIVERGENT_DUPLICATE_EVENT", event_id, pre_hash, pre_hash, [], [], str(model_revision), "INTEGRITY_FAILURE")
        return {"outcome": "INTEGRITY_FAILURE", "state": original, "transitionRecord": record, "effectIntents": []}

    expected_sequence = original.get("lastAppliedEventSequence", -1) + 1
    if event.get("sequence") != expected_sequence:
        record = _record("EVENT_SEQUENCE_VALIDATION", event_id, pre_hash, pre_hash, [], [], str(model_revision), "CONTROL_FAILURE")
        return {"outcome": "CONTROL_FAILURE", "state": original, "transitionRecord": record, "effectIntents": []}

    transition_registry = pinned_models["transitionRegistry"]
    predicate_registry = pinned_models["predicateRegistry"]
    allowed_predicates = {p["id"] for p in predicate_registry.get("predicates", [])}

    applicable: List[Tuple[Mapping[str, Any], List[Dict[str, Any]]]] = []
    for transition in transition_registry.get("transitions", []):
        if event.get("eventType") not in transition.get("eventTypes", []):
            continue
        if event.get("subject", {}).get("type") != transition.get("subjectType"):
            continue
        current_status = _subject_status(original, transition, event)
        if current_status not in transition.get("fromStatus", []):
            continue
        guard_results: List[Dict[str, Any]] = []
        try:
            passed = _evaluate_guard(transition["guards"], original, transition, event, allowed_predicates, guard_results)
        except (KeyError, ValueError) as exc:
            guard_results.append({"predicate": "CONTROL_EVALUATION", "result": False, "detail": str(exc)})
            passed = False
        if passed:
            applicable.append((transition, guard_results))

    applicable.sort(key=lambda pair: (-pair[0]["priority"], pair[0]["transitionId"]))
    if not applicable:
        record = _record("NO_TRANSITION", event_id, pre_hash, pre_hash, [], [], str(model_revision), "NO_TRANSITION")
        return {"outcome": "NO_TRANSITION", "state": original, "transitionRecord": record, "effectIntents": []}
    if len(applicable) > 1:
        detail = [{"predicate": "AMBIGUOUS_TRANSITION", "result": False, "detail": ",".join(x[0]["transitionId"] for x in applicable)}]
        record = _record("AMBIGUOUS_TRANSITION", event_id, pre_hash, pre_hash, detail, [], str(model_revision), "CONTROL_FAILURE")
        return {"outcome": "CONTROL_FAILURE", "state": original, "transitionRecord": record, "effectIntents": []}

    transition, guard_results = applicable[0]
    new_state = copy.deepcopy(original)
    try:
        for effect in transition.get("effects", []):
            _apply_effect(effect, new_state, transition, event)
    except (KeyError, ValueError, TypeError) as exc:
        detail = guard_results + [{"predicate": "EFFECT_APPLICATION", "result": False, "detail": str(exc)}]
        record = _record(transition["transitionId"], event_id, pre_hash, pre_hash, detail, [], str(model_revision), "CONTROL_FAILURE")
        return {"outcome": "CONTROL_FAILURE", "state": original, "transitionRecord": record, "effectIntents": []}

    new_state["lastAppliedEventSequence"] = event["sequence"]
    new_state["lastAppliedEventId"] = event_id
    new_state.setdefault("processedEvents", {})[event_id] = incoming_hash
    new_state["stateHash"] = state_hash(new_state)

    intents = _make_effect_intents(transition, event)
    record = _record(
        transition["transitionId"],
        event_id,
        pre_hash,
        new_state["stateHash"],
        guard_results,
        intents,
        str(model_revision),
        "APPLIED",
    )
    return {"outcome": "APPLIED", "state": new_state, "transitionRecord": record, "effectIntents": intents}


def replay(
    genesis_projection_set: Mapping[str, Any],
    events: Iterable[Mapping[str, Any]],
    pinned_models: Mapping[str, Any],
) -> Dict[str, Any]:
    """Replay a unique contiguous event sequence from a verified genesis snapshot."""
    ordered = list(events)
    sequences = [event.get("sequence") for event in ordered]
    if sequences != sorted(sequences):
        raise ValueError("Replay events must be supplied in ascending sequence order")
    if len(sequences) != len(set(sequences)):
        raise ValueError("Replay event sequences must be unique")

    state = copy.deepcopy(dict(genesis_projection_set))
    records = []
    effect_intents = []
    for event in ordered:
        result = reduce(state, event, pinned_models)
        if result["outcome"] not in ("APPLIED", "IDEMPOTENT_NO_OP"):
            raise ValueError(f"Replay stopped at event {event.get('eventId')}: {result['outcome']}")
        state = result["state"]
        records.append(result["transitionRecord"])
        effect_intents.extend(result["effectIntents"])
    return {"state": state, "transitionRecords": records, "effectIntents": effect_intents}
