# SAFOR 0.14.0-rc.4 Release Notes

## Purpose

This release candidate integrates the rc.3 review remediation and produces a reproducible rc.4 distribution without changing SAFOR's chat-first product boundary.

## Corrected contracts

- Legacy conformance assertions are explicitly superseded and active rules are scope-aware.
- REMOTE_GIT and LOCAL_GIT initialization are mutually exclusive; LOCAL_GIT does not require remote safor-memory.
- HUMAN response menus are derived from the platform response class; informational notices are menu-free.
- HUMAN-GO claim authority requires exact full-state provider readback, canonical digest equality and bound identity/job/chat/dispatch fields.
- BLOCKED agent output enforces a strict persistence XOR: persisted details reference or persistence-failure object, never both.
- VERSION, release facts, manifest, readiness and 33-requirement traceability are synchronized to rc.4.
- The historical safomwebsite migration remains legacy evidence; rc.4 candidate migration remains NOT_STARTED until isolated real-Git E2E passes.

## Distribution files

- `SAFOR-FRAMEWORK-v0.14.0-rc.4.json`
- `SAFOR-FRAMEWORK.json`
- `SAFOR-FRAMEWORK-WEBSITE.json`
- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- `SAFOR-TEST-ACCESS-SAAS.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json`

## Evidence boundary

Automated source, schema, reproducibility and regression PASS does not constitute fresh-chat real-Git E2E, cross-host equivalence, rc.4 safomwebsite migration acceptance, empirical cognitive-load evidence, commercial GA or General Availability.
