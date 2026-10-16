# SAFOR Product Readiness

Current target: **v0.6.0-rc.1**

Current modular source: **`v0.6.0/`**

## Release-candidate gates

| Gate | State |
|---|---|
| Self-contained single-file distribution | PASS |
| Product repository separated from runtime memory | PASS |
| Mandatory writable `safor-memory` gate | PASS |
| Software/Website Factory | PASS |
| Book Factory | PASS |
| Factory-bound Discovery | PASS |
| Factory-bound Planning | PASS |
| Factory-bound Evidence | PASS |
| Chat-native HUMAN interface policy | PASS |
| Bounded self-healing | PASS |
| Persistent repository-native agent identity | PASS by schema/conformance |
| Agent inbox/outbox job protocol | PASS by schema/conformance |
| MASTER-authoritative agent lifecycle | PASS by schema/conformance |
| Agent Workspace end-to-end acceptance | OPEN |
| Machine-readable validation | PASS |
| CI validation | PASS on validated PR head |
| Product repository slug without trailing punctuation | PASS |
| Explicit distribution/license decision | OPEN |
| GitHub end-to-end blank-chat acceptance run | OPEN |
| GitLab end-to-end blank-chat acceptance run | OPEN |

## Maturity meaning

**Release Candidate** means the architecture and distribution are internally coherent and machine-checkable. It does not mean every supported host/provider path has been empirically acceptance-tested.

## Acceptance evidence

The required GitHub/GitLab scenarios are defined in `ACCEPTANCE-TESTS.md` and must be retained with release evidence.

## General Availability definition

SAFOR can be called GA only when every OPEN gate above is resolved and the release artifact is generated from the canonical product repository at an immutable revision.
