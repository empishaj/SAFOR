# SAFOR 0.14.0-rc.5 Release Notes

## Purpose

This release candidate makes the MASTER-to-subagent communication path operationally match the intended SAFOR model: MASTER writes the job into the assigned agent's personal Git INBOX and the initialized agent pulls that job after explicit HUMAN `GO`.

## Agent orchestration correction

- MASTER dispatches an immutable Agent Job to `agents/{agentId}/inbox/{jobId}.json` and updates `agents/{agentId}/inbox/index.json`.
- The job itself is never transported in the HUMAN `GO` message.
- After `GO`, the agent reads its pinned ACTIVE identity, its personal INBOX index, the selected authoritative Job JSON, MASTER job state and only the job-pinned inputs.
- Execution identity is proven from project, agentId, identityRevision, personal INBOX binding, Job assignment and dispatchRevision.
- Host-side `sessionId` or `chatBindingId` attestation is not required.
- Foreign INBOX, stale identityRevision, foreign Job assignment or stale dispatchRevision fail closed before claim.
- Git pushes, polling, inbox creation, automation, scheduler activity and background host events still never activate a normal chat agent.
- Provider compare-and-swap and exact provider readback remain mandatory for authoritative claim confirmation.
- Substantive Agent-to-MASTER communication remains typed and persisted in the Agent OUTBOX.

## Distribution files

- `SAFOR-FRAMEWORK-v0.14.0-rc.5.json`
- `SAFOR-FRAMEWORK.json`
- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- `SAFOR-TEST-ACCESS-SAAS.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json`

## Evidence boundary

Automated source, schema, reproducibility and regression PASS proves the Framework contracts and reference runtime agree. It does not prove behavior of every external LLM host, provider permission, commercial production readiness, empirical cognitive-load impact or General Availability.
