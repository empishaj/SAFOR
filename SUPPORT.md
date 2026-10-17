# Support and Product Boundaries

## Current maturity

SAFOR v0.13.0-rc.7 is a **Release Candidate**.

The architecture and complete distribution are machine-checkable, but General Availability requires explicit end-to-end acceptance on every claimed provider path.

## Supported creation types

- Website — free starter
- Software / SaaS — commercial
- Buch — commercial

Additional Factories are not implicitly supported until they are published, bound and validated.

## Supported provider contracts

- GitHub
- GitLab

Actual usability depends on the chat host exposing the required provider connection and capabilities.

## Agent runtime boundary

SAFOR can persist agent identities and repository-native jobs, but a normal chat is not assumed to wake automatically when a new inbox job appears. A HUMAN, automation or host-supported activation mechanism must activate the agent runtime. After activation, the job contract comes from the repository rather than HUMAN prompt copying.

## What SAFOR does not promise

- It cannot create provider permissions that the HUMAN/account does not have.
- It cannot force a chat host to expose native UI controls.
- It cannot make a normal chat execute in the background when the host provides no activation mechanism.
- It cannot guarantee cancellation of an external operation without provider evidence.
- It does not treat delivery as proof of business/reader outcome.
- It does not silently repair high-impact or authorization-expanding failures.

## Escalation

When safe automatic continuation is impossible, SAFOR stops or waits for the HUMAN and reports:
1. what failed,
2. what was already attempted,
3. the current safe state,
4. the smallest required HUMAN action.


## Project workspace support in 0.13

SAFOR distinguishes package/framework sources from HUMAN project storage.

Supported project workspace classes:
- **REMOTE_GIT** — GitHub or GitLab project repository controlled by the HUMAN or HUMAN organization; separate writable `safor-memory` is used for control state.
- **LOCAL_GIT** — HUMAN-selected local Git repository when the chat/host exposes actual local filesystem and Git capabilities; `.safor/` is MASTER-only control state.

SAFOR does not claim local execution when the current host cannot actually access the local filesystem/Git repository.

Paid Factory/Operating Model access additionally requires supported entitlement verification. The 0.13 schema supports authorized provider readback or verified offline signature evidence; production entitlement infrastructure remains a release-readiness gate.



## Product paths in the current release candidate

**Website** is the free supported starter:
- `safor.factory.website-delivery@1.1.0`
- `safor.om.website-team@1.1.0`

**Software / SaaS** is commercial:
- Software Factory entitlement required.
- SaaS Engineering Operating Model entitlement required.
- Both packages must be paid; a free override is not valid for this Creation Profile.

**Book** remains commercial.

rc.4 provides the machine-enforced entitlement/delivery contract and reference verification logic. A production billing system, entitlement issuer/verifier service and protected package delivery service remain GA-readiness work.


## Domain Framework files in rc.6

End users should normally load a domain-specific Framework rather than the generic base Framework:

- Website: `SAFOR-FRAMEWORK-WEBSITE.json` — public.
- SaaS: `SAFOR-FRAMEWORK-SAAS.json` — public test/evaluation artifact; paid-mode test modules.
- Book: `SAFOR-FRAMEWORK-BOOK-CREATION.json` — public test/evaluation artifact; paid-mode test modules.

For rc.6, SaaS and Book test Frameworks are committed publicly to enable end-to-end testing. Their embedded packages are prerelease test versions and are not the protected commercial production package source.

Premium Factory or Operating Model replacement is supported only inside the active domain and after bidirectional package-family and counterpart compatibility checks.


### Public evaluation access

Use `SAFOR-TEST-ACCESS-SAAS.json` with the SaaS test Framework and `SAFOR-TEST-ACCESS-BOOK-CREATION.json` with the Book test Framework.

These access bundles authorize only their explicit test package versions and declare `productionAuthorization=false`. Production licensing and delivery remain separate GA work.
