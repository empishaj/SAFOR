# SAFOR 0.14.0-rc.3

## Corrected contract

The project descriptor now accepts exactly WEBSITE, SOFTWARE_SAAS and BOOK. The old SOFTWARE_WEBSITE enum could not satisfy the Website/SaaS package contracts. Active selection rules and the derived menu use the same vocabulary; domain distributions continue to suppress redundant creation-type questions.

## Regression protection and integrity

A pure type-contract validator is called by both builders and the distribution validator. The regression suite checks all domains, legacy/unknown values, missing or duplicate records, source/embedded schema agreement, source blob identities and distribution digests. A deliberately reintroduced schema conflict is rejected even after recomputing the distribution digest.

## Migration boundary

Pre-0.14 sources remain unchanged. Previous release bytes remain unchanged in pinned Git history; the superseded generated root bundle is retired according to the existing repository-retention policy. This candidate does not rewrite existing projects, select a domain for ambiguous legacy records, activate agents or authorize deployment. An existing project still needs its explicit, non-destructive migration and provider readback. Existing GA blockers and commercial entitlement policies remain in force.
