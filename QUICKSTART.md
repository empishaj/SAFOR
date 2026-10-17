# SAFOR Quickstart

## What you need

Always:
- A compatible chat host.
- The domain Framework file for what you want to create.
- A HUMAN-controlled Git project workspace.

For Website work, load `SAFOR-FRAMEWORK-WEBSITE.json`. The Website domain and default Factory/Operating Model are already embedded, so SAFOR does not ask you to choose Website/SaaS/Book again.

## Domain-specific Frameworks

### Website — free

Default packages:
- `safor.factory.website-delivery@1.1.0`
- `safor.om.website-team@1.1.0`

Both are `FREE_PUBLIC` and resolve from canonical public SAFOR Git at immutable revision/blob.

The Website path covers:
- audience/purpose/scope,
- content and information architecture,
- experience design,
- web implementation,
- accessibility, responsive and performance verification,
- optional search-visibility verification,
- publishing,
- post-publish observation,
- website outcome assessment.

If the requested result requires application logic, SaaS/service lifecycle or broader software engineering/operations, the Website Factory stops and requires an explicit change to **Software / SaaS**.

### Software / SaaS — paid, public test artifact in rc.6

For testing, load `SAFOR-FRAMEWORK-SAAS.json`. Then load `SAFOR-TEST-ACCESS-SAAS.json` to exercise the paid-access gate with the public `1.7.0-test.1` Factory/OM pair.

The public test access is not a production license.

Default product identities:
- `safor.factory.software-delivery`
- `safor.om.saas-engineering`

Both selected packages must be `PAID_ENTITLEMENT_REQUIRED`.

You need:
1. a licensed Software Factory artifact,
2. a verified entitlement for that Factory/version,
3. a licensed SaaS Engineering Operating Model artifact,
4. a separate verified entitlement for that Operating Model/version.

A free Factory or free Operating Model cannot be used to bypass the Software/SaaS commercial profile.

### Buch — paid, public test artifact in rc.6

For testing, load `SAFOR-FRAMEWORK-BOOK-CREATION.json`. Then load `SAFOR-TEST-ACCESS-BOOK-CREATION.json` to exercise the paid-access gate with the public `1.0.0-test.1` Factory/OM pair.

Book likewise requires a paid Factory and paid Operating Model with independent entitlement evidence.

## Start

1. Load `SAFOR-FRAMEWORK-v0.13.0-rc.6.json`.
2. SAFOR verifies Framework, Self-Healing and deterministic-control integrity.
3. Choose **Website**, **Software / SaaS** or **Buch**.
4. SAFOR resolves the Creation Profile and its selected-package access policy.
5. SAFOR resolves Factory and Operating Model access separately.
6. For commercial profiles, SAFOR rejects a free selected member before binding.
7. Every paid selected package requires its own verified entitlement.
8. SAFOR verifies package structure, SHA-256 contract digest, Framework range, Creation-Type scope and pair compatibility.
9. SAFOR materializes the package selection and compatibility decision.
10. Choose **In meinem Git-Repository** or **Lokal auf meinem Rechner**.
11. SAFOR verifies actual provider/local Git capabilities and binds HUMAN-owned control storage.
12. Only then does Factory Discovery begin.

## Commercial boundary

Entitlement answers only: **May this exact package/version be used?**

It never grants organizational authority, provider permissions, project scope, execution mandate or acceptance authority.

Historical public Software Factory/SaaS OM 1.6.0 bytes are legacy disclosure, not the current commercial delivery source.


## Paid package verification in rc.6

For every paid package SAFOR requires a verification context containing:
- explicit `evaluatedAt`,
- active `subjectRef`,
- trusted entitlement issuer IDs,
- trusted entitlement verifier IDs,
- trusted delivery verifier IDs.

The entitlement must be `ACTIVE`, time-valid, bound to the active subject and exact package/version, and backed by commercial-basis evidence whose SKU matches the grant.

For `ENTITLED_PACKAGE_SOURCE`, the package source must additionally return external delivery evidence that binds:
- entitlement ID,
- package ID,
- exact version,
- domain-package digest,
- delivery validity window,
- trusted delivery verifier.

A mismatched or expired delivery record blocks package use. `HUMAN_LOADED_PACKAGE` remains supported for a licensed file supplied manually, but the entitlement checks remain mandatory.


## Replacing Factory or Operating Model

A domain Framework starts with an embedded default Factory and Operating Model. Either module may later be replaced independently, for example by a Premium version.

SAFOR adopts a replacement only when package access/integrity, active Framework version, active Creation Type, active `domainId`, allowed `packageFamily`, Factory → Operating Model requirements and Operating Model → Factory requirements all pass.

A different package ID is allowed when it belongs to an accepted family and remains compatible.

Examples:
- Premium Website Factory + Website Operating Model → may be accepted.
- Website Factory + Premium Website Operating Model → may be accepted.
- Book Factory + SaaS Engineering Operating Model → rejected.
- SaaS Factory loaded into the Website Framework → rejected.

An incompatible replacement never silently changes the other module or the active domain; the previously valid binding remains active.
