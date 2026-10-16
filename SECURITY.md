# Security Policy — SAFOR v0.5

## Core model

SAFOR treats the HUMAN/organization-controlled Memory provider as the authoritative project state. Chat history and LLM context are non-authoritative caches.

## Memory safety

A Memory provider is eligible only after SAFOR proves:
- read,
- write,
- revision identity,
- durability,
- future-session resume.

Shared Team additionally requires shared access plus compare-and-swap or locking.

A stale Memory revision must produce `RECONCILE_REQUIRED`. Silent last-write-wins overwrite is forbidden.

## Ownership

SAFOR/LLMs never own project Memory. Physical control remains with the HUMAN or organization.

## Credentials

Never paste passwords, PATs, private keys, recovery codes or comparable secrets into chat. Permissions are established through host/provider connections.

## Provider safety

Provider package manifests describe semantics only. They never prove:
- a connector is installed,
- a tool exists,
- a permission is granted.

Missing tools remain unavailable; SAFOR must not simulate mutations.

## Provenance

Every persisted Factory output requires producer/session provenance. LLM provider/model/version are stored only when the host exposes them. SAFOR must never guess unavailable model identity.

## Self-healing

Self-healing may not:
- change Memory provider/owner implicitly,
- overwrite unseen Memory revisions,
- bypass HUMAN gates/reviews,
- expand mandates,
- force-push/rewrite history,
- delete authoritative Memory without a verified restore path,
- invent evidence.

## Vulnerability reporting

Do not publish secrets or directly exploitable details in a public issue. Contact the repository owner privately before disclosure.
