# SAFOR v0.5 End-to-End Acceptance Tests

Run every scenario in a fresh chat using the exact release artifact.

## A — Versioned Memory + independent work provider

Example:
- Memory: GitHub/GitLab/generic versioned repository
- Work provider: a different GitHub/GitLab/Generic Git/Plastic workspace

Expected:
1. Memory is selected before the work provider.
2. SAFOR proves durable read/write/revision/resume semantics.
3. Memory and work provider bindings remain distinct.
4. Factory selection occurs after Memory is ready.
5. Software/Website requires a versioned work provider.
6. All authoritative state is persisted to Memory.

## B — Persistent host filesystem Memory

Run only when the host exposes persistent storage.

Expected:
- SAFOR does not accept ephemeral scratch space.
- It proves the same stable location can be reopened.
- Personal mode works with revision tracking.
- Shared Team is offered only if shared access plus CAS/lock can be proven.

## C — No eligible Memory

Precondition: no durable read/write/resume-capable storage is available.

Expected:
- SAFOR stops.
- Missing GitHub/GitLab is not named as the reason unless that was the selected provider.
- SAFOR does not continue to Factory selection.
- No credentials are requested in chat.

## D — Memory location creation

Precondition: selected Memory provider supports creating a location.

Expected:
- SAFOR proposes the location identity/scope.
- Creation occurs only after explicit HUMAN approval.
- The created location is read back and bound.
- No silent creation.

## E — Shared Team / two sessions

Start two independent chats against the same Memory.

Expected:
1. Each registers a unique session ID and base Memory revision.
2. Session A persists a state change.
3. Session B attempts a write from its stale revision.
4. SAFOR returns `RECONCILE_REQUIRED`.
5. Session B reloads current Memory before proceeding.
6. No unseen state is overwritten.

## F — Fresh-chat resume

1. Complete Discovery or Planning in Chat A.
2. Close Chat A.
3. Start Chat B without providing Chat A's transcript.
4. Connect to the same Memory.

Expected:
- Project, bindings, Factory, Operating Model, decisions and current state are reconstructed.
- A new session is registered.
- Work can continue from the correct checkpoint.

## G — Output provenance

Create at least one Factory output with an LLM.

Expected output record:
- actor/role,
- session ID,
- Memory revision,
- SAFOR/kernel version,
- Factory package/version,
- Operating Model package/version,
- LLM provider/model/version when exposed by the host,
- `NOT_EXPOSED` + null values when exact model identity is unavailable.

SAFOR must never guess the model.

## H — Software provider diversity

Run the Software/Website Factory with:
- GitHub or GitLab,
- Generic/self-hosted Git when connector exists,
- Plastic SCM / Unity Version Control when connector exists.

Expected:
- only actual exposed capabilities are used;
- unavailable pull-request/issues/checks features are not simulated;
- provider-specific terminology does not leak into the Factory contract.

## I — Book Memory-only mode

Expected:
- Book Factory can proceed without an external work provider when HUMAN selects Memory-only.
- Discovery, Planning and Evidence remain Book-specific.

## Evidence retained per run

- release commit/bundle SHA,
- Memory provider/binding,
- work-provider binding if any,
- session IDs,
- Memory revisions,
- output provenance records,
- provider readback references,
- final PASS/FAIL decision.
