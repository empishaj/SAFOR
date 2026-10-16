# Changelog

All notable SAFOR product changes are documented here.

## 0.5.0-rc.1 — 2026-10-16

### Changed
- Promoted the SAFOR product baseline to kernel/schema contract version 0.5.0.
- Added the dedicated modular source tree `v0.5.0/` while retaining `v0.4.0/` as historical source.
- Completed the legacy namespace migration across formats, package IDs, schema URNs and runtime identifiers.
- Canonical product source is `empishaj/SAFOR`; project runtime memory remains `{OWNER}/safor-memory`.
- Package compatibility for the v0.5.0 source tree now requires kernel `>=0.5.0 <0.6.0`.
- Release distribution is now explicitly versioned as `SAFOR-MASTER-COMPLETE-v0.5.0-rc.1.json`, with `SAFOR-MASTER-COMPLETE.json` retained as the latest alias.

### Retained
- Mandatory pre-existing writable `safor-memory` hard gate.
- Mandatory HUMAN selection of Software / Website or Buch.
- Factory-bound Discovery, Planning and Evidence.
- Chat-native HUMAN interaction only.
- Conservative bounded self-healing.
- Evidence-before-belief and authoritative provider readback.

### Product status
This version remains a **Release Candidate**. General Availability still requires the explicit licensing decision plus recorded GitHub and GitLab fresh-chat end-to-end acceptance.

## 0.4.0-rc.1 — 2026-10-16

### Added
- Self-contained `SAFOR-MASTER-COMPLETE.json`
- Guided GitHub/GitLab initialization
- Mandatory pre-existing writable `{OWNER}/safor-memory`
- Mandatory HUMAN creation-type selection: Software / Website or Book
- Factory-specific Discovery, Planning and Evidence contracts
- Chat-native HUMAN interaction only
- Conservative self-healing with bounded retry, reconciliation and HUMAN escalation
- Product/runtime separation between the SAFOR repository and project memory
- Product validation script and CI release gates
