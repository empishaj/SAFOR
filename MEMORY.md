# SAFOR Memory

SAFOR Memory is the authoritative project memory shared across chats, humans and LLM instances.

## Ownership

- **Logical owner:** the SAFOR project.
- **Physical owner/controller:** the HUMAN or organization.
- **LLM:** access participant only; never owner.

## Eligible providers

### Versioned repository
Examples include GitHub, GitLab, generic Git or another SCM when its adapter exposes equivalent artifact/revision semantics.

`safor-memory` is a recommended repository name, not a protocol requirement.

### Host filesystem
Eligible only when the host proves that the same stable location survives session boundaries and can be reopened.

Ephemeral scratch storage is not SAFOR Memory.

### Custom provider
Organizations may implement the Memory Provider Adapter contract.

## Mandatory capabilities

- `memory.object.read`
- `memory.object.write`
- `memory.revision.read`
- `memory.durability.prove`
- `memory.resume.prove`

Shared Team additionally requires:

- `memory.shared_access`
- and either `memory.compare_and_swap` or `memory.lock`

## Persistence rule

No later action may rely on an authoritative project fact until that fact is persisted and read back from Memory.

## Concurrency rule

Every write carries an expected Memory revision. A mismatch results in `RECONCILE_REQUIRED`.

No last-write-wins overwrite of unseen project state is allowed.

## Fresh-session rule

Prior chat history is optional. SAFOR must be able to reconstruct actionable project state from:

- Memory binding,
- project descriptor,
- pinned packages,
- state aggregates,
- sessions,
- decisions,
- outputs,
- evidence.

## Provenance rule

Each output records which actor/session created it and which LLM was used when that information is actually observable.
