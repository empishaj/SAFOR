# SAFOR Agent Workspace Protocol

SAFOR v0.14 coordinates persistent chat agents through Git while keeping the HUMAN's operational effort small.

## Goal

A chat agent receives a stable identity once. MASTER writes immutable jobs into its personal workspace. The HUMAN starts each future job by typing exactly `GO` in the same bound agent chat. The agent retrieves the job itself and writes typed responses and evidence back for MASTER verification.

The HUMAN does not transport job prompts, artifact lists or return instructions between chats.

## Project structure

```text
projects/{projectSlug}/
├── agents/
│   ├── index.json
│   └── {agentId}/
│       ├── identity.json
│       ├── initialization.json
│       ├── state.json
│       ├── inbox/
│       │   ├── index.json
│       │   ├── {jobId}.json
│       │   └── {jobId}.md
│       ├── outbox/
│       │   ├── index.json
│       │   └── {jobId}/
│       │       └── {responseId}.json
│       ├── evidence/{jobId}/
│       └── audit/{jobId}/
└── master/
    ├── jobs/{jobId}.json
    ├── response-resolutions/{responseId}.json
    ├── scheduler/state.json
    └── status/
        ├── project.json
        ├── agents.json
        ├── jobs.json
        ├── responses.json
        ├── reviews.json
        └── blockers.json
```

## Ownership

### MASTER-owned

- agent registry and identities;
- one-time initialization artifacts;
- inbox indices and immutable job contracts;
- HUMAN-readable job projections;
- authoritative MASTER job lifecycle;
- response resolutions;
- scheduler, lease and compact status projections.

### AGENT-owned within the job authorization

- its own runtime state;
- typed response objects and response-index update;
- job evidence and audit records;
- product artifacts only in the explicitly assigned work repository, branch and paths.

These ownership rules are protocol limits. Actual provider permissions remain authoritative. JSON cannot grant missing rights.

## One-time chat initialization

MASTER generates an immutable initialization artifact containing:

1. project and MASTER identity;
2. technical `agentId`;
3. separate HUMAN-readable `displayName`;
4. control repository;
5. exact identity, state and inbox-index pointers;
6. communication contract;
7. fail-closed reidentification behavior.

The HUMAN pastes the generated prompt once into a new chat. The agent reads back and validates the referenced identity. Future jobs use the same continued chat and need no new job prompt.

If chat continuity or identity cannot be proven, the agent does not guess. It emits `REIDENTIFICATION_REQUIRED` and directs the HUMAN back to MASTER.

## Activation

A normal `CHAT_AGENT` begins work only after direct HUMAN input:

```text
GO
```

The token is trimmed and may be case-insensitive, but additional job text is not allowed. The activation is bound once to the selected job and dispatch revision.

A Git push, repository change, polling loop, scheduler decision, automation or host event does not activate a normal chat agent. The scheduler publishes a safe job as `WAITING_HUMAN_GO` and lists it for the HUMAN.

Service agents, when supported, use a separate explicit activation contract. Their semantics must not be silently applied to normal chat agents.

## Pointer-only job discovery

After `GO`, the agent reads in order:

1. pinned identity;
2. own state;
3. fixed personal `inbox/index.json`;
4. selected immutable job;
5. selected authoritative `master/jobs/{jobId}.json`;
6. only inputs explicitly pinned by the job.

The normal flow forbids:

- global repository search;
- project-tree full scan;
- reading other agents' inboxes;
- unreferenced artifact discovery.

The inbox index is only a discoverability projection. Job contract and MASTER job state remain authoritative.

## Preflight before mutation

The agent verifies:

- identity status and chat binding;
- identity revision and exact assignment;
- HUMAN-GO evidence for the selected job;
- job and projection blob identities;
- active mandate;
- role, skill, domain and technology compatibility;
- immutable inputs;
- dedicated product branch and allowed paths;
- separate product and response write targets;
- actual provider capabilities and rights;
- active resource leases;
- STOP, PAUSE and stale-reference conditions.

A failed preflight produces a typed blocker response before unauthorized product mutation.

## Typed responses

Every job binds exact templates, schemas and paths for:

- `JOB_RESULT`
- `JOB_ERROR`
- `CLARIFICATION_REQUEST`
- `CAPABILITY_MISMATCH`
- `IMPROVEMENT_PROPOSAL`

The response is immutable and tied to project, job, package, work item, agent, identity revision and observed job blob.

A later MASTER resolution is a separate immutable artifact. It may acknowledge the response, document a decision or reference a superseding job. It never rewrites the original response.

## Minimal agent chat

Detailed work, checks, errors, conflicts and evidence are Git artifacts. The agent chat emits only one-line statuses:

- `READY`
- `STARTED`
- `SUBMITTED`
- `BLOCKED`
- `REIDENTIFICATION_REQUIRED`

The agent does not conduct domain discussion or scope negotiation with the HUMAN. MASTER owns those interactions.

## Authoritative lifecycle

```text
PREPARED
→ WAITING_HUMAN_GO
→ GO_OBSERVED
→ CLAIMED
→ RUNNING
→ RESPONSE_SUBMITTED
→ VERIFIED
→ ACCEPTED
→ INTEGRATED
```

Possible branches include `BLOCKED`, `REJECTED`, `REWORK_READY`, `CANCELED` and `SUPERSEDED`.

`RESPONSE_SUBMITTED` is not verification. `VERIFIED` is not acceptance. `ACCEPTED` is not integration.

## Rework

A substantial task, role, skill or authority change creates a new job. Historical job IDs are never reused. Rework records:

- new UUIDv7 job ID;
- incremented attempt/rework lineage;
- `supersedesJobId`;
- triggering conflict or decision reference.

## Concurrency

Claims use optimistic concurrency on the agent state. Mutating jobs use dedicated branches and leases. Ambiguous mutation overlap is treated as a conflict. Lease expiry produces `RECONCILE_REQUIRED`; it never authorizes silent reassignment.

## MASTER status

Routine status is built from compact registry and status indices. MASTER resolves detailed jobs, responses, reviews or provider mutations only through exact pointers when status is stale, contradictory, materially risky or explicitly requested.

The HUMAN can ask MASTER which agents need `GO`, what is running, what is blocked, which reviews remain open and whether all expected responses arrived without inspecting raw JSON.
