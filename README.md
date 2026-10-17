# SAFOR

**Systemic AI Factory Orchestration Runtime**

SAFOR is a system-oriented orchestration runtime for HUMAN-governed, evidence-backed AI work across interchangeable Factories.

> Current maturity: **v0.13.0-rc.1 — Release Candidate**

## Start here

1. Read [QUICKSTART.md](QUICKSTART.md).
2. Load `SAFOR-FRAMEWORK.json` into a compatible chat.
3. Choose what you want to create.
4. **Software / Website** starts with a FREE_PUBLIC Factory and a FREE_PUBLIC Operating Model; both are independent `SAFOR_DOMAIN_PACKAGE` JSON artifacts.
5. You may later replace only the Factory, only the Operating Model, or both with compatible alternatives.
6. Every selected paid package requires its own externally verified entitlement; free and paid packages may be combined.
7. Choose where the HUMAN project lives: **REMOTE_GIT** (GitHub/GitLab) or **LOCAL_GIT**. Remote projects use separate HUMAN-controlled `safor-memory`; local projects use protected `.safor/` control state.

## Repository separation

- **`empishaj/SAFOR`** — public SAFOR Framework source, package catalog, free starter package source, Provider Adapters, schemas and historical development baselines. It is never a HUMAN project workspace.
- **`{OWNER}/safor-memory`** — HUMAN-controlled remote control workspace used only for REMOTE_GIT projects.
- **HUMAN project workspace** — either a HUMAN-controlled remote Git repository or a HUMAN-controlled local Git repository; all domain work artifacts stay here.

These concerns are intentionally separate.

## Distribution

- `SAFOR-FRAMEWORK-v0.13.0-rc.1.json` — versioned public Framework release candidate.
- `SAFOR-FRAMEWORK.json` — latest Framework RC alias.
- `v0.13.0/` — composable domain-package contract, independent Factory/Operating Model selection, per-package entitlement, SHA-256 package integrity and compatibility decisions.
- `v0.12.0/` — modular package/workspace boundary baseline.
- `v0.11.0/` — deterministic control and deterministic acceptance baseline.
- `v0.10.0/` and earlier — historical development baselines. Pre-0.12 package prototypes already published there cannot be made confidential retroactively.

Factories and Operating Models are independently loadable JSON products. Creation Profiles define defaults rather than locked commercial bundles. Paid package model content is not embedded in the public Framework artifact; entitlement evidence remains external to the package JSON.

## Product documentation

- [Quickstart](QUICKSTART.md)
- [Architecture](ARCHITECTURE.md)
- [Agent Workspace Protocol](AGENT-WORKSPACE.md)
- [Agent Job Contract](AGENT-JOB-CONTRACT.md)
- [Module-wide Self-Healing](MODULE-SELF-HEALING.md)
- [HUMAN Cognitive Load](HUMAN-COGNITIVE-LOAD.md)
- [Multi-Agent Scheduler](MULTI-AGENT-SCHEDULER.md)
- [Security](SECURITY.md)
- [Support & boundaries](SUPPORT.md)
- [Product readiness](PRODUCT-READINESS.md)
- [Release checklist](RELEASE-CHECKLIST.md)
- [End-to-end acceptance tests](ACCEPTANCE-TESTS.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)

## Validation

```bash
python tools/validate_safor.py
```

The same validation runs in GitHub Actions.

## Product status

SAFOR is currently a **Release Candidate**, not General Availability. v0.13.0-rc.1 proves the composable Factory/Operating-Model contract, per-package commercial gating, declared-contract integrity, compatibility binding and retained Framework/workspace boundaries in machine tests. Real entitlement delivery, Local-Git host execution and provider/agent end-to-end scenarios remain GA gates.

The commercial product decision is explicit: the Framework and Website starter defaults are public/free; Factories and Operating Models are independently selectable and independently licensable. A customer can therefore add a premium Factory, a premium Operating Model, or both without replacing the Framework. Final legal license text, pricing and entitlement-service operations remain open.