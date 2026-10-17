# SAFOR 0.13.0-rc.1 — Composable Domain Packages

## Objective

Turn Factory and Operating Model into independent, chat-loadable JSON products without coupling commercial access to an entire Creation Type.

## Product contract

- SAFOR Framework remains the public bootstrap/runtime JSON.
- Factory and Operating Model are separate `SAFOR_DOMAIN_PACKAGE` JSON artifacts.
- Creation Profiles define defaults only.
- HUMAN may replace Factory, Operating Model, or both.
- FREE_PUBLIC and PAID_ENTITLEMENT_REQUIRED packages may be mixed.
- Each selected paid package requires its own independently verified entitlement.
- Entitlement evidence is external to the package artifact.
- Every package is integrity-checked and scoped to Framework version plus Creation Type.
- Every selected pair requires a materialized COMPATIBLE decision before binding.
- Project source/control stays in HUMAN-owned REMOTE_GIT or LOCAL_GIT workspaces.

## Corrected 0.12 weaknesses

1. The legacy package-manifest regex used `saf.*` although package IDs are `safor.*`.
2. The old free starter packages still declared kernel range `>=0.10.0 <0.11.0`.
3. Creation Profiles carried a shared access mode, which prevented a clean free+paid mixed pair.
4. Pair compatibility checked capability/authority coverage but did not yet include a first-class package-integrity and compatibility-decision record.

0.13 introduces a dedicated domain-package schema instead of mutating the provider-adapter manifest contract.

## Acceptance

- Free Website defaults work without entitlement.
- Paid Factory + free OM works with only Factory entitlement.
- Free Factory + paid OM works with only OM entitlement.
- Missing paid entitlement fails closed.
- Tampered package model changes fail digest verification.
- Package kind must match package ID namespace.
- Framework and Creation Type scope are enforced.
- Factory capability/authority requirements must be covered by the selected OM.
- Framework bundle is reproducible and contains no paid domain-package model content.
