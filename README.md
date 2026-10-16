# SAFOR

**Systemic AI Factory Orchestration Runtime**

SAFOR is a system-oriented orchestration runtime for HUMAN-governed, evidence-backed AI work across interchangeable Factories.

> Current maturity: **v0.6.0-rc.1 — Release Candidate**

## Start here

1. Read [QUICKSTART.md](QUICKSTART.md).
2. Load `SAFOR-MASTER-COMPLETE.json` into a compatible chat.
3. Connect GitHub or GitLab.
4. SAFOR requires a pre-existing writable `{OWNER}/safor-memory`; otherwise it stops.
5. Choose **Software / Website** or **Buch**.
6. Continue through the native chat actions.

## Repository separation

- **`empishaj/SAFOR`** — canonical SAFOR product source, runtime definition, Factories, Operating Models, Provider Adapters, schemas and distribution.
- **`{OWNER}/safor-memory`** — mandatory project-scoped runtime/control memory used after SAFOR is loaded.
- **Project repository** — domain work artifacts such as software, website content or book manuscripts.

These concerns are intentionally separate.

## Distribution

- `SAFOR-MASTER-COMPLETE-v0.6.0-rc.1.json` — immutable-name release-candidate distribution.
- `SAFOR-MASTER-COMPLETE.json` — latest release-candidate alias.
- `v0.6.0/` — current modular source baseline with repository-native Agent Workspace Protocol.
- `v0.5.0/` and `v0.4.0/` — retained historical source baselines.

## Product documentation

- [Quickstart](QUICKSTART.md)
- [Architecture](ARCHITECTURE.md)
- [Agent Workspace Protocol](AGENT-WORKSPACE.md)
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

SAFOR is currently a **Release Candidate**, not General Availability. GA requires clean GitHub/GitLab end-to-end acceptance and an explicit HUMAN licensing/distribution decision.
