# SAFOR Quickstart

For a nontechnical German walkthrough, start with [START-HIER.md](START-HIER.md).

## Recommended end-user start

A normal user loads exactly one domain-specific Framework:

| Goal | Files |
|---|---|
| Website | `SAFOR-FRAMEWORK-WEBSITE.json` |
| SaaS public evaluation | `SAFOR-FRAMEWORK-SAAS.json` + `SAFOR-TEST-ACCESS-SAAS.json` |
| Book public evaluation | `SAFOR-FRAMEWORK-BOOK-CREATION.json` + `SAFOR-TEST-ACCESS-BOOK-CREATION.json` |

The Domain Framework already selects the domain, creation type, default Factory and default Operating Model. It does **not** ask the HUMAN to select Website, SaaS or Book again.

Send:

```text
Work with the loaded SAFOR Domain Framework.
Validate the Framework, embedded Factory, Operating Model and any matching evaluation-access artifact first.
Use the preselected domain and do not ask me to select Website, SaaS or Book again.
Guide me through my own Git project and Discovery. Never use the public SAFOR repository as my project workspace.
```

## No additional end-user runtime installation

SAFOR is designed to run as declarative JSON guidance inside a compatible ordinary LLM chat. The user does not install a separate SAFOR daemon, service or UI.

Python modules in `runtime/` are optional deterministic reference implementations for CI and compatible hosts/adapters. A generic chat does not automatically execute them when JSON is uploaded. Report model-level contract following and machine-enforced controls separately.

Actual provider tools and rights remain mandatory. JSON never grants credentials or repository permissions.

## HUMAN and MASTER

The HUMAN plans, approves and asks status questions only in the MASTER chat. MASTER owns work decomposition, roles, jobs, branches, reviews, acceptance and integration order.

## Persistent agent chat

For a new chat agent, MASTER prepares one initialization prompt. The HUMAN pastes it once. The agent validates its identity and waits.

Every later job starts with exactly:

```text
GO
```

A normal chat agent is not activated by a Git push, scheduler, polling, automation or host event.

After `GO`, the agent reads only:

1. its immutable identity;
2. its runtime state;
3. its personal inbox index;
4. the selected job and MASTER job state;
5. inputs explicitly pinned by the job.

The agent persists details in Git and emits only a minimal one-line chat status.

## Typed responses

Every v0.14 job binds exact templates and targets for:

- `JOB_RESULT`
- `JOB_ERROR`
- `CLARIFICATION_REQUEST`
- `CAPABILITY_MISMATCH`
- `IMPROVEMENT_PROPOSAL`

The response does not change the job or grant authority. MASTER stores any resolution separately and creates a superseding job when required.

## Generic engineering start — advanced

`SAFOR-FRAMEWORK.json` and the versioned generic Framework are build/engineering entrypoints. They expose generic profile resolution and are not the simplest end-user route.

Do not load the generic `SAFOR-FRAMEWORK.json` when a domain-specific Framework exists for the intended result.

## Workspace classes

- `REMOTE_GIT`: HUMAN-controlled GitHub/GitLab work repository plus separate `{OWNER}/safor-memory`.
- `LOCAL_GIT`: HUMAN-selected local Git repository only when the host actually exposes local filesystem and Git capabilities.

The public `empishaj/SAFOR` repository is never the project workspace.

## Public evaluation boundary

Public SaaS and Book access files declare `productionAuthorization=false`. They authorize only their explicit public test package versions.

`runtime/public_evaluation_access.py` is the optional deterministic reference verifier for CI/host integration. Possessing the JSON files is not production entitlement.

## Validation

```bash
python tools/build_bundle.py --check
python tools/build_domain_framework.py --check
python tools/validate_safor.py
python -m unittest discover -s tests -v
```
