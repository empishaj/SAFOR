import ast
import copy
import json
import unittest
from pathlib import Path

from runtime.deterministic_control import acceptance_contract_hash, initialize_state_hash, reduce, replay

ROOT = Path(__file__).resolve().parents[1]


def load_models():
    return {
        "modelRevision": "0.11.0-rc.2",
        "transitionRegistry": json.loads((ROOT / "v0.11.0/transition-registry.json").read_text(encoding="utf-8")),
        "predicateRegistry": json.loads((ROOT / "v0.11.0/predicate-registry.json").read_text(encoding="utf-8")),
    }


def base_snapshot():
    snapshot = {
        "format": "SAFOR_STATE_SNAPSHOT",
        "schemaVersion": "0.11.0",
        "projectId": "P-001",
        "modelRevision": "0.11.0-rc.2",
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
                    "authorityRequirements": ["quality_risk_decision"],
                    "inputs": [{"ref": "design", "expectedType": "SOLUTION_DESIGN"}],
                    "acceptanceCriteria": [
                        "Implementation artifact exists and is provider-pinned.",
                        "Independent technical review approves the contribution.",
                        "Required risk authority approves acceptance."
                    ],
                    "dependencies": ["WI-DESIGN"],
                    "assignment": {
                        "performerActorId": "dev-1",
                        "reviewerActorIds": ["reviewer-1"]
                    },
                    "review": {
                        "required": True,
                        "independencePolicy": "PERFORMER_MUST_DIFFER_FROM_APPROVING_REVIEWER",
                        "status": "NOT_STARTED",
                        "evidenceRefs": []
                    },
                    "evidenceRequirements": [
                        "CONTRIBUTION_REFERENCE",
                        "INDEPENDENT_TECHNICAL_REVIEW_WHEN_REQUIRED"
                    ],
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
        "acceptance": {
            "revision": 0,
            "contracts": [],
            "evidenceRecords": [],
            "reviewDecisions": [],
            "authorityDecisions": []
        },
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


def acceptance_contract():
    contract = {
        "format": "SAFOR_ACCEPTANCE_CONTRACT",
        "schemaVersion": "0.11.0",
        "contractId": "AC-WI-IMPL-1",
        "projectId": "P-001",
        "workItemId": "WI-IMPL",
        "revision": 1,
        "status": "ACTIVE",
        "source": {
            "planRef": "plan@sha256:abc",
            "factoryRef": "safor.factory.software-delivery@1.4.0",
            "workItemRef": "WI-IMPL@rev1",
            "approvalDecisionRef": "DEC-PLAN-1"
        },
        "criteria": [
            {
                "criterionId": "C-1",
                "description": "Implementation artifact exists and is provider-pinned.",
                "satisfactionMode": "ALL",
                "requirementRefs": ["R-EVIDENCE"]
            },
            {
                "criterionId": "C-2",
                "description": "Independent technical review approves the contribution.",
                "satisfactionMode": "ALL",
                "requirementRefs": ["R-REVIEW"]
            },
            {
                "criterionId": "C-3",
                "description": "Required risk authority approves acceptance.",
                "satisfactionMode": "ALL",
                "requirementRefs": ["R-AUTH"]
            }
        ],
        "requirements": [
            {
                "requirementId": "R-EVIDENCE",
                "type": "EVIDENCE",
                "sourceRequirement": "CONTRIBUTION_REFERENCE",
                "evidenceType": "CONTRIBUTION_REFERENCE",
                "requiredIntegrity": "PINNED"
            },
            {
                "requirementId": "R-REVIEW",
                "type": "REVIEW",
                "sourceRequirement": "INDEPENDENT_TECHNICAL_REVIEW_WHEN_REQUIRED",
                "capability": "technical_review",
                "requiredDecision": "PASS",
                "independencePolicy": "PERFORMER_MUST_DIFFER_FROM_APPROVING_REVIEWER"
            },
            {
                "requirementId": "R-AUTH",
                "type": "AUTHORITY",
                "sourceRequirement": "quality_risk_decision",
                "authorityId": "quality_risk_decision",
                "requiredDecision": "APPROVED"
            }
        ],
        "policy": {
            "allCriteriaRequired": True,
            "selfAcceptanceForbidden": True,
            "immutableAfterApproval": True,
            "noAssistantClaimAsEvidence": True,
            "noDeliveryAsOutcomeEvidence": True
        },
        "contractHash": ""
    }
    contract["contractHash"] = acceptance_contract_hash(contract)
    return contract


def evidence_record(evidence_id="EV-1", source="GITHUB_PROVIDER_READBACK", revision_ref="commit:abc"):
    return {
        "format": "SAFOR_EVIDENCE_RECORD",
        "schemaVersion": "0.10.0",
        "evidenceId": evidence_id,
        "evidenceType": "CONTRIBUTION_REFERENCE",
        "subjectRef": "WI-IMPL",
        "source": source,
        "observedAt": "2026-10-17T02:00:00Z",
        "reference": "repo://org/repo/commit/abc",
        "integrity": {"stableId": "org/repo", "revisionRef": revision_ref},
        "claims": ["Contribution exists at pinned revision."]
    }


def review_record(review_id="REV-1", reviewer="reviewer-1", performer="dev-1", decision="PASS"):
    return {
        "format": "SAFOR_REVIEW_DECISION",
        "schemaVersion": "0.11.0",
        "reviewId": review_id,
        "workItemId": "WI-IMPL",
        "reviewerActorId": reviewer,
        "performerActorId": performer,
        "capability": "technical_review",
        "independencePolicy": "PERFORMER_MUST_DIFFER_FROM_APPROVING_REVIEWER",
        "decision": decision,
        "evidenceRef": f"review://{review_id}",
        "observedAt": "2026-10-17T02:01:00Z",
        "sourceRevisionRef": "review-commit:123"
    }


def authority_record(decision_id="AUTH-1", decision="APPROVED"):
    return {
        "format": "SAFOR_AUTHORITY_DECISION",
        "schemaVersion": "0.11.0",
        "decisionId": decision_id,
        "workItemId": "WI-IMPL",
        "authorityId": "quality_risk_decision",
        "actorId": "qa-owner",
        "decision": decision,
        "decisionRef": f"decision://{decision_id}",
        "observedAt": "2026-10-17T02:02:00Z",
        "sourceRevisionRef": "decision-commit:456"
    }


def acceptance_snapshot():
    snapshot = base_snapshot()
    item = next(x for x in snapshot["valueStream"]["workItems"] if x["id"] == "WI-IMPL")
    item["status"] = "HANDOFF_READY"
    item["review"]["status"] = "NOT_STARTED"
    return initialize_state_hash(snapshot)


def acceptance_events(include_evidence=True, include_review=True, include_authority=True, authority_decision="APPROVED"):
    events = []
    seq = 1
    events.append(event("E-CONTRACT", seq, "ACCEPTANCE_CONTRACT_REGISTERED", "WORK_ITEM", "WI-IMPL", {"contract": acceptance_contract()}))
    seq += 1
    if include_evidence:
        events.append(event("E-EVIDENCE", seq, "EVIDENCE_RECORDED", "WORK_ITEM", "WI-IMPL", {"record": evidence_record()}))
        seq += 1
    if include_review:
        events.append(event("E-REVIEW", seq, "REVIEW_APPROVED_RECORDED", "WORK_ITEM", "WI-IMPL", {"record": review_record()}))
        seq += 1
    if include_authority:
        event_type = "AUTHORITY_APPROVED_RECORDED" if authority_decision == "APPROVED" else "AUTHORITY_REJECTED_RECORDED"
        events.append(event("E-AUTH", seq, event_type, "WORK_ITEM", "WI-IMPL", {"record": authority_record(decision=authority_decision)}))
        seq += 1
    events.append(event("E-ACCEPT", seq, "ACCEPTANCE_REEVALUATION_REQUESTED", "WORK_ITEM", "WI-IMPL"))
    return events


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


    def test_full_acceptance_path_reaches_accepted(self):
        state = acceptance_snapshot()
        results = []
        for e in acceptance_events():
            result = reduce(state, e, self.models)
            results.append(result)
            self.assertEqual("APPLIED", result["outcome"])
            state = result["state"]
        item = next(x for x in state["valueStream"]["workItems"] if x["id"] == "WI-IMPL")
        self.assertEqual("ACCEPTED", item["status"])
        self.assertEqual("APPROVED", item["review"]["status"])
        self.assertEqual("WORK_ITEM_ACCEPTED", results[-1]["transitionRecord"]["transitionId"])

    def test_missing_evidence_blocks_acceptance(self):
        state = acceptance_snapshot()
        events = acceptance_events(include_evidence=False)
        for e in events[:-1]:
            result = reduce(state, e, self.models)
            self.assertEqual("APPLIED", result["outcome"])
            state = result["state"]
        blocked = reduce(state, events[-1], self.models)
        self.assertEqual("NO_TRANSITION", blocked["outcome"])
        item = next(x for x in blocked["state"]["valueStream"]["workItems"] if x["id"] == "WI-IMPL")
        self.assertNotEqual("ACCEPTED", item["status"])

    def test_self_review_cannot_be_recorded_as_approved(self):
        state = acceptance_snapshot()
        contract_event = event("E-CONTRACT", 1, "ACCEPTANCE_CONTRACT_REGISTERED", "WORK_ITEM", "WI-IMPL", {"contract": acceptance_contract()})
        registered = reduce(state, contract_event, self.models)
        self.assertEqual("APPLIED", registered["outcome"])
        self_review = event(
            "E-SELF-REVIEW", 2, "REVIEW_APPROVED_RECORDED", "WORK_ITEM", "WI-IMPL",
            {"record": review_record(review_id="REV-SELF", reviewer="dev-1", performer="dev-1")}
        )
        rejected = reduce(registered["state"], self_review, self.models)
        self.assertEqual("NO_TRANSITION", rejected["outcome"])
        self.assertEqual([], rejected["state"]["acceptance"]["reviewDecisions"])

    def test_review_changes_required_routes_to_rework(self):
        state = acceptance_snapshot()
        registered = reduce(
            state,
            event("E-CONTRACT", 1, "ACCEPTANCE_CONTRACT_REGISTERED", "WORK_ITEM", "WI-IMPL", {"contract": acceptance_contract()}),
            self.models
        )
        change = reduce(
            registered["state"],
            event(
                "E-REVIEW-CHANGE", 2, "REVIEW_CHANGES_REQUIRED_RECORDED", "WORK_ITEM", "WI-IMPL",
                {"record": review_record(review_id="REV-CHG", decision="CHANGES_REQUIRED")}
            ),
            self.models
        )
        self.assertEqual("APPLIED", change["outcome"])
        item = next(x for x in change["state"]["valueStream"]["workItems"] if x["id"] == "WI-IMPL")
        self.assertEqual("CHANGES_REQUIRED", item["status"])
        self.assertEqual("CHANGES_REQUIRED", item["review"]["status"])

    def test_missing_authority_blocks_acceptance(self):
        state = acceptance_snapshot()
        events = acceptance_events(include_authority=False)
        for e in events[:-1]:
            result = reduce(state, e, self.models)
            self.assertEqual("APPLIED", result["outcome"])
            state = result["state"]
        blocked = reduce(state, events[-1], self.models)
        self.assertEqual("NO_TRANSITION", blocked["outcome"])

    def test_rejected_authority_blocks_acceptance(self):
        state = acceptance_snapshot()
        events = acceptance_events(authority_decision="REJECTED")
        for e in events[:-1]:
            result = reduce(state, e, self.models)
            self.assertEqual("APPLIED", result["outcome"])
            state = result["state"]
        blocked = reduce(state, events[-1], self.models)
        self.assertEqual("NO_TRANSITION", blocked["outcome"])

    def test_contract_hash_tampering_fails_closed(self):
        state = acceptance_snapshot()
        contract = acceptance_contract()
        contract["criteria"][0]["description"] = "Tampered after approval"
        result = reduce(
            state,
            event("E-CONTRACT", 1, "ACCEPTANCE_CONTRACT_REGISTERED", "WORK_ITEM", "WI-IMPL", {"contract": contract}),
            self.models
        )
        self.assertEqual("NO_TRANSITION", result["outcome"])
        self.assertEqual([], result["state"]["acceptance"]["contracts"])

    def test_duplicate_evidence_record_id_under_new_event_is_rejected(self):
        state = acceptance_snapshot()
        contract = reduce(
            state,
            event("E-CONTRACT", 1, "ACCEPTANCE_CONTRACT_REGISTERED", "WORK_ITEM", "WI-IMPL", {"contract": acceptance_contract()}),
            self.models
        )
        first = reduce(
            contract["state"],
            event("E-EVIDENCE-1", 2, "EVIDENCE_RECORDED", "WORK_ITEM", "WI-IMPL", {"record": evidence_record("EV-DUP")}),
            self.models
        )
        duplicate = reduce(
            first["state"],
            event("E-EVIDENCE-2", 3, "EVIDENCE_RECORDED", "WORK_ITEM", "WI-IMPL", {"record": evidence_record("EV-DUP")}),
            self.models
        )
        self.assertEqual("NO_TRANSITION", duplicate["outcome"])
        self.assertEqual(1, len(duplicate["state"]["acceptance"]["evidenceRecords"]))

    def test_assistant_claim_does_not_enter_acceptance_ledger(self):
        state = acceptance_snapshot()
        bad = event(
            "E-BAD-EVIDENCE", 1, "EVIDENCE_RECORDED", "WORK_ITEM", "WI-IMPL",
            {"record": evidence_record("EV-BAD", source="ASSISTANT_CLAIM")}
        )
        result = reduce(state, bad, self.models)
        self.assertEqual("NO_TRANSITION", result["outcome"])
        self.assertEqual([], result["state"]["acceptance"]["evidenceRecords"])

    def test_qualitative_criterion_without_typed_requirement_is_rejected(self):
        state = acceptance_snapshot()
        contract = acceptance_contract()
        contract["criteria"][1]["requirementRefs"] = []
        contract["contractHash"] = acceptance_contract_hash(contract)
        result = reduce(
            state,
            event("E-CONTRACT", 1, "ACCEPTANCE_CONTRACT_REGISTERED", "WORK_ITEM", "WI-IMPL", {"contract": contract}),
            self.models
        )
        self.assertEqual("NO_TRANSITION", result["outcome"])

    def test_acceptance_replay_matches_sequential_reduction(self):
        genesis = acceptance_snapshot()
        events = acceptance_events()
        state = genesis
        for e in events:
            result = reduce(state, e, self.models)
            self.assertEqual("APPLIED", result["outcome"])
            state = result["state"]
        replayed = replay(genesis, events, self.models)
        self.assertEqual(state["stateHash"], replayed["state"]["stateHash"])
        self.assertEqual(state, replayed["state"])

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
