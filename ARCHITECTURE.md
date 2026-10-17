# SAFOR Architecture

**SAFOR — Systemic AI Factory Orchestration Runtime**

## Architectural formula

```text
SAFOR
= MASTER Kernel
+ Operating Model
+ Factory
+ Provider Adapter
+ Project State
+ Agent Job Contract
+ Agent Workspace Protocol
+ Multi-Agent Scheduler
+ Module Self-Healing
+ HUMAN Interaction Governance
+ Evidence
+ HUMAN Authority
```

## Layers

### MASTER Kernel
Domain-neutral orchestration, authorization, state transitions, reconciliation, evidence rules and recovery.

### Operating Model
Defines roles, capabilities, mandates, decision rights, gates and separation of duties.

### Factory
Defines domain-specific Discovery, Planning, value-stream transformations, acceptance requirements, Evidence and outcome logic.

### HUMAN Interaction Governance
Controls when HUMAN cognition is valuable and when SAFOR must absorb complexity. It applies a phase-aware Cognitive Load Policy, derive-before-ask Decision Gate, unchanged-decision reuse, HUMAN-domain terminology and dynamic primary-action labels.

### Module Self-Healing
Assigns exactly one recovery profile to every embedded module. Profiles define authority type, repairability, detectors, allowed/forbidden repairs, retry budget, verification and escalation. Recovery is fail-closed when recovery-control integrity cannot be proven.

### Provider Adapter
Maps provider-neutral capabilities onto the actual GitHub/GitLab tools exposed by the host.

### Project Instance
Binds the selected Factory and Operating Model to concrete actors, repositories, state, decisions and evidence.

### Agent Job Contract
Defines the immutable MASTER-to-agent execution contract: job/package/sequence lineage, MASTER provenance, assigned identity, explicit role, versioned skills, immutable inputs, authorization boundaries, workspace/scheduling, fixed return routes, verification and the paired HUMAN-readable job projection.

### Agent Workspace Protocol
Provides repository-native persistent identities and job handoff for agent actors. MASTER writes identity, inbox contracts and authoritative job lifecycle. Agents write only their own runtime state, outbox results, evidence and audit records. HUMAN prompt copying is not authoritative job transport.

### Multi-Agent Scheduler
Builds conflict-free dispatch waves across multiple agent chats. It decomposes composite work into atomic execution units, matches required capabilities to free agent slots, acquires resource leases, isolates mutating work on dedicated Git branches and releases downstream fan-in only from accepted upstream work.

## Repository separation

```text
empishaj/SAFOR
  └─ canonical SAFOR product source and distribution

{OWNER}/safor-memory
  └─ mandatory project control/runtime memory

{OWNER}/{project-repository}
  └─ domain work artifacts
```

## Control-plane lifecycle

```text
BOOTSTRAP
  → DISCOVERY
  → PLANNING
  → SCHEDULING
  → EXECUTION
  → RECOVERY (when required)
  → OUTCOME
  → CLOSING
```

## Factory consistency

A HUMAN explicitly selects the creation type before Discovery.

The selected Factory owns:
- `discoveryContract`
- `planningContract`
- `evidenceContract`
- `flowGraph`
- `outcomeModel`

Cross-Factory substitution is forbidden.

## Evidence before belief

An external mutation is not complete merely because an agent says it happened. Completion requires authoritative provider readback or equivalent bound evidence.

Unknown mutation outcome → `RECONCILE_REQUIRED`.

## Self-healing

Self-healing is conservative and bounded:

```text
Detect
→ Classify
→ Check eligibility
→ Plan repair
→ Execute repair
→ Verify
→ Resume or escalate to HUMAN
```

Self-healing cannot expand mandates, bypass HUMAN gates/reviews, force-push, rewrite history, delete repositories, or invent evidence.

## HUMAN interface

SAFOR uses chat-native UI only. It may use native buttons, selects, cards and Markdown exposed by the host. It does not inject custom HTML/CSS/JavaScript UI.


## Repository-native agent execution

```text
MASTER
  │
  ├─ agents/index.json
  ├─ agents/{agentId}/identity.json
  ├─ agents/{agentId}/inbox/index.json
  ├─ agents/{agentId}/inbox/{jobId}.json
  ├─ agents/{agentId}/inbox/{jobId}.md
  └─ master/jobs/{jobId}.json
                    │
                    ▼
                AGENT CHAT
                    │
                    ├─ state.json
                    ├─ outbox/{jobId}.result.json
                    ├─ outbox/{jobId}.result.md
                    └─ evidence/{jobId}/
                    │
                    ▼
                  MASTER
          verifies result + evidence
```

The agent receives its identity once. Subsequent jobs are retrieved from its repository workspace. Job discovery starts from the fixed MASTER-owned `inbox/index.json` projection; the agent then verifies the referenced immutable job and authoritative `master/jobs/{jobId}.json` state before claim. A normal chat still requires an external HUMAN, automation or host-supported activation trigger; SAFOR does not assume autonomous background wakeup.


## Parallel execution safety

Parallelism is explicit, never assumed. The MASTER dispatches only ATOMIC READY work with accepted dependencies, immutable read inputs, available agent capacity and non-overlapping write conflict domains/exclusive keys.

Mutating jobs receive dedicated `safor/job/{jobKey}/{agentKey}` branches from immutable base commits. Agents do not write the default branch or another job's branch.

Each scheduling decision is persisted as a dispatch-wave record and protected by MASTER-owned resource leases. Unknown mutation overlap is serialized. Lease expiry triggers reconciliation rather than silent reassignment.

See [MULTI-AGENT-SCHEDULER.md](MULTI-AGENT-SCHEDULER.md).


## Module-wide recovery safety

Every embedded module is bound to one recovery profile in `module-self-healing-model.json`.

Automatic repair is the intersection of:
1. failure-class policy,
2. module recovery profile,
3. current SAFOR authority/policy,
4. actual provider rights.

Authoritative semantics are never guessed or silently rewritten. Derived projections may be regenerated only from verified authoritative sources. Unknown mutation effects reconcile before retry.

See [MODULE-SELF-HEALING.md](MODULE-SELF-HEALING.md).


## Phase-aware HUMAN cognitive load

SAFOR intentionally permits higher HUMAN load during Discovery because goals, priorities and value judgments cannot always be derived. Once plan and authority are established, routine interaction load falls.

```text
BOOTSTRAP          MEDIUM
DISCOVERY          HIGH
PLANNING           MEDIUM
SCHEDULING         VERY_LOW
AGENT_COORDINATION VERY_LOW
EXECUTION          LOW
RECOVERY           LOW
OUTCOME            MEDIUM
CLOSING            LOW
```

Every question passes the HUMAN Decision Gate. SAFOR derives/reuses before asking and keeps internal orchestration behind the interaction abstraction layer.

See [HUMAN-COGNITIVE-LOAD.md](HUMAN-COGNITIVE-LOAD.md).

## Deterministic Control Kernel

SAFOR separates probabilistic work from authoritative governance. HUMANs, AGENTs and providers may create artifacts, evidence, reviews and typed events; within the migrated executable transition slice they do not directly mutate authoritative SAFOR state.

The deterministic control path is:

`Projection Set + Typed Event + Pinned Models -> Predicate Evaluation -> One Transition -> New Projection Set + Effect Intents`.

The reducer is pure: no provider I/O, no LLM invocation, no wall-clock reads, no randomness and no arbitrary executable code from JSON. External mutations are emitted as effect intents and become facts only after provider outcome/readback events. Duplicate identical events are idempotent, divergent duplicates are integrity failures, transition ambiguity fails closed, and replay must reproduce the canonical state hash.

v0.11.0-rc.1 deliberately migrates only an explicit transition slice. Existing Factory, Operating Model, Agent Workspace, Scheduler and HUMAN-governance semantics remain valid and are not falsely labeled executable until migrated.

## Deterministic Acceptance

SAFOR v0.11.0-rc.2 moves Work Item acceptance into the deterministic control plane. Planning materializes one approved, immutable Acceptance Contract per executable Work Item. The contract preserves each accepted criterion and binds it to typed EVIDENCE, REVIEW or AUTHORITY requirements.

Qualitative judgment remains probabilistic where appropriate, but it enters governance as an explicit review or authority-decision record. The kernel never turns free-text LLM confidence into PASS. Independent-review policies are enforced structurally, agent self-checks remain advisory, and a required authority rejection blocks the current contract revision.

The replay-derived acceptance ledger contains pinned copies of contracts, evidence, review decisions and authority decisions. It is not a new business-authority source. The sole rc.2 transition that materializes Work Item status ACCEPTED is `WORK_ITEM_ACCEPTED` after every typed requirement passes. Work Item acceptance remains separate from business/reader outcome success.


## 0.12 Framework / Package / Workspace Boundary

SAFOR now separates four independent planes:

1. **Framework** — generic orchestration, deterministic control, agent protocol, interaction and recovery.
2. **Factory / Operating Model Packages** — separately loaded domain/organizational knowledge.
3. **Commercial Entitlement** — package-use permission only.
4. **HUMAN Project Workspace** — the only place where project-specific work is created.

The public Framework does not embed paid Factory or Operating Model model content.

### Free Website starter

`SOFTWARE_WEBSITE` is `FREE_PUBLIC`. The canonical package catalog points to the public Software Delivery Factory and SaaS Engineering Operating Model. SAFOR may resolve them from public SAFOR Git only after pinning an immutable revision/blob.

### Commercial packages

`BOOK` is `PAID_ENTITLEMENT_REQUIRED`. Paid package metadata can be public, but model content resolves only from `HUMAN_LOADED_PACKAGE` or `ENTITLED_PACKAGE_SOURCE` with independently verified entitlement.

Entitlement and organizational authority are orthogonal. Buying an Operating Model never grants any role/authority declared inside it.

### HUMAN-owned workspaces

`REMOTE_GIT` stores domain work in a HUMAN/HUMAN-organization GitHub or GitLab repository and control state in separate HUMAN-owned `safor-memory`.

`LOCAL_GIT` stores domain work in the HUMAN-selected local Git repository. SAFOR maintains Git-tracked MASTER-only control state below `.safor/`; worker jobs are forbidden from writing that prefix.

The SAFOR product repository and package sources are invalid project targets in both modes.

### Legacy disclosure

Package prototypes committed publicly before 0.12 remain part of public Git history and cannot be made confidential retroactively. Commercially protected package versions must therefore be delivered through future entitled/signed package channels and must not rely on secrecy of those legacy prototype versions.



## rc.3 Creation-Type product boundary

SAFOR now distinguishes Website creation from Software/SaaS product engineering at the Creation-Type level.

```text
SAFOR Framework
│
├── WEBSITE                         FREE_PUBLIC defaults
│   ├── safor.factory.website-delivery@1.0.0
│   └── safor.om.website-team@1.0.0
│
├── SOFTWARE_SAAS                   COMMERCIAL
│   ├── safor.factory.software-delivery
│   └── safor.om.saas-engineering
│       both selected packages must be PAID_ENTITLEMENT_REQUIRED
│       + one independent entitlement per package/version
│
└── BOOK                            COMMERCIAL
    ├── safor.factory.book-production
    └── safor.om.book-authoring
```

The Website Factory deliberately owns only the website value stream: audience/purpose, content and information architecture, experience design, web implementation, web-quality verification, publishing, observation and outcome. It explicitly escalates to `SOFTWARE_SAAS` when discovery reveals application/service lifecycle requirements.

The Software/SaaS Factory and Operating Model remain independently licensed package identities, but the Creation Profile prevents a free package from satisfying either commercial slot.

Historical Software Factory/SaaS OM versions through 1.6.0 remain public repository history and are not the current protected commercial distribution source.


## Commercial entitlement and protected delivery chain

Paid package use is a multi-stage trust chain, not a boolean field in package JSON:

```text
COMMERCIAL BASIS
      ↓
ENTITLEMENT ISSUED
      ↓
STRICT EXTERNAL VERIFICATION
(status + time + subject + trusted issuer/verifier)
      ↓
PACKAGE DELIVERY AUTHORIZED
      ↓
DELIVERY EVIDENCE
(entitlement + package + version + digest + expiry + trusted verifier)
      ↓
DOMAIN PACKAGE INTEGRITY
      ↓
FACTORY / OPERATING MODEL COMPATIBILITY
      ↓
IMMUTABLE PROJECT BINDING
```

The pure bootstrap policy receives `evaluatedAt` and trusted identity sets as explicit input. It does not read wall-clock time and never derives trust from issuer/verifier names inside a commercial record.

`ENTITLED_PACKAGE_SOURCE` requires a time-bounded `SAFOR_COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE` record. `HUMAN_LOADED_PACKAGE` is still valid for a licensed artifact supplied manually, but the entitlement verification chain remains mandatory.

rc.4 is a protocol/reference implementation. Billing, transaction processing, real entitlement issuance, network package delivery and cryptographic offline-signature verification remain external production services.


## Domain-specific single-file Framework distributions

SAFOR separates **internal modularity** from **user-facing distribution**. The Kernel remains shared; each end-user artifact embeds one domain's default Factory and Operating Model.

```text
                    shared SAFOR kernel
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
SAFOR-FRAMEWORK-   SAFOR-FRAMEWORK-  SAFOR-FRAMEWORK-
WEBSITE.json       SAAS.json          BOOK-CREATION.json
          │               │                │
 WEBSITE_CREATION   SAAS_ENGINEERING   BOOK_CREATION
 Factory default    Factory default    Factory default
 OM default         OM default         OM default
```

A domain distribution preselects its `domainId`, Creation Type, default Factory and default Operating Model. The Creation-Type question is therefore suppressed when such a file is loaded.

### Package families and Premium replacement

V2 domain packages declare a stable `packageFamily` in addition to `packageId`.

A Premium replacement may have a different packageId while remaining in the same accepted family. For example:

- `safor.factory.website-delivery` belongs to `safor.factory.website`.
- `safor.om.website-team` belongs to `safor.om.website`.

The V2 package digest covers the package family, so family identity cannot be changed without invalidating integrity.

### Bidirectional compatibility

Compatibility is evaluated in both directions:

```text
active domain
    ↓
Factory ──requires──▶ Operating Model
   ▲                      │
   └──────requires────────┘
```

A Factory may constrain acceptable Operating Model families and require capabilities, authorities, work-item types or artifact types.

An Operating Model may independently constrain acceptable Factory families and require corresponding Factory exports.

Only when both directions and the active domain pass may the pair bind.

This intentionally rejects cross-domain composition. A Book Factory and a SaaS Engineering Operating Model are incompatible even when some generic capabilities overlap, unless both explicitly support the same active domain and accept each other's package families/contracts.

### Public and commercial distributions

`SAFOR-FRAMEWORK-WEBSITE.json` is reproducibly built from public modules and committed publicly.

`SAFOR-FRAMEWORK-SAAS.json` and `SAFOR-FRAMEWORK-BOOK-CREATION.json` are defined commercial output filenames. Their completed bytes require protected licensed Factory/Operating Model inputs and therefore are not committed to the public repository.
