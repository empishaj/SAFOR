# SAFOR Quickstart

SAFOR is loaded as one self-contained JSON file and then guides the HUMAN through a controlled project bootstrap.

## Prerequisites

- A supported chat host with an available GitHub or GitLab connection.
- A HUMAN-controlled owner/namespace.
- A repository named exactly `safor-memory` under that owner.
- Proven read **and** write access to `{OWNER}/safor-memory`.

If `safor-memory` does not already exist or is not writable, SAFOR stops. It never creates that repository automatically.

## Start

1. Load `SAFOR-MASTER-COMPLETE-v0.5.0-rc.1.json` into a new compatible chat. For convenience, `SAFOR-MASTER-COMPLETE.json` is the latest RC alias.
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
