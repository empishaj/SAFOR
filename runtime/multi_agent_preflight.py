from __future__ import annotations

from typing import Any, Mapping

from runtime.agent_jobs import (
    AgentJobValidationError,
    validate_agent_job,
    validate_authority_basis_coverage,
)


class MultiAgentWavePreflightError(ValueError):
    """Raised when a multi-agent wave is unsafe to publish or activate."""


_ALLOWED_CLAIM_POLICY_FIELDS = {
    "exclusiveAgentClaim",
    "optimisticConcurrencyRequired",
    "humanGoEvidenceRequired",
    "claimStateTarget",
    "claimAuthority",
    "humanGoEvidenceSchemaRef",
    "humanGoEvidenceTemplateRef",
    "goEvidenceWriteTarget",
    "agentStateSchemaRef",
    "claimStateTemplateRef",
    "resultSubmittedStateTemplateRef",
    "preCasSchemaValidationRequired",
    "postReadbackSchemaValidationRequired",
    "goEvidenceProviderReadbackRequired",
}
_REIDENTIFICATION_EVIDENCE_TYPE = "SAFOR_AGENT_REIDENTIFICATION_EVIDENCE"
_REIDENTIFICATION_EVIDENCE_SCHEMA_VERSION = "0.14.0"
_SETTLED_REARM_TEMPLATE_TYPE = "SAFOR_AGENT_STATE_SETTLED_REARM_TEMPLATE"
_SETTLED_REARM_TEMPLATE_PATH = (
    "v0.14.0/templates/agent-state-settled-rearm.template.json"
)
_ALLOWED_PRESELECTION_STATES = {
    "IDLE",
    "WAITING_HUMAN_GO",
    "REIDENTIFICATION_REQUIRED",
    "RESULT_SUBMITTED",
    "BLOCKED",
}


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MultiAgentWavePreflightError(f"{name.upper()}_MUST_BE_MAPPING")
    return value


def _pointer_matches(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return all(left.get(field) == right.get(field) for field in (
        "repository",
        "ref",
        "path",
        "blobSha",
    ))


def _inputs_of_type(job: Mapping[str, Any], expected_type: str) -> list[Mapping[str, Any]]:
    return [
        _mapping(item, "job_input")
        for item in (job.get("inputs") or [])
        if isinstance(item, Mapping) and item.get("expectedType") == expected_type
    ]


def _normalized_path(path: Any) -> str:
    return str(path or "").strip().strip("/")


def _paths_overlap(first: str, second: str) -> bool:
    first = _normalized_path(first)
    second = _normalized_path(second)
    if not first or not second:
        return False
    return (
        first == second
        or first.startswith(second + "/")
        or second.startswith(first + "/")
    )


def _control_write_domains(job: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    domains: list[tuple[str, str, str]] = []
    authorization = _mapping(job.get("authorization"), "authorization")
    for raw_permission in authorization.get("repositoryPermissions") or []:
        permission = _mapping(raw_permission, "repository_permission")
        if permission.get("repositoryClass") != "CONTROL_REPOSITORY":
            continue
        write = _mapping(permission.get("write"), "control_write")
        if write.get("allowed") is not True:
            continue
        repository = str(permission.get("repository") or "")
        for branch in write.get("allowedBranches") or []:
            for path in write.get("allowedPaths") or []:
                domains.append((repository, str(branch), _normalized_path(path)))
    return domains


def _assert_no_product_access(job: Mapping[str, Any], job_id: str) -> None:
    authorization = _mapping(job.get("authorization"), "authorization")
    work_permissions = [
        _mapping(permission, "work_permission")
        for permission in (authorization.get("repositoryPermissions") or [])
        if isinstance(permission, Mapping)
        and permission.get("repositoryClass") == "WORK_REPOSITORY"
    ]
    for permission in work_permissions:
        write = _mapping(permission.get("write"), "work_write")
        if permission.get("read") is not False or write.get("allowed") is not False:
            raise MultiAgentWavePreflightError(
                f"PRODUCT_ACCESS_FORBIDDEN:{job_id}"
            )
    workspace = _mapping(job.get("workspace"), "workspace")
    output = _mapping(job.get("outputContract"), "output_contract")
    if workspace.get("productWorkspace") is not None:
        raise MultiAgentWavePreflightError(
            f"PRODUCT_WORKSPACE_FORBIDDEN:{job_id}"
        )
    if output.get("productWriteTarget") is not None:
        raise MultiAgentWavePreflightError(
            f"PRODUCT_WRITE_TARGET_FORBIDDEN:{job_id}"
        )


def _validate_reidentification_evidence(
    *,
    job: Mapping[str, Any],
    state: Mapping[str, Any],
    evidence_binding: Mapping[str, Any] | None,
) -> None:
    job_id = str(_mapping(job.get("identity"), "identity").get("jobId"))
    assignment = _mapping(job.get("assignment"), "assignment")
    agent_id = str(assignment.get("agentId"))
    identity_revision = assignment.get("identityRevision")
    evidence_inputs = _inputs_of_type(job, _REIDENTIFICATION_EVIDENCE_TYPE)
    if len(evidence_inputs) != 1:
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_INPUT_REQUIRED:{job_id}"
        )
    binding = _mapping(evidence_binding, "reidentification_evidence_binding")
    evidence_ref = _mapping(binding.get("ref"), "reidentification_evidence_ref")
    evidence = _mapping(binding.get("evidence"), "reidentification_evidence")
    job_ref = _mapping(evidence_inputs[0].get("artifactRef"), "job_evidence_ref")
    if not _pointer_matches(job_ref, evidence_ref):
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_POINTER_MISMATCH:{job_id}"
        )
    if evidence.get("format") != _REIDENTIFICATION_EVIDENCE_TYPE:
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_FORMAT_INVALID:{job_id}"
        )
    if evidence.get("schemaVersion") != _REIDENTIFICATION_EVIDENCE_SCHEMA_VERSION:
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_SCHEMA_INVALID:{job_id}"
        )
    if evidence.get("projectId") != state.get("projectId"):
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_PROJECT_MISMATCH:{job_id}"
        )
    if evidence.get("agentId") != agent_id:
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_AGENT_MISMATCH:{job_id}"
        )
    if evidence.get("identityRevision") != identity_revision:
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_REVISION_MISMATCH:{job_id}"
        )
    if evidence.get("result") != "PASS":
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_NOT_PASS:{job_id}"
        )
    if evidence.get("validForRearm") is not True or evidence.get("immutable") is not True:
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_EVIDENCE_NOT_REARMABLE:{job_id}"
        )
    if evidence.get("observedAgentReply") != evidence.get("expectedAgentReply"):
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_ACKNOWLEDGEMENT_MISMATCH:{job_id}"
        )
    bootstrap_state = _mapping(evidence.get("stateAtBootstrap"), "state_at_bootstrap")
    if bootstrap_state.get("runtimeStatus") != "REIDENTIFICATION_REQUIRED":
        raise MultiAgentWavePreflightError(
            f"REIDENTIFICATION_BOOTSTRAP_STATE_INVALID:{job_id}"
        )


def _validate_preselection_state(
    *,
    job: Mapping[str, Any],
    state: Mapping[str, Any],
    evidence_binding: Mapping[str, Any] | None,
) -> None:
    identity = _mapping(job.get("identity"), "identity")
    assignment = _mapping(job.get("assignment"), "assignment")
    job_id = str(identity.get("jobId"))
    agent_id = str(assignment.get("agentId"))
    if state.get("agentId") != agent_id:
        raise MultiAgentWavePreflightError(f"AGENT_STATE_AGENT_MISMATCH:{job_id}")
    if state.get("projectId") != _mapping(job.get("lineage"), "lineage").get("projectId"):
        raise MultiAgentWavePreflightError(f"AGENT_STATE_PROJECT_MISMATCH:{job_id}")
    if state.get("identityRevision") != assignment.get("identityRevision"):
        raise MultiAgentWavePreflightError(f"AGENT_STATE_REVISION_MISMATCH:{job_id}")
    runtime_status = state.get("runtimeStatus")
    if runtime_status not in _ALLOWED_PRESELECTION_STATES:
        raise MultiAgentWavePreflightError(
            f"AGENT_STATE_NOT_PRESELECTION_READY:{job_id}:{runtime_status}"
        )
    if runtime_status == "REIDENTIFICATION_REQUIRED":
        _validate_reidentification_evidence(
            job=job,
            state=state,
            evidence_binding=evidence_binding,
        )
    elif runtime_status in {"RESULT_SUBMITTED", "BLOCKED"}:
        templates = _inputs_of_type(job, _SETTLED_REARM_TEMPLATE_TYPE)
        if len(templates) != 1:
            raise MultiAgentWavePreflightError(
                f"SETTLED_REARM_TEMPLATE_INPUT_REQUIRED:{job_id}"
            )
        template_ref = _mapping(templates[0].get("artifactRef"), "settled_rearm_ref")
        if template_ref.get("path") != _SETTLED_REARM_TEMPLATE_PATH:
            raise MultiAgentWavePreflightError(
                f"SETTLED_REARM_TEMPLATE_PATH_INVALID:{job_id}"
            )


def validate_multi_agent_wave_preflight(
    *,
    wave: Mapping[str, Any],
    jobs_by_id: Mapping[str, Mapping[str, Any]],
    authority_bases_by_job_id: Mapping[str, Mapping[str, Any]],
    agent_states_by_agent_id: Mapping[str, Mapping[str, Any]],
    reidentification_evidence_by_agent_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> Mapping[str, Any]:
    """Fail closed before a multi-agent wave is published or HUMAN-activatable."""
    wave = _mapping(wave, "wave")
    if wave.get("format") != "SAFOR_DISPATCH_WAVE":
        raise MultiAgentWavePreflightError("WAVE_FORMAT_INVALID")
    if wave.get("schemaVersion") != "0.14.0":
        raise MultiAgentWavePreflightError("WAVE_SCHEMA_VERSION_INVALID")
    if wave.get("status") != "PREPARED":
        raise MultiAgentWavePreflightError("WAVE_MUST_BE_PREPARED")
    if wave.get("immutable") is not True:
        raise MultiAgentWavePreflightError("WAVE_MUST_BE_IMMUTABLE")
    wave_jobs = wave.get("jobs")
    if not isinstance(wave_jobs, list) or not wave_jobs:
        raise MultiAgentWavePreflightError("WAVE_JOBS_REQUIRED")

    reidentification_evidence_by_agent_id = (
        reidentification_evidence_by_agent_id or {}
    )
    seen_job_ids: set[str] = set()
    seen_agent_ids: set[str] = set()
    seen_exclusive_keys: set[str] = set()
    write_domains: list[tuple[str, str, str, str]] = []
    product_access_allowed = bool(
        _mapping(wave.get("conflictAnalysis"), "conflict_analysis").get(
            "productRepositoryAccess"
        )
    )

    for raw_entry in wave_jobs:
        entry = _mapping(raw_entry, "wave_job")
        job_id = str(entry.get("jobId") or "")
        agent_id = str(entry.get("agentId") or "")
        if not job_id or not agent_id:
            raise MultiAgentWavePreflightError("WAVE_JOB_BINDING_INCOMPLETE")
        if job_id in seen_job_ids:
            raise MultiAgentWavePreflightError(f"DUPLICATE_WAVE_JOB:{job_id}")
        if agent_id in seen_agent_ids:
            raise MultiAgentWavePreflightError(f"AGENT_CAPACITY_EXCEEDED:{agent_id}")
        seen_job_ids.add(job_id)
        seen_agent_ids.add(agent_id)

        job = _mapping(jobs_by_id.get(job_id), f"job:{job_id}")
        try:
            validate_agent_job(job)
        except AgentJobValidationError as exc:
            raise MultiAgentWavePreflightError(
                f"JOB_CONTRACT_INVALID:{job_id}:{exc}"
            ) from exc
        identity = _mapping(job.get("identity"), "identity")
        assignment = _mapping(job.get("assignment"), "assignment")
        if identity.get("jobId") != job_id:
            raise MultiAgentWavePreflightError(f"WAVE_JOB_ID_MISMATCH:{job_id}")
        if assignment.get("agentId") != agent_id:
            raise MultiAgentWavePreflightError(f"WAVE_AGENT_ID_MISMATCH:{job_id}")

        claim = _mapping(
            _mapping(job.get("scheduling"), "scheduling").get("claimPolicy"),
            "claim_policy",
        )
        unknown_claim_fields = sorted(set(claim) - _ALLOWED_CLAIM_POLICY_FIELDS)
        if unknown_claim_fields:
            raise MultiAgentWavePreflightError(
                f"CLAIM_POLICY_UNKNOWN_FIELDS:{job_id}:{unknown_claim_fields}"
            )

        authority_basis = _mapping(
            authority_bases_by_job_id.get(job_id),
            f"authority_basis:{job_id}",
        )
        try:
            validate_authority_basis_coverage(
                job=job,
                authority_basis=authority_basis,
                authority_basis_ref=job["authorization"]["authorityBasis"],
            )
        except AgentJobValidationError as exc:
            raise MultiAgentWavePreflightError(
                f"AUTHORITY_BASIS_INVALID:{job_id}:{exc}"
            ) from exc

        state = _mapping(
            agent_states_by_agent_id.get(agent_id),
            f"agent_state:{agent_id}",
        )
        _validate_preselection_state(
            job=job,
            state=state,
            evidence_binding=reidentification_evidence_by_agent_id.get(agent_id),
        )

        if not product_access_allowed:
            _assert_no_product_access(job, job_id)

        workspace = _mapping(job.get("workspace"), "workspace")
        for exclusive_key in workspace.get("exclusiveKeys") or []:
            key = str(exclusive_key)
            if key in seen_exclusive_keys:
                raise MultiAgentWavePreflightError(
                    f"EXCLUSIVE_KEY_CONFLICT:{key}"
                )
            seen_exclusive_keys.add(key)
        for repository, branch, path in _control_write_domains(job):
            for other_job_id, other_repository, other_branch, other_path in write_domains:
                if (
                    repository == other_repository
                    and branch == other_branch
                    and _paths_overlap(path, other_path)
                ):
                    raise MultiAgentWavePreflightError(
                        f"MUTABLE_PATH_CONFLICT:{other_job_id}:{job_id}:{path}:{other_path}"
                    )
            write_domains.append((job_id, repository, branch, path))

    if seen_job_ids != set(jobs_by_id):
        raise MultiAgentWavePreflightError("WAVE_AND_JOB_SET_MISMATCH")
    if seen_job_ids != set(authority_bases_by_job_id):
        raise MultiAgentWavePreflightError("WAVE_AND_AUTHORITY_SET_MISMATCH")

    return {
        "status": "PASS",
        "jobCount": len(seen_job_ids),
        "agentCount": len(seen_agent_ids),
        "exclusiveKeyCount": len(seen_exclusive_keys),
        "mutableControlDomainCount": len(write_domains),
        "productRepositoryAccessAllowed": product_access_allowed,
    }
