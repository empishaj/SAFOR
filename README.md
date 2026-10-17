# SAFOR

**Systemic AI Factory Orchestration Runtime**

SAFOR is a system-oriented, JSON-based orchestration framework for HUMAN-governed, evidence-backed AI work across interchangeable Factories and Operating Models.

> Current maturity: **Release Candidate** — exact version in [`VERSION`](VERSION)

## Start here

- German end-user guide: [START-HIER.md](START-HIER.md)
- Technical quickstart: [QUICKSTART.md](QUICKSTART.md)
- Master–Subagent contract: [MASTER-SUBAGENT-ORCHESTRATION.md](MASTER-SUBAGENT-ORCHESTRATION.md)

Use the domain-specific entrypoint:

| Creation Type | Files loaded by the user | Factory | Operating Model | Access |
|---|---|---|---|---|
| WEBSITE | `SAFOR-FRAMEWORK-WEBSITE.json` | `safor.factory.website-delivery@1.1.0` | `safor.om.website-team@1.1.0` | FREE_PUBLIC |
| SOFTWARE_SAAS evaluation | `SAFOR-FRAMEWORK-SAAS.json` + `SAFOR-TEST-ACCESS-SAAS.json` | public prerelease test Factory | public prerelease test Operating Model | non-production test only |
| BOOK evaluation | `SAFOR-FRAMEWORK-BOOK-CREATION.json` + `SAFOR-TEST-ACCESS-BOOK-CREATION.json` | public prerelease test Factory | public prerelease test Operating Model | non-production test only |

A Domain Framework already fixes Website, SaaS or Book and embeds the matching default Factory and Operating Model. SAFOR must not ask the HUMAN to choose that domain again. The SaaS/Book access file is entitlement evidence for exact public test versions; it is not a domain module and never grants production authorization.

## Direct chat product boundary

The end-user product is the loaded JSON contract in a compatible ordinary LLM chat. The model interprets the embedded rules and uses only provider/file tools actually exposed by the chat host.

**Normal SAFOR use does not require the HUMAN to install a separate runtime, daemon, service or custom UI.**

The modules under `runtime/` are deterministic reference implementations used by CI and optionally by hosts/adapters that want stronger machine enforcement. A generic chat does not automatically execute Python when JSON is uploaded. Therefore:

- model-level contract following and machine-enforced controls are reported separately;
- JSON never proves credentials, provider rights or external effects;
- branch protection, CI, reviews and host adapters may strengthen enforcement without changing the chat-first product model.

## Platform-owned HUMAN communication

The SAFOR platform—not a Factory or Operating Model—owns every HUMAN-visible response. Domain modules supply facts, risks, evidence and genuine decision requirements. The platform controls interaction, disclosure and response budgets.

The **MASTER** is the only fachliche and organizational HUMAN interface. The HUMAN discusses goals, planning, roadmap, status, risks, approvals and conflict decisions with MASTER.

## Persistent Subagents and HUMAN `GO`

A normal `CHAT_AGENT` is initialized once with a MASTER-generated prompt that binds:

- technical `agentId`;
- separate `displayName`;
- project and MASTER identity;
- control repository and personal workspace;
- identity, state and inbox-index pointers;
- communication boundary.

After that one-time initialization, every future job starts only when the HUMAN types exactly:

```text
GO
```

Git pushes, polling, scheduler decisions, automation and host events do not activate a normal chat agent. The scheduler prepares a safe job and leaves it in `WAITING_HUMAN_GO`.

After `GO`, the agent reads only its identity, state, personal index, selected immutable job, MASTER job state and explicitly pinned inputs. It does not scan the entire project or other agents' inboxes.

## Explicit job and response contracts

Every v0.14 job binds:

- package/work-item lineage and UUIDv7 job identity;
- target agent and identity revision;
- Factory/Operating-Model/domain context;
- role and immutable versioned skills;
- task scope, exclusions, assumptions and acceptance criteria;
- pinned input revisions;
- dedicated product branch and allowed paths for mutating work;
- separate product and control-repository permissions;
- all required review and evidence gates;
- five typed response templates and their exact Git targets;
- minimal chat-output rules.

Typed responses are:

- `JOB_RESULT`
- `JOB_ERROR`
- `CLARIFICATION_REQUEST`
- `CAPABILITY_MISMATCH`
- `IMPROVEMENT_PROPOSAL`

Responses are immutable. MASTER resolutions are separate records. `RESPONSE_SUBMITTED`, `VERIFIED`, `ACCEPTED` and `INTEGRATED` are distinct lifecycle states.

## Minimal agent chat

Detailed work, tests, errors, decisions and evidence are persisted in Git. The agent chat emits only a one-line status such as:

```text
GO bestätigt | Agent: Nova Dev (agent-dev-003) | Job: WP-014-IMPL | Status: RUNNING | Zielbranch: safor/job/wp-014/agent-dev-003
```

The agent does not conduct domain discussion with the HUMAN. Clarification and mismatch responses go to MASTER.

## Public paid-domain evaluation

The SaaS and Book distributions in the public repository are test/evaluation artifacts. Their access bundles set:

```text
productionAuthorization = false
```

`runtime/public_evaluation_access.py` is the optional deterministic reference implementation for CI or compatible hosts. It rejects wrong filenames, cross-domain bundles, changed contracts, imprecise grants and production-authorization escalation.

A chat-only evaluation verifies how the model follows the declared contract; it does not prove technical entitlement enforcement unless the host/provider path supplies corresponding evidence. This distinction does not make a separate runtime an end-user installation prerequisite.

## Repository separation

- **`empishaj/SAFOR`** — public Framework source, schemas, free Website packages and public evaluation artifacts; never the HUMAN project workspace.
- **`{OWNER}/safor-memory`** — HUMAN-controlled control workspace for REMOTE_GIT projects.
- **HUMAN project workspace** — remote or local Git repository containing domain work.
- **Commercial package source** — protected delivery channel for production-paid packages.

Product artifacts and control/response artifacts have separate write targets. A permission for one never grants the other.

## Product paths and package compatibility

The Website starter is deliberately narrower than the Software/SaaS lifecycle. If Website Discovery finds application logic or SaaS operations, SAFOR requires an explicit governed profile switch.

All Domain Frameworks share the SAFOR kernel. Embedded Factory and Operating Model are replaceable defaults. A replacement is adopted only when access, integrity, active domain, package-family and bidirectional Factory ↔ Operating-Model compatibility pass.

## Commercial trust chain

Production paid-package use requires:

```text
commercial basis
→ ACTIVE entitlement
→ trusted entitlement verification
→ protected package delivery evidence
→ package digest verification
→ Factory/Operating-Model compatibility
→ immutable project binding
```

Entitlement answers only whether an exact package version may be used. It does not grant provider permissions, organizational authority, project scope, execution mandate or acceptance authority.

## Validation

```bash
python tools/build_bundle.py --check
python tools/build_domain_framework.py --check
python tools/validate_safor.py
python -m unittest discover -s tests -v
```

The same validation runs in GitHub Actions.

## Maturity and evidence limits

SAFOR remains a Release Candidate. Normative contracts and the GitHub reference path can be machine-tested. Claims about a specific external LLM host, GitLab deployment, local filesystem environment or commercial provider require separate empirical evidence on that path.

See [SUPPORT.md](SUPPORT.md), [PRODUCT-READINESS.md](PRODUCT-READINESS.md), [LICENSE-DECISION.md](LICENSE-DECISION.md) and [ACCEPTANCE-TESTS.md](ACCEPTANCE-TESTS.md).
