# SAFOR

**Systemic AI Factory Orchestration Runtime**

SAFOR is a system-oriented orchestration runtime for HUMAN-governed, evidence-backed AI work across interchangeable Factories and Operating Models.

> Current maturity: **v0.13.0-rc.4 — Release Candidate**

## Product paths

| Creation Type | Factory | Operating Model | Access |
|---|---|---|---|
| WEBSITE | `safor.factory.website-delivery@1.0.0` | `safor.om.website-team@1.0.0` | FREE_PUBLIC |
| SOFTWARE_SAAS | `safor.factory.software-delivery` | `safor.om.saas-engineering` | **both paid** |
| BOOK | `safor.factory.book-production` | `safor.om.book-authoring` | **both paid** |

The Website starter is deliberately narrower than the Software/SaaS path. If Website Discovery reveals application logic, service/SaaS lifecycle or broader software operations, SAFOR requires an explicit switch to `SOFTWARE_SAAS`.

## Start here

1. Read [QUICKSTART.md](QUICKSTART.md).
2. Load `SAFOR-FRAMEWORK.json` or the versioned rc.3 artifact into a compatible chat.
3. Choose **Website**, **Software / SaaS** or **Buch**.
4. Website resolves its free Factory/Operating Model defaults from public canonical SAFOR Git.
5. Software/SaaS requires a licensed Software Factory **and** licensed SaaS Engineering Operating Model; each package needs its own verified entitlement.
6. Choose where the HUMAN project lives: **REMOTE_GIT** or **LOCAL_GIT**.

## Repository separation

- **`empishaj/SAFOR`** — public Framework, metadata, schemas, free Website packages and historical baselines. Never the HUMAN project workspace.
- **`{OWNER}/safor-memory`** — HUMAN-controlled remote control workspace for REMOTE_GIT projects.
- **HUMAN project workspace** — the selected remote or local Git repository containing domain work.
- **Commercial package source** — separate entitled/private distribution for current paid Software/SaaS and Book package content.

## Distribution

- `SAFOR-FRAMEWORK-v0.13.0-rc.4.json` — versioned public Framework release candidate.
- `SAFOR-FRAMEWORK.json` — current Framework alias.
- `v0.13.0/ packages/factories/website-delivery/1.0.0/package.json` — free Website Factory.
- `v0.13.0/packages/operating-models/website-team/1.0.0/package.json` — free Website Operating Model.

Software Factory/SaaS OM versions through 1.6.0 remain visible as historical public disclosure. They are not the current protected commercial package channel.

## Validation

```bash
python tools/validate_safor.py
python -m unittest discover -s tests -v
```

The same validation runs in GitHub Actions.

## Product status

SAFOR remains a **Release Candidate**, not General Availability. The Framework/package/licensing boundary is machine-enforced, while real commercial package delivery, entitlement infrastructure and provider/agent end-to-end acceptance remain GA gates.

See [LICENSE-DECISION.md](LICENSE-DECISION.md), [PRODUCT-READINESS.md](PRODUCT-READINESS.md) and [ACCEPTANCE-TESTS.md](ACCEPTANCE-TESTS.md).


## Commercial trust chain

Paid package access in rc.4 is not satisfied by possession of JSON or a purchase receipt alone.

The required chain is:

`commercial basis → ACTIVE entitlement → trusted entitlement verification → protected delivery evidence (for ENTITLED_PACKAGE_SOURCE) → package digest verification → compatibility → immutable binding`

Strict entitlement verification requires an explicit evaluation timestamp, matching HUMAN/organization subject, trusted issuer, trusted entitlement verifier, matching SKU/package/version and valid entitlement interval.

An `ENTITLED_PACKAGE_SOURCE` additionally supplies `SAFOR_COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE` binding the entitlement ID, exact package/version and artifact digest through a trusted delivery verifier. A HUMAN may still manually load a licensed paid package, but manual loading never bypasses entitlement verification.
