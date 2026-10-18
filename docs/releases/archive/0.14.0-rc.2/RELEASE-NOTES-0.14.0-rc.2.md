# SAFOR 0.14.0-rc.2 Release Notes

## Purpose

This release candidate integrates the audited SAFOR 0.14 orchestration contracts into the actual uploadable generic and domain Framework distributions on top of the rc.9 product baseline.

## Major changes

- Structured, immutable and single-use HUMAN-GO evidence bound to project, agent, identity revision, chat binding, job and dispatch revision.
- Atomic optimistic-concurrency claim reference path; stale, foreign or reused GO evidence fails closed.
- MASTER response completeness is derived from schema-valid, job-bound provider readback or an explicit waiver decision.
- Status freshness is derived as `CURRENT`, `STALE` or `UNKNOWN` from deadline, source revisions and provider readback.
- Product-commit/control-response partial failures reconcile without repeating a known product mutation.
- All 33 requirements expose separate design, implementation, automated-test, bundle, real-Git-E2E and cross-host evidence dimensions.
- All active Framework modules are materialized from `v0.14.0/` sources with exact recovery-profile coverage.
- Website, SaaS evaluation and Book evaluation Factory/Operating-Model pairs are upgraded for the 0.14 framework range.
- GitHub and GitLab provider adapter contracts are upgraded to `0.6.0`.

## Files for end users

- `SAFOR-FRAMEWORK-WEBSITE.json` — free public Website path.
- `SAFOR-FRAMEWORK-SAAS.json` with `SAFOR-TEST-ACCESS-SAAS.json` — public SaaS evaluation, not a commercial production license.
- `SAFOR-FRAMEWORK-BOOK-CREATION.json` with `SAFOR-TEST-ACCESS-BOOK-CREATION.json` — public Book evaluation, not a commercial production license.
- `SAFOR-FRAMEWORK-v0.14.0-rc.2.json` — versioned generic Framework.
- `SAFOR-FRAMEWORK.json` — byte-identical current generic alias.

## Evidence boundary

The release proves reproducible bundles, automated contract validation and negative failure-injection coverage on the exact branch head. It does not claim a completed fresh-chat real-Git E2E, universal ChatGPT/Claude/Gemini equivalence, GitLab E2E, empirical cognitive-load reduction or General Availability. Those remain explicit release blockers.
