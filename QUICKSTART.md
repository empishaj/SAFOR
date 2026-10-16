# SAFOR Quickstart

SAFOR is loaded as one self-contained JSON file and then guides the HUMAN through a controlled project bootstrap.

## Prerequisites

- A supported chat host with an available GitHub or GitLab connection.
- A HUMAN-controlled owner/namespace.
- A repository named exactly `safor-memory` under that owner.
- Proven read **and** write access to `{OWNER}/safor-memory`.

If `safor-memory` does not already exist or is not writable, SAFOR stops. It never creates that repository automatically.

## Start

1. Load `SAFOR-MASTER-COMPLETE-v0.7.0-rc.1.json` into a new compatible chat. For convenience, `SAFOR-MASTER-COMPLETE.json` is the latest RC alias.
2. Choose **GitHub** or **GitLab**.
3. SAFOR verifies the actual provider connection and baseline read/write capabilities.
4. Choose the owner/namespace.
5. SAFOR verifies `{OWNER}/safor-memory`.
6. Choose exactly one creation type:
   - **Software / Website**
   - **Buch**
7. Choose **existing project** or **new project**.
8. Confirm the resolved Factory, Operating Model and Provider Adapter.
9. Approve project materialization.
10. Continue through the chat-native action menu.

## Factory binding

The HUMAN-selected creation type remains authoritative:

- Software / Website → Software Delivery Factory + SaaS Engineering Operating Model.
- Buch → Book Production Factory + Book Authoring Operating Model.

Discovery, Planning and domain Evidence always come from that same Factory. SAFOR must not mix contracts across Factories.

## Runtime memory vs product source

- Product source: `empishaj/SAFOR`
- Project runtime/control memory: `{OWNER}/safor-memory`

These repositories serve different purposes and must not be conflated.

## Safety

Do not paste passwords, PATs, private keys or other credentials into chat. Provider rights must be observed through the actual connected provider.


## Persistent agent chats

When an Operating Model resolves work to an AGENT actor, SAFOR can create a persistent agent workspace in `safor-memory`.

The agent is initialized once with:
- control repository,
- project ID,
- agent ID.

After that, the HUMAN does **not** copy full job prompts into the agent chat. On activation the agent loads its identity/state, scans its inbox, verifies an eligible job, claims it with optimistic concurrency, performs only the authorized scope, and writes its result/evidence back to the repository.

See `AGENT-WORKSPACE.md`.


## Parallel agent scheduling

SAFOR v0.7 can serve multiple persistent agent chats in parallel. Work is dispatched only as ATOMIC units whose dependencies are accepted, inputs are pinned, required capabilities are available, and mutation/resource domains do not conflict.

With six active chat agents at one scheduling slot each, the MASTER can dispatch up to six mutually conflict-free READY jobs in one wave. Mutating jobs use dedicated `safor/job/{jobKey}/{agentKey}` branches.

Every agent job writes:
- machine result: `outbox/{jobId}.result.json`
- HUMAN-readable result: `outbox/{jobId}.result.md`

The Markdown report is the default HUMAN view; mutating results also include verifiable Git base/head commits, result commits and changed paths.

See `MULTI-AGENT-SCHEDULER.md`.
