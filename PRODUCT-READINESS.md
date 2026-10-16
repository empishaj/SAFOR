# SAFOR Product Readiness

Current target: **v0.4.0-rc.1**

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
| Machine-readable validation | PASS |
| CI validation | PASS when workflow is green |
| Product repository slug without trailing punctuation | OPEN |
| Explicit distribution/license decision | OPEN |
| GitHub end-to-end blank-chat acceptance run | OPEN |
| GitLab end-to-end blank-chat acceptance run | OPEN |

## Maturity meaning

**Release Candidate** means the architecture and distribution are internally coherent and machine-checkable. It does not mean every supported host/provider path has been empirically acceptance-tested.

## General Availability definition

SAFOR can be called GA only when every OPEN gate above is resolved and the release artifact is generated from the canonical product repository at an immutable revision.
