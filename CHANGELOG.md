# Changelog

## 0.5.0-rc.1 — 2026-10-16

### Memory architecture
- SAFOR Memory is provider-neutral and no longer defined by GitHub/GitLab or a mandatory repository name.
- HUMAN explicitly selects/approves Memory provider and physical ownership.
- Durable read/write/revision/resume capability proof is mandatory; missing GitHub/GitLab alone is not a STOP condition.
- Versioned-repository and persistent host-filesystem Memory adapters added.
- PERSONAL and SHARED_TEAM modes added; shared mode requires shared access plus CAS/lock concurrency.
- Memory provider and work/SCM provider are independent bindings.
- Generic Git and Plastic SCM / Unity Version Control work-provider contracts added.
- Fresh sessions rehydrate from SAFOR Memory without prior chat history.
- Session records and per-output provenance records added, including observed LLM provider/model/version and SAFOR/Factory/Operating-Model versions.
- Authoritative project facts may not live only in chat context.


All notable SAFOR product changes are documented here.

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

### Product status
This version is a **Release Candidate**, not General Availability.

GA still requires:
- final product repository slug `SAFOR` without the trailing dot;
- an explicit HUMAN licensing decision;
- clean end-to-end acceptance runs for the supported provider paths.
