# SAFOR 0.14.0-rc.5 — Framework Audit: MASTER → Personal INBOX → Agent Pull

## Scope

This audit covers only the SAFOR Framework. It verifies the corrected MASTER-to-subagent communication contract introduced in `0.14.0-rc.5`.

## Audit trigger

The previous contract required a normal chat agent to prove a host-level chat/session binding before it could claim work. In ordinary separated LLM chat threads, the agent may have no authoritative host API exposing a stable session identifier or attested chat-binding handle. A Git declaration that a chat is `BOUND` cannot independently prove that the current chat thread is that bound session.

The required product behavior is therefore:

1. MASTER creates or reuses a persistent agent identity.
2. MASTER writes an immutable Job JSON to that agent's personal Git INBOX.
3. MASTER updates the personal INBOX index.
4. The agent remains idle.
5. HUMAN types exactly `GO` in the initialized agent chat.
6. The agent reads its pinned identity and personal INBOX.
7. The agent selects the next eligible assigned Job.
8. The agent validates assignment, identity revision, dispatch revision, role, skills, mandate and actual provider rights.
9. The agent atomically claims exactly that Job.
10. The agent performs the work and writes a typed response to its OUTBOX for MASTER.

## Audit findings

| ID | Audit point | rc.5 result |
|---|---|---|
| A-01 | Host `sessionId` required for HUMAN-GO evidence | **CLOSED** — removed from active schema/runtime contract |
| A-02 | Host `chatBindingId` required for claim authority | **CLOSED** — removed from active schema/runtime/provider claim binding |
| A-03 | `CONTINUED_CHAT_HISTORY` required as identity proof | **CLOSED** — Agent Identity now binds to pinned identity + personal INBOX |
| A-04 | `VERIFY_CHAT_BINDING_BOUND` required before claim | **CLOSED** — replaced by personal-INBOX and identity checks |
| A-05 | Job delivered through copied chat prompt | **CLOSED** — authoritative Job transport is personal Git INBOX |
| A-06 | Git push/inbox creation may automatically start agent | **PASS / FORBIDDEN** — explicit HUMAN `GO` remains mandatory |
| A-07 | Agent may take another agent's Job | **PASS / FAIL-CLOSED** — personal INBOX project/agent/identityRevision and Job assignment are checked |
| A-08 | Stale Job may be claimed | **PASS / FAIL-CLOSED** — dispatchRevision and identityRevision remain bound |
| A-09 | In-memory claim considered authoritative | **PASS / FORBIDDEN** — provider CAS + exact full-state readback remain mandatory |
| A-10 | Subagent returns substantive work in HUMAN chat | **PASS / FORBIDDEN** — typed Git OUTBOX remains authoritative |
| A-11 | Materialized Framework differs from canonical sources | **PASS** — reproducible bundle and domain distributions validated |
| A-12 | Regression could silently restore host-session dependency | **CLOSED** — dedicated `test_inbox_pull_audit_rc5.py` added |

## Canonical communication contract

```text
MASTER
  |
  | writes immutable Job
  v
agents/{agentId}/inbox/{jobId}.json
agents/{agentId}/inbox/index.json
  |
  | agent remains idle
  v
HUMAN: GO
  |
  v
initialized agent
  |
  | reads pinned identity + personal INBOX
  | selects eligible assigned Job
  | validates identityRevision + dispatchRevision + role/skills/rights
  | provider-CAS claim + exact readback
  v
WORK
  |
  v
agents/{agentId}/outbox/{jobId}/{responseId}.json
  |
  v
MASTER
```

## Security boundary after the correction

rc.5 deliberately does **not** claim that the external LLM host cryptographically identifies a chat thread.

Execution authority is instead based on:

- pinned ACTIVE Agent Identity;
- exact `agentId`;
- exact `identityRevision`;
- personal INBOX binding;
- Job assignment to that Agent;
- exact `dispatchRevision`;
- explicit HUMAN `GO`;
- actual provider read/write rights;
- provider compare-and-swap;
- exact committed-state provider readback;
- single-use activation consumption.

This is a deliberate architecture boundary, not an implicit host guarantee.

A host still must expose the repository/provider capabilities needed by the agent to read its INBOX and perform its authorized work. SAFOR JSON cannot manufacture unavailable tools or provider permissions.

## Automated evidence

### Materialization

- Workflow: `SAFOR rc.5 Materialization`
- Run: `39129067804`
- Result: **SUCCESS**
- Materialization commit: `2d65a8e`
- Framework modules / recovery profiles: **93 / 93**
- Release checksums: **7 / 7 PASS**
- Full suite during materialization: **267 tests PASS**

### Post-audit regression

- Dedicated regression: `tests/test_inbox_pull_audit_rc5.py`
- Focused validation run: `39129220852` — **SUCCESS**
- Standard SAFOR validation run: `39129220880` — **SUCCESS**
- Full suite after audit regression: **275 tests PASS**

## Verdict

**PASS — audit root cause closed at Framework contract level.**

SAFOR `0.14.0-rc.5` now implements the intended orchestration model: **MASTER writes the Job to the assigned agent's personal INBOX; the initialized agent pulls and claims that Job after explicit HUMAN `GO`.**

The former host-session/chat-binding proof is no longer an execution prerequisite.
