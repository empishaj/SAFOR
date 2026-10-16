# SAFOR

**Systemic AI Factory Orchestration Runtime**

SAFOR guides HUMAN-governed, evidence-backed AI work through explicit Operating Models and Factories.

> Current development target: **v0.5.0-rc.1**

## Core idea

SAFOR separates four concerns:

- **SAFOR product** — this repository.
- **SAFOR Memory** — authoritative, durable project state controlled by the HUMAN or organization.
- **Work provider** — where domain work happens, e.g. GitHub, GitLab, generic/self-hosted Git or Plastic SCM / Unity Version Control when a compatible connector exists.
- **Chat/LLM session** — an interchangeable working session; it is never the authoritative project memory.

Memory and work provider may be completely different systems.

## Start

1. Load `SAFOR-MASTER-COMPLETE.json` into a compatible chat.
2. SAFOR discovers actually available durable Memory options.
3. Choose/approve the Memory provider and ownership.
4. SAFOR proves read, write, revision and resume semantics.
5. Choose **Personal** or **Shared Team**.
6. Choose **Software / Website** or **Buch**.
7. Select the work provider required by the chosen Factory.
8. SAFOR persists the project and registers the current session.

If no durable Memory can be proven, SAFOR stops. Missing GitHub or GitLab by itself is not a blocker.

## Memory options

Supported contracts include:

- versioned repository Memory,
- persistent host filesystem / mounted storage,
- future organization-specific Memory adapters.

For repository-backed Memory, `safor-memory` is a recommended repository name, not a universal protocol requirement.

## Multi-Human / Multi-LLM

Different humans and LLM sessions can work on the same project when they share the same SAFOR Memory. Every authoritative session has a session ID and base Memory revision. Shared writes require conflict-safe concurrency.

Every persisted output records producer/session provenance and, when exposed by the host, LLM provider, model and model version. SAFOR never invents unavailable model identity.

## Documentation

- [Quickstart](QUICKSTART.md)
- [Memory model](MEMORY.md)
- [Architecture](ARCHITECTURE.md)
- [Security](SECURITY.md)
- [Support](SUPPORT.md)
- [Acceptance tests](ACCEPTANCE-TESTS.md)
- [Product readiness](PRODUCT-READINESS.md)
- [Release checklist](RELEASE-CHECKLIST.md)

## Validation

```bash
python tools/build_bundle.py --check
python tools/validate_safor.py
```
