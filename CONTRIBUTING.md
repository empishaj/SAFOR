# Contributing to SAFOR

## Product source vs project state

- Product/runtime definitions belong in `empishaj/SAFOR`.
- Project-specific authoritative state belongs in the selected SAFOR Memory provider.
- Domain artifacts belong in Factory-selected workspaces/providers.

Do not commit real project Memory into the SAFOR product repository.

## Architecture boundaries

1. MASTER Kernel stays domain- and provider-neutral.
2. `MEMORY_PROVIDER_ADAPTER` implements durable Memory semantics only.
3. `PROVIDER_ADAPTER` implements work/SCM semantics and is Factory-dependent.
4. Factory references capabilities, authorities and workspace requirements — never concrete actors.
5. Operating Model maps capabilities/authorities to roles but does not own Factory flow order.
6. Chat context is never authoritative state.
7. Shared writes use expected revisions and conflict-safe reconciliation.
8. Every persisted Factory output has an output provenance record.
9. LLM identity is observed only; never guessed.
10. HUMAN authority, reviews and safety gates may not be weakened.

## Change workflow

1. Create a branch.
2. Update schemas/models/packages consistently.
3. Rebuild `SAFOR-MASTER-COMPLETE.json`.
4. Run:
   ```bash
   python tools/build_bundle.py --check
   python tools/validate_safor.py
   ```
5. Update changelog and acceptance tests for user-visible behavior.
6. Open a pull request.
