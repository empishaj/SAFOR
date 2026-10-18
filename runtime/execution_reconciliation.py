from __future__ import annotations

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
