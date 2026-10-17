# Support and Product Boundaries

## Current maturity

SAFOR is a **Release Candidate**. The exact current version is recorded in [`VERSION`](VERSION).

The JSON distributions, schemas and reference validators are machine-checkable. General Availability additionally requires explicit provider- and host-specific end-to-end evidence for every externally claimed path.

## Product boundary: ordinary chat use

SAFOR is designed for direct use in a compatible ordinary LLM chat by loading a Domain Framework JSON file. The JSON contains declarative orchestration, governance, role, job, evidence and interaction contracts.

A HUMAN does **not** have to install an additional SAFOR runtime, background service, daemon or separate user interface for normal use.

The Python modules in `runtime/` are optional reference implementations. They serve three purposes:

1. deterministic CI and regression tests;
2. reusable enforcement logic for hosts or adapters that choose to invoke it;
3. precise executable examples of the rules already declared in the Framework JSON.

A generic chat does not automatically execute Python merely because JSON was uploaded. Therefore SAFOR distinguishes:

- **declarative chat conformance** — the model reads and follows the embedded contracts;
- **optional machine enforcement** — CI, a compatible host, provider policy, branch protection or an adapter technically enforces selected invariants.

Missing optional enforcement must never be described as an existing technical access barrier.

## Supported creation types

- Website — free starter
- Software / SaaS — commercial; public non-production evaluation artifacts exist
- Book — commercial; public non-production evaluation artifacts exist

Additional Factories are not implicitly supported until they are published, bound and validated.

## Supported provider contracts

- GitHub
- GitLab
- Local Git when the current host actually exposes local filesystem and Git capabilities

A JSON declaration cannot create provider tools, credentials or repository rights. Actual usability depends on the current chat host and authenticated account.

## MASTER and normal CHAT_AGENT boundary

The MASTER is the only fachliche and organizational HUMAN interface. It owns planning, assignment, branch/workspace coordination, status, review, acceptance and conflict resolution.

A normal persistent `CHAT_AGENT`:

- is initialized once with a MASTER-generated identity prompt;
- waits in `WAITING_HUMAN_GO`;
- begins only after the HUMAN types exactly `GO` in its bound continued chat;
- is not activated by Git push, polling, scheduler, automation or host event;
- reads its identity, state, personal inbox index, selected job and pinned inputs only;
- writes detailed results and problems as typed Git responses to MASTER;
- emits only a minimal one-line chat status.

Service agents are a separate actor class. Their activation contract must never be silently reused for a normal HUMAN-operated chat agent.

## Identity and reidentification

A chat agent has a stable technical `agentId`, a separate HUMAN-readable `displayName`, an `identityRevision` and a chat binding.

If chat continuity, identity, repository binding or revision cannot be proven, the agent stops fail-closed with `REIDENTIFICATION_REQUIRED`. It must not guess its identity from a display name, job or repository path.

## Agent responses

SAFOR defines five agent-to-MASTER response types:

- `JOB_RESULT`
- `JOB_ERROR`
- `CLARIFICATION_REQUEST`
- `CAPABILITY_MISMATCH`
- `IMPROVEMENT_PROPOSAL`

The response is immutable. A later MASTER decision is stored separately as a resolution record and may reference a superseding job. `SUBMITTED`, `VERIFIED`, `ACCEPTED` and `INTEGRATED` remain different states.

## What SAFOR does not promise

- It cannot create tools or provider permissions the account does not have.
- It cannot force every LLM host to interpret declarative JSON identically.
- It cannot make a normal chat run in the background.
- It cannot prove cancellation of an external operation without provider readback.
- It does not treat delivery as proof of business or reader outcome.
- It does not silently repair high-impact, irreversible or authority-expanding failures.
- It does not claim machine-enforced licensing when only model-level contract following was observed.

## Project workspace support

SAFOR keeps package/framework sources separate from HUMAN project storage.

- **REMOTE_GIT** — a HUMAN-controlled GitHub or GitLab work repository plus separate writable `{OWNER}/safor-memory` control repository.
- **LOCAL_GIT** — a HUMAN-selected local Git repository only when the host exposes actual local filesystem and Git capabilities; `.safor/` is the local MASTER-only control root.

The public `empishaj/SAFOR` repository is never the HUMAN project workspace.

## Product paths

### Website

Free public starter:

- `safor.factory.website-delivery@1.1.0`
- `safor.om.website-team@1.1.0`

### Software / SaaS

Commercial path:

- Software Factory entitlement required;
- SaaS Engineering Operating Model entitlement required;
- both selected packages must satisfy the active profile and compatibility rules.

### Book

Commercial path with its own Factory, Operating Model and evidence requirements.

Premium Factory or Operating Model replacement is allowed only inside the active domain after access, integrity, package-family and bidirectional counterpart compatibility checks pass.

## Public evaluation access

Use:

- `SAFOR-TEST-ACCESS-SAAS.json` with `SAFOR-FRAMEWORK-SAAS.json`;
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json` with `SAFOR-FRAMEWORK-BOOK-CREATION.json`.

These bundles bind only to explicit public test versions and declare `productionAuthorization=false`. They are not purchase evidence or a production license.

`runtime/public_evaluation_access.py` is the optional deterministic reference verifier for compatible CI/host integrations. The same access semantics remain declared in the uploaded Framework and access JSON artifacts.

## Escalation

When safe continuation is impossible, SAFOR stops or waits and reports through the MASTER:

1. what failed;
2. what was attempted;
3. the current safe state;
4. the smallest required HUMAN action;
5. the immutable Git reference containing details.
