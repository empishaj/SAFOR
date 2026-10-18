# SAFOR Quickstart

For a nontechnical German walkthrough, start with [START-HIER.md](START-HIER.md).

## Recommended end-user start

A normal user loads the domain-specific Framework for the intended result. The domain file already contains the SAFOR Framework, the default Factory and the default Operating Model.

| Intended result | Files to load into the same chat | Access |
|---|---|---|
| Website | `SAFOR-FRAMEWORK-WEBSITE.json` | Free public path |
| Software / SaaS evaluation | `SAFOR-FRAMEWORK-SAAS.json` and `SAFOR-TEST-ACCESS-SAAS.json` | Public test access; no production authorization |
| Book evaluation | `SAFOR-FRAMEWORK-BOOK-CREATION.json` and `SAFOR-TEST-ACCESS-BOOK-CREATION.json` | Public test access; no production authorization |

Do not load the generic `SAFOR-FRAMEWORK.json` as the normal end-user entrypoint. It is the shared engineering and distribution-building base and intentionally asks for a Creation Type.

## Domain-specific start sequence

1. Load exactly one domain Framework and, for a paid-domain evaluation, its matching test access bundle.
2. SAFOR verifies the Framework, Self-Healing and deterministic-control baselines.
3. SAFOR reads the domain and Creation Type from the domain distribution. It does **not** ask the HUMAN to select Website, SaaS or Book again.
4. SAFOR verifies the embedded default Factory and Operating Model separately.
5. For SaaS or Book evaluation, SAFOR verifies that the access bundle targets the exact distribution, domain, Creation Type, package IDs and `*-test.1` versions.
6. The test bundle must keep `productionAuthorization=false`; otherwise access is rejected.
7. SAFOR verifies package structure, SHA-256 contract digest, Framework range and bidirectional Factory ↔ Operating-Model compatibility.
8. SAFOR materializes the package selection and compatibility decision.
9. SAFOR asks whether the HUMAN project is in **REMOTE_GIT** or **LOCAL_GIT**.
10. SAFOR verifies actual provider or local Git capabilities and binds HUMAN-owned control storage.
11. Only then does Factory Discovery begin.

A successful public paid-domain evaluation resolves to:

```text
PUBLIC_EVALUATION_ACCESS_RESOLVED
→ SELECT_PROJECT_WORKSPACE_TYPE
```

## Website — free

Default packages:

- `safor.factory.website-delivery@1.1.0`
- `safor.om.website-team@1.1.0`

Both are `FREE_PUBLIC`. The Website path covers audience, purpose and scope; content and information architecture; experience design; web implementation; accessibility, responsive and performance verification; optional search-visibility verification; publishing; post-publish observation; and website outcome assessment.

If Discovery reveals application logic, a SaaS/service lifecycle or broader software engineering and operations, the Website Factory stops and requires an explicit switch to **Software / SaaS**.

## Software / SaaS — paid-mode public evaluation in rc.6

Load both:

- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-TEST-ACCESS-SAAS.json`

The distribution embeds:

- `safor.factory.software-delivery@1.7.0-test.1`
- `safor.om.saas-engineering@1.7.0-test.1`

Both modules remain `PAID_ENTITLEMENT_REQUIRED`. The public access bundle grants only those exact test versions and is not a production license.

A production SaaS selection requires a licensed Software Factory artifact, a verified entitlement for that exact Factory/version, a licensed SaaS Engineering Operating Model artifact and a separate verified entitlement for that exact Operating Model/version. A free member cannot be used to bypass the paid-pair policy.

## Book — paid-mode public evaluation in rc.6

Load both:

- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json`

The distribution embeds:

- `safor.factory.book-production@1.0.0-test.1`
- `safor.om.book-authoring@1.0.0-test.1`

Book likewise requires independent entitlement evidence for Factory and Operating Model. Its public test access authorizes only the exact test pair and never production use.

## Generic engineering start — advanced

Framework engineers may load `SAFOR-FRAMEWORK-v0.14.0-rc.2.json` or the current alias `SAFOR-FRAMEWORK.json`. This generic base intentionally follows a different sequence:

1. Verify the shared Framework.
2. Select **Website**, **Software / SaaS** or **Book**.
3. Resolve the selected Creation Profile.
4. Resolve Factory and Operating Model from public or entitled package sources.
5. Apply the same access, integrity, compatibility and workspace gates.

This route is useful for Framework engineering and distribution construction, not for the simplest end-user experience.

## Commercial boundary

Entitlement answers only: **May this exact package/version be used?**

It never grants organizational authority, provider permissions, project scope, execution mandate or acceptance authority.

For every paid production package SAFOR requires an explicit evaluation timestamp, active subject, trusted issuer IDs, trusted entitlement verifier IDs and trusted delivery verifier IDs. The entitlement must be `ACTIVE`, time-valid, bound to the active subject and exact package/version, and backed by commercial-basis evidence whose SKU matches the grant.

For `ENTITLED_PACKAGE_SOURCE`, the source additionally supplies external delivery evidence binding entitlement ID, package ID, exact version, artifact digest, delivery validity window and trusted delivery verifier. A mismatched or expired record blocks package use. `HUMAN_LOADED_PACKAGE` remains supported for a licensed file supplied manually, but manual loading never bypasses entitlement verification.

Historical public Software Factory/SaaS Operating Model 1.6.0 bytes are legacy disclosure, not the current commercial delivery source.

## Replacing Factory or Operating Model

A domain Framework starts with an embedded default Factory and Operating Model. Either module may later be replaced independently, for example by a Premium version.

SAFOR adopts a replacement only when package access and integrity, active Framework version, active Creation Type, active `domainId`, allowed `packageFamily`, Factory → Operating Model requirements and Operating Model → Factory requirements all pass.

A different package ID is allowed when it belongs to an accepted family and remains compatible.

Examples:

- Premium Website Factory + Website Operating Model → may be accepted.
- Website Factory + Premium Website Operating Model → may be accepted.
- Book Factory + SaaS Engineering Operating Model → rejected.
- SaaS Factory loaded into the Website Framework → rejected.

An incompatible replacement never silently changes the other module or the active domain; the previously valid binding remains active.
