# SAFOR 0.14.0-rc.3 Release Notes

## Purpose

This release candidate remediates the independent rc.2 audit without redesigning SAFOR or adding a mandatory customer runtime.

## Corrected contracts

- Canonical Creation Types are `WEBSITE`, `SOFTWARE_SAAS` and `BOOK` across new project descriptors and domain profiles.
- Legacy `SOFTWARE_WEBSITE` remains historical and requires explicit contextual migration.
- Current kernel model/schema/template references resolve to active v0.14 modules.
- Invariants are machine-classified as `ACTIVE`, `SUPERSEDED` or `LEGACY_ONLY`.
- `REMOTE_GIT` requires separate `safor-memory`; `LOCAL_GIT` uses a MASTER-only Git-tracked `.safor/` root without remote-memory requirement.
- Control-response persistence failure can be reported locally without inventing a Git reference or repeating a verified product commit.
- HUMAN-GO claim success requires provider compare-and-swap, provider readback and persisted activation consumption.
- Current documentation is checked against release facts.

## Distribution files

- `SAFOR-FRAMEWORK-v0.14.0-rc.3.json`
- `SAFOR-FRAMEWORK.json`
- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- public SaaS and Book evaluation access bundles

## Evidence boundary

Automated schema, reference, invariant, policy, failure-injection, reproducibility and regression checks do not constitute a fresh-chat real-Git E2E, cross-host equivalence, `safomwebsite` migration acceptance, empirical cognitive-load evidence or General Availability.
