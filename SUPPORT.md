# Support and Product Boundaries

## Current maturity

SAFOR v0.13.0-rc.2 is a **Release Candidate**.

The architecture and complete distribution are machine-checkable, but General Availability requires explicit end-to-end acceptance on every claimed provider path.

## Supported creation types

- Software / Website
- Buch

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


## Free Website starter in rc.2

The canonical free Website defaults are:
- `safor.factory.software-delivery@1.6.0`
- `safor.om.saas-engineering@1.6.0`

Factory 1.6 models Product Definition, Quality/Security Requirements, Solution Design/Threat Assessment, small-batch Implementation with continuous verification, independent/security verification, Release, Deployment, Activation, Operate/Observe, conditional Recovery/Vulnerability Response and Outcome Assessment.
