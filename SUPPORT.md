# Support and Product Boundaries

## Current maturity

SAFOR v0.5.0-rc.1 is a Release Candidate architecture.

## Memory

SAFOR does not require a specific storage vendor. It requires a Memory provider that can prove durability, read/write access, revision identity and future-session resume.

Supported contracts:
- versioned repository,
- persistent host filesystem,
- custom Memory Provider Adapter.

A provider contract is not proof that the current chat host exposes the necessary tool.

## Work providers

SAFOR includes contracts for GitHub, GitLab, generic/self-hosted Git and Plastic SCM / Unity Version Control.

Actual execution depends on host connectors. SAFOR will not simulate missing provider tools.

## Collaboration

Shared Team mode is supported only when the Memory provider can prove shared access and safe multi-writer concurrency.

## LLM portability

Project continuation must not depend on one LLM or one chat transcript. Exact model provenance is recorded only when exposed by the host.

## Non-promises

SAFOR cannot:
- grant provider/storage permissions,
- turn ephemeral filesystem storage into durable Memory,
- infer exact LLM model versions the host does not expose,
- guarantee provider features that are not connected,
- treat delivery as proof of outcome,
- bypass HUMAN authority or reviews.
