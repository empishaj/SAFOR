# Security Policy

## SAFOR security model

SAFOR is deny-by-default and evidence-driven.

### Non-negotiable rules
- Never paste passwords, personal access tokens, private keys, recovery codes, or other secrets into chat.
- Provider permissions come from the actual GitHub/GitLab connection, never from JSON declarations.
- `{OWNER}/safor-memory` must be readable and writable before SAFOR proceeds.
- External mutations require authoritative provider readback before they are treated as completed.
- The free Website Factory uses its dedicated Website quality boundary; the broader secure software lifecycle belongs to the commercial Software/SaaS Factory.
- Unknown mutation effects transition to reconciliation before any retry.
- Self-healing may not bypass HUMAN gates, reviews, separation of duties, or active mandate scope.
- Force-push, history rewrite, destructive repository deletion, and invented evidence are forbidden automatic repairs.

## Reporting a vulnerability

Do not post secrets or exploitable details in a public issue. Contact the repository owner through a private GitHub channel before public disclosure.

## Supported version

Security hardening currently targets SAFOR v0.13.0-rc.8 and the free Website Factory/Operating Model 1.1.0 pair.


## Commercial package boundary

Commercial **production** Software/SaaS and Book package content is never resolved from the public canonical repository. rc.6 additionally publishes explicitly marked prerelease test/evaluation package bytes and domain Frameworks for testing; those bytes do not satisfy the production commercial package source contract. SOFTWARE_SAAS additionally fails closed if either selected domain package is FREE_PUBLIC or lacks independent entitlement evidence.


### Commercial entitlement and delivery trust

- A purchase receipt is not an entitlement.
- An entitlement record is not trusted merely because it names an issuer/verifier.
- Trust anchors are supplied externally as explicit trusted issuer/verifier identities.
- Paid entitlement status must be ACTIVE and valid for the explicit evaluation timestamp and active subject.
- `ENTITLED_PACKAGE_SOURCE` must return separate delivery evidence binding entitlement, package ID/version and artifact digest.
- Expired delivery evidence, untrusted delivery verifier or digest mismatch fails closed.
- The pure reference policy reads no wall clock and performs no network/provider calls.
- rc.4 models and validates the trust chain but does not claim that a production billing/licensing backend or cryptographic offline-signature verifier has been deployed.


### Public evaluation safety

- Public test packages use prerelease `*-test.1` versions and explicit `PUBLIC_TEST_EVALUATION` provenance.
- Test access bundles set `productionAuthorization=false`.
- Public possession of test Framework/package bytes never proves entitlement for production packages.
- Production catalog entries remain `ENTITLED_PACKAGE_SOURCE` with no public model path.
