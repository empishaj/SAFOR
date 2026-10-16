# Release Checklist — SAFOR v0.5

## Build

- [ ] `VERSION` matches release.
- [ ] `CHANGELOG.md` contains release.
- [ ] `python tools/build_bundle.py --check` passes.
- [ ] `python tools/validate_safor.py` passes.
- [ ] CI is green on exact release commit.
- [ ] Complete bundle contains all 32 v0.5 modules.

## Memory architecture

- [ ] No universal GitHub/GitLab prerequisite exists.
- [ ] No universal exact `safor-memory` repository requirement exists.
- [ ] Memory provider is HUMAN-selected/approved.
- [ ] Durable read/write/revision/resume capabilities are mandatory.
- [ ] New Memory location creation requires explicit HUMAN approval.
- [ ] Memory physical owner is HUMAN or organization.
- [ ] Chat is non-authoritative.
- [ ] SHARED_TEAM requires shared access + CAS/lock.
- [ ] Stale Memory write produces `RECONCILE_REQUIRED`.

## Collaboration and provenance

- [ ] Fresh chat can rehydrate without previous transcript.
- [ ] Every session has session ID and base Memory revision.
- [ ] Every persisted Factory output has an output provenance record.
- [ ] LLM identity is observed, never guessed.

## Factory/work providers

- [ ] Creation type remains mandatory.
- [ ] Software/Website requires a versioned work provider.
- [ ] Book can use Memory-only mode.
- [ ] Generic Git adapter validates.
- [ ] Plastic/Unity Version Control adapter never claims unavailable host tools.
- [ ] Memory and work providers may differ.

## GA

- [ ] End-to-end acceptance scenarios pass.
- [ ] HUMAN approves license/distribution terms.
