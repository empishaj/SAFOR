# SAFOR Canonical Agent Job Contract

SAFOR v0.14 defines every MASTER-to-agent job as an immutable, self-describing execution contract.

## Authoritative artifacts

```text
agents/{agentId}/inbox/{jobId}.json   authoritative machine contract
agents/{agentId}/inbox/{jobId}.md     derived HUMAN-readable projection
master/jobs/{jobId}.json              authoritative lifecycle
```

The Markdown projection may never override or expand the JSON contract. MASTER writes and reads back both job artifacts before publishing the job as `WAITING_HUMAN_GO`.

## Required contract areas

1. **Identity** — UUIDv7 job identity, Git-safe key, type, contract revision and immutability.
2. **Lineage** — project, value stream, package, work item, sequence, attempt, rework, predecessor and conflict references.
3. **Provenance** — creation/issue timestamps and exact MASTER version, run and state revision.
4. **Assignment** — target agent ID, display name, identity revision, immutable identity pointer and reason.
5. **Domain context** — creation type, domain, Factory, Operating Model and compatibility decision.
6. **Role contract** — mission, responsibilities, prohibited substitutions and decision boundaries.
7. **Skills** — explicit versioned descriptions, execution instructions and immutable source pointers.
8. **Task** — objective, instruction, expected outcome, completion definition, scope, exclusions, assumptions and acceptance criteria.
9. **Dependencies and inputs** — accepted predecessors and immutable read-only source pointers.
10. **Authorization** — mandate, actual-rights requirement, separate work/control repository rights and explicit prohibitions.
11. **Workspace** — product repository, dedicated branch, immutable base commit, allowed paths, response workspace and conflict keys.
12. **Scheduling** — priority, dispatch revision, wave, leases and `HUMAN_GO_REQUIRED` claim policy.
13. **Product output contract** — required artifact types and exact product write target.
14. **Response contracts** — all five typed response templates, schemas, control-repository targets, response index and resolution schema.
15. **Communication contract** — minimal chat-output model and prohibition of HUMAN domain conversation.
16. **Verification contract** — evidence, independent review, acceptance and integration authority.
17. **Constraints** — STOP/PAUSE/stale/mismatch behavior and prohibitions against scope expansion, role switch, self-acceptance, MASTER-state writes, automatic job switching and prompt transport.
18. **HUMAN-readable projection** — immutable repository/ref/path/blob pointer.

## Activation semantics

Publication of a job does not activate a normal chat agent. The job enters:

```text
WAITING_HUMAN_GO
```

The HUMAN opens the already bound agent chat and types exactly `GO`. The agent binds single-use GO evidence to that job and dispatch revision before claiming.

A Git push, scheduler, polling, automation or host event cannot replace this HUMAN action for a normal `CHAT_AGENT`.

## Permission semantics

A declared job permission is only an upper bound.

An operation is executable only when:

```text
JOB allows
AND active mandate allows
AND SAFOR policy allows
AND actual host/provider rights allow
```

JSON never creates credentials, provider capabilities or repository rights.

## Separate write targets

A mutating job normally has two independent targets:

```text
WORK_REPOSITORY
  dedicated job branch
  allowed product paths

CONTROL_REPOSITORY
  agent state
  typed responses
  response index
  evidence and audit
```

Product-write permission never grants response-write permission. Response-write permission never grants product-write permission.

Direct default-branch mutation, merge and deployment are forbidden unless a separate later authority explicitly performs those operations outside the agent job.

## Response contracts

Every job binds all five response types:

| Type | Purpose | Blocking |
|---|---|---:|
| `JOB_RESULT` | Completed work, outputs, Git trace, checks and open items | no; current execution ends as submitted |
| `JOB_ERROR` | Technical failure and safe-state evidence | yes |
| `CLARIFICATION_REQUEST` | Ambiguous, incomplete or contradictory job | yes |
| `CAPABILITY_MISMATCH` | Role, skill, domain, technology or identity mismatch | yes |
| `IMPROVEMENT_PROPOSAL` | Advisory non-blocking improvement | no |

Each binding contains response type, exact immutable template pointer, schema pointer and deterministic write target.

A response cannot grant authority, change role, expand scope or alter the job. MASTER records its resolution separately.

## Conflict fields

Blocking responses contain at least:

```text
conflictId
conflictType
severity
description
blockedStep
affectedRefs
suggestedResolution
status = OPEN
responseTemplateVersion
```

The agent stops the affected execution before further product mutation.

## Lifecycle separation

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

These states are not interchangeable:

- submission is the agent's claim;
- verification checks binding, evidence and provider effects;
- acceptance applies Factory, review and governance criteria;
- integration records the actual merge or equivalent adoption.

## Rework and supersession

A historical job ID is never reused. Rework or substantial changes produce a new UUIDv7 job with:

- incremented attempt/rework lineage;
- `supersedesJobId`;
- immutable conflict/decision reference;
- fresh authority, input and branch snapshots.

## Independent review

When independent review is required, the reviewer must differ from the contribution author. The reviewer receives a separate job with its own role, skills, inputs, branch/read scope and response contracts.

## Minimal chat output

The agent chat is not a result store. It may emit only `READY`, `STARTED`, `SUBMITTED`, `BLOCKED` or `REIDENTIFICATION_REQUIRED`, each as one short line. Detailed content belongs in Git.
