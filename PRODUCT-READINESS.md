# SAFOR Product Readiness

Current target: **v0.13.0-rc.7**

Current source baselines: **`v0.13.0/` composable domain-package overlay + `v0.12.0/` Framework/workspace boundary + `v0.11.0/` deterministic control + retained `v0.10.0/` protocol baselines**

## Release-candidate gates

| Gate | State |
|---|---|
| Public single-file Framework distribution | PASS |
| Framework/domain-package separation | PASS by builder/validator |
| Paid Factory/OM content excluded from Framework bundle | PASS |
| Package catalog metadata | PASS |
| WEBSITE FREE_PUBLIC Factory + Operating Model defaults | PASS by unit/validator |
| Website single-file domain Framework | PASS by reproducible builder/CI |
| Domain Framework preselects domain + creation type | PASS by model/unit/validator |
| Website defaults family-aware at 1.1.0 | PASS |
| Package-family compatibility for Premium replacements | PASS by runtime/unit |
| Bidirectional Factory ↔ Operating Model compatibility | PASS by runtime/unit |
| Operating Model required Factory work-item/artifact contract | PASS by unit |
| Cross-domain combinations fail closed | PASS by unit |
| Incompatible replacement preserves existing valid binding | PASS by governance/conformance |
| SaaS public test/evaluation domain Framework | PASS by builder/validator/unit; paid-mode test bytes public |
| Book public test/evaluation domain Framework | PASS by builder/validator/unit; paid-mode test bytes public |
| Public SaaS test access bundle | PASS by validator/unit |
| Public Book test access bundle | PASS by validator/unit |
| Public paid-test bytes remain non-production authorization | PASS by kernel/conformance/validator |
| Production paid catalog still has no public model path | PASS by validator |
| Website Factory scope boundary | PASS by unit/validator |
| Website accessibility/responsive/performance verification | PASS by unit/validator |
| Website public-discoverability check | PASS by unit |
| Website → Software/SaaS escalation boundary | PASS by unit/validator |
| SOFTWARE_SAAS Factory access is paid | PASS by catalog/runtime/validator |
| SOFTWARE_SAAS Operating Model access is paid | PASS by catalog/runtime/validator |
| SOFTWARE_SAAS requires both paid selected packages | PASS by runtime/unit/validator |
| SOFTWARE_SAAS requires two independent entitlements | PASS by unit/policy |
| Legacy public Software/SaaS 1.6 disclosure isolated from commercial source | PASS by catalog/validator |
| Factory independently replaceable from Operating Model | PASS by unit/validator |
| Operating Model independently replaceable from Factory | PASS by unit/validator |
| Mixed FREE_PUBLIC/PAID package pair | PASS by unit |
| Per-selected-package entitlement | PASS by unit/validator |
| External entitlement evidence boundary | PASS by schema/policy |
| Domain-package SHA-256 declared-contract integrity | PASS by unit/validator |
| Framework/Creation-Type package scope | PASS by unit/validator |
| Materialized package selection + compatibility decision | PASS by schema/validator |
| Public immutable-resolution requirement for free packages | PASS by schema/policy |
| Book PAID_ENTITLEMENT_REQUIRED profile | PASS by unit/validator |
| Self-asserted entitlement forbidden | PASS by unit/policy |
| Entitlement ACTIVE/status/time verification | PASS by runtime/unit/validator |
| Entitlement subject binding | PASS by runtime/unit/validator |
| Trusted issuer + entitlement verifier enforcement | PASS by runtime/unit/validator |
| Commercial-basis evidence + SKU binding | PASS by schema/runtime/validator |
| ENTITLED_PACKAGE_SOURCE delivery evidence | PASS by runtime/unit/validator |
| Delivery entitlement/package/version/digest binding | PASS by runtime/unit/validator |
| Trusted delivery verifier + delivery expiry | PASS by runtime/unit/validator |
| Commercial entitlement end-to-end acceptance | OPEN |
| Commercial package delivery/entitlement provider implementation | OPEN |
| Final legal commercial license terms | OPEN |
| HUMAN licensing/product strategy decision | DECIDED |
| HUMAN-owned REMOTE_GIT workspace | PASS by schema/unit |
| Remote separate `safor-memory` strategy | PASS by schema/policy |
| HUMAN-owned LOCAL_GIT workspace | PASS by schema/unit |
| Local MASTER-only `.safor/` control root | PASS by schema/unit |
| LOCAL_GIT end-to-end acceptance | OPEN |
| Canonical SAFOR repository forbidden as project target | PASS by unit/validator |
| Package source forbidden as project target | PASS by unit/validator |
| Software/Website Factory/OM compatibility | PASS by unit/validator |
| Factory-bound Discovery | PASS by schema/conformance |
| Factory-bound Planning | PASS by schema/conformance |
| Factory-bound Evidence | PASS by schema/conformance |
| Deterministic Control Kernel unit/replay suite | PASS |
| Deterministic Acceptance unit/replay suite | PASS |
| Modular bootstrap/package/workspace unit suite | PASS |
| Current unit and regression suite | **PASS in CI; count derived from workflow logs** |
| Module-wide Self-Healing exact coverage | **65/65 PASS** |
| Package/workspace Self-Healing boundary SH-23 | PASS by schema/conformance |
| HUMAN Decision Gate / derive-before-ask | PASS by schema/conformance |
| Terminal HUMAN menu contract | PASS by schema/conformance |
| Platform-owned HUMAN response governor | PASS by policy/reference runtime/unit |
| Domain-module presentation override | FORBIDDEN and regression-tested |
| Framework-detection informational notice budget | PASS by unit/validator |
| Platform response governor host end-to-end acceptance | OPEN |
| HUMAN cognitive-load end-to-end acceptance | OPEN |
| Persistent Agent Workspace | PASS by schema/conformance |
| Canonical explicit Agent Job Contract | PASS by schema/conformance |
| Conflict-aware Multi-Agent Scheduler | PASS by schema/conformance |
| Agent Workspace end-to-end acceptance | OPEN |
| Six-agent parallel scheduling acceptance | OPEN |
| HUMAN-readable + Git-trace result acceptance | OPEN |
| Explicit Job Contract end-to-end acceptance | OPEN |
| Module-wide Self-Healing end-to-end acceptance | OPEN |
| Deterministic Control end-to-end acceptance | OPEN |
| Deterministic Replay acceptance | OPEN |
| Deterministic Acceptance end-to-end acceptance | OPEN |
| GitHub REMOTE_GIT blank-chat acceptance | OPEN |
| GitLab REMOTE_GIT blank-chat acceptance | OPEN |
| Full governance transition migration | OPEN |
| Framework build reproducibility | PASS in CI |
| Machine-readable validation | PASS in CI |

## Maturity meaning

**Release Candidate** means the architecture, composable package/workspace boundaries and machine-level invariants are internally coherent and reproducibly validated. It does not mean the commercial entitlement channel, Local Git host path or all provider/agent scenarios have been empirically proven end to end.

## Commercial boundary

The Framework and Website starter are public/free. Factories and Operating Models are independently licensable packages. Book and future premium packages require verified entitlement.

The licensing **architecture/product decision is complete**. Final legal license language, pricing, billing and entitlement-provider implementation remain separate GA work.

## General Availability definition

GA requires all OPEN gates above to be resolved or explicitly removed from GA scope through a governed HUMAN product decision, with evidence retained at immutable release revisions.
