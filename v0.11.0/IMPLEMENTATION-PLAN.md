# SAFOR 0.11.0-rc.1 — Deterministic Control Kernel Implementation Plan

## Objective

Formalize the existing SAFOR governance rules as executable, replayable control semantics without replacing Factories, Operating Models, Agent Workspace, Scheduler, HUMAN Decision Gate, Self-Healing, or Terminal HUMAN Response governance.

The target invariant is:

> Probabilistic actors may create proposals, artifacts, reviews, evidence and external outcomes; only the deterministic SAFOR Control Kernel may authorize and materialize authoritative state transitions.

## Scope

### In scope for rc.1

1. Typed append-only SAFOR events.
2. Declarative transition definitions.
3. Closed predicate registry with no arbitrary code execution from JSON.
4. Declarative effect intents separated from provider execution.
5. Pure deterministic transition evaluator/reducer reference implementation.
6. Canonical JSON hashing.
7. State snapshots with last-applied event sequence and state hash.
8. Replay verification.
9. Deterministic READY lifecycle example transitions.
10. Deterministic pause/stop/resume examples.
11. Duplicate-event idempotency and event-integrity checks.
12. Unknown external mutation outcome -> RECONCILE_REQUIRED transition.
13. Kernel binding, recovery profiles, conformance assertions and reproducible bundle integration.
14. Deterministic test vectors executable in CI.

### Explicitly deferred

- Full conversion of every Factory acceptance criterion to typed executable predicates.
- Full Agent Job lifecycle conversion.
- Full Scheduler implementation in the new reducer.
- Full Self-Healing transition conversion.
- Complete event-sourced replacement of existing state aggregates.
- Historical reconstruction of pre-0.11 projects.

Existing 0.10 aggregates remain authoritative persisted projections during rc.1. Event replay is introduced as a verified deterministic control mechanism, not as an immediate destructive migration.

## Architecture

External HUMAN, AGENT and PROVIDER observations become typed events. The kernel validates the event, selects transitions by deterministic registry order, evaluates closed predicates against explicit context, applies declarative state effects to a copy of the input state, and returns a transition result plus zero or more effect intents.

No transition evaluator may:
- call an LLM;
- call GitHub/GitLab;
- read wall-clock time;
- generate randomness;
- infer HUMAN approval;
- mutate input state in place;
- execute an external effect.

## Deterministic function

`reduce(state, event, pinnedModels) -> transitionResult`

For identical canonical inputs and identical model revisions, the logical output and resulting state hash must be identical.

## Event ordering

Events carry:
- eventId
- sequence
- eventType
- occurredAt
- source
- subject
- correlationId
- causationId
- payload
- evidenceRefs

`sequence` is authoritative for replay order. `occurredAt` is evidence/context and never a tie-breaker for state application.

## Transition semantics

Each transition defines:
- transitionId
- priority
- aggregate
- accepted event types
- from-state matcher
- guard expression
- effects
- emitted effect intents
- resulting transition status

Candidate transitions are sorted by:
1. priority DESC
2. transitionId ASC

At most one authoritative transition may apply for an aggregate/event pair in rc.1. Ambiguity is a control failure.

## Predicate model

Only predicate identifiers from the pinned predicate registry may execute. rc.1 includes structural predicates for:
- field equality / membership
- all dependencies accepted
- active mandate coverage
- required inputs resolvable
- resource declaration complete
- duplicate event detection
- event sequence continuity
- external effect type classification

No free-form executable expression is permitted.

## Effects

State effects are restricted to a closed operation set:
- SET
- SET_FROM_EVENT
- APPEND_UNIQUE
- INCREMENT
- REMOVE_MATCHING

External mutations are represented as `SAFOR_EFFECT_INTENT` records and executed outside the pure reducer. Provider outcomes return as new events.

## Replay

Every deterministic state snapshot records:
- lastAppliedEventSequence
- lastAppliedEventId
- modelRevision
- stateHash

Replay from a genesis snapshot plus ordered events must reproduce the same state hash.

Existing projects migrate with a verified `MIGRATION_GENESIS_SNAPSHOT`; historical events are never fabricated.

## rc.1 executable transition slice

The first executable slice proves the architecture with:
- PLANNED -> READY when readiness guards pass
- READY -> PAUSED on valid pause event
- PAUSED -> READY on valid resume event when readiness guards still pass
- any executable state -> STOPPED on valid stop event
- external mutation outcome unknown -> RECONCILE_REQUIRED
- duplicate event -> idempotent no-op
- same eventId with divergent payload -> integrity failure

## Acceptance criteria

The release candidate is acceptable only when:

1. All new JSON schemas parse.
2. Every new embedded module has exactly one recovery profile.
3. Bundle reproducibility passes.
4. Existing SAFOR validation remains green.
5. Deterministic test vectors pass in CI.
6. Same state + same event + same pinned models yields identical state hash.
7. Replay yields the stored state hash.
8. Duplicate event is idempotent.
9. Divergent duplicate event is rejected.
10. No arbitrary code is executable from transition/predicate JSON.
11. Reducer contains no provider or LLM integration.
12. Unknown external mutation outcome deterministically produces RECONCILE_REQUIRED.
13. Existing 0.10 Factory/Operating Model/Agent/Scheduler semantics remain intact unless explicitly bound into the deterministic rc.1 slice.

## Release boundary

Version: `0.11.0-rc.1`

This release candidate proves the deterministic control substrate. It must not claim that every existing SAFOR rule is already executable. Remaining natural-language governance rules are tracked as migration work for later 0.11 release candidates.
