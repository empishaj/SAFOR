import ast
import copy
import json
import unittest
from pathlib import Path

from runtime.deterministic_control import initialize_state_hash, reduce, replay

ROOT = Path(__file__).resolve().parents[1]


def load_models():
    return {
        "modelRevision": "0.11.0-rc.1",
        "transitionRegistry": json.loads((ROOT / "v0.11.0/transition-registry.json").read_text(encoding="utf-8")),
        "predicateRegistry": json.loads((ROOT / "v0.11.0/predicate-registry.json").read_text(encoding="utf-8")),
    }


def base_snapshot():
    snapshot = {
        "format": "SAFOR_STATE_SNAPSHOT",
        "schemaVersion": "0.11.0",
        "projectId": "P-001",
        "modelRevision": "0.11.0-rc.1",
        "lastAppliedEventSequence": 0,
        "lastAppliedEventId": "GENESIS",
        "processedEvents": {},
        "control": {
            "mode": "EXECUTING",
            "status": "RUNNING",
            "stateRevision": 7,
            "resumeMode": None,
            "mandates": [
                {
                    "mandateId": "M-1",
                    "type": "EXECUTION",
                    "active": True,
                    "scope": {
                        "workItemIds": ["WI-IMPL"],
                        "capabilities": ["code_contribution"],
                        "objectRefs": []
                    },
                    "decisionRef": "D-1",
                    "issuedAt": "2026-10-17T00:00:00Z",
                    "revokedAt": None
                }
            ]
        },
        "valueStream": {
            "revision": 12,
            "objects": [
                {"id": "design", "type": "SOLUTION_DESIGN", "status": "AVAILABLE", "artifactRef": "repo://design@abc"}
            ],
            "workItems": [
                {"id": "WI-DESIGN", "status": "ACCEPTED"},
                {
                    "id": "WI-IMPL",
                    "status": "PLANNED",
                    "requiredCapabilities": ["code_contribution"],
                    "inputs": [{"ref": "design", "expectedType": "SOLUTION_DESIGN"}],
                    "dependencies": ["WI-DESIGN"],
                    "execution": {
                        "readySince": None,
                        "resourceAccess": {
                            "readSet": [{"repository": "org/repo", "path": "design.md", "immutableRevision": "abc"}],
                            "writeSet": [{"repository": "org/repo", "path": "src/", "conflictDomain": "src"}],
                            "exclusiveKeys": []
                        }
                    }
                }
            ]
        },
        "execution": {"revision": 4},
        "stateHash": "",
        "genesisRef": "MIGRATION-GENESIS-001"
    }
    return initialize_state_hash(snapshot)


def event(event_id, sequence, event_type, subject_type="PROJECT", subject_ref="P-001", payload=None, occurred_at=None):
    return {
        "format": "SAFOR_EVENT",
        "schemaVersion": "0.11.0",
        "eventId": event_id,
        "sequence": sequence,
        "eventType": event_type,
        "occurredAt": occurred_at or f"2026-10-17T00:00:{sequence:02d}Z",
        "source": {"type": "HUMAN" if "REQUESTED" in event_type else "KERNEL", "actorId": "human" if "REQUESTED" in event_type else "kernel"},
        "subject": {"type": subject_type, "ref": subject_ref},
        "correlationId": "P-001",
        "causationId": None,
        "payload": payload or {},
        "evidenceRefs": []
    }


class DeterministicControlTests(unittest.TestCase):
    def setUp(self):
        self.models = load_models()

    def test_same_inputs_produce_same_hash(self):
        s = base_snapshot()
        e = event("E-1", 1, "WORK_ITEM_READINESS_REEVALUATION_REQUESTED", "WORK_ITEM", "WI-IMPL")
        a = reduce(copy.deepcopy(s), copy.deepcopy(e), copy.deepcopy(self.models))
        b = reduce(copy.deepcopy(s), copy.deepcopy(e), copy.deepcopy(self.models))
        self.assertEqual("APPLIED", a["outcome"])
        self.assertEqual(a["state"]["stateHash"], b["state"]["stateHash"])
        self.assertEqual(a["transitionRecord"]["transitionRecordId"], b["transitionRecord"]["transitionRecordId"])

    def test_planned_work_becomes_ready_only_when_guards_pass(self):
        s = base_snapshot()
        e = event("E-1", 1, "WORK_ITEM_READINESS_REEVALUATION_REQUESTED", "WORK_ITEM", "WI-IMPL")
        result = reduce(s, e, self.models)
        self.assertEqual("APPLIED", result["outcome"])
        self.assertEqual("WORK_ITEM_BECOMES_READY", result["transitionRecord"]["transitionId"])
        item = next(x for x in result["state"]["valueStream"]["workItems"] if x["id"] == "WI-IMPL")
        self.assertEqual("READY", item["status"])
        self.assertEqual(e["occurredAt"], item["execution"]["readySince"])
        self.assertEqual(13, result["state"]["valueStream"]["revision"])

    def test_missing_mandate_blocks_ready_transition(self):
        s = base_snapshot()
        s["control"]["mandates"] = []
        s = initialize_state_hash(s)
        e = event("E-1", 1, "WORK_ITEM_READINESS_REEVALUATION_REQUESTED", "WORK_ITEM", "WI-IMPL")
        result = reduce(s, e, self.models)
        self.assertEqual("NO_TRANSITION", result["outcome"])
        item = next(x for x in result["state"]["valueStream"]["workItems"] if x["id"] == "WI-IMPL")
        self.assertEqual("PLANNED", item["status"])

    def test_duplicate_event_is_idempotent(self):
        s = base_snapshot()
        e = event("E-1", 1, "WORK_ITEM_READINESS_REEVALUATION_REQUESTED", "WORK_ITEM", "WI-IMPL")
        first = reduce(s, e, self.models)
        second = reduce(first["state"], copy.deepcopy(e), self.models)
        self.assertEqual("IDEMPOTENT_NO_OP", second["outcome"])
        self.assertEqual(first["state"]["stateHash"], second["state"]["stateHash"])

    def test_divergent_duplicate_event_is_integrity_failure(self):
        s = base_snapshot()
        e = event("E-1", 1, "WORK_ITEM_READINESS_REEVALUATION_REQUESTED", "WORK_ITEM", "WI-IMPL")
        first = reduce(s, e, self.models)
        divergent = copy.deepcopy(e)
        divergent["payload"] = {"changed": True}
        second = reduce(first["state"], divergent, self.models)
        self.assertEqual("INTEGRITY_FAILURE", second["outcome"])
        self.assertEqual(first["state"]["stateHash"], second["state"]["stateHash"])

    def test_out_of_order_event_fails_closed(self):
        s = base_snapshot()
        e = event("E-2", 2, "PAUSE_PROJECT_REQUESTED")
        result = reduce(s, e, self.models)
        self.assertEqual("CONTROL_FAILURE", result["outcome"])

    def test_state_hash_tamper_is_integrity_failure(self):
        s = base_snapshot()
        s["control"]["mode"] = "PLANNING"
        e = event("E-1", 1, "PAUSE_PROJECT_REQUESTED")
        result = reduce(s, e, self.models)
        self.assertEqual("INTEGRITY_FAILURE", result["outcome"])

    def test_pause_and_resume_preserve_resume_mode(self):
        s = base_snapshot()
        pause = event("E-1", 1, "PAUSE_PROJECT_REQUESTED")
        paused = reduce(s, pause, self.models)
        self.assertEqual("APPLIED", paused["outcome"])
        self.assertEqual("PAUSED", paused["state"]["control"]["mode"])
        self.assertEqual("EXECUTING", paused["state"]["control"]["resumeMode"])
        self.assertEqual("WAITING_HUMAN", paused["state"]["control"]["status"])

        resume = event("E-2", 2, "RESUME_PROJECT_REQUESTED")
        resumed = reduce(paused["state"], resume, self.models)
        self.assertEqual("APPLIED", resumed["outcome"])
        self.assertEqual("EXECUTING", resumed["state"]["control"]["mode"])
        self.assertIsNone(resumed["state"]["control"]["resumeMode"])
        self.assertEqual("READY", resumed["state"]["control"]["status"])

    def test_stop_revokes_mandates_and_resume_requires_authorization(self):
        s = base_snapshot()
        stop = event("E-1", 1, "STOP_PROJECT_REQUESTED", occurred_at="2026-10-17T01:00:00Z")
        stopped = reduce(s, stop, self.models)
        self.assertEqual("APPLIED", stopped["outcome"])
        self.assertEqual("STOPPED", stopped["state"]["control"]["mode"])
        mandate = stopped["state"]["control"]["mandates"][0]
        self.assertFalse(mandate["active"])
        self.assertEqual(stop["occurredAt"], mandate["revokedAt"])

        resume = event("E-2", 2, "RESUME_PROJECT_REQUESTED")
        resumed = reduce(stopped["state"], resume, self.models)
        self.assertEqual("APPLIED", resumed["outcome"])
        self.assertEqual("AWAITING_AUTHORIZATION", resumed["state"]["control"]["mode"])
        self.assertFalse(any(m["active"] for m in resumed["state"]["control"]["mandates"]))

    def test_unknown_external_mutation_requires_reconciliation_and_readback(self):
        s = base_snapshot()
        e = event("E-1", 1, "EXTERNAL_MUTATION_OUTCOME_UNKNOWN", subject_type="PROJECT", payload={"effectIntentId": "EFF-X"})
        result = reduce(s, e, self.models)
        self.assertEqual("APPLIED", result["outcome"])
        self.assertEqual("RECOVERING", result["state"]["control"]["mode"])
        self.assertEqual("RECONCILE_REQUIRED", result["state"]["control"]["status"])
        self.assertEqual(1, len(result["effectIntents"]))
        self.assertEqual("PROVIDER_READBACK", result["effectIntents"][0]["effectType"])

    def test_replay_matches_sequential_reduction(self):
        genesis = base_snapshot()
        events = [
            event("E-1", 1, "PAUSE_PROJECT_REQUESTED"),
            event("E-2", 2, "RESUME_PROJECT_REQUESTED")
        ]
        first = reduce(genesis, events[0], self.models)
        second = reduce(first["state"], events[1], self.models)
        replayed = replay(genesis, events, self.models)
        self.assertEqual(second["state"]["stateHash"], replayed["state"]["stateHash"])
        self.assertEqual(second["state"], replayed["state"])

    def test_ambiguous_transition_fails_closed(self):
        models = copy.deepcopy(self.models)
        duplicate = copy.deepcopy(models["transitionRegistry"]["transitions"][0])
        duplicate["transitionId"] = "WORK_ITEM_BECOMES_READY_DUPLICATE"
        models["transitionRegistry"]["transitions"].append(duplicate)
        s = base_snapshot()
        e = event("E-1", 1, "WORK_ITEM_READINESS_REEVALUATION_REQUESTED", "WORK_ITEM", "WI-IMPL")
        result = reduce(s, e, models)
        self.assertEqual("CONTROL_FAILURE", result["outcome"])
        self.assertEqual("AMBIGUOUS_TRANSITION", result["transitionRecord"]["transitionId"])

    def test_transition_registry_contains_no_arbitrary_code_fields(self):
        registry = self.models["transitionRegistry"]
        forbidden = {"code", "script", "javascript", "python", "command", "eval", "exec"}

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(key.lower(), forbidden)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(registry)

    def test_reference_reducer_imports_no_external_execution_facility(self):
        source = (ROOT / "runtime/deterministic_control.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertTrue(imports.issubset({"__future__", "copy", "hashlib", "json", "typing"}))
        for forbidden in ("requests.", "subprocess.", "socket.", "random.", "datetime.now", "time.time", "eval(", "exec("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
