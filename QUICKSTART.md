# SAFOR Quickstart

## What you need

Always:
- A compatible chat host.
- `SAFOR-FRAMEWORK-v0.12.0-rc.2.json` or the latest `SAFOR-FRAMEWORK.json`.
- A HUMAN-controlled Git project workspace.

For **Software / Website**:
- No commercial package entitlement is required for the default starter Factory/Operating Model.
- SAFOR may resolve the FREE_PUBLIC pair from the canonical public SAFOR Git at an immutable revision/blob.

For paid creation paths such as **Buch**:
- The required Factory and Operating Model must be supplied through a HUMAN-loaded or entitled package source.
- Verified entitlement evidence is mandatory. Merely possessing JSON or stating that it was purchased is not sufficient.

For **REMOTE_GIT** projects:
- GitHub or GitLab access with the required project read/write capabilities.
- A HUMAN-controlled `{OWNER}/safor-memory` for SAFOR control state.

For **LOCAL_GIT** projects:
- Host access to the HUMAN-selected local filesystem and Git repository.
- Proven read/write, Git history, branch and commit capabilities.
- No remote `safor-memory` is required; SAFOR uses a Git-tracked MASTER-only `.safor/` control root.

## First: SAFOR resolves the operation mode

Before project/package initialization SAFOR derives one of:

- **DESIGN** — you are changing SAFOR Framework/schema/package architecture.
- **VALIDATION** — you are running an isolated test or E2E harness.
- **EXECUTION** — you are creating value in a real HUMAN project.

When the intent and target make the mode deterministic, SAFOR does not ask. Only genuine ambiguity may create a HUMAN decision.

For EXECUTION, Creation Type / Factory / Operating Model / project workspace initialization follows. For DESIGN and VALIDATION, SAFOR does not force the HUMAN through the project-creation flow.

## Start

1. Load `SAFOR-FRAMEWORK-v0.12.0-rc.2.json`.
2. SAFOR verifies its Framework, Self-Healing and deterministic-control integrity.
3. Choose **Software / Website** or **Buch**.
4. SAFOR resolves package access before asking where the project lives.
5. For Website starter, SAFOR resolves the free Factory/OM from public SAFOR Git unless you explicitly loaded another compatible pair.
6. For paid paths, SAFOR requires valid package artifacts plus independently verified entitlement.
7. SAFOR verifies Factory/Operating Model compatibility.
8. Choose **In meinem Git-Repository** or **Lokal auf meinem Rechner**.
9. SAFOR verifies the actual remote-provider or local Git capabilities.
10. Select/define the HUMAN project.
11. SAFOR binds control storage:
   - Remote → separate HUMAN-owned `safor-memory`
   - Local → MASTER-only `.safor/`
12. Approve setup. Only then does SAFOR materialize control state and enter Factory Discovery.

## Ownership boundary

The canonical SAFOR repository and any commercial package source are package/framework sources only. They are never valid project targets.

Project code, manuscripts, assets and other Factory-produced work remain in the HUMAN-selected remote or local Git workspace.

## Package and authority boundary

Commercial entitlement answers only: **May this package be used?**

It never grants:
- Operating Model decision authority,
- provider permissions,
- execution mandate,
- project scope,
- review/acceptance authority.

Technical compatibility and organizational authority are evaluated separately.

## Factory consistency

Once resolved and pinned, Discovery, Planning and domain Evidence use the same Factory. Factory/Operating Model snapshots are immutable project binding evidence; they cannot be reused to expand commercial access.




## Agent Runtime requirement

An AGENT job is dispatchable in EXECUTION only when an Agent Runtime binding has verified `HOST_NATIVE_AUTOMATIC` or `EXTERNAL_AUTOMATION` activation and continuation capability.

If the host supports only manual chat activation, SAFOR must not turn that limitation into instructions for the HUMAN to operate agent chats. The job remains blocked with `AGENT_RUNTIME_AUTOMATION_UNAVAILABLE`.

Manual activation is permitted only in an explicitly labeled VALIDATION test harness and never proves production runtime readiness.
