# Changelog

All notable SAFOR product changes are documented here.

## 0.7.0-rc.1 — 2026-10-16

### Added
- Conflict-aware MASTER-owned Multi-Agent Scheduler.
- ATOMIC vs COMPOSITE work-package execution model with explicit fan-out/fan-in.
- Agent scheduling capacity and dispatch-enabled state in the Agent Registry.
- Parallel dispatch waves, resource leases and conservative conflict-domain locking.
- Dedicated Git job branches for mutating agent work.
- Mandatory HUMAN-readable Markdown result alongside machine-readable JSON.
- Provider-verifiable Git trace with base/head commits, result commits, changed paths and readback evidence.
- Scheduler/HUMAN status surface for agent utilization and blockers.
- Six-agent parallel scheduling, conflict serialization and HUMAN-result acceptance scenarios.

### Changed
- Agent work is dispatched only through scheduler-validated waves.
- Factory planning now requires execution/resource/parallelization declarations.
- Unknown mutation conflicts are serialized.
- Downstream fan-in waits for ACCEPTED upstream work.
- Product schema/kernel contract version advanced to 0.7.0.

### Product status
This version is a **Release Candidate**. General Availability additionally requires recorded six-agent parallel scheduling and Git-trace/HUMAN-result acceptance.

## 0.6.0-rc.1 — 2026-10-16

### Added
- Repository-native Agent Workspace Protocol.
- Persistent agent identity initialized once per agent/project.
- MASTER-owned agent registry, identity, deterministic inbox index, inbox job contracts and authoritative job lifecycle.
- AGENT-owned runtime state, outbox results, evidence and audit workspace.
- Immutable agent job contracts with explicit scope, mandate, output and evidence requirements.
- Optimistic-concurrency job claiming to prevent duplicate concurrent claims.
- MASTER verification of agent results before VERIFIED/ACCEPTED.
- Explicit external-activation rule: normal chats are not assumed to wake themselves when a job appears.
- Seven dedicated agent schemas plus the agent workspace model.

### Changed
- Agent job discovery uses the fixed `agents/{agentId}/inbox/index.json` projection; the authoritative MASTER job state is always re-read before claim, so directory enumeration is not required.
- Agent work is transported through `safor-memory` rather than HUMAN-copied job prompts.
- Execution state references MASTER-owned agent job lifecycle records without duplicating lifecycle authority.
- Product schema/kernel contract version advanced to 0.6.0.

### Product status
This version is a **Release Candidate**. General Availability still requires the explicit licensing decision and recorded GitHub, GitLab and Agent Workspace end-to-end acceptance.

## 0.5.0-rc.1 — 2026-10-16

### Changed
- Promoted the SAFOR product baseline to kernel/schema contract version 0.5.0.
- Added the dedicated modular source tree `v0.5.0/` while retaining `v0.4.0/` as historical source.
- Completed the legacy namespace migration across formats, package IDs, schema URNs and runtime identifiers.
- Canonical product source is `empishaj/SAFOR`; project runtime memory remains `{OWNER}/safor-memory`.
- Package compatibility for the v0.5.0 source tree now requires kernel `>=0.5.0 <0.6.0`.
- Release distribution is now explicitly versioned as `SAFOR-MASTER-COMPLETE-v0.5.0-rc.1.json`, with `SAFOR-MASTER-COMPLETE.json` retained as the latest alias.

### Retained
- Mandatory pre-existing writable `safor-memory` hard gate.
- Mandatory HUMAN selection of Software / Website or Buch.
- Factory-bound Discovery, Planning and Evidence.
- Chat-native HUMAN interaction only.
- Conservative bounded self-healing.
- Evidence-before-belief and authoritative provider readback.

### Product status
This version remains a **Release Candidate**. General Availability still requires the explicit licensing decision plus recorded GitHub and GitLab fresh-chat end-to-end acceptance.

## 0.4.0-rc.1 — 2026-10-16

### Added
- Self-contained `SAFOR-MASTER-COMPLETE.json`
- Guided GitHub/GitLab initialization
- Mandatory pre-existing writable `{OWNER}/safor-memory`
- Mandatory HUMAN creation-type selection: Software / Website or Book
- Factory-specific Discovery, Planning and Evidence contracts
- Chat-native HUMAN interaction only
- Conservative self-healing with bounded retry, reconciliation and HUMAN escalation
- Product/runtime separation between the SAFOR repository and project memory
- Product validation script and CI release gates
