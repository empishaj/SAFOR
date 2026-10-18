# SAFOR 0.13.0-rc.9 Release Notes

## Purpose

This release candidate republishes the complete SAFOR Framework set after the `safomwebsite` reference control plane was migrated non-destructively to the HUMAN-GO agent contracts introduced in rc.8.

## User-facing files

- `SAFOR-FRAMEWORK-WEBSITE.json` — free public Website Framework.
- `SAFOR-FRAMEWORK-SAAS.json` plus `SAFOR-TEST-ACCESS-SAAS.json` — public SaaS evaluation path; not a commercial production license.
- `SAFOR-FRAMEWORK-BOOK-CREATION.json` plus `SAFOR-TEST-ACCESS-BOOK-CREATION.json` — public Book evaluation path; not a commercial production license.
- `SAFOR-FRAMEWORK-v0.13.0-rc.9.json` — generic engineering distribution.
- `SAFOR-FRAMEWORK.json` — byte-identical current generic alias.

## Evidence added in rc.9

- Reference migration merge: `empishaj/safor-memory@85e08eab15b18a86868090d7b18573b9e2484aea`.
- Reference migration PR: `empishaj/safor-memory#4`.
- Authoritative project pointer: `projects/safomwebsite/state/current.json`.
- Complete reference agent registry: nine agents with distinct display names and fail-closed `REBIND_REQUIRED` state until one-time chat binding.
- Migration audit: 16 checks passed, 45 materialized project paths, zero unexpected paths and zero deleted historical paths.
- Product repository head at migration remained `1026ff2176d739aeedc506e5970b48528aa8ad23`.

## Compatibility and limits

The schema and kernel baseline remain `0.13.0`. rc.9 does not turn public SaaS or Book evaluation bytes into commercial production packages. It also does not claim that JSON can create provider rights or force a non-conforming LLM host. Remaining GA blockers stay explicit in `RELEASE-MANIFEST.json`.

## Validation

The release is accepted only when bundle reproducibility, all domain distribution checks, `tools/validate_safor.py` and the complete unit/regression suite pass on the final branch head and again on `main` after merge.
