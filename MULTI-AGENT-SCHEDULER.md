# SAFOR Multi-Agent Scheduler

SAFOR v0.14 provides a MASTER-owned scheduler for safe parallel work across persistent agents.

## Boundary: scheduling is not chat activation

The scheduler may:

- derive READY atomic work;
- match roles, capabilities and actual provider rights;
- reserve capacity and conflict domains;
- create dedicated job branches;
- materialize immutable jobs and inbox pointers;
- publish a HUMAN start list.

For a normal `CHAT_AGENT`, the scheduler may **not** start the chat. The dispatch result is:

```text
WAITING_HUMAN_GO
```

The HUMAN deliberately types `GO` in each bound agent chat. Git push, polling, automation and host events do not replace this step.

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

## Atomic work

A work item is either:

- `COMPOSITE` — planning/container work; never dispatched directly;
- `ATOMIC` — independently executable and assessable agent work.

Every atomic work item declares:

- dependencies and join predicate;
- required capabilities;
- immutable inputs;
- product write conflict domains;
- exclusive keys;
- expected outputs;
- acceptance and evidence requirements;
- reviewer independence constraints;
- priority and readiness metadata.

## Eligibility

An agent is eligible only when:

- identity status is `ACTIVE`;
- registry dispatch is enabled;
- a normal chat identity has `BOUND` chat binding;
- required role and capabilities match;
- at least one scheduling slot is free;
- separation of duties remains satisfiable;
- actual provider rights cover the proposed job;
- no reidentification requirement exists.

## Conflict model

Parallel execution is allowed only when:

- dependencies are already accepted;
- reads are pinned to immutable revisions;
- write conflict domains do not overlap;
- exclusive keys do not overlap;
- dedicated branches are unique;
- capacities are free;
- mandates, rights and review constraints pass.

`UNKNOWN` or `PROJECT_WIDE` mutation scope conflicts with all other mutating jobs. Ambiguity is serialized.

Read-only jobs do not conflict solely because they inspect the same immutable input.

## Deterministic order

Candidates are ordered by:

1. priority descending;
2. ready-since timestamp ascending;
3. work-item ID ascending;
4. agent ID ascending.

This makes equivalent scheduling inputs replayable.

## Dispatch waves

MASTER persists every decision in:

```text
master/dispatch-waves/{waveId}.json
```

A wave records considered work, assignments, job pointers, branch names, acquired leases and the activation boundary:

```text
normalChatAgentsActivated = false
dispatchOutcome = WAITING_HUMAN_GO
humanGoRequired = true
```

## Resource leases

Before publication, MASTER reserves:

- agent slot;
- write conflict domain;
- exclusive key;
- dedicated branch.

Lease states are:

```text
RESERVED
→ ACTIVE
→ RELEASE_PENDING
→ RELEASED
```

If expiry or external effects are uncertain:

```text
RECONCILE_REQUIRED
```

Expiry never authorizes silent reassignment. MASTER must first prove whether the previous agent can still create effects.

## Git isolation

Every mutating job uses a dedicated branch:

```text
safor/job/{jobKey}/{agentKey}
```

The job is based on an immutable commit. Agents do not write the default branch, another job's branch or undeclared paths.

Branches are integrated only after:

- typed response submission;
- provider readback;
- required independent review;
- MASTER verification;
- acceptance criteria and evidence gates;
- explicit integration authority.

## Separation of duties

The author cannot perform a configured independent review of the same contribution. Review work is a separate atomic job. If no independent eligible reviewer exists, the work is blocked with `SOD_CONFLICT`.

## HUMAN start list

After safe publication, MASTER provides a compact list:

```text
Display name | agentId | jobKey | bound chat | instruction = GO
```

The HUMAN does not transport the job body. Each agent retrieves it through its own index.

## Status and fan-in

Downstream work becomes READY only when its declared join predicate is satisfied by `ACCEPTED` upstream work. `RESPONSE_SUBMITTED` alone is insufficient.

MASTER reports utilization, startable agents, running work, responses, reviews and blockers through compact status indices instead of rescanning the repository.
