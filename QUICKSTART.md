# SAFOR Quickstart — v0.5

## Prerequisites

You need a compatible chat host that can expose at least one **durable Memory option**.

A valid Memory option must prove:

- read,
- write,
- revision identity,
- durability,
- ability to reopen the same state in a future session.

GitHub or GitLab are optional implementations, not prerequisites.

## Bootstrap

1. Upload only `SAFOR-MASTER-COMPLETE.json`.
2. SAFOR asks: **Wo soll dein SAFOR Memory liegen?**
3. Choose one eligible Memory option.
4. Approve ownership: HUMAN or organization.
5. Choose collaboration mode:
   - **Personal**
   - **Shared Team**
6. SAFOR verifies Memory. Shared Team also requires shared access plus CAS/lock style concurrency.
7. Choose what you want to create:
   - **Software / Website**
   - **Buch**
8. SAFOR resolves the Factory and Operating Model.
9. Choose a work provider only if the Factory requires one.
10. Select or create the concrete project/workspace.
11. Approve setup.
12. SAFOR persists project state, registers the session and reads it back.

## Examples

### Software with GitHub
- Memory: persistent filesystem
- Work provider: GitHub
- Valid: yes, if filesystem persistence is proven.

### Software with Plastic SCM
- Memory: versioned repository
- Work provider: Plastic SCM / Unity Version Control
- Valid: yes, if the host exposes a compatible Plastic connector.

### Book
- Memory: versioned repository or persistent filesystem
- Work provider: optional
- A book may run in **Memory-only** mode.

## Fresh chat

A new chat must be able to:

1. connect to the same Memory,
2. load project/package state,
3. register a new session,
4. continue without the previous chat transcript.

If this cannot be done, the Memory provider is not eligible.
