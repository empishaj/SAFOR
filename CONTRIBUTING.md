# Contributing to SAFOR

SAFOR separates product source from project runtime memory.

## Product source
Changes to the SAFOR framework belong in this repository.

## Runtime memory
Project-specific state belongs in the HUMAN's `{OWNER}/safor-memory` repository and must never be committed here.

## Change rules
1. Create a dedicated branch.
2. Preserve kernel/domain separation.
3. Factories reference capabilities and authorities, not concrete actors.
4. Discovery, Planning, and Evidence must remain bound to the same selected Factory.
5. Do not weaken HUMAN authority, provider readback, reconciliation, or self-healing safety boundaries.
6. Update the changelog for user-visible behavior.
7. Run `python tools/validate_safor.py`.
8. Open a pull request; do not treat a local JSON edit as a release.

## Versioning
SAFOR follows semantic-versioning intent:
- PATCH: compatible corrections/hardening
- MINOR: compatible capabilities/factories
- MAJOR: incompatible control-plane or persistence contracts
