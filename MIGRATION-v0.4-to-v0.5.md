# Migration: SAFOR v0.4 → v0.5

v0.5 changes the persistence contract and therefore requires explicit migration.

## Breaking conceptual changes

### 1. Control repository → SAFOR Memory
v0.4 bound authoritative control state to a repository-oriented `safor-memory` model.

v0.5 binds a provider-neutral `MEMORY_PROVIDER_ADAPTER`.

A repository named `safor-memory` may still be used, but the name and Git hosting product are no longer protocol requirements.

### 2. Memory provider ≠ work provider
v0.5 stores these as independent bindings.

Example:
- Memory: persistent filesystem
- Work: GitHub

or:
- Memory: GitLab repository
- Work: Plastic SCM / Unity Version Control

### 3. New Memory binding
Projects require `memory-binding.json` containing ownership, stable location, verified capabilities and concurrency strategy.

### 4. Session state
Each chat/agent session receives a session record with actor/host/LLM observability and base Memory revision.

### 5. Output provenance
Every persisted Factory output requires a `SAFOR_OUTPUT_RECORD`.

### 6. Project descriptor
`controlRepository` / repository-centric assumptions are replaced by:
- `memoryBindingRef`
- zero or more `workspaces`

### 7. Bindings
v0.5 separates:
- `memoryProvider`
- `workProviderAdapters`

## Migration procedure

1. Select/approve the target Memory provider.
2. Prove durability/read/write/revision/resume.
3. Bind physical owner (HUMAN or organization).
4. Choose PERSONAL or SHARED_TEAM.
5. For SHARED_TEAM prove shared access + CAS/lock.
6. Create `memory-binding.json`.
7. Convert project descriptor to v0.5.
8. Convert package bindings.
9. Register the migration session.
10. Persist current state at an expected Memory revision.
11. Read back all aggregates.
12. Continue only after consistency verification.

Migration must never silently change project authority, Factory or Operating Model.
