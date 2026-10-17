# SAFOR Product Readiness

Current target: **v0.11.0-rc.2**

Current modular source: **`v0.11.0/` overlay + retained `v0.10.0/` baseline**

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
| Phase-aware HUMAN cognitive-load policy | PASS by schema/conformance |
| HUMAN Decision Gate / derive-before-ask | PASS by schema/conformance |
| Unchanged decision reuse | PASS by schema/conformance |
| HUMAN-domain terminology abstraction | PASS by schema/conformance |
| Dynamic primary-action labels | PASS by schema/conformance |
| HUMAN cognitive-load end-to-end acceptance | OPEN |
| Deterministic Control Kernel unit/replay suite | PASS in CI |
| Deterministic Acceptance unit/replay suite | PASS in CI (25 total deterministic tests) |
| Acceptance Contract / Review Independence / Authority validation | PASS by schema/conformance |
| Deterministic Control end-to-end acceptance | OPEN |
| Full governance transition migration | OPEN |
| Bounded self-healing | PASS |
| Module-wide self-healing coverage | PASS by schema/conformance |
| Exact one-profile-per-module binding | PASS by validator contract |
| Profile-constrained recovery modes | PASS by schema/conformance |
| Fail-closed recovery-control integrity | PASS by schema/conformance |
| Module-aware repair records | PASS by schema/conformance |
| Module-wide Self-Healing end-to-end acceptance | OPEN |
| Persistent repository-native agent identity | PASS by schema/conformance |
| Agent inbox/outbox job protocol | PASS by schema/conformance |
| MASTER-authoritative agent lifecycle | PASS by schema/conformance |
| Canonical explicit agent job contract | PASS by schema/conformance |
| Package/work-item/sequence job lineage | PASS by schema/conformance |
| MASTER job provenance/timestamps | PASS by schema/conformance |
| Explicit per-job role binding | PASS by schema/conformance |
| Explicit versioned skill contract | PASS by schema/conformance |
| Granular job authorization | PASS by schema/conformance |
| Fixed result/evidence/audit return routes | PASS by schema/conformance |
| HUMAN-readable job Markdown projection | PASS by schema/conformance |
| Explicit Job Contract end-to-end acceptance | OPEN |
| Conflict-aware multi-agent scheduler | PASS by schema/conformance |
| ATOMIC/COMPOSITE work decomposition | PASS by schema/conformance |
| Explicit agent scheduling capacity | PASS by schema/conformance |
| Dispatch waves and resource leases | PASS by schema/conformance |
| Dedicated Git branches for mutating agent jobs | PASS by schema/conformance |
| HUMAN-readable agent Markdown results | PASS by schema/conformance |
| Provider-verifiable agent Git trace | PASS by schema/conformance |
| Six-agent parallel scheduling acceptance | OPEN |
| Conflict-aware serialization acceptance | OPEN |
| HUMAN-readable + Git-trace result acceptance | OPEN |
| Agent Workspace end-to-end acceptance | OPEN |
| Machine-readable validation | PASS on PR #8 validated head |
| CI validation | PASS on PR #8 validated head |
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
