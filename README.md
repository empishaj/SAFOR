# SAFOR

**Systemic AI Factory Orchestration Runtime**

SAFOR is a system-oriented orchestration runtime for HUMAN-governed, evidence-backed AI work across interchangeable Factories.

> Current maturity: **v0.12.0-rc.1 — Release Candidate**

## Start here

1. Read [QUICKSTART.md](QUICKSTART.md).
2. Load `SAFOR-FRAMEWORK.json` into a compatible chat.
3. Choose what you want to create.
4. **Software / Website** uses the FREE_PUBLIC starter Factory + Operating Model and may resolve them from the public SAFOR Git.
5. Paid paths such as **Buch** require separately loaded/entitled Factory and Operating Model packages.
6. Choose where the HUMAN project lives: **REMOTE_GIT** (GitHub/GitLab) or **LOCAL_GIT**.
7. Remote projects use a separate HUMAN-controlled `safor-memory`; local projects use protected `.safor/` control state in the local Git workspace.

## Repository separation

- **`empishaj/SAFOR`** — public SAFOR Framework source, package catalog, free starter package source, Provider Adapters, schemas and historical development baselines. It is never a HUMAN project workspace.
- **`{OWNER}/safor-memory`** — HUMAN-controlled remote control workspace used only for REMOTE_GIT projects.
- **HUMAN project workspace** — either a HUMAN-controlled remote Git repository or a HUMAN-controlled local Git repository; all domain work artifacts stay here.

These concerns are intentionally separate.

## Distribution

- `SAFOR-FRAMEWORK-v0.12.0-rc.1.json` — versioned public Framework release candidate.
- `SAFOR-FRAMEWORK.json` — latest Framework RC alias.
- `v0.12.0/` — modular package distribution, commercial entitlement policy and HUMAN-owned remote/local workspace model.
- `v0.11.0/` — deterministic control and deterministic acceptance baseline.
- `v0.10.0/` and earlier — historical development baselines. Pre-0.12 package prototypes already published there cannot be made confidential retroactively.

Factories and Operating Models are independently loadable packages. Paid package model content is not embedded in the 0.12 public Framework artifact.

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

SAFOR is currently a **Release Candidate**, not General Availability. v0.12.0-rc.1 proves the Framework/package/workspace boundary in machine tests, but real entitlement distribution, local-Git host execution and existing provider/agent end-to-end scenarios remain GA gates.

The commercial product decision is now explicit: the Framework and Website starter path are public/free; Factories and Operating Models can be independently licensed, with Book and future premium packages entitlement-gated. Final legal license text, pricing and entitlement-service operations are still open.