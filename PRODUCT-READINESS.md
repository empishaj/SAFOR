# SAFOR Product Readiness

Current target: **v0.5.0-rc.1**

## Architecture gates

| Gate | State |
|---|---|
| Provider-neutral SAFOR Memory model | PASS |
| Memory/Work-provider separation | PASS |
| HUMAN/organization Memory ownership | PASS |
| PERSONAL + SHARED_TEAM collaboration model | PASS |
| Multi-writer CAS/lock conflict model | PASS |
| Fresh-session resume contract | PASS |
| Per-output provenance schema | PASS |
| Generic Git provider contract | PASS |
| Plastic/Unity Version Control provider contract | PASS |
| Host filesystem Memory contract | PASS |
| Factory-specific Discovery/Planning/Evidence | PASS |
| Reproducible single-file build | PASS · run 38931573636 |
| v0.5 validator | PASS · run 38931573636 |

## Empirical RC gates

| Gate | State |
|---|---|
| Versioned-repository Memory end-to-end | OPEN |
| Persistent filesystem Memory end-to-end on supporting host | OPEN |
| Two-session shared-memory conflict test | OPEN |
| Fresh-chat resume test | OPEN |
| Output provenance observed in real run | OPEN |
| Software run with non-GitHub/GitLab provider connector | OPEN WHEN CONNECTOR AVAILABLE |
| Explicit license/distribution decision | OPEN |

## Meaning

v0.5.0 is a Release Candidate only after machine validation is green. General Availability requires the empirical scenarios in `ACCEPTANCE-TESTS.md` plus a HUMAN licensing decision.
