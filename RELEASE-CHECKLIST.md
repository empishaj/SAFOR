# Release Checklist

## Required before every SAFOR 0.13 release

- [x] `VERSION` matches the intended release candidate.
- [x] `CHANGELOG.md` contains the release.
- [x] `RELEASE-MANIFEST.json` points to `SAFOR-FRAMEWORK-v0.13.0-rc.1.json`.
- [x] `SAFOR-FRAMEWORK.json` exactly matches the versioned Framework artifact.
- [x] `python tools/build_bundle.py --check` passes.
- [x] `python tools/validate_safor.py` passes.
- [x] CI is green on the tested 0.13 branch head.
- [x] Public Framework embeds no Factory/Operating Model domain package content.
- [x] Exactly 65 embedded Framework modules have exactly 65 recovery profiles.
- [x] All embedded references resolve.
- [x] Software/Website starter catalog entries are FREE_PUBLIC.
- [x] Free Website Factory/OM public paths resolve the expected package IDs/versions.
- [x] Book Factory/OM catalog entries are PAID_ENTITLEMENT_REQUIRED and expose no public model-content path.
- [x] Public canonical package source is restricted to FREE_PUBLIC packages.
- [x] HUMAN-loaded paid packages still require independently verified entitlement.
- [x] Self-asserted entitlement is rejected.
- [x] Entitlement cannot grant Operating Model authority, provider rights, mandate or project scope.
- [x] Factory/Operating Model compatibility is checked independently from entitlement.
- [x] Factory and Operating Model can each be overridden independently.
- [x] Creation Profiles define defaults rather than locked package pairs.
- [x] Access and entitlement are resolved per selected package.
- [x] FREE_PUBLIC/PAID_ENTITLEMENT_REQUIRED mixed pairs are supported when the paid package is entitled.
- [x] Entitlement evidence remains external to SAFOR_DOMAIN_PACKAGE JSON.
- [x] Domain-package declared-contract SHA-256 integrity is verified.
- [x] Domain-package Framework range and Creation-Type scope are enforced.
- [x] Package-selection and COMPATIBLE compatibility-decision references are persisted before binding.
- [x] SH-24 covers composable package integrity/access/compatibility failures.
- [x] CF-217 through CF-230 cover the 0.13 composable package contract.
- [x] Project workspace is HUMAN-controlled REMOTE_GIT or LOCAL_GIT.
- [x] Canonical SAFOR repository cannot be a project target.
- [x] Commercial package source cannot be a project target.
- [x] REMOTE_GIT uses separate HUMAN-controlled `safor-memory`.
- [x] LOCAL_GIT does not require remote `safor-memory`.
- [x] LOCAL_GIT requires actual filesystem + Git read/history/branch/commit capabilities.
- [x] LOCAL_GIT uses Git-tracked MASTER-only `.safor/`.
- [x] Worker write scopes cannot include `.safor/`.
- [x] Project/Bindings/Package Selection/Compatibility/Workspace schemas are 0.13-aware.
- [x] Deterministic Control and Acceptance suites remain green.
- [x] Modular package/workspace bootstrap tests pass.
- [x] Total current unit suite: 48 tests PASS.
- [x] SH-23 forbids entitlement fabrication, paid-public resolution, workspace redirection and Local-Git bypass.
- [x] HUMAN Decision Gate and terminal-menu contracts remain intact.
- [x] Product licensing strategy is explicitly recorded in `LICENSE-DECISION.md`.
- [x] Legacy pre-0.12 public package disclosure is explicitly recorded.

## Required before GA

- [ ] Final legal commercial license text/terms approved.
- [ ] Pricing/SKU policy finalized.
- [ ] Billing/purchase flow implemented or approved external process defined.
- [ ] Entitlement issuer/verifier implemented.
- [ ] Commercial paid package delivery source implemented.
- [ ] Scenario A — GitHub REMOTE_GIT free Website happy path PASS.
- [ ] Scenario B — remote control-workspace blocker PASS.
- [ ] Scenario C — Free/Paid package separation PASS.
- [ ] Scenario E — GitLab REMOTE_GIT PASS.
- [ ] Scenario F–H — Agent Workspace PASS.
- [ ] Scenario I–K — parallel scheduling/conflict/Git-trace PASS.
- [ ] Scenario L — explicit Agent Job Contract PASS.
- [ ] Scenario M — module-wide Self-Healing PASS.
- [ ] Scenario N — HUMAN cognitive-load/communication PASS.
- [ ] Scenario O — Deterministic Control PASS.
- [ ] Scenario P — Deterministic Acceptance PASS.
- [ ] Scenario Q — Commercial Package Entitlement PASS.
- [ ] Scenario R — LOCAL_GIT HUMAN Project Workspace PASS.
- [ ] Full governance transition migration completed or remaining non-executable boundary explicitly accepted for GA scope.
