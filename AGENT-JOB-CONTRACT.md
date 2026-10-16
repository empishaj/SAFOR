# SAFOR Canonical Agent Job Contract

SAFOR v0.8 defines every MASTER-to-agent job as an immutable execution contract.

## Authoritative artifacts

```text
agents/{agentId}/inbox/{jobId}.json   authoritative machine contract
agents/{agentId}/inbox/{jobId}.md     derived HUMAN-readable projection
```

The Markdown projection never overrides the JSON. MASTER writes and reads back both artifacts before the job may become `READY`.

## Contract areas

1. **identity** — UUIDv7 job identity, HUMAN/Git-safe job key, type and contract revision.
2. **lineage** — project, value stream, package, work item, parent/root package and plan/package/dispatch/attempt/rework sequence.
3. **provenance** — creation/issue timestamps and exact MASTER version/run/state that created the job.
4. **assignment** — target agent, name, persistent identity revision and assignment reason.
5. **roleContract** — the role the agent must assume for this job, mission, responsibilities, prohibited role substitutions and decision rights.
6. **skills** — explicit versioned skill descriptions, execution instructions, usage and immutable skill refs.
7. **task** — objective, instruction, expected outcome, completion definition and in/out-of-scope.
8. **dependencies / inputs** — accepted predecessors and immutable read-only source revisions.
9. **authorization** — mandate basis, provider capability bounds and repository-level read/write/branch/commit/push/change-request/merge/deploy rights.
10. **workspace** — resource snapshot, read/write sets, exclusive keys and dedicated Git workspaces.
11. **scheduling** — priority, dispatch revision/wave, resource leases and claim/reconciliation policy.
12. **outputContract** — fixed machine result, HUMAN result, evidence, audit and required outputs.
13. **verificationContract** — acceptance criteria, evidence requirements, review/SoD and MASTER acceptance authority.
14. **constraints** — non-negotiable prohibitions and stop conditions.
15. **humanReadableProjection** — repository path and blob binding of the derived `job.md`.

## Permission semantics

A job permission is only an upper bound.

An operation is executable only when all four conditions hold:

```text
JOB allows
AND active mandate allows
AND SAFOR policy allows
AND actual host/provider rights allow
```

JSON never grants provider rights.

## Rework

A historical `jobId` is never reused. Rework receives a new UUIDv7 jobId and increments attempt/rework lineage. The new job may point to the superseded job.

## HUMAN-readable job

The Markdown projection contains fourteen sections:

- Job Identity
- Package & Sequence
- MASTER Provenance
- Assignment
- Role
- Skills
- Task
- Dependencies & Inputs
- Authorization
- Workspace & Git
- Scheduling
- Expected Outputs & Return Paths
- Verification & Review
- Constraints & Stop Conditions

Its purpose is auditability and HUMAN inspection. The JSON remains authoritative.
