# SAFOR 0.12.0-rc.1 — Modular Packages and HUMAN-owned Workspaces

## Objective

Separate SAFOR into four independent concerns:

1. SAFOR Framework — public orchestration/control runtime.
2. Factory / Operating Model Packages — independently loadable, versioned and commercially classifiable knowledge packages.
3. Commercial Entitlement — determines whether a paid package may be used; never grants organizational authority.
4. HUMAN Project Workspace — the exclusive location for project-specific work, either a HUMAN-controlled remote Git repository or a HUMAN-controlled local Git workspace.

The canonical SAFOR product repository is a Framework/package-catalog source and MUST NOT become an implicit project workspace.

## Product decisions

- SOFTWARE_WEBSITE is the free starter path.
- Its current Factory and Operating Model are FREE_PUBLIC and may be resolved automatically from the public canonical SAFOR repository.
- BOOK is PAID_ENTITLEMENT_REQUIRED.
- Paid package metadata may be public, but paid package model content MUST NOT be embedded in the public Framework bundle.
- Future premium Factories and Operating Models are independently purchasable and may be combined only when compatibility checks pass.
- Package access/entitlement and organizational decision authority are orthogonal.

## Distribution

The 0.12 public artifact becomes a Framework bundle, not a complete catalog of every Factory/Operating Model.

The Framework bundle contains:
- Kernel/control/runtime models and schemas.
- Package catalog metadata.
- Package distribution and entitlement policy.
- Workspace policy.
- Provider adapters needed by Framework bootstrap.
- No paid Factory or paid Operating Model model content.
- No project-specific content.

Free website Factory/OM content is resolved from the public canonical SAFOR repository at an immutable provider revision/blob before project binding.

## Package source classes

- PUBLIC_CANONICAL_REPOSITORY — only FREE_PUBLIC packages.
- HUMAN_LOADED_PACKAGE — package artifact explicitly supplied by the HUMAN.
- ENTITLED_PACKAGE_SOURCE — commercial package source accessible only with verified entitlement.
- PROJECT_PINNED_SNAPSHOT — immutable project/control snapshot after successful resolution; never a discovery source for a different package.

## Commercial access

Access modes:
- FREE_PUBLIC
- PAID_ENTITLEMENT_REQUIRED

A paid package may bind only when:
- the exact package/version is present from HUMAN_LOADED_PACKAGE or ENTITLED_PACKAGE_SOURCE;
- entitlement evidence is independently verifiable;
- entitlement covers packageId/version/customer scope;
- technical package integrity and kernel compatibility pass;
- Factory/Operating Model compatibility passes.

Possession of a JSON claiming to be entitled is not sufficient. Entitlement evidence must be verified by an allowed verifier/source.

## Project workspace

Every project binds exactly one HUMAN-owned project workspace:

### REMOTE_GIT
- repository belongs to/is controlled by the HUMAN/organization;
- GitHub or GitLab baseline in rc.1;
- project source/manuscript/assets remain there;
- SAFOR product repository and package sources are read-only package sources, never project targets.

### LOCAL_GIT
- local filesystem path selected/approved by HUMAN;
- a valid local Git repository is required;
- SAFOR verifies local read/write and Git capabilities before execution;
- project source/manuscript/assets remain on the HUMAN machine;
- MASTER may maintain a protected .safor/ control root in the HUMAN local repository; worker jobs may never write that root.

## Control workspace

- REMOTE_GIT project baseline: separate HUMAN-controlled `safor-memory` repository remains the default control workspace.
- LOCAL_GIT project baseline: control state is stored under `.safor/` inside the HUMAN local Git repository, MASTER-only, with worker writes prohibited.
- A future LOCAL_SEPARATE_CONTROL_REPOSITORY may be added without changing Factory/OM semantics.

## Initialization order

1. Verify Framework/recovery/deterministic-control baseline.
2. Select/load Creation Type.
3. Resolve package access profile.
4. For FREE_PUBLIC packages, resolve public Factory/OM from canonical SAFOR Git at immutable revision/blob.
5. For PAID packages, require loaded/entitled Factory and OM; otherwise PACKAGE_ACCESS_REQUIRED.
6. Validate package integrity/kernel compatibility.
7. Validate Factory/OM capability compatibility.
8. Select Project Workspace: REMOTE_GIT or LOCAL_GIT.
9. Verify actual workspace capabilities.
10. Bind Control Workspace according to workspace mode.
11. Select/create project only inside HUMAN workspace.
12. Materialize control and begin Factory Discovery.

## Hard invariants

- SAFOR product/package source can never become project workspace implicitly.
- Entitlement never grants business/organizational authority.
- Project workspace selection never grants package entitlement.
- Paid package content is never embedded in the public Framework distribution.
- FREE_PUBLIC auto-resolution must use an immutable package revision/blob.
- Local workspace without Git does not qualify for mutating SAFOR execution.
- Worker agents cannot mutate local .safor/ control paths.
- Remote project artifacts remain outside safor-memory.
- Package snapshots are read-only after pinning.

## Legacy disclosure boundary

Pre-0.12 development packages that were already committed publicly cannot be made secret retroactively. 0.12 must stop embedding or resolving any package designated PAID from public source. Commercially protected paid versions must be distributed through future entitled package sources or signed HUMAN-loaded artifacts.

## rc.1 acceptance criteria

- Public Framework bundle contains no paid Factory/OM module content.
- Website creation profile resolves the free Factory/OM only from PUBLIC_CANONICAL_REPOSITORY.
- Book creation profile cannot resolve paid model content from the public Framework/public package source.
- Paid path without verified entitlement returns PACKAGE_ACCESS_REQUIRED.
- Entitlement cannot satisfy any Operating Model authority.
- REMOTE_GIT and LOCAL_GIT project workspace schemas validate.
- LOCAL_GIT requires Git/read/write capability and protects .safor/.
- Remote project target cannot equal canonical SAFOR product/package repository.
- Build/validator/unit tests pass reproducibly.
