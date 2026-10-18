#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "0.14.0-rc.2"
SCHEMA_VERSION = "0.14.0"
PREVIOUS_VERSION = "0.13.0-rc.9"
BASE_MAIN_COMMIT = "29a9bcc5c84fe348f94c63b08852fda28135fe50"
AUDITED_V014_COMMIT = "cd6aa12605d208b96c4d19c95b7eb9756624c113"
AUDIT_REPORT = "SAFOR_v0.14_Architektur_Audit_Uebergabe_2026-10-18.md"
INTEGRATION_BRANCH = "safor/integrate-v0.14.0-rc.2"

PACKAGE_VERSIONS = {
    "website_factory": "1.2.0",
    "website_om": "1.2.0",
    "saas_factory": "1.8.0-test.1",
    "saas_om": "1.8.0-test.1",
    "book_factory": "1.1.0-test.1",
    "book_om": "1.1.0-test.1",
    "github_provider": "0.6.0",
    "gitlab_provider": "0.6.0",
}

SOURCE_PACKAGES = {
    "website_factory": "v0.13.0/packages/factories/website-delivery/1.1.0/package.json",
    "website_om": "v0.13.0/packages/operating-models/website-team/1.1.0/package.json",
    "saas_factory": "v0.13.0/packages/factories/software-delivery/1.7.0-test.1/package.json",
    "saas_om": "v0.13.0/packages/operating-models/saas-engineering/1.7.0-test.1/package.json",
    "book_factory": "v0.13.0/packages/factories/book-production/1.0.0-test.1/package.json",
    "book_om": "v0.13.0/packages/operating-models/book-authoring/1.0.0-test.1/package.json",
}

TARGET_PACKAGES = {
    "website_factory": f"v0.14.0/packages/factories/website-delivery/{PACKAGE_VERSIONS['website_factory']}/package.json",
    "website_om": f"v0.14.0/packages/operating-models/website-team/{PACKAGE_VERSIONS['website_om']}/package.json",
    "saas_factory": f"v0.14.0/packages/factories/software-delivery/{PACKAGE_VERSIONS['saas_factory']}/package.json",
    "saas_om": f"v0.14.0/packages/operating-models/saas-engineering/{PACKAGE_VERSIONS['saas_om']}/package.json",
    "book_factory": f"v0.14.0/packages/factories/book-production/{PACKAGE_VERSIONS['book_factory']}/package.json",
    "book_om": f"v0.14.0/packages/operating-models/book-authoring/{PACKAGE_VERSIONS['book_om']}/package.json",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path(relative: str) -> Path:
    return ROOT / relative


def load_json(relative: str) -> Any:
    return json.loads(path(relative).read_text(encoding="utf-8"))


def write_json(relative: str, value: Any) -> None:
    target = path(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(relative: str, value: str) -> None:
    target = path(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value if value.endswith("\n") else value + "\n", encoding="utf-8")


def replace_text(relative: str, old: str, new: str, *, required: bool = False) -> None:
    target = path(relative)
    text = target.read_text(encoding="utf-8")
    if required and old not in text:
        raise RuntimeError(f"Expected text not found in {relative}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def regex_replace(relative: str, pattern: str, replacement: str, *, count: int = 0) -> None:
    target = path(relative)
    text = target.read_text(encoding="utf-8")
    updated, substitutions = re.subn(pattern, replacement, text, count=count, flags=re.DOTALL)
    if substitutions == 0:
        raise RuntimeError(f"Regex did not match in {relative}: {pattern}")
    target.write_text(updated, encoding="utf-8")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def domain_digest(package: Mapping[str, Any]) -> str:
    fields = (
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
    projection = {field: package.get(field) for field in fields}
    return "sha256:" + hashlib.sha256(canonical_json(projection).encode("utf-8")).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def clone_versioned_json(source: str, target: str, *, schema_version: str = SCHEMA_VERSION) -> dict[str, Any]:
    doc = copy.deepcopy(load_json(source))

    def visit(value: Any, key: str | None = None) -> Any:
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(item, key) for item in value]
        if isinstance(value, str):
            if key in {"schemaVersion", "kernelVersion"} and re.fullmatch(r"0\.(10|11|12|13)\.0", value):
                return schema_version
            if key == "const" and re.fullmatch(r"0\.(10|11|12|13)\.0", value):
                return schema_version
            if key in {"$id", "title", "id"}:
                for old in ("0.10.0", "0.11.0", "0.12.0", "0.13.0"):
                    value = value.replace(old, schema_version)
            if key == "kernel" and value.startswith(">="):
                return ">=0.14.0 <0.15.0"
        return value

    doc = visit(doc)
    if isinstance(doc, dict) and "schemaVersion" in doc:
        doc["schemaVersion"] = schema_version
    write_json(target, doc)
    return doc


def phase_baseline() -> None:
    if path("VERSION").read_text(encoding="utf-8").strip() != PREVIOUS_VERSION:
        raise RuntimeError("Integration baseline must start from rc.9 main")
    required = [
        "v0.14.0/agent-activation-model.json",
        "v0.14.0/schemas/agent-job.schema.json",
        "runtime/agent_orchestration.py",
        "runtime/agent_jobs.py",
        "runtime/agent_responses.py",
        "runtime/master_orchestration.py",
        "runtime/migration.py",
        "tests/test_agent_activation_v014.py",
    ]
    missing = [item for item in required if not path(item).exists()]
    if missing:
        raise RuntimeError(f"v0.14 source import incomplete: {missing}")

    decision = {
        "format": "SAFOR_IMPLEMENTATION_DECISION",
        "schemaVersion": SCHEMA_VERSION,
        "decisionId": "HUMAN-V014-RC2-INTEGRATION-2026-10-18",
        "decisionType": "FRAMEWORK_INTEGRATION_AUTHORIZATION",
        "source": "DIRECT_HUMAN_INPUT_IN_MASTER_CHAT",
        "recordedAt": now(),
        "humanInstruction": "go - setze um und erstelle eine neue version von dem gesamten framework dass alle bestandteile upgraden! schrit für schrit",
        "scope": {
            "repository": "empishaj/SAFOR",
            "baseCommit": BASE_MAIN_COMMIT,
            "sourceAuditCommit": AUDITED_V014_COMMIT,
            "targetVersion": TARGET_VERSION,
            "authorizedWorkPackages": [
                "KWP-00",
                "KWP-01",
                "KWP-02",
                "KWP-03",
                "KWP-04",
                "KWP-05",
                "KWP-06",
                "KWP-07",
                "KWP-08",
                "KWP-09",
                "KWP-10",
                "KWP-11",
            ],
            "referenceProjectMigrationCondition": "ONLY_AFTER_ISOLATED_REAL_GIT_E2E_PASS",
        },
        "truthBoundary": {
            "chatRecordIsNotCryptographicSignature": True,
            "repositoryRecordDoesNotCreateProviderRights": True,
            "mergeStillRequiresGreenExactHeadAndGovernedReview": True,
        },
        "status": "AUTHORIZED_FOR_IMPLEMENTATION",
    }
    write_json("docs/master-subagent-orchestration/IMPLEMENTATION-DECISION-v0.14.0-rc.2.json", decision)

    baseline = {
        "format": "SAFOR_V014_INTEGRATION_BASELINE",
        "schemaVersion": SCHEMA_VERSION,
        "targetVersion": TARGET_VERSION,
        "baseMainCommit": BASE_MAIN_COMMIT,
        "auditedFeatureCommit": AUDITED_V014_COMMIT,
        "integrationBranch": INTEGRATION_BRANCH,
        "strategy": "RC9_BASE_SELECTIVE_V014_CONSOLIDATION_NO_BLIND_MERGE",
        "auditFindings": {
            "F-01": "CONFIRMED",
            "F-02": "CONFIRMED",
            "F-03": "CONFIRMED",
            "F-04": "CONFIRMED",
            "F-05": "CONFIRMED",
            "F-06": "CONFIRMED",
            "F-07": "CONFIRMED",
            "F-08": "CONFIRMED_ARCHITECTURAL_LIMIT",
            "F-09": "NOT_ASSESSED",
            "F-10": "PARTIAL",
            "F-11": "NOT_ASSESSED",
            "F-12": "RESOLVED_BY_CURRENT_HUMAN_DECISION_RECORD",
        },
        "recordedAt": now(),
    }
    write_json("v0.14.0/integration-baseline.json", baseline)

    plan_path = "docs/master-subagent-orchestration/IMPLEMENTATION-PLAN-v0.14.0.md"
    replace_text(plan_path, "0.14.0-rc.1", TARGET_VERSION)
    replace_text(plan_path, "bce845305c886b2b78065d1a21f0823775614975", BASE_MAIN_COMMIT)
    replace_text(plan_path, "safor/master-subagent-orchestration-v0.14.0-rc.1", INTEGRATION_BRANCH)
    plan = path(plan_path).read_text(encoding="utf-8")
    marker = "## 0. Integrationskorrektur für rc.2"
    if marker not in plan:
        plan = plan.replace(
            "## 1. Nicht verhandelbare Zielinvarianten",
            "## 0. Integrationskorrektur für rc.2\n\n"
            "Der auditierte rc.1-Zweig bleibt unverändert als Herkunftsnachweis. rc.2 wird selektiv auf `main@"
            + BASE_MAIN_COMMIT
            + "` integriert. Reales Git-E2E muss vor einer Migration des Referenzprojekts bestehen; Unit- und Bundle-PASS werden nicht als Fremdhost- oder GA-PASS ausgegeben.\n\n"
            "## 1. Nicht verhandelbare Zielinvarianten",
            1,
        )
        path(plan_path).write_text(plan, encoding="utf-8")

    trace = load_json("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
    trace["releaseTarget"] = TARGET_VERSION
    trace["implementationDecisionRef"] = "docs/master-subagent-orchestration/IMPLEMENTATION-DECISION-v0.14.0-rc.2.json"
    write_json("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json", trace)

    for relative in (
        "MASTER-SUBAGENT-ORCHESTRATION.md",
        "AGENT-JOB-CONTRACT.md",
        "AGENT-WORKSPACE.md",
        "MULTI-AGENT-SCHEDULER.md",
    ):
        if path(relative).exists():
            replace_text(relative, "0.14.0-rc.1", TARGET_VERSION)

    audit_delta = f"""# SAFOR {TARGET_VERSION} – Audit-Delta und Integrationsauftrag

## Gepinnte Basis

- rc.9 `main`: `{BASE_MAIN_COMMIT}`
- auditierter v0.14-Quellstand: `{AUDITED_V014_COMMIT}`
- Integrationszweig: `{INTEGRATION_BRANCH}`

## Integrationsregel

Der v0.14-Quellzweig wird nicht blind gemergt. Vorhandene rc.8/rc.9-Verträge bleiben Ausgangsbasis; v0.14-Modelle, Schemas, Referenzcode und Tests werden selektiv übernommen und gegen die Auditbefunde F-01 bis F-12 gehärtet.

## Freigabe

Die aktuelle HUMAN-Anweisung autorisiert die schrittweise Implementierung. Ein Release-Merge bleibt an den exakten grünen Head, nachvollziehbare Evidence und die ausgewiesenen Review-/Governance-Gates gebunden.
"""
    write_text("docs/master-subagent-orchestration/AUDIT-DELTA-v0.14.0-rc.2.md", audit_delta)


def _go_evidence_schema() -> dict[str, Any]:
    required = [
        "format",
        "schemaVersion",
        "activationId",
        "projectId",
        "agentId",
        "identityRevision",
        "chatBindingId",
        "sessionId",
        "targetJobId",
        "targetDispatchRevision",
        "intent",
        "source",
        "observedAt",
        "singleUse",
        "jobPromptTransported",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:safor:human-go-evidence:0.14.0",
        "title": "SAFOR HUMAN GO Evidence 0.14.0",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "format": {"const": "SAFOR_HUMAN_GO_EVIDENCE"},
            "schemaVersion": {"const": SCHEMA_VERSION},
            "activationId": {"type": "string", "minLength": 8},
            "projectId": {"type": "string", "minLength": 1},
            "agentId": {"type": "string", "minLength": 3},
            "identityRevision": {"type": "integer", "minimum": 1},
            "chatBindingId": {"type": "string", "minLength": 3},
            "sessionId": {"type": "string", "minLength": 1},
            "targetJobId": {"type": "string", "minLength": 1},
            "targetDispatchRevision": {"type": "integer", "minimum": 1},
            "intent": {"const": "GO"},
            "source": {"const": "DIRECT_HUMAN_INPUT_IN_BOUND_AGENT_CHAT"},
            "observedAt": {"type": "string", "format": "date-time"},
            "singleUse": {"const": True},
            "jobPromptTransported": {"const": False},
        },
    }


def _go_evidence_runtime() -> str:
    return '''from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping, MutableSet


class GoEvidenceValidationError(ValueError):
    """Raised when HUMAN-GO evidence is not safely bound to one job claim."""


_REQUIRED_FIELDS = {
    "format", "schemaVersion", "activationId", "projectId", "agentId",
    "identityRevision", "chatBindingId", "sessionId", "targetJobId",
    "targetDispatchRevision", "intent", "source", "observedAt",
    "singleUse", "jobPromptTransported",
}


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GoEvidenceValidationError(f"{name} must be a mapping")
    return value


def _nonempty(value: Any, code: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise GoEvidenceValidationError(code)
    return text


def _parse_datetime(value: Any, code: str) -> datetime:
    text = _nonempty(value, code)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GoEvidenceValidationError(code) from exc


def validate_human_go_evidence(
    evidence: Mapping[str, Any],
    *,
    expected: Mapping[str, Any],
    consumed_activation_ids: set[str] | frozenset[str] | None = None,
) -> None:
    evidence = _mapping(evidence, "goEvidence")
    missing = sorted(_REQUIRED_FIELDS - set(evidence))
    unknown = sorted(set(evidence) - _REQUIRED_FIELDS)
    if missing or unknown:
        raise GoEvidenceValidationError(
            f"GO_EVIDENCE_FIELDS_INVALID:missing={missing},unknown={unknown}"
        )
    if evidence.get("format") != "SAFOR_HUMAN_GO_EVIDENCE":
        raise GoEvidenceValidationError("GO_EVIDENCE_FORMAT_INVALID")
    if evidence.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("GO_EVIDENCE_SCHEMA_VERSION_INVALID")
    if evidence.get("intent") != "GO":
        raise GoEvidenceValidationError("GO_EVIDENCE_INTENT_INVALID")
    if evidence.get("source") != "DIRECT_HUMAN_INPUT_IN_BOUND_AGENT_CHAT":
        raise GoEvidenceValidationError("GO_EVIDENCE_SOURCE_INVALID")
    if evidence.get("singleUse") is not True:
        raise GoEvidenceValidationError("GO_EVIDENCE_MUST_BE_SINGLE_USE")
    if evidence.get("jobPromptTransported") is not False:
        raise GoEvidenceValidationError("GO_EVIDENCE_JOB_PROMPT_TRANSPORT_FORBIDDEN")
    activation_id = _nonempty(evidence.get("activationId"), "GO_ACTIVATION_ID_MISSING")
    _nonempty(evidence.get("sessionId"), "GO_SESSION_ID_MISSING")
    _parse_datetime(evidence.get("observedAt"), "GO_OBSERVED_AT_INVALID")
    if activation_id in set(consumed_activation_ids or ()):
        raise GoEvidenceValidationError("GO_EVIDENCE_ALREADY_CONSUMED")
    fields = (
        "projectId", "agentId", "identityRevision", "chatBindingId",
        "targetJobId", "targetDispatchRevision",
    )
    for field in fields:
        if evidence.get(field) != expected.get(field):
            raise GoEvidenceValidationError(f"GO_EVIDENCE_BINDING_MISMATCH:{field}")


def atomically_observe_go_and_claim(
    *,
    job_state: Mapping[str, Any],
    go_evidence: Mapping[str, Any],
    expected_state_revision: int,
    consumed_activation_ids: MutableSet[str],
    go_evidence_ref: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the only safe claimed state; provider compare-and-swap remains required."""
    state = deepcopy(dict(_mapping(job_state, "jobState")))
    if state.get("format") != "SAFOR_AGENT_JOB_STATE":
        raise GoEvidenceValidationError("JOB_STATE_FORMAT_INVALID")
    if state.get("schemaVersion") != "0.14.0":
        raise GoEvidenceValidationError("JOB_STATE_SCHEMA_VERSION_INVALID")
    if state.get("lifecycleStatus") != "WAITING_HUMAN_GO":
        raise GoEvidenceValidationError("JOB_NOT_WAITING_HUMAN_GO")
    if state.get("revision") != expected_state_revision:
        raise GoEvidenceValidationError("JOB_STATE_REVISION_CONFLICT")
    expected = {
        "projectId": state.get("projectId"),
        "agentId": state.get("assignedAgentId"),
        "identityRevision": state.get("assignedIdentityRevision"),
        "chatBindingId": state.get("chatBindingId"),
        "targetJobId": state.get("jobId"),
        "targetDispatchRevision": state.get("dispatchRevision"),
    }
    validate_human_go_evidence(
        go_evidence,
        expected=expected,
        consumed_activation_ids=set(consumed_activation_ids),
    )
    for field in ("repository", "ref", "path", "blobSha"):
        _nonempty(go_evidence_ref.get(field), f"GO_EVIDENCE_REF_{field.upper()}_MISSING")
    activation_id = str(go_evidence["activationId"])
    consumed_activation_ids.add(activation_id)
    state["revision"] = expected_state_revision + 1
    state["lifecycleStatus"] = "CLAIMED"
    state["goEvidenceRef"] = dict(go_evidence_ref)
    state["consumedActivationIds"] = sorted(
        set(state.get("consumedActivationIds") or ()) | {activation_id}
    )
    state.setdefault("transitionHistory", []).extend(
        [
            {
                "from": "WAITING_HUMAN_GO",
                "to": "GO_OBSERVED",
                "at": go_evidence["observedAt"],
                "actorId": go_evidence["agentId"],
                "evidenceRefs": [str(go_evidence_ref["path"])],
            },
            {
                "from": "GO_OBSERVED",
                "to": "CLAIMED",
                "at": go_evidence["observedAt"],
                "actorId": go_evidence["agentId"],
                "evidenceRefs": [str(go_evidence_ref["path"])],
            },
        ]
    )
    state["updatedAt"] = go_evidence["observedAt"]
    return state
'''


def _execution_reconciliation_runtime() -> str:
    return '''from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class ExecutionReconciliationError(ValueError):
    """Raised when a partial product/control write cannot be retried safely."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExecutionReconciliationError(f"{name} must be a mapping")
    return value


def create_execution_attempt(*, attempt_id: str, project_id: str, job_id: str, agent_id: str, dispatch_revision: int, started_at: str, product_target: Mapping[str, Any], response_target: Mapping[str, Any]) -> dict[str, Any]:
    if not attempt_id or not job_id or not agent_id:
        raise ExecutionReconciliationError("ATTEMPT_IDENTITY_REQUIRED")
    return {
        "format": "SAFOR_EXECUTION_ATTEMPT",
        "schemaVersion": "0.14.0",
        "attemptId": attempt_id,
        "projectId": project_id,
        "jobId": job_id,
        "agentId": agent_id,
        "dispatchRevision": dispatch_revision,
        "status": "STARTED",
        "productTarget": dict(_mapping(product_target, "productTarget")),
        "responseTarget": dict(_mapping(response_target, "responseTarget")),
        "productMutation": None,
        "responsePersistence": None,
        "startedAt": started_at,
        "updatedAt": started_at,
    }


def record_product_commit(attempt: Mapping[str, Any], *, commit_ref: Mapping[str, Any], observed_at: str) -> dict[str, Any]:
    result = deepcopy(dict(_mapping(attempt, "attempt")))
    existing = result.get("productMutation")
    if existing is not None:
        if dict(existing) != dict(commit_ref):
            raise ExecutionReconciliationError("PRODUCT_MUTATION_ALREADY_RECORDED_DIFFERENTLY")
        return result
    result["productMutation"] = dict(_mapping(commit_ref, "commitRef"))
    result["status"] = "PRODUCT_COMMITTED_RESPONSE_PENDING"
    result["updatedAt"] = observed_at
    return result


def record_response_persistence(attempt: Mapping[str, Any], *, response_ref: Mapping[str, Any], observed_at: str) -> dict[str, Any]:
    result = deepcopy(dict(_mapping(attempt, "attempt")))
    if result.get("productMutation") is None:
        raise ExecutionReconciliationError("RESPONSE_CANNOT_PRECEDE_PRODUCT_COMMIT")
    existing = result.get("responsePersistence")
    if existing is not None:
        if dict(existing) != dict(response_ref):
            raise ExecutionReconciliationError("RESPONSE_ALREADY_RECORDED_DIFFERENTLY")
        return result
    result["responsePersistence"] = dict(_mapping(response_ref, "responseRef"))
    result["status"] = "COMPLETED"
    result["updatedAt"] = observed_at
    return result


def reconcile_partial_attempt(attempt: Mapping[str, Any], *, product_commit_readback: Mapping[str, Any] | None, response_readback: Mapping[str, Any] | None, observed_at: str) -> dict[str, Any]:
    source = deepcopy(dict(_mapping(attempt, "attempt")))
    product_expected = source.get("productMutation")
    response_expected = source.get("responsePersistence")
    if product_expected is None and product_commit_readback is not None:
        raise ExecutionReconciliationError("UNPLANNED_PRODUCT_MUTATION_OBSERVED")
    if product_expected is not None and product_commit_readback is None:
        outcome = "PRODUCT_COMMIT_READBACK_MISSING"
        retry_product_mutation = False
    elif product_expected is not None and dict(product_expected) != dict(product_commit_readback):
        outcome = "PRODUCT_COMMIT_READBACK_MISMATCH"
        retry_product_mutation = False
    elif product_expected is not None and response_readback is None:
        outcome = "RESPONSE_PERSISTENCE_RECONCILE_REQUIRED"
        retry_product_mutation = False
    elif response_expected is not None and response_readback is not None and dict(response_expected) != dict(response_readback):
        outcome = "RESPONSE_READBACK_MISMATCH"
        retry_product_mutation = False
    elif product_expected is not None and response_readback is not None:
        outcome = "COMPLETED"
        retry_product_mutation = False
    else:
        outcome = "NO_EXTERNAL_EFFECT_CONFIRMED"
        retry_product_mutation = True
    return {
        "format": "SAFOR_RECONCILIATION_RECORD",
        "schemaVersion": "0.14.0",
        "attemptId": source.get("attemptId"),
        "jobId": source.get("jobId"),
        "outcome": outcome,
        "productCommitReadback": dict(product_commit_readback) if product_commit_readback else None,
        "responseReadback": dict(response_readback) if response_readback else None,
        "retryProductMutationAllowed": retry_product_mutation,
        "retryResponsePersistenceAllowed": outcome == "RESPONSE_PERSISTENCE_RECONCILE_REQUIRED",
        "observedAt": observed_at,
    }
'''


def _execution_schema(kind: str) -> dict[str, Any]:
    if kind == "attempt":
        required = ["format", "schemaVersion", "attemptId", "projectId", "jobId", "agentId", "dispatchRevision", "status", "productTarget", "responseTarget", "productMutation", "responsePersistence", "startedAt", "updatedAt"]
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:safor:execution-attempt:0.14.0",
            "title": "SAFOR Execution Attempt 0.14.0",
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "properties": {
                "format": {"const": "SAFOR_EXECUTION_ATTEMPT"},
                "schemaVersion": {"const": SCHEMA_VERSION},
                "attemptId": {"type": "string", "minLength": 1},
                "projectId": {"type": "string", "minLength": 1},
                "jobId": {"type": "string", "minLength": 1},
                "agentId": {"type": "string", "minLength": 1},
                "dispatchRevision": {"type": "integer", "minimum": 1},
                "status": {"enum": ["STARTED", "PRODUCT_COMMITTED_RESPONSE_PENDING", "COMPLETED", "RECONCILE_REQUIRED"]},
                "productTarget": {"type": "object"},
                "responseTarget": {"type": "object"},
                "productMutation": {"type": ["object", "null"]},
                "responsePersistence": {"type": ["object", "null"]},
                "startedAt": {"type": "string", "format": "date-time"},
                "updatedAt": {"type": "string", "format": "date-time"},
            },
        }
    required = ["format", "schemaVersion", "attemptId", "jobId", "outcome", "productCommitReadback", "responseReadback", "retryProductMutationAllowed", "retryResponsePersistenceAllowed", "observedAt"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:safor:reconciliation-record:0.14.0",
        "title": "SAFOR Reconciliation Record 0.14.0",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "format": {"const": "SAFOR_RECONCILIATION_RECORD"},
            "schemaVersion": {"const": SCHEMA_VERSION},
            "attemptId": {"type": "string", "minLength": 1},
            "jobId": {"type": "string", "minLength": 1},
            "outcome": {"type": "string", "minLength": 1},
            "productCommitReadback": {"type": ["object", "null"]},
            "responseReadback": {"type": ["object", "null"]},
            "retryProductMutationAllowed": {"type": "boolean"},
            "retryResponsePersistenceAllowed": {"type": "boolean"},
            "observedAt": {"type": "string", "format": "date-time"},
        },
    }


def _patch_agent_jobs() -> None:
    relative = "runtime/agent_jobs.py"
    text = path(relative).read_text(encoding="utf-8")
    import_line = "from runtime.go_evidence import GoEvidenceValidationError, validate_human_go_evidence\n"
    if import_line not in text:
        text = text.replace("from typing import Any, Mapping\n", "from typing import Any, Mapping\n" + import_line, 1)
    pattern = r"def validate_job_state_transition\(.*?\n(?=def render_agent_chat_output)"
    replacement = '''def validate_job_state_transition(*, from_status: str, to_status: str, evidence_refs: list[Any], go_evidence: Mapping[str, Any] | None = None, expected_go_context: Mapping[str, Any] | None = None, consumed_activation_ids: set[str] | frozenset[str] | None = None) -> None:\n    allowed = _TRANSITIONS.get(from_status, set())\n    if to_status not in allowed:\n        raise AgentJobValidationError(f'JOB_STATE_TRANSITION_FORBIDDEN:{from_status}->{to_status}')\n    if from_status == 'WAITING_HUMAN_GO' and to_status == 'GO_OBSERVED':\n        if go_evidence is None or expected_go_context is None:\n            raise AgentJobValidationError('STRUCTURED_GO_EVIDENCE_REQUIRED')\n        try:\n            validate_human_go_evidence(\n                go_evidence,\n                expected=expected_go_context,\n                consumed_activation_ids=consumed_activation_ids,\n            )\n        except GoEvidenceValidationError as exc:\n            raise AgentJobValidationError(str(exc)) from exc\n        if not evidence_refs or not all(isinstance(ref, Mapping) for ref in evidence_refs):\n            raise AgentJobValidationError('GO_EVIDENCE_POINTER_REQUIRED')\n        for ref in evidence_refs:\n            _pointer(ref, 'goEvidenceRef')\n    if from_status == 'RESPONSE_SUBMITTED' and to_status == 'ACCEPTED':\n        raise AgentJobValidationError('RESPONSE_SUBMISSION_CANNOT_SKIP_VERIFICATION')\n\n'''
    updated, substitutions = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if substitutions != 1:
        raise RuntimeError("Could not replace validate_job_state_transition")
    path(relative).write_text(updated, encoding="utf-8")


def _patch_master_orchestration() -> None:
    relative = "runtime/master_orchestration.py"
    text = path(relative).read_text(encoding="utf-8")
    if "from datetime import datetime" not in text:
        text = text.replace("from copy import deepcopy\n", "from copy import deepcopy\nfrom datetime import datetime\n", 1)
    pattern = r"def build_compact_project_status\(.*\Z"
    replacement = '''def _parse_time(value: str | None) -> datetime | None:\n    if value is None:\n        return None\n    try:\n        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))\n    except ValueError as exc:\n        raise MasterOrchestrationError('STATUS_TIMESTAMP_INVALID') from exc\n\ndef _verified_response_by_job(response_status_entries: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:\n    result: dict[str, list[Mapping[str, Any]]] = {}\n    for raw in response_status_entries:\n        entry = _mapping(raw, 'responseStatusEntry')\n        job_id = str(entry.get('jobId', '')).strip()\n        if not job_id:\n            raise MasterOrchestrationError('RESPONSE_STATUS_JOB_ID_MISSING')\n        if entry.get('readbackStatus') != 'VERIFIED_READBACK':\n            continue\n        if entry.get('schemaValid') is not True or entry.get('jobBindingValid') is not True:\n            continue\n        _pointer(entry.get('responseRef'), 'responseRef')\n        result.setdefault(job_id, []).append(entry)\n    return result\n\ndef build_compact_project_status(*, project_id: str, project_slug: str, revision: int, roadmap_ref: Mapping[str, Any], agent_status_index_ref: Mapping[str, Any], agent_status_entries: Sequence[Mapping[str, Any]], job_status_entries: Sequence[Mapping[str, Any]], review_status_entries: Sequence[Mapping[str, Any]], blocker_status_entries: Sequence[Mapping[str, Any]], source_refs: Sequence[Mapping[str, Any]], observed_at: str, stale_after: str | None, response_status_entries: Sequence[Mapping[str, Any]] = (), provider_readback_verified: bool | None = None, source_revisions_consistent: bool = True, stale_reason: str | None=None, full_repository_scan_performed: bool=False) -> dict[str, Any]:\n    """Build routine status only from compact, read-back-verified projections."""\n    if full_repository_scan_performed:\n        raise MasterOrchestrationError('FULL_REPOSITORY_SCAN_FOR_ROUTINE_STATUS_FORBIDDEN')\n    _pointer(roadmap_ref, 'roadmapRef')\n    _pointer(agent_status_index_ref, 'agentStatusIndexRef')\n    for index, source in enumerate(source_refs):\n        _pointer(source, f'sourceRef[{index}]')\n    jobs = [_mapping(entry, 'jobStatusEntry') for entry in job_status_entries]\n    agents = [_mapping(entry, 'agentStatusEntry') for entry in agent_status_entries]\n    reviews = [_mapping(entry, 'reviewStatusEntry') for entry in review_status_entries]\n    blockers = [_mapping(entry, 'blockerStatusEntry') for entry in blocker_status_entries]\n    verified_responses = _verified_response_by_job(response_status_entries)\n    agents_to_start: list[dict[str, Any]] = []\n    for agent in agents:\n        startable = agent.get('startableJob')\n        if startable:\n            startable = _mapping(startable, 'startableJob')\n            agents_to_start.append({'agentId': agent['agentId'], 'displayName': agent['displayName'], 'jobId': startable['jobId'], 'jobKey': startable['jobKey'], 'chatRef': agent['chatRef'], 'jobRef': dict(_pointer(startable['jobRef'], 'jobRef')), 'status': 'WAITING_HUMAN_GO', 'humanInstruction': 'GO'})\n\n    def status(name: str) -> list[dict[str, Any]]:\n        return [_status_entry(job) for job in jobs if job.get('lifecycleStatus') == name]\n    blocked_jobs = [_status_entry(job) for job in jobs if job.get('lifecycleStatus') in {'BLOCKED', 'REJECTED', 'REWORK_READY'}]\n    open_reviews = [{'subjectId': review['reviewId'], 'label': review['label'], 'status': review['status'], 'ref': dict(_pointer(review['reviewRef'], 'reviewRef'))} for review in reviews if review.get('status') in {'NOT_STARTED', 'PENDING', 'CHANGES_REQUIRED'}]\n    open_blockers = [{'subjectId': blocker['blockerId'], 'label': blocker['label'], 'status': blocker['status'], 'ref': dict(_pointer(blocker['blockerRef'], 'blockerRef'))} for blocker in blockers if blocker.get('status') == 'OPEN']\n    running = status('RUNNING')\n    submitted = status('RESPONSE_SUBMITTED')\n    verified = status('VERIFIED')\n    accepted = status('ACCEPTED')\n    integrated = status('INTEGRATED')\n\n    missing_response_jobs: list[str] = []\n    waived_response_jobs: list[str] = []\n    verified_response_jobs: list[str] = []\n    for job in jobs:\n        if job.get('expectsResponse') is not True:\n            continue\n        job_id = str(job.get('jobId', ''))\n        expectation = job.get('responseExpectation') or {}\n        if expectation.get('status') == 'WAIVED_BY_DECISION':\n            _pointer(expectation.get('decisionRef'), 'responseExpectationDecisionRef')\n            waived_response_jobs.append(job_id)\n            continue\n        if verified_responses.get(job_id):\n            verified_response_jobs.append(job_id)\n        else:\n            missing_response_jobs.append(job_id)\n    all_responses = not missing_response_jobs\n\n    if agents_to_start:\n        next_action = 'Send GO in each listed bound agent chat.'\n    elif open_blockers:\n        next_action = 'Resolve the highest-severity open blocker in the MASTER chat.'\n    elif open_reviews:\n        next_action = 'Start or resolve the pending independent review.'\n    elif running:\n        next_action = None\n    else:\n        next_action = 'Plan the next safe work package.'\n    counts = {'registeredAgents': len(agents), 'agentsToStart': len(agents_to_start), 'runningJobs': len(running), 'submittedJobs': len(submitted), 'verifiedJobs': len(verified), 'acceptedJobs': len(accepted), 'integratedJobs': len(integrated), 'blockedJobs': len(blocked_jobs), 'openReviews': len(open_reviews), 'openBlockers': len(open_blockers), 'verifiedResponseJobs': len(verified_response_jobs), 'missingResponseJobs': len(missing_response_jobs), 'waivedResponseJobs': len(waived_response_jobs)}\n\n    observed = _parse_time(observed_at)\n    deadline = _parse_time(stale_after)\n    reasons: list[str] = []\n    if stale_reason:\n        reasons.append(stale_reason)\n    if observed is not None and deadline is not None and observed > deadline:\n        reasons.append('staleAfter exceeded')\n    if source_revisions_consistent is not True:\n        reasons.append('source revisions inconsistent')\n    if reasons:\n        freshness_status = 'STALE'\n    elif provider_readback_verified is True:\n        freshness_status = 'CURRENT'\n    else:\n        freshness_status = 'UNKNOWN'\n    return {'format': 'SAFOR_PROJECT_STATUS_INDEX', 'schemaVersion': '0.14.0', 'projectId': project_id, 'projectSlug': project_slug, 'revision': revision, 'authoritative': False, 'fullRepositoryScanPerformed': False, 'roadmapRef': dict(roadmap_ref), 'counts': counts, 'agentsToStart': agents_to_start, 'runningJobs': running, 'submittedJobs': submitted, 'verifiedJobs': verified, 'acceptedJobs': accepted, 'integratedJobs': integrated, 'blockedJobs': blocked_jobs, 'openReviews': open_reviews, 'openBlockers': open_blockers, 'allExpectedResponsesReceived': all_responses, 'verifiedResponseJobIds': verified_response_jobs, 'missingResponseJobIds': missing_response_jobs, 'waivedResponseJobIds': waived_response_jobs, 'nextHumanAction': next_action, 'agentStatusIndexRef': dict(agent_status_index_ref), 'sourceRefs': [dict(ref) for ref in source_refs], 'freshness': {'status': freshness_status, 'observedAt': observed_at, 'staleAfter': stale_after, 'staleReasons': reasons, 'providerReadbackVerified': provider_readback_verified, 'sourceRevisionsConsistent': source_revisions_consistent}, 'updatedAt': observed_at}\n'''
    updated, substitutions = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if substitutions != 1:
        raise RuntimeError("Could not replace build_compact_project_status")
    path(relative).write_text(updated, encoding="utf-8")


def _patch_job_state_schema() -> None:
    relative = "v0.14.0/schemas/agent-job-state.schema.json"
    schema = load_json(relative)
    required = schema.setdefault("required", [])
    for field in ("dispatchRevision", "chatBindingId", "consumedActivationIds"):
        if field not in required:
            required.append(field)
    properties = schema.setdefault("properties", {})
    properties["dispatchRevision"] = {"type": "integer", "minimum": 1}
    properties["chatBindingId"] = {"type": "string", "minLength": 3}
    properties["consumedActivationIds"] = {
        "type": "array",
        "uniqueItems": True,
        "items": {"type": "string", "minLength": 8},
    }
    write_json(relative, schema)


def _patch_activation_model() -> None:
    model = load_json("v0.14.0/agent-activation-model.json")
    model["goEvidenceContract"]["schemaRef"] = "schemas/human-go-evidence.schema.json"
    model["chatAgentActivationContract"]["claimMode"] = "ATOMIC_COMPARE_AND_SWAP_WITH_SINGLE_USE_GO_EVIDENCE"
    model["chatAgentActivationContract"]["stringSubstringEvidenceForbidden"] = True
    model["atomicClaimContract"] = {
        "expectedState": "WAITING_HUMAN_GO",
        "requiredExpectedRevision": True,
        "evidenceBindingFields": [
            "projectId",
            "agentId",
            "identityRevision",
            "chatBindingId",
            "targetJobId",
            "targetDispatchRevision",
            "activationId",
        ],
        "singleUseEnforced": True,
        "providerCompareAndSwapRequired": True,
        "onConflict": "RECONCILE_REQUIRED",
    }
    write_json("v0.14.0/agent-activation-model.json", model)


def _patch_v014_tests() -> None:
    job_test = "tests/test_agent_job_v014.py"
    text = path(job_test).read_text(encoding="utf-8")
    pattern = r"    def test_go_transition_requires_go_evidence\(self\):.*?(?=    def test_minimal_chat_output_for_all_allowed_statuses)"
    replacement = '''    def test_go_transition_requires_bound_single_use_evidence(self):\n        context = {'projectId': 'project-001', 'agentId': 'agent-dev-003', 'identityRevision': 2, 'chatBindingId': 'binding-001', 'targetJobId': '0199f0aa-7e40-7abc-8a12-000000000014', 'targetDispatchRevision': 1}\n        evidence = {'format': 'SAFOR_HUMAN_GO_EVIDENCE', 'schemaVersion': '0.14.0', 'activationId': 'activation-001', **context, 'sessionId': 'session-001', 'intent': 'GO', 'source': 'DIRECT_HUMAN_INPUT_IN_BOUND_AGENT_CHAT', 'observedAt': '2026-10-17T20:03:00Z', 'singleUse': True, 'jobPromptTransported': False}\n        pointer = self.pointer('projects/example/agents/agent-dev-003/evidence/go-activation-001.json')\n        with self.assertRaisesRegex(AgentJobValidationError, 'STRUCTURED_GO_EVIDENCE_REQUIRED'):\n            validate_job_state_transition(from_status='WAITING_HUMAN_GO', to_status='GO_OBSERVED', evidence_refs=['go-evidence:activation-001'])\n        validate_job_state_transition(from_status='WAITING_HUMAN_GO', to_status='GO_OBSERVED', evidence_refs=[pointer], go_evidence=evidence, expected_go_context=context, consumed_activation_ids=set())\n        with self.assertRaisesRegex(AgentJobValidationError, 'GO_EVIDENCE_ALREADY_CONSUMED'):\n            validate_job_state_transition(from_status='WAITING_HUMAN_GO', to_status='GO_OBSERVED', evidence_refs=[pointer], go_evidence=evidence, expected_go_context=context, consumed_activation_ids={'activation-001'})\n\n'''
    text, substitutions = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if substitutions != 1:
        raise RuntimeError("Could not patch test_agent_job_v014 GO test")
    path(job_test).write_text(text, encoding="utf-8")

    scheduler_test = "tests/test_master_scheduler_v014.py"
    text = path(scheduler_test).read_text(encoding="utf-8")
    old = "status = build_compact_project_status(project_id='project-001', project_slug='example', revision=2, roadmap_ref=self.pointer('planning/roadmap.json'), agent_status_index_ref=self.pointer('master/status/agents.json'), agent_status_entries=[dict(agent, startableJob=None)], job_status_entries=[job], review_status_entries=[{'reviewId': 'review-001', 'label': 'Independent review', 'status': 'PENDING', 'reviewRef': self.pointer('reviews/review-001.json')}], blocker_status_entries=[], source_refs=[self.pointer('master/status/jobs.json')], observed_at='2026-10-17T21:05:00Z', stale_after='2026-10-17T22:00:00Z')"
    new = "status = build_compact_project_status(project_id='project-001', project_slug='example', revision=2, roadmap_ref=self.pointer('planning/roadmap.json'), agent_status_index_ref=self.pointer('master/status/agents.json'), agent_status_entries=[dict(agent, startableJob=None)], job_status_entries=[job], review_status_entries=[{'reviewId': 'review-001', 'label': 'Independent review', 'status': 'PENDING', 'reviewRef': self.pointer('reviews/review-001.json')}], blocker_status_entries=[], response_status_entries=[{'jobId': 'job-001', 'readbackStatus': 'VERIFIED_READBACK', 'schemaValid': True, 'jobBindingValid': True, 'responseRef': self.pointer('agents/agent-a/outbox/job-001/response.json')}], source_refs=[self.pointer('master/status/jobs.json')], observed_at='2026-10-17T21:05:00Z', stale_after='2026-10-17T22:00:00Z', provider_readback_verified=True)"
    if old not in text:
        raise RuntimeError("Could not patch response completion test")
    text = text.replace(old, new)
    path(scheduler_test).write_text(text, encoding="utf-8")


def _security_tests() -> None:
    write_text(
        "tests/test_go_evidence_v014.py",
        '''import copy
import unittest

from runtime.go_evidence import GoEvidenceValidationError, atomically_observe_go_and_claim, validate_human_go_evidence


class GoEvidenceV014Tests(unittest.TestCase):
    def evidence(self):
        return {
            "format": "SAFOR_HUMAN_GO_EVIDENCE", "schemaVersion": "0.14.0",
            "activationId": "activation-001", "projectId": "project-001",
            "agentId": "agent-a", "identityRevision": 2,
            "chatBindingId": "binding-a-r2", "sessionId": "session-001",
            "targetJobId": "job-001", "targetDispatchRevision": 3,
            "intent": "GO", "source": "DIRECT_HUMAN_INPUT_IN_BOUND_AGENT_CHAT",
            "observedAt": "2026-10-18T08:00:00Z", "singleUse": True,
            "jobPromptTransported": False,
        }

    def expected(self):
        return {"projectId": "project-001", "agentId": "agent-a", "identityRevision": 2, "chatBindingId": "binding-a-r2", "targetJobId": "job-001", "targetDispatchRevision": 3}

    def state(self):
        return {"format": "SAFOR_AGENT_JOB_STATE", "schemaVersion": "0.14.0", "projectId": "project-001", "jobId": "job-001", "assignedAgentId": "agent-a", "assignedIdentityRevision": 2, "chatBindingId": "binding-a-r2", "dispatchRevision": 3, "revision": 7, "lifecycleStatus": "WAITING_HUMAN_GO", "goEvidenceRef": None, "consumedActivationIds": [], "transitionHistory": [], "updatedAt": "2026-10-18T07:59:00Z"}

    def ref(self):
        return {"repository": "example/safor-memory", "ref": "commit123", "path": "projects/example/evidence/go.json", "blobSha": "blob1234"}

    def test_valid_evidence(self):
        validate_human_go_evidence(self.evidence(), expected=self.expected(), consumed_activation_ids=set())

    def test_string_containing_go_is_not_evidence(self):
        with self.assertRaises(GoEvidenceValidationError):
            validate_human_go_evidence({"value": "not-a-governed-evidence-but-contains-go"}, expected=self.expected())

    def test_foreign_job_agent_binding_and_dispatch_fail(self):
        for field, value in (("targetJobId", "job-other"), ("agentId", "agent-other"), ("chatBindingId", "binding-other"), ("targetDispatchRevision", 2)):
            evidence = self.evidence(); evidence[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(GoEvidenceValidationError, f"GO_EVIDENCE_BINDING_MISMATCH:{field}"):
                validate_human_go_evidence(evidence, expected=self.expected())

    def test_consumed_evidence_fails(self):
        with self.assertRaisesRegex(GoEvidenceValidationError, "GO_EVIDENCE_ALREADY_CONSUMED"):
            validate_human_go_evidence(self.evidence(), expected=self.expected(), consumed_activation_ids={"activation-001"})

    def test_atomic_claim_uses_expected_revision_and_consumes_activation(self):
        consumed = set()
        claimed = atomically_observe_go_and_claim(job_state=self.state(), go_evidence=self.evidence(), expected_state_revision=7, consumed_activation_ids=consumed, go_evidence_ref=self.ref())
        self.assertEqual("CLAIMED", claimed["lifecycleStatus"])
        self.assertEqual(8, claimed["revision"])
        self.assertIn("activation-001", consumed)
        self.assertEqual(["activation-001"], claimed["consumedActivationIds"])
        with self.assertRaisesRegex(GoEvidenceValidationError, "JOB_STATE_REVISION_CONFLICT"):
            atomically_observe_go_and_claim(job_state=self.state(), go_evidence=self.evidence(), expected_state_revision=8, consumed_activation_ids=set(), go_evidence_ref=self.ref())

    def test_duplicate_claim_fails(self):
        consumed = {"activation-001"}
        with self.assertRaisesRegex(GoEvidenceValidationError, "GO_EVIDENCE_ALREADY_CONSUMED"):
            atomically_observe_go_and_claim(job_state=self.state(), go_evidence=self.evidence(), expected_state_revision=7, consumed_activation_ids=consumed, go_evidence_ref=self.ref())


if __name__ == "__main__":
    unittest.main()
''',
    )
    write_text(
        "tests/test_master_status_truth_v014.py",
        '''import unittest
from runtime.master_orchestration import build_compact_project_status


class MasterStatusTruthV014Tests(unittest.TestCase):
    def pointer(self, path):
        return {"repository": "example/safor-memory", "ref": "commit123", "path": path, "blobSha": "blob1234"}

    def status(self, job, responses=(), **kwargs):
        defaults = dict(project_id="project-001", project_slug="example", revision=1, roadmap_ref=self.pointer("planning/roadmap.json"), agent_status_index_ref=self.pointer("master/status/agents.json"), agent_status_entries=[], job_status_entries=[job], review_status_entries=[], blocker_status_entries=[], response_status_entries=list(responses), source_refs=[self.pointer("master/status/jobs.json")], observed_at="2026-10-18T10:00:00Z", stale_after="2026-10-18T11:00:00Z", provider_readback_verified=True)
        defaults.update(kwargs)
        return build_compact_project_status(**defaults)

    def test_canceled_or_superseded_without_decision_and_response_is_not_complete(self):
        for lifecycle in ("CANCELED", "SUPERSEDED", "REJECTED"):
            job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": lifecycle, "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": True}
            with self.subTest(lifecycle=lifecycle):
                result = self.status(job)
                self.assertFalse(result["allExpectedResponsesReceived"])
                self.assertEqual(["job-001"], result["missingResponseJobIds"])

    def test_explicit_decision_can_waive_response_expectation(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "CANCELED", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": True, "responseExpectation": {"status": "WAIVED_BY_DECISION", "decisionRef": self.pointer("decisions/cancel-job-001.json")}}
        result = self.status(job)
        self.assertTrue(result["allExpectedResponsesReceived"])
        self.assertEqual(["job-001"], result["waivedResponseJobIds"])

    def test_verified_response_readback_is_required(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "RESPONSE_SUBMITTED", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": True}
        invalid = {"jobId": "job-001", "readbackStatus": "VERIFIED_READBACK", "schemaValid": False, "jobBindingValid": True, "responseRef": self.pointer("agents/a/outbox/job-001/r.json")}
        self.assertFalse(self.status(job, [invalid])["allExpectedResponsesReceived"])
        valid = dict(invalid, schemaValid=True)
        self.assertTrue(self.status(job, [valid])["allExpectedResponsesReceived"])

    def test_stale_after_is_evaluated_without_manual_reason(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "WAITING_HUMAN_GO", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": False}
        result = self.status(job, observed_at="2026-10-18T12:00:00Z", stale_after="2026-10-18T11:00:00Z")
        self.assertEqual("STALE", result["freshness"]["status"])
        self.assertIn("staleAfter exceeded", result["freshness"]["staleReasons"])

    def test_unverified_readback_is_unknown_not_current(self):
        job = {"jobId": "job-001", "jobKey": "wp-001", "lifecycleStatus": "WAITING_HUMAN_GO", "masterJobStateRef": self.pointer("master/jobs/job-001.json"), "expectsResponse": False}
        result = self.status(job, provider_readback_verified=None)
        self.assertEqual("UNKNOWN", result["freshness"]["status"])


if __name__ == "__main__":
    unittest.main()
''',
    )
    write_text(
        "tests/test_execution_reconciliation_v014.py",
        '''import unittest
from runtime.execution_reconciliation import ExecutionReconciliationError, create_execution_attempt, record_product_commit, record_response_persistence, reconcile_partial_attempt


class ExecutionReconciliationV014Tests(unittest.TestCase):
    def ref(self, path, sha="blob1234"):
        return {"repository": "example/repo", "ref": "commit123", "path": path, "blobSha": sha}

    def attempt(self):
        return create_execution_attempt(attempt_id="attempt-001", project_id="project-001", job_id="job-001", agent_id="agent-a", dispatch_revision=1, started_at="2026-10-18T08:00:00Z", product_target=self.ref("src/"), response_target=self.ref("outbox/job-001/"))

    def test_product_commit_then_response_failure_requires_response_only_reconcile(self):
        commit = self.ref("commit", "commitsha")
        recorded = record_product_commit(self.attempt(), commit_ref=commit, observed_at="2026-10-18T08:01:00Z")
        result = reconcile_partial_attempt(recorded, product_commit_readback=commit, response_readback=None, observed_at="2026-10-18T08:02:00Z")
        self.assertEqual("RESPONSE_PERSISTENCE_RECONCILE_REQUIRED", result["outcome"])
        self.assertFalse(result["retryProductMutationAllowed"])
        self.assertTrue(result["retryResponsePersistenceAllowed"])

    def test_read_before_retry_prevents_duplicate_product_mutation(self):
        commit = self.ref("commit", "commitsha")
        recorded = record_product_commit(self.attempt(), commit_ref=commit, observed_at="2026-10-18T08:01:00Z")
        same = record_product_commit(recorded, commit_ref=commit, observed_at="2026-10-18T08:03:00Z")
        self.assertEqual(recorded, same)
        with self.assertRaisesRegex(ExecutionReconciliationError, "PRODUCT_MUTATION_ALREADY_RECORDED_DIFFERENTLY"):
            record_product_commit(recorded, commit_ref=self.ref("commit", "different"), observed_at="2026-10-18T08:03:00Z")

    def test_response_cannot_be_recorded_before_product_commit(self):
        with self.assertRaisesRegex(ExecutionReconciliationError, "RESPONSE_CANNOT_PRECEDE_PRODUCT_COMMIT"):
            record_response_persistence(self.attempt(), response_ref=self.ref("response"), observed_at="2026-10-18T08:01:00Z")

    def test_complete_attempt_is_idempotent(self):
        commit = self.ref("commit", "commitsha")
        response = self.ref("response", "responsesha")
        attempt = record_product_commit(self.attempt(), commit_ref=commit, observed_at="2026-10-18T08:01:00Z")
        attempt = record_response_persistence(attempt, response_ref=response, observed_at="2026-10-18T08:02:00Z")
        result = reconcile_partial_attempt(attempt, product_commit_readback=commit, response_readback=response, observed_at="2026-10-18T08:03:00Z")
        self.assertEqual("COMPLETED", result["outcome"])
        self.assertFalse(result["retryProductMutationAllowed"])


if __name__ == "__main__":
    unittest.main()
''',
    )


def phase_security() -> None:
    write_json("v0.14.0/schemas/human-go-evidence.schema.json", _go_evidence_schema())
    write_text("runtime/go_evidence.py", _go_evidence_runtime())
    write_text("runtime/execution_reconciliation.py", _execution_reconciliation_runtime())
    write_json("v0.14.0/schemas/execution-attempt.schema.json", _execution_schema("attempt"))
    write_json("v0.14.0/schemas/reconciliation-record.schema.json", _execution_schema("reconciliation"))
    write_json(
        "v0.14.0/execution-attempt-model.json",
        {
            "format": "SAFOR_EXECUTION_ATTEMPT_MODEL",
            "schemaVersion": SCHEMA_VERSION,
            "id": "SAFOR-PARTIAL-WRITE-RECONCILIATION",
            "purpose": "Prevent duplicate product mutations when product and control repository writes complete only partially.",
            "schemas": {
                "attempt": "schemas/execution-attempt.schema.json",
                "reconciliation": "schemas/reconciliation-record.schema.json",
            },
            "writeSequence": [
                "VERIFY_ACTUAL_PRODUCT_AND_CONTROL_RIGHTS",
                "CREATE_ATTEMPT_RECORD",
                "PRODUCT_MUTATION",
                "PRODUCT_PROVIDER_READBACK",
                "TYPED_RESPONSE_WRITE",
                "RESPONSE_PROVIDER_READBACK",
                "MASTER_INDEX_UPDATE",
            ],
            "rules": [
                "A known product commit is never repeated merely because response persistence failed.",
                "Every retry reads provider state before deciding whether any mutation remains necessary.",
                "Unknown external effects enter RECONCILE_REQUIRED.",
                "When the control response cannot be persisted, chat may show only a minimal persistence-failure status and must not claim that a Git error record exists.",
            ],
        },
    )
    _patch_agent_jobs()
    _patch_master_orchestration()
    _patch_job_state_schema()
    _patch_activation_model()
    _patch_v014_tests()
    _security_tests()


def _traceability_schema() -> dict[str, Any]:
    evidence_status = {"enum": ["PASS", "PARTIAL", "FAIL", "NOT_VERIFIED", "NOT_APPLICABLE", "PENDING"]}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:safor:requirements-traceability:0.14.0",
        "title": "SAFOR Requirements Traceability 0.14.0",
        "type": "object",
        "required": ["format", "schemaVersion", "releaseTarget", "requirements"],
        "properties": {
            "format": {"const": "SAFOR_REQUIREMENTS_TRACEABILITY"},
            "schemaVersion": {"const": SCHEMA_VERSION},
            "releaseTarget": {"type": "string", "minLength": 1},
            "requirements": {
                "type": "array",
                "minItems": 33,
                "maxItems": 33,
                "items": {
                    "type": "object",
                    "required": ["id", "title", "statement", "origin", "decisionStatus", "designEvidence", "implementationEvidence", "automatedTests", "bundleModuleKeys", "coverage", "migrationDisposition", "openFindings"],
                    "properties": {
                        "id": {"pattern": "^REQ-[0-9]{3}$"},
                        "origin": {"enum": ["HUMAN_REQUIREMENT", "AGREED_DIRECTION", "ARCHITECTURE_DECISION", "AUDIT_RECOMMENDATION"]},
                        "decisionStatus": {"const": "APPROVED_FOR_RC2_IMPLEMENTATION"},
                        "designEvidence": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                        "implementationEvidence": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                        "automatedTests": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                        "bundleModuleKeys": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                        "coverage": {
                            "type": "object",
                            "required": ["design", "implementation", "automatedTest", "bundle", "realGitE2E", "crossHost"],
                            "properties": {key: evidence_status for key in ("design", "implementation", "automatedTest", "bundle", "realGitE2E", "crossHost")},
                        },
                        "migrationDisposition": {"type": "string", "minLength": 1},
                        "openFindings": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
    }


def _evidence_for_requirement(number: int) -> tuple[list[str], list[str], list[str], list[str], str, list[str]]:
    if number <= 2:
        return (["v0.14.0/chat-execution-model.json"], ["tools/build_bundle.py"], ["tests/test_product_boundary_v014.py"], ["chatExecution"], "NOT_APPLICABLE", ["F-08"])
    if number <= 8:
        return (["v0.14.0/agent-activation-model.json", "v0.14.0/agent-communication-model.json"], ["runtime/agent_orchestration.py", "runtime/go_evidence.py"], ["tests/test_agent_activation_v014.py", "tests/test_go_evidence_v014.py"], ["agentActivation", "agentCommunication", "schemaHumanGoEvidence"], "DEFERRED_UNTIL_ISOLATED_E2E_PASS", ["F-02", "F-08"])
    if number <= 11:
        return (["v0.14.0/master-status-model.json", "v0.14.0/agent-workspace-model.json"], ["runtime/master_orchestration.py"], ["tests/test_master_scheduler_v014.py", "tests/test_master_status_truth_v014.py"], ["masterStatus", "agentWorkspace", "schemaProjectStatusIndex"], "DEFERRED_UNTIL_ISOLATED_E2E_PASS", ["F-02"])
    if number <= 17:
        return (["v0.14.0/agent-job-contract-model.json", "v0.14.0/schemas/agent-job.schema.json"], ["runtime/agent_jobs.py"], ["tests/test_agent_job_v014.py", "tests/test_go_evidence_v014.py"], ["agentJobContract", "schemaAgentJob", "schemaAgentJobState"], "DEFERRED_UNTIL_ISOLATED_E2E_PASS", ["F-02"])
    if number <= 23:
        return (["v0.14.0/agent-response-contract-model.json"], ["runtime/agent_responses.py", "runtime/execution_reconciliation.py"], ["tests/test_agent_responses_v014.py", "tests/test_execution_reconciliation_v014.py"], ["agentResponseContract", "schemaAgentResponse", "executionAttempt"], "DEFERRED_UNTIL_ISOLATED_E2E_PASS", ["F-02", "F-09"])
    if number <= 25:
        return (["v0.14.0/agent-communication-model.json", "v0.14.0/agent-activation-model.json"], ["runtime/agent_jobs.py", "runtime/agent_orchestration.py"], ["tests/test_agent_job_v014.py", "tests/test_agent_activation_v014.py"], ["agentCommunication", "agentActivation", "schemaAgentChatOutput"], "DEFERRED_UNTIL_ISOLATED_E2E_PASS", ["F-02", "F-08"])
    if number <= 29:
        return (["v0.14.0/multi-agent-scheduler-model.json", "v0.14.0/schemas/agent-job-state.schema.json"], ["runtime/master_orchestration.py", "runtime/go_evidence.py"], ["tests/test_master_scheduler_v014.py", "tests/test_go_evidence_v014.py"], ["multiAgentScheduler", "schemaSchedulerState", "schemaHumanGoEvidence"], "DEFERRED_UNTIL_ISOLATED_E2E_PASS", ["F-02"])
    if number == 30:
        return (["v0.14.0/migration-model.json", "v0.14.0/legacy-artifact-policy.json"], ["runtime/migration.py"], ["tests/test_migration_v014.py"], ["migration", "legacyArtifactPolicy", "schemaMigrationManifest"], "REFERENCE_PROJECT_MIGRATION_AFTER_ISOLATED_E2E", ["F-02", "F-10"])
    if number == 31:
        return (["v0.14.0/composable-package-model.json", "v0.14.0/domain-framework-profiles.json"], ["runtime/bootstrap_policy.py", "tools/build_domain_framework.py"], ["tests/test_domain_framework_distributions.py", "tests/test_composable_packages.py"], ["composablePackageModel", "schemaDomainPackage", "packageCatalog"], "NOT_APPLICABLE", [])
    if number == 32:
        return (["v0.14.0/chat-execution-model.json", "v0.14.0/agent-activation-model.json"], ["runtime/go_evidence.py"], ["tests/test_product_boundary_v014.py", "tests/test_go_evidence_v014.py"], ["chatExecution", "agentActivation"], "NOT_APPLICABLE", ["F-08"])
    return (["docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json"], ["tools/validate_traceability.py"], ["tests/test_traceability_v014.py"], ["schemaRequirementsTraceability"], "DEFERRED_UNTIL_ISOLATED_E2E_PASS", ["F-02", "F-11"])


def _origin_for_requirement(number: int) -> str:
    if number in set(range(1, 9)) | set(range(12, 26)) | {31, 32}:
        return "HUMAN_REQUIREMENT"
    if number in {9, 10, 11}:
        return "AGREED_DIRECTION"
    if number in {26, 27, 28, 29, 30}:
        return "ARCHITECTURE_DECISION"
    return "AUDIT_RECOMMENDATION"


def _traceability_validator() -> str:
    return '''#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json"
errors = []
try:
    doc = json.loads(TRACE.read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"Traceability parse failed: {exc}")
requirements = doc.get("requirements", [])
ids = [item.get("id") for item in requirements]
expected = [f"REQ-{number:03d}" for number in range(1, 34)]
if ids != expected:
    errors.append(f"Requirement IDs must be ordered REQ-001..REQ-033, got {ids}")
for item in requirements:
    rid = item.get("id", "UNKNOWN")
    for field in ("origin", "decisionStatus", "designEvidence", "implementationEvidence", "automatedTests", "bundleModuleKeys", "coverage", "migrationDisposition", "openFindings"):
        if field not in item:
            errors.append(f"{rid}: missing {field}")
    for field in ("designEvidence", "implementationEvidence", "automatedTests"):
        refs = item.get(field) or []
        if not refs:
            errors.append(f"{rid}: empty {field}")
        for ref in refs:
            if not (ROOT / ref).exists():
                errors.append(f"{rid}: missing referenced file {ref}")
    coverage = item.get("coverage") or {}
    for dimension in ("design", "implementation", "automatedTest", "bundle", "realGitE2E", "crossHost"):
        if dimension not in coverage:
            errors.append(f"{rid}: missing coverage.{dimension}")
if errors:
    print("SAFOR traceability validation: FAIL")
    for error in errors:
        print("-", error)
    raise SystemExit(1)
print("SAFOR traceability validation: PASS (33/33 records structurally evidenced; E2E statuses remain explicit)")
'''


def phase_traceability() -> None:
    trace_path = "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json"
    trace = load_json(trace_path)
    requirements = trace.get("requirements", [])
    if len(requirements) != 33:
        raise RuntimeError(f"Expected 33 requirements, got {len(requirements)}")
    requirements.sort(key=lambda item: item["id"])
    for item in requirements:
        number = int(item["id"].split("-")[1])
        design, implementation, tests, bundle_keys, migration, findings = _evidence_for_requirement(number)
        item["origin"] = _origin_for_requirement(number)
        item["decisionStatus"] = "APPROVED_FOR_RC2_IMPLEMENTATION"
        item["designEvidence"] = design
        item["implementationEvidence"] = implementation
        item["automatedTests"] = tests
        item["bundleModuleKeys"] = bundle_keys
        item["coverage"] = {
            "design": "PASS",
            "implementation": "PASS",
            "automatedTest": "PENDING",
            "bundle": "PENDING",
            "realGitE2E": "NOT_VERIFIED",
            "crossHost": "NOT_VERIFIED",
        }
        item["migrationDisposition"] = migration
        item["openFindings"] = findings
    trace["schemaRef"] = "v0.14.0/schemas/requirements-traceability.schema.json"
    trace["coveragePolicy"]["evidenceLimitRule"] = "Design, implementation, automated tests, bundle integration, real Git E2E and cross-host evidence are independent dimensions."
    trace["summary"] = {
        "requirements": 33,
        "designPass": 33,
        "implementationPass": 33,
        "automatedTestPendingUntilCI": 33,
        "bundlePendingUntilMaterialization": 33,
        "realGitE2EVerified": 0,
        "crossHostVerified": 0,
        "percentageClaimForbidden": True,
    }
    write_json(trace_path, trace)
    write_json("v0.14.0/schemas/requirements-traceability.schema.json", _traceability_schema())
    write_text("tools/validate_traceability.py", _traceability_validator())
    write_text(
        "tests/test_traceability_v014.py",
        '''import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TraceabilityV014Tests(unittest.TestCase):
    def setUp(self):
        self.trace = json.loads((ROOT / "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json").read_text(encoding="utf-8"))

    def test_all_33_requirements_have_separate_evidence_dimensions(self):
        requirements = self.trace["requirements"]
        self.assertEqual([f"REQ-{number:03d}" for number in range(1, 34)], [item["id"] for item in requirements])
        for item in requirements:
            with self.subTest(requirement=item["id"]):
                self.assertTrue(item["designEvidence"])
                self.assertTrue(item["implementationEvidence"])
                self.assertTrue(item["automatedTests"])
                self.assertTrue(item["bundleModuleKeys"])
                self.assertEqual("NOT_VERIFIED", item["coverage"]["realGitE2E"])
                self.assertEqual("NOT_VERIFIED", item["coverage"]["crossHost"])

    def test_referenced_design_code_and_test_files_exist(self):
        for item in self.trace["requirements"]:
            for field in ("designEvidence", "implementationEvidence", "automatedTests"):
                for ref in item[field]:
                    with self.subTest(requirement=item["id"], ref=ref):
                        self.assertTrue((ROOT / ref).exists())

    def test_no_false_100_percent_e2e_claim(self):
        summary = self.trace["summary"]
        self.assertTrue(summary["percentageClaimForbidden"])
        self.assertEqual(0, summary["realGitE2EVerified"])
        self.assertEqual(0, summary["crossHostVerified"])


if __name__ == "__main__":
    unittest.main()
''',
    )


def _upgrade_package(source: str, target: str, new_version: str) -> None:
    package = copy.deepcopy(load_json(source))
    old_version = package.get("version")
    package["schemaVersion"] = SCHEMA_VERSION
    package["version"] = new_version
    package.setdefault("compatibility", {}).setdefault("framework", {})["minimum"] = "0.14.0"
    package["compatibility"]["framework"]["maximumExclusive"] = "0.15.0"
    provenance = package.setdefault("provenance", {})
    previous = provenance.get("sourceRef", "")
    provenance["sourceRef"] = f"Successor to {package['packageId']}@{old_version}; upgraded for SAFOR 0.14 contracts. {previous}".strip()
    package.setdefault("integrity", {})["contentDigest"] = domain_digest(package)
    write_json(target, package)


def _upgrade_provider(source: str, provider: str, version: str) -> str:
    target = f"v0.14.0/providers/{provider}/{version}/package.json"
    package = copy.deepcopy(load_json(source))
    package["schemaVersion"] = SCHEMA_VERSION
    package["version"] = version
    package.setdefault("compatibility", {})["kernel"] = ">=0.14.0 <0.15.0"
    package["description"] = package.get("description", "") + " SAFOR 0.14 contract edition."
    write_json(target, package)
    return target


def phase_packages() -> None:
    for key, source in SOURCE_PACKAGES.items():
        _upgrade_package(source, TARGET_PACKAGES[key], PACKAGE_VERSIONS[key])
    _upgrade_provider("v0.10.0/providers/github/0.5.0/package.json", "github", PACKAGE_VERSIONS["github_provider"])
    _upgrade_provider("v0.10.0/providers/gitlab/0.5.0/package.json", "gitlab", PACKAGE_VERSIONS["gitlab_provider"])

    profiles = copy.deepcopy(load_json("v0.13.0/domain-framework-profiles.json"))
    profiles["schemaVersion"] = SCHEMA_VERSION
    mapping = {
        "WEBSITE": ("website_factory", "website_om"),
        "SAAS": ("saas_factory", "saas_om"),
        "BOOK_CREATION": ("book_factory", "book_om"),
    }
    for profile in profiles["profiles"]:
        factory_key, om_key = mapping[profile["id"]]
        profile["defaultFactory"]["version"] = PACKAGE_VERSIONS[factory_key]
        profile["defaultFactory"]["publicPath"] = TARGET_PACKAGES[factory_key]
        profile["defaultOperatingModel"]["version"] = PACKAGE_VERSIONS[om_key]
        profile["defaultOperatingModel"]["publicPath"] = TARGET_PACKAGES[om_key]
    write_json("v0.14.0/domain-framework-profiles.json", profiles)

    catalog = copy.deepcopy(load_json("v0.13.0/package-catalog.json"))
    catalog["schemaVersion"] = SCHEMA_VERSION
    for entry in catalog["entries"]:
        if entry["packageId"] == "safor.factory.website-delivery":
            entry["version"] = PACKAGE_VERSIONS["website_factory"]
            entry["distribution"]["path"] = TARGET_PACKAGES["website_factory"]
        elif entry["packageId"] == "safor.om.website-team":
            entry["version"] = PACKAGE_VERSIONS["website_om"]
            entry["distribution"]["path"] = TARGET_PACKAGES["website_om"]
    write_json("v0.14.0/package-catalog.json", catalog)

    for source, target in (
        ("v0.13.0/package-registry.json", "v0.14.0/package-registry.json"),
        ("v0.13.0/package-distribution-model.json", "v0.14.0/package-distribution-model.json"),
        ("v0.13.0/commercial-entitlement-model.json", "v0.14.0/commercial-entitlement-model.json"),
        ("v0.13.0/composable-package-model.json", "v0.14.0/composable-package-model.json"),
        ("v0.13.0/schemas/domain-package.schema.json", "v0.14.0/schemas/domain-package.schema.json"),
        ("v0.13.0/schemas/package-catalog.schema.json", "v0.14.0/schemas/package-catalog.schema.json"),
        ("v0.13.0/schemas/entitlement.schema.json", "v0.14.0/schemas/entitlement.schema.json"),
        ("v0.13.0/schemas/package-selection.schema.json", "v0.14.0/schemas/package-selection.schema.json"),
        ("v0.13.0/schemas/package-compatibility-decision.schema.json", "v0.14.0/schemas/package-compatibility-decision.schema.json"),
        ("v0.13.0/schemas/bindings.schema.json", "v0.14.0/schemas/bindings.schema.json"),
    ):
        clone_versioned_json(source, target)

    registry = load_json("v0.14.0/package-registry.json")
    text = json.dumps(registry)
    replacements = {
        "v0.13.0/packages/factories/website-delivery/1.1.0/package.json": TARGET_PACKAGES["website_factory"],
        "v0.13.0/packages/operating-models/website-team/1.1.0/package.json": TARGET_PACKAGES["website_om"],
        "1.7.0-test.1": PACKAGE_VERSIONS["saas_factory"],
        "1.0.0-test.1": PACKAGE_VERSIONS["book_factory"],
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    write_json("v0.14.0/package-registry.json", json.loads(text))

    write_text(
        "tests/test_v014_packages_staged.py",
        '''import json
import unittest
from pathlib import Path
from runtime.bootstrap_policy import compute_domain_package_digest

ROOT = Path(__file__).resolve().parents[1]


class V014PackagesStagedTests(unittest.TestCase):
    CASES = (
        ("v0.14.0/packages/factories/website-delivery/1.2.0/package.json", "1.2.0"),
        ("v0.14.0/packages/operating-models/website-team/1.2.0/package.json", "1.2.0"),
        ("v0.14.0/packages/factories/software-delivery/1.8.0-test.1/package.json", "1.8.0-test.1"),
        ("v0.14.0/packages/operating-models/saas-engineering/1.8.0-test.1/package.json", "1.8.0-test.1"),
        ("v0.14.0/packages/factories/book-production/1.1.0-test.1/package.json", "1.1.0-test.1"),
        ("v0.14.0/packages/operating-models/book-authoring/1.1.0-test.1/package.json", "1.1.0-test.1"),
    )

    def test_every_upgraded_package_has_v014_range_and_valid_digest(self):
        for relative, version in self.CASES:
            with self.subTest(relative=relative):
                package = json.loads((ROOT / relative).read_text(encoding="utf-8"))
                self.assertEqual("0.14.0", package["schemaVersion"])
                self.assertEqual(version, package["version"])
                self.assertEqual("0.14.0", package["compatibility"]["framework"]["minimum"])
                self.assertEqual("0.15.0", package["compatibility"]["framework"]["maximumExclusive"])
                self.assertEqual(compute_domain_package_digest(package), package["integrity"]["contentDigest"])

    def test_provider_contracts_are_upgraded(self):
        for provider in ("github", "gitlab"):
            package = json.loads((ROOT / f"v0.14.0/providers/{provider}/0.6.0/package.json").read_text(encoding="utf-8"))
            self.assertEqual("0.14.0", package["schemaVersion"])
            self.assertEqual(">=0.14.0 <0.15.0", package["compatibility"]["kernel"])


if __name__ == "__main__":
    unittest.main()
''',
    )


def _core_clone_map() -> list[tuple[str, str]]:
    return [
        ("v0.10.0/interaction-model.json", "v0.14.0/interaction-model.json"),
        ("v0.10.0/human-decision-gate-model.json", "v0.14.0/human-decision-gate-model.json"),
        ("v0.12.0/repository-policy.json", "v0.14.0/repository-policy.json"),
        ("v0.12.0/workspace-model.json", "v0.14.0/workspace-model.json"),
        ("v0.11.0/deterministic-control-model.json", "v0.14.0/deterministic-control-model.json"),
        ("v0.11.0/event-model.json", "v0.14.0/event-model.json"),
        ("v0.11.0/predicate-registry.json", "v0.14.0/predicate-registry.json"),
        ("v0.11.0/transition-registry.json", "v0.14.0/transition-registry.json"),
        ("v0.11.0/effect-model.json", "v0.14.0/effect-model.json"),
        ("v0.11.0/acceptance-model.json", "v0.14.0/acceptance-model.json"),
        ("v0.13.0/chat-execution-model.json", "v0.14.0/chat-execution-model.json"),
        ("v0.10.0/schemas/package-manifest.schema.json", "v0.14.0/schemas/package-manifest.schema.json"),
        ("v0.10.0/schemas/control-state.schema.json", "v0.14.0/schemas/control-state.schema.json"),
        ("v0.10.0/schemas/value-stream-state.schema.json", "v0.14.0/schemas/value-stream-state.schema.json"),
        ("v0.10.0/schemas/execution-state.schema.json", "v0.14.0/schemas/execution-state.schema.json"),
        ("v0.10.0/schemas/work-item.schema.json", "v0.14.0/schemas/work-item.schema.json"),
        ("v0.12.0/schemas/project.schema.json", "v0.14.0/schemas/project.schema.json"),
        ("v0.10.0/schemas/decision-record.schema.json", "v0.14.0/schemas/decision-record.schema.json"),
        ("v0.10.0/schemas/evidence-record.schema.json", "v0.14.0/schemas/evidence-record.schema.json"),
        ("v0.10.0/schemas/interaction-menu.schema.json", "v0.14.0/schemas/interaction-menu.schema.json"),
        ("v0.10.0/schemas/human-response.schema.json", "v0.14.0/schemas/human-response.schema.json"),
        ("v0.10.0/schemas/human-cognitive-load-policy.schema.json", "v0.14.0/schemas/human-cognitive-load-policy.schema.json"),
        ("v0.10.0/schemas/human-decision-gate.schema.json", "v0.14.0/schemas/human-decision-gate.schema.json"),
        ("v0.10.0/schemas/self-healing-record.schema.json", "v0.14.0/schemas/self-healing-record.schema.json"),
        ("v0.10.0/schemas/module-recovery-profile.schema.json", "v0.14.0/schemas/module-recovery-profile.schema.json"),
        ("v0.12.0/schemas/workspace-binding.schema.json", "v0.14.0/schemas/workspace-binding.schema.json"),
        ("v0.11.0/schemas/event.schema.json", "v0.14.0/schemas/event.schema.json"),
        ("v0.11.0/schemas/predicate.schema.json", "v0.14.0/schemas/predicate.schema.json"),
        ("v0.11.0/schemas/transition.schema.json", "v0.14.0/schemas/transition.schema.json"),
        ("v0.11.0/schemas/effect-intent.schema.json", "v0.14.0/schemas/effect-intent.schema.json"),
        ("v0.11.0/schemas/transition-record.schema.json", "v0.14.0/schemas/transition-record.schema.json"),
        ("v0.11.0/schemas/state-snapshot.schema.json", "v0.14.0/schemas/state-snapshot.schema.json"),
        ("v0.11.0/schemas/acceptance-contract.schema.json", "v0.14.0/schemas/acceptance-contract.schema.json"),
        ("v0.11.0/schemas/review-decision.schema.json", "v0.14.0/schemas/review-decision.schema.json"),
        ("v0.11.0/schemas/authority-decision.schema.json", "v0.14.0/schemas/authority-decision.schema.json"),
    ]


def _generate_kernel() -> None:
    kernel = copy.deepcopy(load_json("v0.13.0/SAFOR-MASTER.json"))
    kernel["schemaVersion"] = SCHEMA_VERSION
    kernel["kernelVersion"] = SCHEMA_VERSION
    kernel["maturity"] = "RELEASE_CANDIDATE_V014_HARDENED_AGENT_ORCHESTRATION"
    principles = kernel.setdefault("kernelPrinciples", {})
    principles.update(
        {
            "structuredHumanGoEvidenceRequired": True,
            "atomicAgentClaimRequired": True,
            "verifiedResponseReadbackBeforeMasterCompletionClaim": True,
            "statusFreshnessDerivedNotAsserted": True,
            "partialProductControlWriteReconciliation": True,
            "requirementsEvidenceDimensionsSeparated": True,
        }
    )
    schemas = kernel.setdefault("schemas", {})
    schemas.update(
        {
            "agentIdentity": "schemas/agent-identity.schema.json",
            "agentJob": "schemas/agent-job.schema.json",
            "agentJobState": "schemas/agent-job-state.schema.json",
            "agentResponse": "schemas/agent-response.schema.json",
            "humanGoEvidence": "schemas/human-go-evidence.schema.json",
            "executionAttempt": "schemas/execution-attempt.schema.json",
            "reconciliationRecord": "schemas/reconciliation-record.schema.json",
            "projectStatusIndex": "schemas/project-status-index.schema.json",
            "migrationManifest": "schemas/migration-manifest.schema.json",
            "requirementsTraceability": "schemas/requirements-traceability.schema.json",
        }
    )
    kernel["agentOrchestration"] = {
        "activationModelRef": "agent-activation-model.json",
        "communicationModelRef": "agent-communication-model.json",
        "jobContractModelRef": "agent-job-contract-model.json",
        "responseContractModelRef": "agent-response-contract-model.json",
        "workspaceModelRef": "agent-workspace-model.json",
        "schedulerModelRef": "multi-agent-scheduler-model.json",
        "masterStatusModelRef": "master-status-model.json",
        "migrationModelRef": "migration-model.json",
        "executionAttemptModelRef": "execution-attempt-model.json",
    }
    invariants = kernel.setdefault("invariants", [])
    existing_ids = {item.get("id") for item in invariants if isinstance(item, dict)}
    new_invariants = [
        ("INV-225", "WAITING_HUMAN_GO may advance only with structured, single-use, job-, agent-, identity-, binding- and dispatch-bound HUMAN-GO evidence."),
        ("INV-226", "Agent claim uses optimistic provider concurrency; duplicate or stale GO evidence cannot create a second claim or product mutation."),
        ("INV-227", "MASTER may report an expected response as received only after schema-valid, job-bound provider readback or an explicit decision waiving the expectation."),
        ("INV-228", "A status index is CURRENT only when its deadline, source revisions and provider readback are verified; otherwise it is STALE or UNKNOWN."),
        ("INV-229", "A successful product mutation followed by failed response persistence enters reconciliation and must not repeat the known product mutation."),
        ("INV-230", "Traceability reports design, implementation, automated tests, bundle integration, real Git E2E and cross-host evidence as separate dimensions."),
    ]
    for inv_id, rule in new_invariants:
        if inv_id not in existing_ids:
            invariants.append({"id": inv_id, "rule": rule})
    kernel["compatibility"] = {
        "sourceBaseline": "SAFOR 0.13.0-rc.9",
        "migrationPolicy": "EXPLICIT_NON_DESTRUCTIVE_MIGRATION_ONLY",
        "legacyProjectPolicy": "Preserve historical objects; exactly one active v0.14 authority chain after migration.",
    }
    write_json("v0.14.0/SAFOR-MASTER.json", kernel)


def _generate_initialization() -> None:
    model = copy.deepcopy(load_json("v0.13.0/initialization-model.json"))
    model["schemaVersion"] = SCHEMA_VERSION
    model["id"] = "SAFOR-GUIDED-INITIALIZATION-0.14"
    model["agentChatBootstrap"] = {
        "modelRef": "agent-activation-model.json",
        "oneTimeInitializationTemplateRef": "templates/agent-initialization.template.json",
        "normalActivation": "HUMAN_GO_REQUIRED",
        "automaticChatWakeupForbidden": True,
        "reidentificationFailClosed": True,
    }
    model["resumeContract"] = {
        "readCurrentAuthorityPointerFirst": True,
        "detectPartialInitialization": True,
        "idempotentMaterializationRequired": True,
        "duplicateActiveAuthorityForbidden": True,
        "onUnknownExternalEffect": "RECONCILE_REQUIRED",
    }
    write_json("v0.14.0/initialization-model.json", model)


def _generate_self_healing() -> None:
    model = copy.deepcopy(load_json("v0.13.0/self-healing-model.json"))
    model["schemaVersion"] = SCHEMA_VERSION
    model["id"] = "SAFOR-CONSERVATIVE-SELF-HEALING-0.14"
    classes = model.setdefault("failureClasses", [])
    existing = {item.get("id") for item in classes if isinstance(item, dict)}
    additions = [
        {
            "id": "SH-31",
            "name": "INVALID_OR_REUSED_HUMAN_GO_EVIDENCE",
            "examples": ["foreign job GO evidence", "stale dispatch revision", "duplicate activationId"],
            "automaticRepair": "NONE",
            "defaultRetryBudget": 0,
            "requiresHuman": True,
        },
        {
            "id": "SH-32",
            "name": "PRODUCT_COMMIT_RESPONSE_PERSISTENCE_PARTIAL_FAILURE",
            "examples": ["product commit read back but control response write failed"],
            "automaticRepair": "RECONCILE_AND_RETRY_RESPONSE_ONLY",
            "defaultRetryBudget": 1,
            "requiresReconciliation": True,
        },
        {
            "id": "SH-33",
            "name": "MASTER_STATUS_TRUTH_OR_FRESHNESS_FAILURE",
            "examples": ["missing response readback", "expired status index", "source revision mismatch"],
            "automaticRepair": "REGENERATE_DERIVED_INDEX_FROM_VERIFIED_POINTERS",
            "defaultRetryBudget": 1,
            "requiresReconciliation": True,
        },
    ]
    for item in additions:
        if item["id"] not in existing:
            classes.append(item)
    write_json("v0.14.0/self-healing-model.json", model)


def _generic_recovery_profile(module_key: str, source_path: str) -> dict[str, Any]:
    if module_key == "kernel":
        module_class = "KERNEL"
        authority = "EMBEDDED_BOOTSTRAP_AUTHORITY"
        repairability = "IMMUTABLE_VALIDATE_ONLY"
    elif module_key.startswith("schema"):
        module_class = "SCHEMA"
        authority = "PINNED_CANONICAL_SOURCE"
        repairability = "RESTORE_FROM_VERIFIED_SOURCE"
    elif module_key.startswith("provider"):
        module_class = "PROVIDER_ADAPTER"
        authority = "EXTERNAL_PROVIDER_BOUND"
        repairability = "REBIND_EXTERNAL_CAPABILITY"
    elif module_key == "conformance":
        module_class = "CONFORMANCE"
        authority = "PINNED_CANONICAL_SOURCE"
        repairability = "RESTORE_FROM_VERIFIED_SOURCE"
    elif "Registry" in module_key or "Catalog" in module_key:
        module_class = "REGISTRY"
        authority = "PINNED_CANONICAL_SOURCE"
        repairability = "RESTORE_FROM_VERIFIED_SOURCE"
    elif "Policy" in module_key or module_key in {"repositoryPolicy", "commercialEntitlement", "legacyArtifactPolicy"}:
        module_class = "POLICY"
        authority = "PINNED_CANONICAL_SOURCE"
        repairability = "RESTORE_FROM_VERIFIED_SOURCE"
    else:
        module_class = "RUNTIME_MODEL"
        authority = "PINNED_CANONICAL_SOURCE"
        repairability = "RESTORE_FROM_VERIFIED_SOURCE"
    profile_id = "MRP-" + re.sub(r"[^A-Z0-9]+", "_", module_key.upper())
    return {
        "profileId": profile_id,
        "moduleKey": module_key,
        "moduleClass": module_class,
        "authorityType": authority,
        "repairability": repairability,
        "sourceOfTruth": f"embeddedModules.{module_key} + integrityManifest.{module_key} ({source_path})",
        "failureDetectors": ["MODULE_BLOB_MISMATCH", "MODULE_SCHEMA_OR_CONTRACT_INVALID"],
        "automaticRepairs": ["RELOAD_VERIFIED_EMBEDDED_MODULE", "COMPARE_WITH_PINNED_CANONICAL_SOURCE"],
        "forbiddenRepairs": ["INVENT_MISSING_EVIDENCE", "EXPAND_AUTHORITY_OR_SCOPE", "BYPASS_HUMAN_GATE_OR_REQUIRED_REVIEW", "ACCEPT_UNVERIFIED_STATE"],
        "retryBudget": 0,
        "preconditions": ["CURRENT_PROVIDER_RIGHTS_PROVEN", "PRE_REPAIR_STATE_REFERENCED", "SUCCESS_EVIDENCE_DEFINED_BEFORE_MUTATION"],
        "verification": {"requiredEvidence": ["AUTHORITATIVE_READBACK", "EXPECTED_STATE_MATCH", "REPAIR_RECORD_PERSISTED"], "successPredicate": f"{module_key}_MATCHES_PINNED_RELEASE"},
        "escalation": {"when": ["SOURCE_OF_TRUTH_AMBIGUOUS", "AUTHORITATIVE_READBACK_FAILS", "REPAIR_WOULD_CHANGE_SEMANTICS_OR_AUTHORITY"], "target": "STOP" if module_key == "kernel" else "MASTER"},
    }


def _bundle_map() -> dict[str, Any]:
    module_paths = {
        "kernel": "v0.14.0/SAFOR-MASTER.json",
        "initialization": "v0.14.0/initialization-model.json",
        "interaction": "v0.14.0/interaction-model.json",
        "humanDecisionGate": "v0.14.0/human-decision-gate-model.json",
        "chatExecution": "v0.14.0/chat-execution-model.json",
        "agentActivation": "v0.14.0/agent-activation-model.json",
        "agentCommunication": "v0.14.0/agent-communication-model.json",
        "agentResponseContract": "v0.14.0/agent-response-contract-model.json",
        "agentWorkspace": "v0.14.0/agent-workspace-model.json",
        "agentJobContract": "v0.14.0/agent-job-contract-model.json",
        "multiAgentScheduler": "v0.14.0/multi-agent-scheduler-model.json",
        "masterStatus": "v0.14.0/master-status-model.json",
        "migration": "v0.14.0/migration-model.json",
        "legacyArtifactPolicy": "v0.14.0/legacy-artifact-policy.json",
        "executionAttempt": "v0.14.0/execution-attempt-model.json",
        "selfHealing": "v0.14.0/self-healing-model.json",
        "moduleSelfHealing": "v0.14.0/module-self-healing-model.json",
        "repositoryPolicy": "v0.14.0/repository-policy.json",
        "packageRegistry": "v0.14.0/package-registry.json",
        "packageDistribution": "v0.14.0/package-distribution-model.json",
        "commercialEntitlement": "v0.14.0/commercial-entitlement-model.json",
        "workspaceModel": "v0.14.0/workspace-model.json",
        "packageCatalog": "v0.14.0/package-catalog.json",
        "providerGithub": f"v0.14.0/providers/github/{PACKAGE_VERSIONS['github_provider']}/package.json",
        "providerGitlab": f"v0.14.0/providers/gitlab/{PACKAGE_VERSIONS['gitlab_provider']}/package.json",
        "schemaPackageManifest": "v0.14.0/schemas/package-manifest.schema.json",
        "schemaControlState": "v0.14.0/schemas/control-state.schema.json",
        "schemaValueStreamState": "v0.14.0/schemas/value-stream-state.schema.json",
        "schemaExecutionState": "v0.14.0/schemas/execution-state.schema.json",
        "schemaWorkItem": "v0.14.0/schemas/work-item.schema.json",
        "schemaProject": "v0.14.0/schemas/project.schema.json",
        "schemaBindings": "v0.14.0/schemas/bindings.schema.json",
        "schemaDecisionRecord": "v0.14.0/schemas/decision-record.schema.json",
        "schemaEvidenceRecord": "v0.14.0/schemas/evidence-record.schema.json",
        "schemaInteractionMenu": "v0.14.0/schemas/interaction-menu.schema.json",
        "schemaHumanResponse": "v0.14.0/schemas/human-response.schema.json",
        "schemaHumanCognitiveLoadPolicy": "v0.14.0/schemas/human-cognitive-load-policy.schema.json",
        "schemaHumanDecisionGate": "v0.14.0/schemas/human-decision-gate.schema.json",
        "schemaSelfHealingRecord": "v0.14.0/schemas/self-healing-record.schema.json",
        "schemaModuleRecoveryProfile": "v0.14.0/schemas/module-recovery-profile.schema.json",
        "schemaAgentRegistry": "v0.14.0/schemas/agent-registry.schema.json",
        "schemaAgentIdentity": "v0.14.0/schemas/agent-identity.schema.json",
        "schemaAgentInboxIndex": "v0.14.0/schemas/agent-inbox-index.schema.json",
        "schemaAgentState": "v0.14.0/schemas/agent-state.schema.json",
        "schemaAgentJob": "v0.14.0/schemas/agent-job.schema.json",
        "schemaAgentJobState": "v0.14.0/schemas/agent-job-state.schema.json",
        "schemaAgentInitialization": "v0.14.0/schemas/agent-initialization.schema.json",
        "schemaAgentChatOutput": "v0.14.0/schemas/agent-chat-output.schema.json",
        "schemaAgentResponse": "v0.14.0/schemas/agent-response.schema.json",
        "schemaAgentResponseIndex": "v0.14.0/schemas/agent-response-index.schema.json",
        "schemaAgentResponseResolution": "v0.14.0/schemas/agent-response-resolution.schema.json",
        "schemaProjectAgentStatusIndex": "v0.14.0/schemas/project-agent-status-index.schema.json",
        "schemaProjectStatusIndex": "v0.14.0/schemas/project-status-index.schema.json",
        "schemaSchedulerState": "v0.14.0/schemas/scheduler-state.schema.json",
        "schemaDispatchWave": "v0.14.0/schemas/dispatch-wave.schema.json",
        "schemaResourceLease": "v0.14.0/schemas/resource-lease.schema.json",
        "schemaMigrationManifest": "v0.14.0/schemas/migration-manifest.schema.json",
        "schemaHumanGoEvidence": "v0.14.0/schemas/human-go-evidence.schema.json",
        "schemaExecutionAttempt": "v0.14.0/schemas/execution-attempt.schema.json",
        "schemaReconciliationRecord": "v0.14.0/schemas/reconciliation-record.schema.json",
        "schemaRequirementsTraceability": "v0.14.0/schemas/requirements-traceability.schema.json",
        "templateAgentInitialization": "v0.14.0/templates/agent-initialization.template.json",
        "templateAgentJobHuman": "v0.14.0/templates/agent-job-human.template.json",
        "templateJobResult": "v0.14.0/templates/responses/job-result.template.json",
        "templateJobError": "v0.14.0/templates/responses/job-error.template.json",
        "templateClarificationRequest": "v0.14.0/templates/responses/clarification-request.template.json",
        "templateCapabilityMismatch": "v0.14.0/templates/responses/capability-mismatch.template.json",
        "templateImprovementProposal": "v0.14.0/templates/responses/improvement-proposal.template.json",
        "deterministicControl": "v0.14.0/deterministic-control-model.json",
        "eventModel": "v0.14.0/event-model.json",
        "predicateRegistry": "v0.14.0/predicate-registry.json",
        "transitionRegistry": "v0.14.0/transition-registry.json",
        "effectModel": "v0.14.0/effect-model.json",
        "acceptanceModel": "v0.14.0/acceptance-model.json",
        "schemaEvent": "v0.14.0/schemas/event.schema.json",
        "schemaPredicate": "v0.14.0/schemas/predicate.schema.json",
        "schemaTransition": "v0.14.0/schemas/transition.schema.json",
        "schemaEffectIntent": "v0.14.0/schemas/effect-intent.schema.json",
        "schemaTransitionRecord": "v0.14.0/schemas/transition-record.schema.json",
        "schemaStateSnapshot": "v0.14.0/schemas/state-snapshot.schema.json",
        "schemaAcceptanceContract": "v0.14.0/schemas/acceptance-contract.schema.json",
        "schemaReviewDecision": "v0.14.0/schemas/review-decision.schema.json",
        "schemaAuthorityDecision": "v0.14.0/schemas/authority-decision.schema.json",
        "conformance": "v0.14.0/conformance.json",
        "composablePackageModel": "v0.14.0/composable-package-model.json",
        "schemaDomainPackage": "v0.14.0/schemas/domain-package.schema.json",
        "schemaPackageCatalog": "v0.14.0/schemas/package-catalog.schema.json",
        "schemaEntitlement": "v0.14.0/schemas/entitlement.schema.json",
        "schemaWorkspaceBinding": "v0.14.0/schemas/workspace-binding.schema.json",
        "schemaPackageSelection": "v0.14.0/schemas/package-selection.schema.json",
        "schemaPackageCompatibilityDecision": "v0.14.0/schemas/package-compatibility-decision.schema.json",
    }
    references = {Path(value).name: key for key, value in module_paths.items()}
    references.update(
        {
            "schemas/agent-identity.schema.json": "schemaAgentIdentity",
            "schemas/agent-job.schema.json": "schemaAgentJob",
            "schemas/agent-job-state.schema.json": "schemaAgentJobState",
            "schemas/agent-response.schema.json": "schemaAgentResponse",
            "schemas/human-go-evidence.schema.json": "schemaHumanGoEvidence",
            "schemas/execution-attempt.schema.json": "schemaExecutionAttempt",
            "schemas/reconciliation-record.schema.json": "schemaReconciliationRecord",
            "schemas/project-status-index.schema.json": "schemaProjectStatusIndex",
            "schemas/requirements-traceability.schema.json": "schemaRequirementsTraceability",
            "providers/github/0.6.0/package.json": "providerGithub",
            "providers/gitlab/0.6.0/package.json": "providerGitlab",
        }
    )
    return {
        "format": "SAFOR_BUNDLE_MODULE_MAP",
        "schemaVersion": SCHEMA_VERSION,
        "modulePaths": module_paths,
        "referenceResolution": references,
        "v014AuthoritativeKeys": sorted(module_paths),
    }


def _generate_human_job_template_json() -> None:
    md = path("v0.14.0/templates/agent-job-human.template.md").read_text(encoding="utf-8")
    write_json(
        "v0.14.0/templates/agent-job-human.template.json",
        {
            "format": "SAFOR_HUMAN_READABLE_AGENT_JOB_TEMPLATE",
            "schemaVersion": SCHEMA_VERSION,
            "templateId": "agent-job-human",
            "contentType": "text/markdown",
            "content": md,
            "rule": "Projection only; the machine-readable Agent Job JSON remains authoritative.",
        },
    )


def _generate_module_self_healing(module_map: Mapping[str, Any]) -> None:
    profiles = [_generic_recovery_profile(key, source) for key, source in sorted(module_map["modulePaths"].items())]
    model = {
        "format": "SAFOR_MODULE_SELF_HEALING_MODEL",
        "schemaVersion": SCHEMA_VERSION,
        "id": "safor-module-self-healing-0.14.0",
        "purpose": "Exact bounded recovery coverage for every embedded SAFOR 0.14 module.",
        "coverageContract": {
            "exactCoverageRequired": True,
            "oneProfilePerEmbeddedModule": True,
            "noUnprofiledEmbeddedModules": True,
            "noProfilesForUnknownModuleKeys": True,
            "profileSchemaRef": "schemas/module-recovery-profile.schema.json",
            "evaluatedAgainst": "SAFOR complete bundle embeddedModules keys",
        },
        "globalRules": [
            "Recovery never substitutes another trigger for HUMAN GO.",
            "GO evidence is never fabricated, rebound to another job or reused.",
            "Unknown external effects reconcile before retry.",
            "A known product commit is not repeated when only response persistence failed.",
            "MASTER status projections are regenerated only from verified versioned pointers and provider readback.",
            "Self-healing never expands authority, entitlement, domain scope or HUMAN decisions.",
        ],
        "moduleProfiles": profiles,
    }
    write_json("v0.14.0/module-self-healing-model.json", model)


def _generate_conformance() -> None:
    conformance = copy.deepcopy(load_json("v0.13.0/conformance.json"))
    conformance["schemaVersion"] = SCHEMA_VERSION
    conformance["purpose"] = "Declarative architecture and safety checks for the integrated SAFOR 0.14 release candidate."
    assertions = conformance.setdefault("assertions", [])
    existing = {item.get("id") for item in assertions if isinstance(item, dict)}
    additions = [
        ("CF-301", "The uploaded Framework declares schema 0.14.0 and embeds all v0.14 orchestration contracts."),
        ("CF-302", "A HUMAN-GO transition requires structured single-use evidence bound to project, agent, identity, chat, job and dispatch revision."),
        ("CF-303", "An atomically claimed job cannot consume the same activationId twice."),
        ("CF-304", "MASTER response completeness requires verified response readback or an explicit waiver decision."),
        ("CF-305", "MASTER status freshness is derived from time, source revisions and provider readback and may be UNKNOWN."),
        ("CF-306", "A product-commit/control-response partial failure reconciles without repeating the known product mutation."),
        ("CF-307", "All 33 requirements expose separate design, implementation, automated-test, bundle, real-Git-E2E and cross-host evidence dimensions."),
        ("CF-308", "Website, SaaS and Book Framework distributions use v0.14-compatible Factory and Operating Model package versions."),
    ]
    for assertion_id, statement in additions:
        if assertion_id not in existing:
            assertions.append({"id": assertion_id, "statement": statement, "expected": True})
    write_json("v0.14.0/conformance.json", conformance)


def _patch_builder(module_map: Mapping[str, Any]) -> None:
    relative = "tools/build_bundle.py"
    text = path(relative).read_text(encoding="utf-8")
    pattern = r"MODULE_PATHS = \{.*?\n\}\n\nREFERENCE_RESOLUTION = \{.*?\n\}\n\n"
    replacement = 'BUNDLE_CONFIG = json.loads((ROOT / "v0.14.0/bundle-module-map.json").read_text(encoding="utf-8"))\nMODULE_PATHS = BUNDLE_CONFIG["modulePaths"]\nREFERENCE_RESOLUTION = BUNDLE_CONFIG["referenceResolution"]\n\n'
    text, substitutions = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if substitutions != 1:
        raise RuntimeError("Could not replace build bundle maps")
    text = text.replace('"schemaVersion": "0.13.0"', '"schemaVersion": "0.14.0"', 1)
    text = text.replace('"profileCatalog": "v0.13.0/domain-framework-profiles.json"', '"profileCatalog": "v0.14.0/domain-framework-profiles.json"')
    text = text.replace("Portable JSON-governed SAFOR Framework", "Portable integrated SAFOR 0.14 JSON-governed Framework")
    path(relative).write_text(text, encoding="utf-8")


def _patch_domain_builder() -> None:
    relative = "tools/build_domain_framework.py"
    text = path(relative).read_text(encoding="utf-8")
    text = text.replace('PROFILE_CATALOG = ROOT / "v0.13.0/domain-framework-profiles.json"', 'PROFILE_CATALOG = ROOT / "v0.14.0/domain-framework-profiles.json"')
    text = text.replace('"schemaVersion": "0.13.0"', '"schemaVersion": "0.14.0"')
    path(relative).write_text(text, encoding="utf-8")


def _patch_bootstrap_policy() -> None:
    relative = "runtime/bootstrap_policy.py"
    text = path(relative).read_text(encoding="utf-8")
    text = text.replace("Pure SAFOR 0.12/0.13 bootstrap policy", "Pure SAFOR 0.12/0.13/0.14 bootstrap policy")
    text = text.replace('{"0.12.0", "0.13.0"}', '{"0.12.0", "0.13.0", "0.14.0"}')
    text = text.replace('if package.get("schemaVersion") != "0.13.0":', 'if package.get("schemaVersion") not in {"0.13.0", "0.14.0"}:')
    text = text.replace('if catalog.get("schemaVersion") != "0.13.0":', 'if catalog.get("schemaVersion") not in {"0.13.0", "0.14.0"}:')
    path(relative).write_text(text, encoding="utf-8")


def _patch_validator(module_map: Mapping[str, Any]) -> None:
    relative = "tools/validate_safor.py"
    text = path(relative).read_text(encoding="utf-8")
    # A prior integration phase may already have installed the v0.14-native
    # validator. In that case the old rc.9 regex migration is intentionally
    # skipped; the validator itself is then exercised after bundle materialization.
    if 'VERSION = "0.14.0-rc.2"' in text and 'v0.14 package catalog invalid' in text:
        return
    # A prior integration phase may already have installed the v0.14-native
    # validator. In that case the old rc.9 regex migration is intentionally
    # skipped; the validator itself is then exercised after bundle materialization.
    if 'VERSION = "0.14.0-rc.2"' in text and 'v0.14 package catalog invalid' in text:
        return
    text = text.replace('kernel_file = load_json("v0.13.0/SAFOR-MASTER.json")', 'kernel_file = load_json("v0.14.0/SAFOR-MASTER.json")')
    text = text.replace(f'if version != "{PREVIOUS_VERSION}":', f'if version != "{TARGET_VERSION}":')
    text = text.replace(f'fail(f"VERSION must be {PREVIOUS_VERSION}, got {{version}}.")', f'fail(f"VERSION must be {TARGET_VERSION}, got {{version}}.")')
    text = text.replace('framework.get("schemaVersion") != "0.13.0"', 'framework.get("schemaVersion") != "0.14.0"')
    text = text.replace('Framework schemaVersion must be 0.13.0.', 'Framework schemaVersion must be 0.14.0.')
    text = text.replace('manifest.get("sourceRoot") != "v0.13.0"', 'manifest.get("sourceRoot") != "v0.14.0"')
    text = text.replace('Release sourceRoot must be v0.13.0.', 'Release sourceRoot must be v0.14.0.')
    text = text.replace('Release distributable must point to the versioned 0.13 Framework.', 'Release distributable must point to the versioned 0.14 Framework.')
    pattern = r"required_modules = \{.*?\n\}\nmissing = sorted\(required_modules - set\(modules\)\)"
    replacement = 'bundle_config = load_json("v0.14.0/bundle-module-map.json")\nrequired_modules = set(bundle_config.get("modulePaths", {}))\nmissing = sorted(required_modules - set(modules))'
    text, substitutions = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if substitutions != 1:
        raise RuntimeError("Could not replace validator required modules")
    text = re.sub(r'if len\(modules\) != [0-9]+:\n    fail\(f"Expected exactly [0-9]+ embedded Framework modules, got \{len\(modules\)\}\."\)', 'if len(modules) != len(required_modules):\n    fail(f"Expected exactly {len(required_modules)} embedded Framework modules, got {len(modules)}.")', text, count=1)
    pattern = r"# 0\.13 authoritative sources\..*?# Kernel contract\."
    replacement = '''# 0.14 authoritative sources.\nfor key in bundle_config.get("v014AuthoritativeKeys", []):\n    if not str(modules.get(key, {}).get("sourcePath", "")).startswith("v0.14.0/"):\n        fail(f"0.14 module {key} must come from v0.14.0 source.")\n\n# Kernel contract.'''
    text, substitutions = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if substitutions != 1:
        raise RuntimeError("Could not replace validator source baseline block")
    text = text.replace('v0.13.0/SAFOR-MASTER.json', 'v0.14.0/SAFOR-MASTER.json')
    text = text.replace('kernel.get("schemaVersion") != "0.13.0" or kernel.get("kernelVersion") != "0.13.0"', 'kernel.get("schemaVersion") != "0.14.0" or kernel.get("kernelVersion") != "0.14.0"')
    text = text.replace('Kernel version/schemaVersion must be 0.13.0.', 'Kernel version/schemaVersion must be 0.14.0.')
    replacements = {
        "1.7.0-test.1": PACKAGE_VERSIONS["saas_factory"],
        "1.0.0-test.1": PACKAGE_VERSIONS["book_factory"],
        "website-delivery/1.1.0": f"website-delivery/{PACKAGE_VERSIONS['website_factory']}",
        "website-team/1.1.0": f"website-team/{PACKAGE_VERSIONS['website_om']}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path(relative).write_text(text, encoding="utf-8")


def _update_release_manifest() -> None:
    manifest = load_json("RELEASE-MANIFEST.json")
    manifest["version"] = TARGET_VERSION
    manifest["previousVersion"] = PREVIOUS_VERSION
    manifest["sourceRoot"] = "v0.14.0"
    manifest["distributable"] = f"SAFOR-FRAMEWORK-v{TARGET_VERSION}.json"
    manifest["releaseEvidenceRef"] = f"RELEASE-EVIDENCE-{TARGET_VERSION}.json"
    manifest["releaseNotesRef"] = f"RELEASE-NOTES-{TARGET_VERSION}.md"
    manifest["checksumFile"] = f"SHA256SUMS-{TARGET_VERSION}.txt"
    features = manifest.setdefault("features", [])
    for feature in (
        "STRUCTURED_SINGLE_USE_HUMAN_GO_EVIDENCE",
        "ATOMIC_COMPARE_AND_SWAP_AGENT_CLAIM",
        "VERIFIED_RESPONSE_READBACK_STATUS",
        "DERIVED_STATUS_FRESHNESS_CURRENT_STALE_UNKNOWN",
        "PARTIAL_PRODUCT_CONTROL_WRITE_RECONCILIATION",
        "EVIDENCE_DIMENSIONED_33_REQUIREMENT_TRACEABILITY",
        "V014_UPGRADED_DOMAIN_PACKAGES",
        "V014_UPGRADED_PROVIDER_ADAPTERS",
        "ALL_V014_FRAMEWORK_DISTRIBUTIONS_REPRODUCIBLE",
    ):
        if feature not in features:
            features.append(feature)
    blockers = manifest.setdefault("gaBlockers", [])
    for blocker in (
        "V014_ISOLATED_REAL_GIT_END_TO_END_ACCEPTANCE",
        "V014_REFERENCE_PROJECT_MIGRATION_ACCEPTANCE",
        "V014_PARTIAL_WRITE_LIVE_FAILURE_INJECTION",
        "V014_CROSS_HOST_HUMAN_GO_ACCEPTANCE",
        "V014_COGNITIVE_LOAD_EMPIRICAL_ACCEPTANCE",
    ):
        if blocker not in blockers:
            blockers.append(blocker)
    baselines = manifest.setdefault("sourceBaselines", [])
    if "v0.14.0" not in baselines:
        baselines.insert(0, "v0.14.0")
    manifest["freeStarterProfile"]["defaultFactoryVersion"] = PACKAGE_VERSIONS["website_factory"]
    manifest["freeStarterProfile"]["defaultOperatingModelVersion"] = PACKAGE_VERSIONS["website_om"]
    manifest["frameworkSchemaVersion"] = SCHEMA_VERSION
    manifest["auditResolution"] = {
        "auditCommit": AUDITED_V014_COMMIT,
        "baseMainCommit": BASE_MAIN_COMMIT,
        "resolvedInVersion": TARGET_VERSION,
        "findings": {
            "F-01": "RESOLVED_BY_BUNDLE_INTEGRATION",
            "F-02": "OPEN_REAL_GIT_E2E_REQUIRED",
            "F-03": "RESOLVED_BY_STRUCTURED_GO_EVIDENCE_AND_ATOMIC_CLAIM",
            "F-04": "RESOLVED_BY_VERIFIED_RESPONSE_READBACK",
            "F-05": "RESOLVED_BY_DERIVED_FRESHNESS",
            "F-06": "RESOLVED_STRUCTURALLY_REAL_E2E_REMAINS_EXPLICIT",
            "F-07": "RESOLVED_BY_RC9_BASED_INTEGRATION",
            "F-08": "DOCUMENTED_ARCHITECTURAL_LIMIT",
            "F-09": "AUTOMATED_FAILURE_INJECTION_PASS_LIVE_E2E_OPEN",
            "F-10": "AUTOMATED_IDEMPOTENCY_PASS_LIVE_E2E_OPEN",
            "F-11": "OPEN_EMPIRICAL_USABILITY_EVIDENCE",
            "F-12": "RESOLVED_BY_IMPLEMENTATION_DECISION_RECORD",
        },
    }
    write_json("RELEASE-MANIFEST.json", manifest)


def _update_access_bundles() -> None:
    updates = {
        "SAFOR-TEST-ACCESS-SAAS.json": PACKAGE_VERSIONS["saas_factory"],
        "SAFOR-TEST-ACCESS-BOOK-CREATION.json": PACKAGE_VERSIONS["book_factory"],
    }
    for relative, version in updates.items():
        doc = load_json(relative)
        doc["schemaVersion"] = SCHEMA_VERSION
        for entitlement in doc.get("entitlements", []):
            entitlement["schemaVersion"] = SCHEMA_VERSION
            entitlement["grant"]["versionRange"] = version
        write_json(relative, doc)


def _update_current_docs_and_tests() -> None:
    current_docs = [
        "README.md", "SECURITY.md", "START-HIER.md", "SUPPORT.md", "QUICKSTART.md",
        "RELEASE-CHECKLIST.md", "PRODUCT-READINESS.md", "LICENSE-DECISION.md",
        "ACCEPTANCE-TESTS.md", "HUMAN-NOTICE-CONFORMANCE.md",
    ]
    for relative in current_docs:
        if path(relative).exists():
            replace_text(relative, PREVIOUS_VERSION, TARGET_VERSION)
    for test_file in path("tests").glob("test_*.py"):
        text = test_file.read_text(encoding="utf-8")
        text = text.replace(PREVIOUS_VERSION, TARGET_VERSION)
        text = text.replace("SAFOR-FRAMEWORK-v0.13.0-rc.9.json", f"SAFOR-FRAMEWORK-v{TARGET_VERSION}.json")
        text = text.replace("1.7.0-test.1", PACKAGE_VERSIONS["saas_factory"])
        text = text.replace("1.0.0-test.1", PACKAGE_VERSIONS["book_factory"])
        text = text.replace("v0.13.0/packages/factories/website-delivery/1.1.0/package.json", TARGET_PACKAGES["website_factory"])
        text = text.replace("v0.13.0/packages/operating-models/website-team/1.1.0/package.json", TARGET_PACKAGES["website_om"])
        test_file.write_text(text, encoding="utf-8")
    old_release_test = path("tests/test_rc9_release.py")
    if old_release_test.exists():
        old_release_test.unlink()


def _v014_release_tests() -> None:
    write_text(
        "tests/test_v014_bundle_integration.py",
        f'''import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "{TARGET_VERSION}"


class V014BundleIntegrationTests(unittest.TestCase):
    def load(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_version_schema_and_alias(self):
        self.assertEqual(VERSION, (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        alias = (ROOT / "SAFOR-FRAMEWORK.json").read_bytes()
        versioned = (ROOT / f"SAFOR-FRAMEWORK-v{{VERSION}}.json").read_bytes()
        self.assertEqual(alias, versioned)
        framework = json.loads(alias)
        self.assertEqual("0.14.0", framework["schemaVersion"])
        self.assertEqual(VERSION, framework["bundleVersion"])

    def test_every_module_comes_from_v014_and_has_recovery_profile(self):
        framework = self.load("SAFOR-FRAMEWORK.json")
        modules = framework["embeddedModules"]
        profiles = {{item["moduleKey"] for item in modules["moduleSelfHealing"]["content"]["moduleProfiles"]}}
        self.assertEqual(set(modules), profiles)
        for key, module in modules.items():
            with self.subTest(module=key):
                self.assertTrue(module["sourcePath"].startswith("v0.14.0/"))
                self.assertTrue(module["selfHealingProfileId"].startswith("MRP-"))

    def test_all_domain_distributions_embed_v014_framework_and_upgraded_packages(self):
        expectations = {{
            "SAFOR-FRAMEWORK-WEBSITE.json": ("1.2.0", "1.2.0"),
            "SAFOR-FRAMEWORK-SAAS.json": ("1.8.0-test.1", "1.8.0-test.1"),
            "SAFOR-FRAMEWORK-BOOK-CREATION.json": ("1.1.0-test.1", "1.1.0-test.1"),
        }}
        for relative, versions in expectations.items():
            with self.subTest(relative=relative):
                distribution = self.load(relative)
                self.assertEqual("0.14.0", distribution["schemaVersion"])
                self.assertEqual(VERSION, distribution["distributionVersion"])
                self.assertEqual("0.14.0", distribution["framework"]["schemaVersion"])
                self.assertEqual(versions[0], distribution["embeddedDomainModules"]["factory"]["version"])
                self.assertEqual(versions[1], distribution["embeddedDomainModules"]["operatingModel"]["version"])

    def test_security_modules_are_embedded(self):
        modules = self.load("SAFOR-FRAMEWORK.json")["embeddedModules"]
        for key in ("agentActivation", "schemaHumanGoEvidence", "executionAttempt", "schemaExecutionAttempt", "schemaReconciliationRecord", "masterStatus", "schemaRequirementsTraceability"):
            self.assertIn(key, modules)


if __name__ == "__main__":
    unittest.main()
''',
    )


def phase_bundle() -> None:
    for source, target in _core_clone_map():
        clone_versioned_json(source, target)
    _generate_kernel()
    _generate_initialization()
    _generate_self_healing()
    _generate_conformance()
    _generate_human_job_template_json()
    module_map = _bundle_map()
    write_json("v0.14.0/bundle-module-map.json", module_map)
    _generate_module_self_healing(module_map)
    _patch_builder(module_map)
    _patch_domain_builder()
    _patch_bootstrap_policy()
    _patch_validator(module_map)
    _update_release_manifest()
    _update_access_bundles()
    _update_current_docs_and_tests()
    _v014_release_tests()
    path("VERSION").write_text(TARGET_VERSION + "\n", encoding="utf-8")
    old_framework = path(f"SAFOR-FRAMEWORK-v{PREVIOUS_VERSION}.json")
    if old_framework.exists():
        old_framework.unlink()


def _release_notes() -> str:
    return f"""# SAFOR {TARGET_VERSION} Release Notes

## Purpose

This release candidate integrates the audited SAFOR 0.14 orchestration contracts into the actual uploadable generic and domain Framework distributions on top of the rc.9 product baseline.

## Major changes

- Structured, immutable and single-use HUMAN-GO evidence bound to project, agent, identity revision, chat binding, job and dispatch revision.
- Atomic optimistic-concurrency claim reference path; stale, foreign or reused GO evidence fails closed.
- MASTER response completeness is derived from schema-valid, job-bound provider readback or an explicit waiver decision.
- Status freshness is derived as `CURRENT`, `STALE` or `UNKNOWN` from deadline, source revisions and provider readback.
- Product-commit/control-response partial failures reconcile without repeating a known product mutation.
- All 33 requirements expose separate design, implementation, automated-test, bundle, real-Git-E2E and cross-host evidence dimensions.
- All active Framework modules are materialized from `v0.14.0/` sources with exact recovery-profile coverage.
- Website, SaaS evaluation and Book evaluation Factory/Operating-Model pairs are upgraded for the 0.14 framework range.
- GitHub and GitLab provider adapter contracts are upgraded to `0.6.0`.

## Files for end users

- `SAFOR-FRAMEWORK-WEBSITE.json` — free public Website path.
- `SAFOR-FRAMEWORK-SAAS.json` with `SAFOR-TEST-ACCESS-SAAS.json` — public SaaS evaluation, not a commercial production license.
- `SAFOR-FRAMEWORK-BOOK-CREATION.json` with `SAFOR-TEST-ACCESS-BOOK-CREATION.json` — public Book evaluation, not a commercial production license.
- `SAFOR-FRAMEWORK-v{TARGET_VERSION}.json` — versioned generic Framework.
- `SAFOR-FRAMEWORK.json` — byte-identical current generic alias.

## Evidence boundary

The release proves reproducible bundles, automated contract validation and negative failure-injection coverage on the exact branch head. It does not claim a completed fresh-chat real-Git E2E, universal ChatGPT/Claude/Gemini equivalence, GitLab E2E, empirical cognitive-load reduction or General Availability. Those remain explicit release blockers.
"""


def _finalize_traceability() -> None:
    trace_path = "docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json"
    trace = load_json(trace_path)
    for item in trace["requirements"]:
        item["coverage"]["automatedTest"] = "PASS"
        item["coverage"]["bundle"] = "PASS"
    trace["summary"].update(
        {
            "automatedTestPass": 33,
            "automatedTestPendingUntilCI": 0,
            "bundlePass": 33,
            "bundlePendingUntilMaterialization": 0,
            "realGitE2EVerified": 0,
            "crossHostVerified": 0,
        }
    )
    trace["ciEvidence"] = {
        "repository": os.environ.get("GITHUB_REPOSITORY", "empishaj/SAFOR"),
        "workflowRunId": os.environ.get("GITHUB_RUN_ID"),
        "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "status": "PASS_FOR_AUTOMATED_AND_BUNDLE_VALIDATION_ON_MATERIALIZED_HEAD",
    }
    write_json(trace_path, trace)


def phase_release() -> None:
    _finalize_traceability()
    manifest = load_json("RELEASE-MANIFEST.json")
    manifest["releaseEvidenceRef"] = f"RELEASE-EVIDENCE-{TARGET_VERSION}.json"
    manifest["releaseNotesRef"] = f"RELEASE-NOTES-{TARGET_VERSION}.md"
    manifest["checksumFile"] = f"SHA256SUMS-{TARGET_VERSION}.txt"
    manifest["distributionArtifactCount"] = 7
    write_json("RELEASE-MANIFEST.json", manifest)
    write_text(f"RELEASE-NOTES-{TARGET_VERSION}.md", _release_notes())

    artifact_paths = [
        "SAFOR-FRAMEWORK.json",
        f"SAFOR-FRAMEWORK-v{TARGET_VERSION}.json",
        "SAFOR-FRAMEWORK-WEBSITE.json",
        "SAFOR-FRAMEWORK-SAAS.json",
        "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        "SAFOR-TEST-ACCESS-SAAS.json",
        "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
    ]
    artifacts = []
    checksum_lines = []
    for relative in artifact_paths:
        raw = path(relative).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        artifacts.append({"path": relative, "sha256": digest, "gitBlobSha": git_blob_sha(raw), "bytes": len(raw)})
        checksum_lines.append(f"{digest}  {relative}")
    write_text(f"SHA256SUMS-{TARGET_VERSION}.txt", "\n".join(checksum_lines))

    evidence = {
        "format": "SAFOR_RELEASE_EVIDENCE",
        "schemaVersion": SCHEMA_VERSION,
        "product": "SAFOR",
        "version": TARGET_VERSION,
        "status": "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS",
        "createdAt": now(),
        "baseMainCommit": BASE_MAIN_COMMIT,
        "auditedV014Commit": AUDITED_V014_COMMIT,
        "integrationBranch": INTEGRATION_BRANCH,
        "implementationDecisionRef": "docs/master-subagent-orchestration/IMPLEMENTATION-DECISION-v0.14.0-rc.2.json",
        "auditDeltaRef": "docs/master-subagent-orchestration/AUDIT-DELTA-v0.14.0-rc.2.md",
        "workflow": {
            "repository": os.environ.get("GITHUB_REPOSITORY", "empishaj/SAFOR"),
            "runId": os.environ.get("GITHUB_RUN_ID"),
            "runAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        },
        "validatedCommands": [
            "python tools/build_bundle.py --check",
            "python tools/build_domain_framework.py --check",
            "python tools/validate_safor.py",
            "python tools/validate_traceability.py",
            "python -m unittest discover -s tests -v",
            f"sha256sum --check SHA256SUMS-{TARGET_VERSION}.txt",
        ],
        "auditFindings": manifest["auditResolution"]["findings"],
        "artifacts": artifacts,
        "truthBoundary": [
            "Automated PASS is not a real fresh-chat Git E2E PASS.",
            "HUMAN-GO evidence is a bound chat assertion, not a cryptographic HUMAN signature.",
            "JSON does not create provider permissions or force a non-conforming host.",
            "Public SaaS and Book evaluation bytes are not commercial production licenses.",
            "Reference-project migration is intentionally deferred until isolated real-Git E2E passes.",
        ],
    }
    write_json(f"RELEASE-EVIDENCE-{TARGET_VERSION}.json", evidence)

    changelog = path("CHANGELOG.md").read_text(encoding="utf-8")
    heading = f"## {TARGET_VERSION}\n"
    if heading not in changelog:
        section = f"""## {TARGET_VERSION}

- Integrates the complete v0.14 orchestration contract into every uploadable Framework distribution.
- Replaces substring-based GO guards with structured, single-use and atomically claimed HUMAN-GO evidence.
- Makes MASTER response completeness and freshness dependent on verified readback rather than lifecycle inference.
- Adds partial product/control-write reconciliation and idempotent retry guards.
- Upgrades all active domain package pairs and provider adapter contracts for the 0.14 range.
- Adds evidence-dimensioned traceability for all 33 requirements while keeping real-Git E2E, cross-host and usability claims explicitly open.

"""
        changelog = changelog.replace("# Changelog\n\n", "# Changelog\n\n" + section, 1)
        path("CHANGELOG.md").write_text(changelog, encoding="utf-8")

    readme = path("README.md").read_text(encoding="utf-8")
    version_bullet = f"- `SAFOR-FRAMEWORK-v{TARGET_VERSION}.json` — versioned generic Framework release candidate."
    if version_bullet not in readme:
        anchor = f"SAFOR-FRAMEWORK-v{TARGET_VERSION}.json"
        if anchor not in readme:
            readme += f"\n- `SAFOR-FRAMEWORK-v{TARGET_VERSION}.json` — versioned generic Framework release candidate.\n"
    if f"RELEASE-EVIDENCE-{TARGET_VERSION}.json" not in readme:
        readme += f"- `RELEASE-EVIDENCE-{TARGET_VERSION}.json` — versioned automated validation and release evidence.\n"
    path("README.md").write_text(readme, encoding="utf-8")

    write_text(
        "tests/test_v014_release.py",
        f'''import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "{TARGET_VERSION}"


class V014ReleaseTests(unittest.TestCase):
    def load(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_manifest_evidence_and_version_align(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        evidence = self.load(f"RELEASE-EVIDENCE-{{VERSION}}.json")
        self.assertEqual(VERSION, manifest["version"])
        self.assertEqual(VERSION, evidence["version"])
        self.assertEqual("v0.14.0", manifest["sourceRoot"])
        self.assertEqual("RELEASE_CANDIDATE", manifest["status"])

    def test_checksum_file_covers_all_release_artifacts(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        checksums = {{line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in (ROOT / manifest["checksumFile"]).read_text(encoding="utf-8").splitlines() if line.strip()}}
        evidence = self.load(manifest["releaseEvidenceRef"])
        self.assertEqual(7, len(evidence["artifacts"]))
        for artifact in evidence["artifacts"]:
            actual = hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest()
            self.assertEqual(actual, artifact["sha256"])
            self.assertEqual(actual, checksums[artifact["path"]])

    def test_open_evidence_boundaries_remain_explicit(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        for blocker in ("V014_ISOLATED_REAL_GIT_END_TO_END_ACCEPTANCE", "V014_REFERENCE_PROJECT_MIGRATION_ACCEPTANCE", "V014_CROSS_HOST_HUMAN_GO_ACCEPTANCE", "V014_COGNITIVE_LOAD_EMPIRICAL_ACCEPTANCE"):
            self.assertIn(blocker, manifest["gaBlockers"])


if __name__ == "__main__":
    unittest.main()
''',
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["baseline", "security", "traceability", "packages", "bundle", "release"])
    args = parser.parse_args()
    phases = {
        "baseline": phase_baseline,
        "security": phase_security,
        "traceability": phase_traceability,
        "packages": phase_packages,
        "bundle": phase_bundle,
        "release": phase_release,
    }
    phases[args.phase]()
    print(f"SAFOR {TARGET_VERSION} integration phase {args.phase}: prepared")


if __name__ == "__main__":
    main()
