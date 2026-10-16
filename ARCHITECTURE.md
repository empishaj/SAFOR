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
+ Agent Workspace Protocol
+ Multi-Agent Scheduler
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

### Provider Adapter
Maps provider-neutral capabilities onto the actual GitHub/GitLab tools exposed by the host.

### Project Instance
Binds the selected Factory and Operating Model to concrete actors, repositories, state, decisions and evidence.

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
