# SAFOR 0.14.0-rc.6 Operational Readiness Baseline

## Status

**FROZEN TARGET / IMPLEMENTATION AND EVIDENCE PENDING**

This document freezes the HUMAN-approved operating target for the rc.6 Operational Readiness candidate. Later implementation may strengthen safety or evidence, but must not silently change this interaction model.

## 1. HUMAN entry point

The HUMAN uploads exactly one applicable SAFOR Domain Framework JSON into the MASTER chat, for example:

- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`

The Domain Framework is the end-user entry artifact. Embedded/default Factory and Operating Model selections are resolved by SAFOR. Compatible replacement packages may be supplied separately when authorized.

## 2. MASTER ownership

The MASTER chat is the only domain-facing HUMAN interface in normal operation.

MASTER owns:

- guided discovery and goal clarification;
- planning and Work Package decomposition;
- role/skill selection;
- Agent Job compilation and dispatch;
- status aggregation;
- review and rework coordination;
- acceptance and integration governance;
- escalation of genuine HUMAN decisions.

The HUMAN must not transport technical job context between chats.

## 3. One-time subagent initialization

Each normal `CHAT_AGENT` receives one MASTER-generated initialization prompt when its chat is created.

That initialization establishes persistent:

- project identity;
- agentId and displayName;
- identityRevision;
- personal Git INBOX binding;
- allowed communication model;
- authority and safety boundaries.

The initialization prompt is identity/bootstrap transport, not recurring Job transport.

## 4. Job transport

After initialization, Job instructions are never copied through HUMAN chat.

MASTER persists an immutable Agent Job under the assigned Agent's personal Git INBOX and updates the bounded inbox index.

The Agent discovers only:

1. its pinned identity;
2. its personal INBOX index;
3. the selected immutable Agent Job;
4. the authoritative MASTER Job state as a read-only guard;
5. explicitly pinned Job inputs.

Normal execution must not require repository-wide discovery.

## 5. HUMAN GO activation

A normal initialized subagent starts no Job merely because Git changed.

The exclusive normal activation signal is an explicit HUMAN message:

`GO`

The GO message contains no Job payload, role instructions, file paths or domain context.

After GO, the Agent validates identity, inbox assignment, Job/dispatch revision, role/skill fit, mandate, STOP/PAUSE state and actual provider rights before claiming.

## 6. Claim authority

The Agent never mutates `master/jobs/{jobId}.json`.

The atomic execution claim is a provider-confirmed compare-and-swap on the assigned Agent's own:

`agents/{agentId}/state.json`

Claim authority requires exact provider readback, persisted single-use activation consumption and matching `currentJob.claimId`.

Product mutation before authoritative claim confirmation is forbidden.

MASTER later reconciles its own Job lifecycle from verified claim and response evidence.

## 7. Agent-to-MASTER communication

Substantive subagent output is persisted through typed Git responses:

- `JOB_RESULT`
- `JOB_ERROR`
- `CLARIFICATION_REQUEST`
- `CAPABILITY_MISMATCH`
- `IMPROVEMENT_PROPOSAL`

The subagent chat exposes only minimal operational status.

Subagents do not conduct normal domain discussion with the HUMAN.

## 8. Review and acceptance

Submission, verification, review, acceptance and integration are distinct states.

An Agent may not self-accept its own contribution. When independent review is required, reviewer identity must differ from author identity.

MASTER remains the acceptance authority unless an explicit HUMAN authority gate is required.

## 9. Operational Readiness gates

The rc.6 candidate may claim Operational Readiness only after evidence for all required gates:

1. `OR-01_EXACT_RELEASE_PROVENANCE_PASS`
2. `OR-02_AUTOMATED_EXACT_HEAD_VALIDATION_PASS`
3. `OR-03_HUMAN_GO_REAL_GIT_PASS`
4. `OR-04_AGENT_STATE_CAS_PASS`
5. `OR-05_MASTER_RECONCILIATION_PASS`
6. `OR-06_REAL_JOB_RESULT_PASS`
7. `OR-07_INDEPENDENT_REVIEW_PASS`
8. `OR-08_FAILURE_RECOVERY_PASS`
9. `OR-09_REFERENCE_MIGRATION_PASS`
10. `OR-10_SINGLE_AGENT_OPERATION_PASS`
11. `OR-11_MULTI_AGENT_OPERATION_PASS`

`OPERATIONAL_READY_SINGLE_AGENT` requires OR-01 through OR-10.

`OPERATIONAL_READY_MULTI_AGENT` additionally requires OR-11.

General Availability remains a separate, stricter release state.

## 10. Fail conditions

The following are architectural failures for this operating mode:

- recurring HUMAN-copied Job prompts;
- HUMAN transport of Job context between MASTER and subagent chats;
- automatic normal chat-agent activation from Git, scheduler, polling or host event;
- Agent mutation of MASTER-owned Job lifecycle state;
- product mutation before provider-confirmed claim;
- untyped substantive result delivery only through chat;
- self-review/self-acceptance where independent review is required;
- release PASS evidence that is not bound to the exact validated source and artifact identities.

## Decision

This operating target is frozen for SAFOR 0.14.0-rc.6 Operational Readiness work.
