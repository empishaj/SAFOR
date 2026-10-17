# Release Checklist

## Required before every SAFOR 0.12.0-rc.2 release

- [x] `VERSION` matches `0.12.0-rc.2`.
- [x] `RELEASE-MANIFEST.json` points to `SAFOR-FRAMEWORK-v0.12.0-rc.2.json`.
- [x] `SAFOR-FRAMEWORK.json` exactly matches the versioned Framework artifact.
- [x] `python tools/build_bundle.py --check` passes.
- [x] `python tools/validate_safor.py` passes.
- [x] CI is green on the exact rc.2 branch head.
- [x] Exactly 65 embedded Framework modules have exactly 65 recovery profiles.
- [x] Existing deterministic control and deterministic acceptance remain green.
- [x] Existing modular package/workspace tests remain green.
- [x] Operation Mode model defines DESIGN, VALIDATION and EXECUTION.
- [x] Operation Mode is resolved before mutating effects.
- [x] DESIGN is not represented as HUMAN project Value Creation execution.
- [x] VALIDATION requires an isolated non-production target.
- [x] VALIDATION evidence cannot silently satisfy production authority/acceptance/outcome.
- [x] EXECUTION targets a HUMAN project.
- [x] Agent Runtime Adapter is logically separate from Provider Adapter.
- [x] Agent Runtime binding requires actual capability evidence.
- [x] Background wakeup defaults false and requires evidence.
- [x] EXECUTION AGENT dispatch permits only HOST_NATIVE_AUTOMATIC or EXTERNAL_AUTOMATION.
- [x] HUMAN_MANUAL_TEST_ONLY is VALIDATION-only.
- [x] Missing EXECUTION automation returns AGENT_RUNTIME_AUTOMATION_UNAVAILABLE.
- [x] HUMAN Decision Gate forbids routine agent wakeup, copied job prompts/contracts, inbox polling, result transport and manual dispatch sequencing.
- [x] EXECUTION cannot silently downgrade to VALIDATION to bypass missing automation.
- [x] Agent Job Contract binds operation mode + Agent Runtime + capability evidence.
- [x] Agent Job Contract keeps repository-pull transport authoritative.
- [x] Agent Runtime binding cannot grant provider rights, Operating Model authority, mandate, entitlement, review approval or acceptance.
- [x] SH-24 prevents runtime-capability fabrication and HUMAN-operation fallback.
- [x] 53 total Python tests PASS.

## Existing rc.1 boundaries retained

- [x] Public Framework embeds no paid Factory/Operating Model domain package content.
- [x] Software/Website starter is FREE_PUBLIC.
- [x] Book is PAID_ENTITLEMENT_REQUIRED.
- [x] Entitlement is separate from organizational authority.
- [x] Project workspace is HUMAN-controlled REMOTE_GIT or LOCAL_GIT.
- [x] Canonical SAFOR repository/package sources cannot be EXECUTION project targets.
- [x] LOCAL_GIT uses MASTER-only `.safor/`.
- [x] REMOTE_GIT uses HUMAN-controlled `safor-memory`.

## Required before GA

- [ ] Scenario S — Operation Mode / Agent Runtime governance PASS.
- [ ] Automatic Agent Runtime EXECUTION E2E PASS without HUMAN chat operation.
- [ ] GitHub REMOTE_GIT free Website path PASS end to end.
- [ ] GitLab REMOTE_GIT path PASS.
- [ ] Commercial Package Entitlement PASS.
- [ ] LOCAL_GIT HUMAN Project Workspace PASS.
- [ ] Agent Workspace / explicit Job Contract PASS with actual automatic runtime.
- [ ] Six-agent scheduling/conflict/Git-trace PASS with actual runtime.
- [ ] Module-wide Self-Healing PASS.
- [ ] HUMAN cognitive-load/communication PASS.
- [ ] Deterministic Control and Acceptance E2E PASS.
- [ ] Final legal commercial license terms approved.
- [ ] Entitlement issuer/verifier and commercial package delivery implemented.
- [ ] Full governance transition migration completed or remaining boundary explicitly accepted for GA.
