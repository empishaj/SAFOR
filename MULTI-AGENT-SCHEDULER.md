# SAFOR Multi-Agent Scheduler

SAFOR v0.10 provides a MASTER-owned scheduler for safe parallel work across multiple persistent agent chats.

## Goal

Use available agent capacity without allowing parallel jobs to overwrite the same resources, violate dependencies, break separation of duties, or lose Git traceability.

## Scheduling formula

```text
parallel dispatch capacity
= min(
    free eligible agent slots,
    READY atomic work,
    project parallelism ceiling,
    maximal conflict-free job set
  )
```

With six ACTIVE chat agents at one slot each, six mutually conflict-free READY atomic work items can be dispatched in one wave.

## Work-package model

A work item is either:

- `COMPOSITE` — planning/container work; never dispatched directly.
- `ATOMIC` — independently executable and independently assessable agent work.

Composite work must declare child work items and a join policy. The safe baseline join is `ALL_CHILDREN_ACCEPTED`.

Every atomic work item declares:
- dependencies,
- immutable read inputs,
- write conflict domains,
- exclusive keys,
- expected outputs,
- acceptance/evidence requirements,
- required capabilities,
- reviewer constraints,
- priority and readiness metadata.

## Conflict model

Parallel execution is allowed only when:
- dependencies are already satisfied,
- reads are pinned to immutable revisions,
- write conflict domains do not overlap,
- exclusive keys do not overlap,
- dedicated job branches are unique,
- agent capacities are free,
- mandates, provider rights and separation of duties pass.

Unknown mutation overlap is treated as a conflict and serialized.

## Dispatch waves

The MASTER persists each scheduling decision in:

```text
projects/{projectSlug}/master/dispatch-waves/{waveId}.json
```

A wave contains the considered READY work, the selected work-item-to-agent assignments and the acquired resource leases.

## Resource leases

Before dispatch, the MASTER reserves:
- one agent slot,
- write conflict domains,
- exclusive keys,
- dedicated job branch names.

Leases live under:

```text
projects/{projectSlug}/master/resource-leases/{leaseId}.json
```

Lease expiry never means "safe to reassign". It means `RECONCILE_REQUIRED` until the MASTER proves the previous agent cannot still create external effects.

## Git isolation

Every mutating agent job uses a dedicated Git branch:

```text
safor/job/{jobKey}/{agentKey}
```

The job is based on an immutable commit. Agents do not write the default branch and do not write another job's branch.

Parallel contribution branches are integrated only after their own results are VERIFIED and all required review/integration gates pass.

## HUMAN-readable results

Every job writes both:

```text
agents/{agentId}/outbox/{jobId}.result.json
agents/{agentId}/outbox/{jobId}.result.md
```

The Markdown report contains:
1. Objective
2. Work Performed
3. Artifacts Changed
4. Git Trace
5. Verification
6. Result
7. Risks and Limits
8. Open Items

The JSON pins the Markdown report by repository, ref/path, blob SHA and commit SHA.

Mutating job results additionally identify:
- base commit,
- job branch,
- all result commit SHAs,
- head commit,
- changed paths,
- PR/MR reference when present,
- provider readback evidence.

## Example: six-agent wave

```text
Wave W-17
├── Agent A -> WP-04A -> branch safor/job/wp04a/agent-a
├── Agent B -> WP-04B -> branch safor/job/wp04b/agent-b
├── Agent C -> WP-05  -> branch safor/job/wp05/agent-c
├── Agent D -> WP-07A -> branch safor/job/wp07a/agent-d
├── Agent E -> WP-07B -> branch safor/job/wp07b/agent-e
└── Agent F -> WP-08  -> branch safor/job/wp08/agent-f
```

This wave is valid only if all six jobs are dependency-ready and mutually conflict-free.
