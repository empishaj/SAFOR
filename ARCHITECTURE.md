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
