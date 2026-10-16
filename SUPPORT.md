# Support and Product Boundaries

## Current maturity

SAFOR v0.5.0-rc.1 is a **Release Candidate**.

The architecture and complete distribution are machine-checkable, but General Availability requires explicit end-to-end acceptance on every claimed provider path.

## Supported creation types

- Software / Website
- Buch

Additional Factories are not implicitly supported until they are published, bound and validated.

## Supported provider contracts

- GitHub
- GitLab

Actual usability depends on the chat host exposing the required provider connection and capabilities.

## What SAFOR does not promise

- It cannot create provider permissions that the HUMAN/account does not have.
- It cannot force a chat host to expose native UI controls.
- It cannot guarantee cancellation of an external operation without provider evidence.
- It does not treat delivery as proof of business/reader outcome.
- It does not silently repair high-impact or authorization-expanding failures.

## Escalation

When safe automatic continuation is impossible, SAFOR stops or waits for the HUMAN and reports:
1. what failed,
2. what was already attempted,
3. the current safe state,
4. the smallest required HUMAN action.
