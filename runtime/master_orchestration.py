from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

class MasterOrchestrationError(ValueError):
    """Raised when compact status or safe scheduling invariants fail."""
_NONTERMINAL = {'WAITING_HUMAN_GO', 'GO_OBSERVED', 'CLAIMED', 'RUNNING', 'RESPONSE_SUBMITTED', 'BLOCKED', 'REWORK_READY'}
_TERMINAL_FOR_RESPONSE_EXPECTATION = {'RESPONSE_SUBMITTED', 'VERIFIED', 'ACCEPTED', 'INTEGRATED', 'REJECTED', 'CANCELED', 'SUPERSEDED'}

def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MasterOrchestrationError(f'{name} must be a mapping')
    return value

def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise MasterOrchestrationError(f'{name} must be a list')
    return value

def _pointer(value: Any, name: str) -> Mapping[str, Any]:
    pointer = _mapping(value, name)
    for field in ('repository', 'ref', 'path', 'blobSha'):
        if not str(pointer.get(field, '')).strip():
            raise MasterOrchestrationError(f'{name.upper()}_{field.upper()}_MISSING')
    return pointer

def _free_slots(agent: Mapping[str, Any]) -> int:
    max_jobs = int(agent.get('maxConcurrentJobs', 1))
    active_jobs = int(agent.get('activeJobs', 0))
    return max(0, max_jobs - active_jobs)

def _is_ready(work: Mapping[str, Any]) -> tuple[bool, str | None]:
    if work.get('executionUnit') != 'ATOMIC':
        return (False, 'NOT_ATOMIC')
    if work.get('status') != 'READY':
        return (False, 'NOT_READY')
    if work.get('dependenciesAccepted') is not True:
        return (False, 'DEPENDENCY_NOT_ACCEPTED')
    if work.get('immutableInputs') is not True:
        return (False, 'MISSING_IMMUTABLE_INPUT')
    if work.get('mandateActive') is not True:
        return (False, 'MANDATE_INACTIVE')
    if work.get('providerRightsVerified') is not True:
        return (False, 'MISSING_PROVIDER_RIGHT')
    mutation = _mapping(work.get('mutation', {}), 'mutation')
    if mutation.get('mutating') is True:
        scope = mutation.get('scope')
        if scope not in {'DECLARED', 'PROJECT_WIDE', 'UNKNOWN'}:
            return (False, 'MUTATION_SCOPE_INVALID')
        if scope == 'DECLARED' and (not (mutation.get('conflictDomains') or mutation.get('exclusiveKeys'))):
            return (False, 'MUTATION_DECLARATION_INCOMPLETE')
        if not str(mutation.get('jobBranch', '')).strip():
            return (False, 'MUTATING_JOB_BRANCH_MISSING')
    return (True, None)

def jobs_conflict(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    """Conservatively decide whether two work items may run in parallel."""
    first_mut = _mapping(first.get('mutation', {}), 'first.mutation')
    second_mut = _mapping(second.get('mutation', {}), 'second.mutation')
    if first_mut.get('mutating') is not True or second_mut.get('mutating') is not True:
        return False
    first_scope = first_mut.get('scope')
    second_scope = second_mut.get('scope')
    if first_scope in {'UNKNOWN', 'PROJECT_WIDE'}:
        return True
    if second_scope in {'UNKNOWN', 'PROJECT_WIDE'}:
        return True
    first_domains = set(first_mut.get('conflictDomains') or ())
    second_domains = set(second_mut.get('conflictDomains') or ())
    if first_domains & second_domains:
        return True
    first_keys = set(first_mut.get('exclusiveKeys') or ())
    second_keys = set(second_mut.get('exclusiveKeys') or ())
    if first_keys & second_keys:
        return True
    first_branch = str(first_mut.get('jobBranch', '')).strip()
    second_branch = str(second_mut.get('jobBranch', '')).strip()
    return bool(first_branch and first_branch == second_branch)

def _eligible_agent(work: Mapping[str, Any], agent: Mapping[str, Any], reserved_slots: Mapping[str, int]) -> bool:
    if agent.get('identityStatus') != 'ACTIVE':
        return False
    if agent.get('dispatchEnabled') is not True:
        return False
    if agent.get('chatBindingStatus') not in {'BOUND', 'NOT_APPLICABLE'}:
        return False
    if agent.get('agentKind') == 'CHAT_AGENT' and agent.get('chatBindingStatus') != 'BOUND':
        return False
    required = set(work.get('requiredCapabilities') or ())
    available = set(agent.get('capabilityIds') or ())
    if not required.issubset(available):
        return False
    if agent.get('agentId') in set(work.get('prohibitedAgentIds') or ()):
        return False
    if work.get('reviewOfAuthorAgentId') == agent.get('agentId'):
        return False
    consumed = reserved_slots.get(str(agent.get('agentId')), 0)
    return _free_slots(agent) - consumed > 0

def select_dispatch_wave(*, work_items: Sequence[Mapping[str, Any]], agents: Sequence[Mapping[str, Any]], max_parallel_jobs: int | None=None) -> dict[str, Any]:
    """Select a deterministic maximal safe wave without activating chat agents."""
    candidates: list[Mapping[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for work in work_items:
        work = _mapping(work, 'work')
        ready, reason = _is_ready(work)
        if ready:
            candidates.append(work)
        else:
            blocked.append({'workItemRef': f"work-item:{work.get('workItemId', 'unknown')}", 'reasonCode': reason, 'conflictingRefs': []})
    candidates.sort(key=lambda work: (-int(work.get('priority', 0)), str(work.get('readySince', '')), str(work.get('workItemId', ''))))
    ordered_agents = sorted(agents, key=lambda agent: str(agent.get('agentId', '')))
    ceiling = max_parallel_jobs if max_parallel_jobs is not None else sum((_free_slots(agent) for agent in ordered_agents))
    selected: list[Mapping[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    reserved_slots: dict[str, int] = {}
    for work in candidates:
        if len(assignments) >= ceiling:
            blocked.append({'workItemRef': f"work-item:{work['workItemId']}", 'reasonCode': 'CAPACITY_EXHAUSTED', 'conflictingRefs': []})
            continue
        conflicts = [f"work-item:{other['workItemId']}" for other in selected if jobs_conflict(work, other)]
        if conflicts:
            reason = 'UNKNOWN_MUTATION_SCOPE' if _mapping(work.get('mutation', {}), 'mutation').get('scope') in {'UNKNOWN', 'PROJECT_WIDE'} else 'WRITE_CONFLICT'
            blocked.append({'workItemRef': f"work-item:{work['workItemId']}", 'reasonCode': reason, 'conflictingRefs': conflicts})
            continue
        eligible = [agent for agent in ordered_agents if _eligible_agent(work, agent, reserved_slots)]
        if not eligible:
            reason = 'SOD_CONFLICT' if work.get('reviewOfAuthorAgentId') else 'NO_ELIGIBLE_AGENT'
            blocked.append({'workItemRef': f"work-item:{work['workItemId']}", 'reasonCode': reason, 'conflictingRefs': []})
            continue
        agent = eligible[0]
        agent_id = str(agent['agentId'])
        reserved_slots[agent_id] = reserved_slots.get(agent_id, 0) + 1
        selected.append(work)
        mutation = _mapping(work.get('mutation', {}), 'mutation')
        assignments.append({'workItemId': work['workItemId'], 'agentId': agent_id, 'displayName': agent['displayName'], 'jobKey': work['jobKey'], 'jobBranch': mutation.get('jobBranch'), 'dispatchState': 'WAITING_HUMAN_GO', 'normalChatActivated': False, 'humanInstruction': 'GO' if agent.get('agentKind') == 'CHAT_AGENT' else None})
    return {'format': 'SAFOR_DISPATCH_DECISION', 'schemaVersion': '0.14.0', 'assignments': assignments, 'blockedWork': blocked, 'normalChatAgentsActivated': False, 'dispatchOutcome': 'WAITING_HUMAN_GO'}

def expire_resource_lease(lease: Mapping[str, Any], *, observed_at: str) -> dict[str, Any]:
    """Expiry never permits silent reassignment."""
    lease = deepcopy(dict(_mapping(lease, 'lease')))
    if lease.get('format') != 'SAFOR_RESOURCE_LEASE':
        raise MasterOrchestrationError('LEASE_FORMAT_INVALID')
    if lease.get('status') not in {'RESERVED', 'ACTIVE', 'RELEASE_PENDING'}:
        raise MasterOrchestrationError('LEASE_NOT_EXPIRABLE')
    lease['status'] = 'RECONCILE_REQUIRED'
    lease['expiredObservedAt'] = observed_at
    lease['onExpiry'] = 'RECONCILE_REQUIRED'
    lease['silentReassignmentAllowed'] = False
    return lease

def _status_entry(job: Mapping[str, Any]) -> dict[str, Any]:
    return {'subjectId': job['jobId'], 'label': job['jobKey'], 'status': job['lifecycleStatus'], 'ref': dict(_pointer(job['masterJobStateRef'], 'masterJobStateRef'))}

def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError as exc:
        raise MasterOrchestrationError('STATUS_TIMESTAMP_INVALID') from exc

def _verified_response_by_job(response_status_entries: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    result: dict[str, list[Mapping[str, Any]]] = {}
    for raw in response_status_entries:
        entry = _mapping(raw, 'responseStatusEntry')
        job_id = str(entry.get('jobId', '')).strip()
        if not job_id:
            raise MasterOrchestrationError('RESPONSE_STATUS_JOB_ID_MISSING')
        if entry.get('readbackStatus') != 'VERIFIED_READBACK':
            continue
        if entry.get('schemaValid') is not True or entry.get('jobBindingValid') is not True:
            continue
        _pointer(entry.get('responseRef'), 'responseRef')
        result.setdefault(job_id, []).append(entry)
    return result

def build_compact_project_status(*, project_id: str, project_slug: str, revision: int, roadmap_ref: Mapping[str, Any], agent_status_index_ref: Mapping[str, Any], agent_status_entries: Sequence[Mapping[str, Any]], job_status_entries: Sequence[Mapping[str, Any]], review_status_entries: Sequence[Mapping[str, Any]], blocker_status_entries: Sequence[Mapping[str, Any]], source_refs: Sequence[Mapping[str, Any]], observed_at: str, stale_after: str | None, response_status_entries: Sequence[Mapping[str, Any]] = (), provider_readback_verified: bool | None = None, source_revisions_consistent: bool = True, stale_reason: str | None=None, full_repository_scan_performed: bool=False) -> dict[str, Any]:
    """Build routine status only from compact, read-back-verified projections."""
    if full_repository_scan_performed:
        raise MasterOrchestrationError('FULL_REPOSITORY_SCAN_FOR_ROUTINE_STATUS_FORBIDDEN')
    _pointer(roadmap_ref, 'roadmapRef')
    _pointer(agent_status_index_ref, 'agentStatusIndexRef')
    for index, source in enumerate(source_refs):
        _pointer(source, f'sourceRef[{index}]')
    jobs = [_mapping(entry, 'jobStatusEntry') for entry in job_status_entries]
    agents = [_mapping(entry, 'agentStatusEntry') for entry in agent_status_entries]
    reviews = [_mapping(entry, 'reviewStatusEntry') for entry in review_status_entries]
    blockers = [_mapping(entry, 'blockerStatusEntry') for entry in blocker_status_entries]
    verified_responses = _verified_response_by_job(response_status_entries)
    agents_to_start: list[dict[str, Any]] = []
    for agent in agents:
        startable = agent.get('startableJob')
        if startable:
            startable = _mapping(startable, 'startableJob')
            agents_to_start.append({'agentId': agent['agentId'], 'displayName': agent['displayName'], 'jobId': startable['jobId'], 'jobKey': startable['jobKey'], 'chatRef': agent['chatRef'], 'jobRef': dict(_pointer(startable['jobRef'], 'jobRef')), 'status': 'WAITING_HUMAN_GO', 'humanInstruction': 'GO'})

    def status(name: str) -> list[dict[str, Any]]:
        return [_status_entry(job) for job in jobs if job.get('lifecycleStatus') == name]
    blocked_jobs = [_status_entry(job) for job in jobs if job.get('lifecycleStatus') in {'BLOCKED', 'REJECTED', 'REWORK_READY'}]
    open_reviews = [{'subjectId': review['reviewId'], 'label': review['label'], 'status': review['status'], 'ref': dict(_pointer(review['reviewRef'], 'reviewRef'))} for review in reviews if review.get('status') in {'NOT_STARTED', 'PENDING', 'CHANGES_REQUIRED'}]
    open_blockers = [{'subjectId': blocker['blockerId'], 'label': blocker['label'], 'status': blocker['status'], 'ref': dict(_pointer(blocker['blockerRef'], 'blockerRef'))} for blocker in blockers if blocker.get('status') == 'OPEN']
    running = status('RUNNING')
    submitted = status('RESPONSE_SUBMITTED')
    verified = status('VERIFIED')
    accepted = status('ACCEPTED')
    integrated = status('INTEGRATED')

    missing_response_jobs: list[str] = []
    waived_response_jobs: list[str] = []
    verified_response_jobs: list[str] = []
    for job in jobs:
        if job.get('expectsResponse') is not True:
            continue
        job_id = str(job.get('jobId', ''))
        expectation = job.get('responseExpectation') or {}
        if expectation.get('status') == 'WAIVED_BY_DECISION':
            _pointer(expectation.get('decisionRef'), 'responseExpectationDecisionRef')
            waived_response_jobs.append(job_id)
            continue
        if verified_responses.get(job_id):
            verified_response_jobs.append(job_id)
        else:
            missing_response_jobs.append(job_id)
    all_responses = not missing_response_jobs

    if agents_to_start:
        next_action = 'Send GO in each listed bound agent chat.'
    elif open_blockers:
        next_action = 'Resolve the highest-severity open blocker in the MASTER chat.'
    elif open_reviews:
        next_action = 'Start or resolve the pending independent review.'
    elif running:
        next_action = None
    else:
        next_action = 'Plan the next safe work package.'
    counts = {'registeredAgents': len(agents), 'agentsToStart': len(agents_to_start), 'runningJobs': len(running), 'submittedJobs': len(submitted), 'verifiedJobs': len(verified), 'acceptedJobs': len(accepted), 'integratedJobs': len(integrated), 'blockedJobs': len(blocked_jobs), 'openReviews': len(open_reviews), 'openBlockers': len(open_blockers), 'verifiedResponseJobs': len(verified_response_jobs), 'missingResponseJobs': len(missing_response_jobs), 'waivedResponseJobs': len(waived_response_jobs)}

    observed = _parse_time(observed_at)
    deadline = _parse_time(stale_after)
    reasons: list[str] = []
    if stale_reason:
        reasons.append(stale_reason)
    if observed is not None and deadline is not None and observed > deadline:
        reasons.append('staleAfter exceeded')
    if source_revisions_consistent is not True:
        reasons.append('source revisions inconsistent')
    if reasons:
        freshness_status = 'STALE'
    elif provider_readback_verified is True:
        freshness_status = 'CURRENT'
    else:
        freshness_status = 'UNKNOWN'
    return {'format': 'SAFOR_PROJECT_STATUS_INDEX', 'schemaVersion': '0.14.0', 'projectId': project_id, 'projectSlug': project_slug, 'revision': revision, 'authoritative': False, 'fullRepositoryScanPerformed': False, 'roadmapRef': dict(roadmap_ref), 'counts': counts, 'agentsToStart': agents_to_start, 'runningJobs': running, 'submittedJobs': submitted, 'verifiedJobs': verified, 'acceptedJobs': accepted, 'integratedJobs': integrated, 'blockedJobs': blocked_jobs, 'openReviews': open_reviews, 'openBlockers': open_blockers, 'allExpectedResponsesReceived': all_responses, 'verifiedResponseJobIds': verified_response_jobs, 'missingResponseJobIds': missing_response_jobs, 'waivedResponseJobIds': waived_response_jobs, 'nextHumanAction': next_action, 'agentStatusIndexRef': dict(agent_status_index_ref), 'sourceRefs': [dict(ref) for ref in source_refs], 'freshness': {'status': freshness_status, 'observedAt': observed_at, 'staleAfter': stale_after, 'staleReason': reasons[0] if reasons else None, 'staleReasons': reasons, 'providerReadbackVerified': provider_readback_verified, 'sourceRevisionsConsistent': source_revisions_consistent}, 'updatedAt': observed_at}
