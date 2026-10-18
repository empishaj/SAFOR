# SAFOR

**Systemic AI Factory Orchestration Runtime**

SAFOR is a system-oriented orchestration runtime for HUMAN-governed, evidence-backed AI work across interchangeable Factories and Operating Models.

> Current maturity: **v0.14.0-rc.5 — Release Candidate**

## Product execution model

SAFOR is loaded as JSON into an ordinary compatible LLM chat. No customer-installed runtime is required. The chat follows the declarative contract and uses only real host/Git capabilities. Optional Python reference implementations support validation and stronger host integration but are not an end-user prerequisite.

MASTER is the only fachliche and organizational HUMAN interface. An agent does not conduct domain discussion with the HUMAN; it writes substantive results, questions, conflicts and evidence to the contracted Git targets and renders only minimal operational status in its initialized agent chat.

## Start here

- Nontechnical German test guide: [START-HIER.md](START-HIER.md)
- Technical and English quickstart: [QUICKSTART.md](QUICKSTART.md)

Use the domain-specific entrypoint:

| Creation Type | Files loaded by the user | Factory | Operating Model | Access |
|---|---|---|---|---|
| WEBSITE | `SAFOR-FRAMEWORK-WEBSITE.json` | `safor.factory.website-delivery@1.2.0` | `safor.om.website-team@1.2.0` | FREE_PUBLIC |
| SOFTWARE_SAAS evaluation | `SAFOR-FRAMEWORK-SAAS.json` + `SAFOR-TEST-ACCESS-SAAS.json` | `safor.factory.software-delivery@1.8.0-test.1` | `safor.om.saas-engineering@1.8.0-test.1` | public test only; both paid-mode |
| BOOK evaluation | `SAFOR-FRAMEWORK-BOOK-CREATION.json` + `SAFOR-TEST-ACCESS-BOOK-CREATION.json` | `safor.factory.book-production@1.1.0-test.1` | `safor.om.book-authoring@1.1.0-test.1` | public test only; both paid-mode |

The Domain Framework already fixes Website, SaaS or Book and embeds the matching default Factory and Operating Model. SAFOR must not ask the user to select the domain again. The additional SaaS/Book test file is entitlement evidence for the exact public test versions; it is not another domain module and never grants production authorization.

`SAFOR-FRAMEWORK.json` and `SAFOR-FRAMEWORK-v0.14.0-rc.5.json` remain the generic shared base Frameworks for engineering and distribution building. They intentionally ask for a Creation Type and are not the simplest end-user entrypoint.

## Platform-owned HUMAN communication

The SAFOR platform—not a Factory or Operating Model—owns every HUMAN-visible response. Domain modules supply facts, risks, evidence and genuine decision requirements; the platform decides whether to speak, how much to show and whether an interaction menu is warranted. Framework detection and safe migration-plan drafting therefore default to a short non-interactive notice, while full technical analysis remains available under Details/Evidence.

## Product paths

The Website starter is deliberately narrower than the Software/SaaS path. If Website Discovery reveals application logic, a service/SaaS lifecycle or broader software operations, SAFOR requires an explicit switch to `SOFTWARE_SAAS`.

All domain Frameworks use the same SAFOR kernel. Embedded Factory and Operating Model are replaceable defaults. Premium replacements are adopted only when access, integrity, active domain, package-family constraints and bidirectional Factory ↔ Operating-Model compatibility all pass.

## Public paid-domain evaluation

The current SaaS and Book distributions are public test/evaluation artifacts. Their embedded modules still declare `PAID_ENTITLEMENT_REQUIRED`.

The matching access bundles are self-describing and bind only to their intended distribution:

- `SAFOR-TEST-ACCESS-SAAS.json` → `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json` → `SAFOR-FRAMEWORK-BOOK-CREATION.json`

`runtime/public_evaluation_access.py` is the deterministic reference implementation for compatible host/runtime integrations between both uploaded artifacts. It rejects wrong filenames, cross-domain bundles, altered activation contracts, additional or imprecise grants and any attempt to set `productionAuthorization=true`. On success it resolves package access and continues at `SELECT_PROJECT_WORKSPACE_TYPE`, without a redundant domain question.

A generic chat host does not automatically execute this Python module merely because JSON files were uploaded. Without a host or adapter invoking the reference implementation, a chat evaluation tests whether the model follows the contract; it does not prove machine-enforced entitlement execution. Optional host integration can provide stronger machine enforcement, but normal SAFOR chat use does not require a separately installed customer runtime.

These public access bundles are not purchase evidence, are not transferable and do not change the production catalog. Production paid packages still resolve through licensed HUMAN delivery or `ENTITLED_PACKAGE_SOURCE` with independently verified entitlement evidence for Factory and Operating Model.

## Repository separation

- **`empishaj/SAFOR`** — public Framework, metadata, schemas, free Website packages and public test artifacts. Never the HUMAN project workspace.
- **`{OWNER}/safor-memory`** — HUMAN-controlled remote control workspace for REMOTE_GIT projects.
- **HUMAN project workspace** — the selected remote or local Git repository containing domain work.
- **Commercial package source** — separate protected distribution for current production-paid Software/SaaS and Book content.

## Distribution

- `SAFOR-FRAMEWORK-v0.14.0-rc.5.json` — versioned generic Framework release candidate.
- `RELEASE-EVIDENCE-0.14.0-rc.5.json` — versioned release, migration and validation evidence.
- `SAFOR-FRAMEWORK.json` — current generic Framework alias.
- `SAFOR-FRAMEWORK-WEBSITE.json` — end-user Website distribution.
- `SAFOR-FRAMEWORK-SAAS.json` — end-user public SaaS evaluation distribution.
- `SAFOR-FRAMEWORK-BOOK-CREATION.json` — end-user public Book evaluation distribution.
- `v0.14.0/packages/factories/website-delivery/1.2.0/package.json` — free Website Factory.
- `v0.14.0/packages/operating-models/website-team/1.2.0/package.json` — free Website Operating Model.

Historical Software Factory/SaaS Operating Model versions remain available through Git history. Version 1.6.0 is retained in the current tree as the explicit legacy-disclosure baseline; it is not the current protected commercial production channel.

## Repository retention

The default branch contains current distributables, required build sources, explicit compatibility/disclosure baselines and maintained documentation/runtime/tests. Superseded generated bundles, prototype trees and non-build source snapshots remain recoverable through Git history instead of being duplicated in the working tree.

The active source tree is `v0.14.0`. `v0.10.0` through `v0.13.0` remain explicit compatibility and audit baselines; earlier product evolution remains auditable through Git history. Repository-hygiene tests prevent retired root bundles, non-build version trees and superseded package worktrees from returning unnoticed.

## Commercial trust chain

Paid package access in the current release candidate is not satisfied by possession of JSON or a purchase receipt alone.

The required production chain is:

```text
commercial basis
→ ACTIVE entitlement
→ trusted entitlement verification
→ protected delivery evidence for ENTITLED_PACKAGE_SOURCE
→ package digest verification
→ Factory/Operating-Model compatibility
→ immutable binding
```

Strict verification requires an explicit evaluation timestamp, a matching HUMAN or organization subject, trusted issuer, trusted entitlement verifier, matching SKU/package/version and a valid entitlement interval.

An `ENTITLED_PACKAGE_SOURCE` additionally supplies `SAFOR_COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE` binding the entitlement ID, exact package/version and artifact digest through a trusted delivery verifier. A HUMAN may manually load a licensed paid package, but manual loading never bypasses entitlement verification.

Entitlement answers only: **May this exact package/version be used?** It never grants organizational authority, provider permissions, project scope, execution mandate or acceptance authority.

## Validation

```bash
python tools/build_bundle.py --check
python tools/build_domain_framework.py --check
python tools/validate_safor.py
python -m unittest discover -s tests -v
```

The same validation runs in GitHub Actions.

## Product status

SAFOR remains a **Release Candidate**, not General Availability. The Framework/package/licensing boundary and public evaluation reference bridge are machine-tested; the new v0.14 real-Git E2E remains an explicit blocker. Generic chat uploads alone do not execute that bridge. Real commercial package delivery, production entitlement infrastructure, optional stronger host integration and provider/agent end-to-end acceptance remain GA gates.

See [LICENSE-DECISION.md](LICENSE-DECISION.md), [PRODUCT-READINESS.md](PRODUCT-READINESS.md) and [ACCEPTANCE-TESTS.md](ACCEPTANCE-TESTS.md).
