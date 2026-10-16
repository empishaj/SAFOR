# SAFOR Architecture — v0.5

## Formula

```text
SAFOR
= MASTER Kernel
+ Memory Provider Adapter
+ Operating Model
+ Factory
+ Work Provider Adapter(s)
+ Project State
+ Evidence
+ Output Provenance
+ HUMAN Authority
```

## Memory is independent

SAFOR Memory is a logical protocol component, not a GitHub/GitLab repository.

```text
                   HUMAN / Organization
                           │ owns
                           ▼
                    SAFOR Memory
                ┌──────────┴──────────┐
                │                     │
      Versioned repository      Persistent filesystem
                │                     │
                └──────────┬──────────┘
                           │ authoritative state
                           ▼
                      MASTER Kernel
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
          Factory                 Work Provider
                                      │
                      GitHub / GitLab / Generic Git /
                      Plastic / future adapters
```

Memory provider and work provider may be different.

## Authority rule

Chat context is a **non-authoritative cache**. A fact required by later work must first be persisted to SAFOR Memory.

This includes:

- HUMAN decisions,
- mandates,
- actor assignments,
- package bindings,
- state transitions,
- work results,
- evidence,
- output provenance,
- repair records.

## Multi-session model

Every session has:

- session ID,
- actor identity,
- host identity,
- observed LLM identity,
- base Memory revision.

Shared Team mode requires shared access plus either compare-and-swap or locking. A stale revision never silently overwrites newer state; it enters `RECONCILE_REQUIRED`.

## Output provenance

Every persisted output has a `SAFOR_OUTPUT_RECORD` containing:

- actor and role,
- session,
- Memory revision,
- SAFOR protocol/kernel version,
- Factory version,
- Operating Model version,
- LLM provider/model/version when exposed by the host,
- input and evidence references.

Unknown model details remain null with `NOT_EXPOSED`; they are never guessed.

## Lifecycle

```text
Memory bootstrap
→ Factory selection
→ Work-provider binding (when required)
→ Discovery
→ Planning
→ Execution
→ Evidence + provenance
→ Review / gates
→ Outcome
→ Closing
```

A fresh chat resumes from Memory, not from prior conversation history.
