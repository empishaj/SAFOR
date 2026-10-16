# SAFOR Agent Workspace Protocol

SAFOR v0.6 introduces repository-native coordination for persistent agent chats.

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
│       │   └── {jobId}.json
│       ├── outbox/
│       │   └── {jobId}.result.json
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
- `agents/{agentId}/inbox/{jobId}.json`
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
  │
  ▼
external activation
  │
  ▼
AGENT
  ├─ loads identity
  ├─ loads state
  ├─ scans inbox
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
