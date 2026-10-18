# SAFOR Commercial Distribution Decision

Decision date: **2026-10-17**
Current implementation baseline: **SAFOR 0.14.0-rc.2**

## Product decision

The HUMAN has selected a modular commercial model with an explicit boundary between simple Website creation and Software/SaaS engineering:

- The **SAFOR Framework** is publicly distributable.
- **WEBSITE** is the free entry path.
- The default Website Factory and Website Operating Model are **FREE_PUBLIC**.
- **SOFTWARE_SAAS** is a commercial creation path.
- A Software/SaaS project requires both a **PAID_ENTITLEMENT_REQUIRED Software Factory** and a **PAID_ENTITLEMENT_REQUIRED Operating Model**.
- Each of those two Software/SaaS packages requires its own independently verified entitlement.
- **BOOK** is also a commercial creation path and requires paid domain packages.
- Factories and Operating Models remain independently versioned/licensable products, but a Creation Profile may constrain which access modes are valid.
- Paid package model content is not embedded in the public Framework artifact and is not resolved from the public canonical repository.

## Free Website starter

The default free Website pair is:

- `safor.factory.website-delivery@1.1.0`
- `safor.om.website-team@1.1.0`

These packages are deliberately narrower than the Software/SaaS products. They cover website intent, audience/content structure, UX, web implementation, accessibility/responsive/performance verification, publishing, post-publish observation and website outcome assessment.

If Website Discovery reveals application logic, a SaaS/service lifecycle or broader software engineering/operations needs, SAFOR requires an explicit Creation-Type change to `SOFTWARE_SAAS`.

## Commercial Software/SaaS path

The Software/SaaS defaults are:

- `safor.factory.software-delivery`
- `safor.om.saas-engineering`

Both are catalogued as `PAID_ENTITLEMENT_REQUIRED` and resolve only from a HUMAN-loaded licensed artifact or an entitled package source.

A free Factory or free Operating Model cannot be used to bypass the Software/SaaS commercial profile, even if it would otherwise be technically compatible.

## Entitlement boundary

Commercial entitlement permits use of the covered package/version only.

It never grants:
- organizational/Operating-Model authority,
- project scope,
- execution mandate,
- provider permissions,
- review or release approval.

## Project ownership

All project-specific work remains under HUMAN control:
- in a HUMAN/HUMAN-organization remote Git repository, or
- in a HUMAN local Git repository.

SAFOR product/package repositories are not project storage.

## Legacy disclosure

Software Factory and SaaS Engineering Operating Model versions through **1.6.0** were already committed publicly before this product split. Those historical bytes cannot be made confidential retroactively.

They are therefore:
- historical/reference artifacts,
- not the current protected commercial package channel,
- not catalogued as the current `SOFTWARE_SAAS` package source in rc.3.

New commercial Software/SaaS package content must be delivered through an entitled/private package channel.

## Still open before GA

This decision establishes and machine-enforces the product/licensing architecture. The following commercial operations remain open:
- final legal license text and terms,
- pricing and SKU policy,
- billing/purchase flow,
- entitlement issuer/verifier implementation,
- commercial package delivery infrastructure,
- end-to-end entitlement acceptance evidence.


## Commercial delivery channel contract

A payment, order reference or possession of package JSON never authorizes use by itself.

For a paid Factory or Operating Model, SAFOR requires:
1. commercial-basis evidence,
2. an ACTIVE entitlement for the exact subject/package/version,
3. verification by explicitly trusted issuer/verifier identities,
4. a valid entitlement time interval at explicit `evaluatedAt`,
5. when resolved from `ENTITLED_PACKAGE_SOURCE`: time-bounded delivery evidence from a trusted delivery verifier,
6. delivery evidence binding entitlementId, packageId, version and package digest,
7. domain-package integrity and compatibility checks before binding.

Manual licensed delivery through `HUMAN_LOADED_PACKAGE` remains allowed but does not bypass entitlement verification.

The public Framework defines this protocol but does not embed payment credentials, private signing keys, customer purchase data or current commercial package content.


## Public evaluation exception

For rc.6 testing, SAFOR deliberately publishes:
- `SAFOR-FRAMEWORK-SAAS.json`,
- `SAFOR-FRAMEWORK-BOOK-CREATION.json`,
- their explicitly versioned `*-test.1` Factory/Operating Model modules,
- matching public test access bundles.

This is a test/evaluation exception, not the commercial production distribution model. The test access bundles state `productionAuthorization=false`; production catalog entries still expose no public model path and continue to require the entitled/private package channel.
