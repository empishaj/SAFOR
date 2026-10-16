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
  ├─ agents/{agentId}/inbox/{jobId}.json
  └─ master/jobs/{jobId}.json
                    │
                    ▼
                AGENT CHAT
                    │
                    ├─ state.json
                    ├─ outbox/{jobId}.result.json
                    └─ evidence/{jobId}/
                    │
                    ▼
                  MASTER
          verifies result + evidence
```

The agent receives its identity once. Subsequent jobs are retrieved from its repository workspace. A normal chat still requires an external HUMAN, automation or host-supported activation trigger; SAFOR does not assume autonomous background wakeup.
