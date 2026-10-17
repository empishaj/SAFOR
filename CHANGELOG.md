# Changelog

## 0.13.0-rc.1

- Introduces `SAFOR_DOMAIN_PACKAGE` as the standalone JSON contract for Factory and Operating Model products.
- Changes Creation Profiles from locked package/access bundles to default Factory/Operating Model candidates with independent HUMAN overrides.
- Resolves access and commercial entitlement separately for the selected Factory and selected Operating Model.
- Allows technically compatible mixed FREE_PUBLIC/PAID_ENTITLEMENT_REQUIRED pairs, requiring entitlement only for each selected paid package.
- Keeps entitlement evidence external to package JSON so possession or modification of the artifact cannot self-authorize access.
- Adds SHA-256 integrity over the declared canonical domain contract and enforces Framework-version and Creation-Type compatibility.
- Adds explicit package-selection and Factory/Operating-Model compatibility-decision schemas.
- Extends project bindings with package selection, compatibility decision, digest, selection origin, integrity-verification and entitlement-evidence references.
- Migrates the free Website Factory and SaaS Engineering Operating Model to 1.5.0 / SAFOR_DOMAIN_PACKAGE / Framework 0.13 compatibility.
- Corrects the legacy `saf.*` package-ID mismatch by defining the domain package namespace as `safor.factory.*` and `safor.om.*`.
- Adds SH-24, INV-166 through INV-175 and CF-217 through CF-230.
- Extends exact Framework recovery coverage to 65 modules / 65 profiles.
- Adds 10 composable-package tests; total Python suite is 48 tests.


## 0.12.0-rc.1

- Reframes the public artifact as `SAFOR-FRAMEWORK` rather than an all-domain `MASTER-COMPLETE` distribution.
- Removes all Factory/Operating Model model content from the embedded Framework module set; domain packages are resolved independently.
- Defines Software / Website as the FREE_PUBLIC starter path resolvable from canonical public SAFOR Git at immutable revision/blob.
- Defines Book as PAID_ENTITLEMENT_REQUIRED and forbids paid package-content resolution from the public canonical source.
- Adds public package catalog, package-distribution policy and commercial-entitlement model.
- Separates entitlement from Operating Model authority, provider rights, mandate and project scope.
- Adds HUMAN-owned REMOTE_GIT and LOCAL_GIT project workspace models.
- Keeps separate HUMAN-controlled `safor-memory` for remote projects and adds MASTER-only Git-tracked `.safor/` for local projects.
- Forbids the canonical SAFOR repository and package sources as project targets.
- Adds SH-23, INV-148 through INV-165 and CF-194 through CF-216.
- Changes exact embedded Framework recovery coverage to 61 modules / 61 profiles.
- Adds 13 modular bootstrap/package/workspace tests; total Python suite is 38 PASS.
- Records the modular commercial product decision and the legacy disclosure boundary for pre-0.12 public prototypes.


## 0.11.0-rc.2

- Extends the Deterministic Control Kernel through Work Item acceptance.
- Adds immutable hash-bound Acceptance Contracts whose approved criteria map to typed EVIDENCE, REVIEW and AUTHORITY requirements.
- Adds replayable acceptance ledger records for provider evidence, independent review and authority decisions.
- Enforces review independence, exact authority matching, duplicate record identity protection and explicit authority rejection blocking.
- Makes E05 deterministic Acceptance Model evaluation while retaining the bound Factory evidence contract as domain input.
- Adds SH-22, INV-136 through INV-147, CF-176 through CF-193 and exact 58-module recovery coverage.
- Expands the deterministic runtime suite to 25 passing tests, including full acceptance replay, missing evidence/authority, self-review, contract tampering and rejection cases.


## 0.11.0-rc.1

- Introduces the Deterministic Control Kernel: probabilistic work is separated from authoritative governance transitions.
- Adds typed events, a closed predicate registry, declarative transition registry and external effect intents.
- Adds a pure Python reference reducer with canonical SHA-256 state hashing, duplicate-event idempotency and replay verification.
- Implements the first executable transition slice: READY derivation, project pause/resume, STOP mandate revocation, resume-after-STOP authorization boundary, and unknown external mutation reconciliation.
- Adds deterministic-control Self-Healing failure class SH-21, 54-module exact recovery coverage, kernel preflight K00A/INIT-00A and conformance CF-160 through CF-175.
- Explicitly limits rc.1 determinism claims to the migrated transition slice; full governance migration remains a GA blocker.


## 0.10.0-rc.2

- Requires every SAFOR-generated HUMAN-facing response to terminate with exactly one interaction menu.
- Adds the schema-bound `SAFOR_HUMAN_RESPONSE` envelope and mandatory HUMAN response finalizer.
- Forbids SAFOR-visible content after the terminal menu while keeping HUMAN Decision Gate semantics independent from menu presence.
- Adds safe fallback-menu regeneration, terminal-menu recovery class SH-20, module recovery coverage and conformance assertions CF-154 through CF-159.


All notable SAFOR product changes are documented here.

## 0.10.0-rc.1 — 2026-10-17

### Added
- Phase-aware HUMAN Cognitive Load Policy.
- HUMAN Decision Gate with derive-before-ask semantics.
- Reuse of unchanged HUMAN decisions and active mandates/identities.
- HUMAN-domain terminology abstraction.
- Dynamic domain-specific primary-action labels with `Weiter` fallback.
- Cognitive-load policy and decision-gate JSON Schemas.
- Interaction-menu metadata for phase/load/reason/gate outcome.
- Self-healing failure class SH-19 for HUMAN interaction governance.

### Changed
- Discovery explicitly permits HIGH necessary HUMAN cognitive load.
- Scheduling and agent coordination default to VERY_LOW HUMAN load.
- Execution and Recovery default to LOW, exception-oriented HUMAN interaction.
- Deterministic K10 Factory/Operating-Model binding no longer asks for redundant approval; K10A handles only exceptional changed/non-standard bindings.
- Internal job/branch/lease/dispatch/readback/evidence mechanics are not HUMAN decisions.
- Primary action no longer defaults to “Nächste Runde starten”; the fallback is “Weiter”.
- Product schema/kernel contract version advanced to 0.10.0.

### Product status
This version is a **Release Candidate**. HUMAN cognitive-load/communication end-to-end acceptance remains required before GA.

## 0.9.0-rc.1 — 2026-10-17

### Added
- Module-wide Self-Healing with exact one-profile-per-embedded-module coverage.
- Module Recovery Profile schema.
- Recovery modes for immutable validation, verified restore, derived regeneration and external capability rebinding.
- Dedicated module-aware failure classes SH-10 through SH-18.
- Module/profile/authority/repairability fields in repair records.
- Fail-closed recovery for self-healing control modules.
- HUMAN module-health/recovery status surface.

### Changed
- Every embedded module and integrity-manifest entry is bound to a `selfHealingProfileId`.
- Automatic repair is now the intersection of failure class, module profile, current authority/policy and actual provider rights.
- Job, Scheduler, Package, Provider, Factory, Operating Model, Schema and Conformance recovery now have explicit safety boundaries.
- Product schema/kernel contract version advanced to 0.9.0.

### Product status
This version is a **Release Candidate**. Module-wide Self-Healing end-to-end acceptance is required before GA.

## 0.8.0-rc.1 — 2026-10-17

### Added
- Canonical hierarchical Agent Job Contract.
- UUIDv7 job identity plus separate HUMAN/Git-safe job key.
- Package/work-item lineage with plan/package/dispatch/attempt/rework sequence.
- MASTER creation provenance and timestamps.
- Explicit per-job role contract.
- Explicit versioned skill descriptions and execution instructions with immutable provenance.
- Immutable read-only inputs.
- Granular provider/repository/branch/write/merge/deploy permission contract.
- Fixed result, HUMAN-report, evidence and audit return paths.
- Mandatory HUMAN-readable `inbox/{jobId}.md` projection paired with authoritative JSON.
- Explicit verification/review/acceptance and stop-condition contracts.

### Changed
- Agent jobs are no longer flat scope/permission records; they are self-describing execution contracts.
- MASTER writes and reads back job JSON and job Markdown before READY.
- Persistent agent identity no longer implicitly determines job role or skills.
- Rework receives a new jobId and retains supersession lineage.
- Product schema/kernel contract version advanced to 0.8.0.

### Product status
This version is a **Release Candidate**. Canonical explicit Job Contract end-to-end acceptance is required before GA.

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
