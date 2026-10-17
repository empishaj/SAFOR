# SAFOR Quickstart

## What you need

Always:
- A compatible chat host.
- `SAFOR-FRAMEWORK-v0.13.0-rc.2.json` or the latest `SAFOR-FRAMEWORK.json`.
- A HUMAN-controlled Git project workspace.

For **Software / Website**:
- No commercial entitlement is required for the default starter Factory or default starter Operating Model.
- The current free defaults are `safor.factory.software-delivery@1.6.0` and `safor.om.saas-engineering@1.6.0`; both are separate `SAFOR_DOMAIN_PACKAGE` JSON artifacts resolved from canonical public SAFOR Git at immutable revision/blob.
- You may independently replace the Factory, the Operating Model, or both.

For any selected **paid Factory or Operating Model**:
- That package must be supplied through a HUMAN-loaded or entitled package source.
- Verified entitlement evidence for that exact selected package/version is mandatory.
- A free Factory may be combined with a paid Operating Model and vice versa when the pair is technically compatible.
- Merely possessing JSON or stating that it was purchased is not sufficient.

For **REMOTE_GIT** projects:
- GitHub or GitLab access with the required project read/write capabilities.
- A HUMAN-controlled `{OWNER}/safor-memory` for SAFOR control state.

For **LOCAL_GIT** projects:
- Host access to the HUMAN-selected local filesystem and Git repository.
- Proven read/write, Git history, branch and commit capabilities.
- No remote `safor-memory` is required; SAFOR uses a Git-tracked MASTER-only `.safor/` control root.

## Start

1. Load `SAFOR-FRAMEWORK-v0.13.0-rc.2.json`.
2. SAFOR verifies its Framework, Self-Healing and deterministic-control integrity.
3. Choose **Software / Website** or **Buch**.
4. SAFOR derives the Creation Profile's default Factory and Operating Model candidates before asking where the project lives.
5. Keep the defaults or independently override the Factory, Operating Model, or both.
6. SAFOR resolves access separately for each selected package; only a selected paid package requires entitlement.
7. SAFOR verifies each package's `SAFOR_DOMAIN_PACKAGE` structure, SHA-256 declared-contract digest, Framework range and Creation-Type scope.
8. SAFOR materializes a package-selection record and a COMPATIBLE Factory/Operating-Model decision.
9. Choose **In meinem Git-Repository** or **Lokal auf meinem Rechner**.
10. SAFOR verifies the actual remote-provider or local Git capabilities.
11. Select/define the HUMAN project.
12. SAFOR binds control storage:
   - Remote → separate HUMAN-owned `safor-memory`
   - Local → MASTER-only `.safor/`
13. Approve setup. Only then does SAFOR materialize control state and enter Factory Discovery.

## Ownership boundary

The canonical SAFOR repository and any commercial package source are package/framework sources only. They are never valid project targets.

Project code, manuscripts, assets and other Factory-produced work remain in the HUMAN-selected remote or local Git workspace.

## Package and authority boundary

Commercial entitlement is evaluated **per selected Factory or Operating Model** and answers only: **May this exact package/version be used?**

It never grants:
- Operating Model decision authority,
- provider permissions,
- execution mandate,
- project scope,
- review/acceptance authority.

Technical compatibility and organizational authority are evaluated separately.

## Factory consistency

Once independently selected, verified, declared COMPATIBLE and pinned, Discovery, Planning and domain Evidence use that exact Factory/Operating-Model pair. The project binding stores package selection, compatibility decision, package digest, selection origin and entitlement-evidence references. Snapshots cannot be reused to expand commercial access.



## Website Factory 1.6 lifecycle

The free Website Factory now models the full value-creation and production lifecycle:

`Product Definition → Quality/Security Requirements → Solution Design/Threat Model → Small-Batch Implementation + Continuous Verification → Independent Verification + Security Verification → Release → Deployment → Activation → Operate/Observe → Outcome Assessment`

Incident Recovery and Vulnerability Response are event-driven side paths after activation. Release, deployment, activation, healthy operation and business outcome remain separate facts.
