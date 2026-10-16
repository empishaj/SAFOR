# SAFOR Agent Workspace Protocol

SAFOR v0.10 uses repository-native coordination for persistent agent chats.

## Goal

An agent receives its identity once. The MASTER then writes jobs into the agent's repository workspace. The agent retrieves the job itself and writes its result and evidence back for MASTER verification.

The HUMAN no longer transports full job prompts between chats.

## Project structure

```text
projects/{projectSlug}/
├── agents/
│   ├── index.json
│   └── {agentId}/
│       ├── identity.json
│       ├── state.json
│       ├── inbox/
│       │   ├── index.json
│       │   ├── {jobId}.json
│       │   └── {jobId}.md
│       ├── outbox/
│       │   ├── {jobId}.result.json
│       │   └── {jobId}.result.md
│       ├── evidence/
│       │   └── {jobId}/
│       └── audit/
└── master/
    └── jobs/
        └── {jobId}.json
```

## Ownership

### MASTER-owned
- `agents/index.json`
- `agents/{agentId}/identity.json`
- `agents/{agentId}/inbox/index.json` — non-authoritative job discovery projection
- `agents/{agentId}/inbox/{jobId}.json`
- `agents/{agentId}/inbox/{jobId}.md` — HUMAN-readable non-authoritative job projection
- `master/jobs/{jobId}.json`

### AGENT-owned
- `agents/{agentId}/state.json`
- `agents/{agentId}/outbox/{jobId}.result.json`
- `agents/{agentId}/evidence/{jobId}/`
- `agents/{agentId}/audit/`

The workspace policy does not create provider permissions. Actual GitHub/GitLab rights remain authoritative.

## One-time agent bootstrap

The agent chat needs only:
1. control repository,
2. project ID,
3. agent ID.

It then loads its own `identity.json` and activation contract.

Identity is stable across jobs. Changing immutable identity fields requires explicit HUMAN re-identification and a new identity revision.

## Job flow

```text
MASTER
  │
  ├─ writes immutable inbox job
  ├─ writes master/jobs state = READY
  ├─ updates inbox/index.json projection
  │
  ▼
external activation
  │
  ▼
AGENT
  ├─ loads identity
  ├─ loads state
  ├─ reads fixed inbox/index.json
  ├─ reads referenced immutable job contract
  ├─ reads authoritative master job state
  ├─ verifies assignment + identity revision
  ├─ verifies mandate + provider rights
  ├─ claims using optimistic concurrency
  ├─ performs authorized work
  ├─ writes evidence
  └─ writes outbox result
  │
  ▼
MASTER
  ├─ reads claim/result
  ├─ verifies job/identity binding
  ├─ verifies evidence and external mutations
  ├─ applies review / SoD / Factory criteria
  └─ advances authoritative job lifecycle
```

## Deterministic job discovery

The agent does **not** rely on listing an inbox directory. It reads the fixed path `agents/{agentId}/inbox/index.json`.

That index is only a discoverability projection. It may point to AVAILABLE or REWORK_AVAILABLE jobs, but it never decides whether a job is actually claimable. Before claiming, the agent must read the referenced immutable job contract, verify its blob identity, and read the authoritative `master/jobs/{jobId}.json` record. If the index is stale, the authoritative artifacts win.

This keeps job pickup deterministic even when a host exposes file read/write but no repository-directory listing primitive.

## Authoritative lifecycle

`master/jobs/{jobId}.json` is authoritative:

`READY → CLAIMED → RUNNING → RESULT_SUBMITTED → VERIFIED → ACCEPTED`

Rework:

`RESULT_SUBMITTED → REJECTED → REWORK_READY → CLAIMED`

The agent's local `state.json` reports runtime activity but is not authoritative project status.

## Concurrency

Claims use optimistic concurrency on the provider-observed current agent state revision/blob identity. If two runtimes try to claim the same job, only one current-state write may succeed. The stale claimant must reconcile and may not execute as if the claim succeeded.

## Result semantics

An agent result is a **submission claim**, not acceptance.

Only the MASTER may mark a job VERIFIED or ACCEPTED after:
- result/job/identity binding is valid,
- required evidence exists,
- provider mutations are read back,
- required reviews and separation of duties pass,
- Factory evidence/acceptance requirements pass.

## Activation limitation

A normal chat does not automatically wake when a repository file changes. SAFOR therefore requires an external activation trigger: HUMAN, automation or a host-supported agent trigger.

The activation instruction can be minimal: **check workspace**. The job content itself remains in the repository.


## HUMAN-readable result

Every job writes a machine-readable result and a HUMAN-readable Markdown report.

The Markdown report is the default HUMAN result view and must contain:
- Objective
- Work Performed
- Artifacts Changed
- Git Trace
- Verification
- Result
- Risks and Limits
- Open Items

The JSON result pins the Markdown report by control repository, ref/path, blob SHA and commit SHA.

For mutating jobs, the result also reports the dedicated work branch, immutable base commit, all produced commit SHAs, head commit, changed paths, PR/MR reference when present, and provider readback evidence.

The MASTER verifies these Git claims before VERIFIED/ACCEPTED.


## Parallel scheduling

Agent work is not dispatched merely because an inbox exists. SAFOR v0.10 routes agent jobs through the conflict-aware Multi-Agent Scheduler.

The scheduler verifies dependency readiness, capability match, free agent slots, separation of duties, immutable read inputs and resource conflicts before dispatch. Mutating jobs receive dedicated `safor/job/{jobKey}/{agentKey}` branches.

See [MULTI-AGENT-SCHEDULER.md](MULTI-AGENT-SCHEDULER.md).


## Canonical job contract

Every dispatch uses the v0.8 canonical Agent Job Contract. The JSON is authoritative and explicitly binds package/sequence lineage, MASTER provenance, target identity, role, versioned skills, task scope, immutable inputs, granular authorization, resource/Git workspace, dispatch wave/leases, result/evidence/audit return paths, acceptance criteria, review and stop conditions.

MASTER also renders `inbox/{jobId}.md`. Its blob SHA is pinned in the JSON. Both artifacts are provider-read back before the job is exposed as READY.
