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
