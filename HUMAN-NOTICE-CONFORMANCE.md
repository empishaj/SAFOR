# HUMAN Notice Conformance – SAFOR 0.14.0-rc.2

## Scope

This matrix maps the binding HUMAN requirements to canonical product sources and executable validation. It distinguishes declarative product guarantees from external host/provider capabilities.

| Requirement | Product source | Executable evidence | rc.8 state |
|---|---|---|---|
| JSON in ordinary compatible LLM chat | `v0.13.0/chat-execution-model.json` | `test_ordinary_chat_is_primary_and_runtime_install_is_not_required` | Implemented |
| No customer-installed runtime | Kernel `executionEnvironmentContract`; `START-HIER.md` | Validator + same test | Implemented |
| MASTER only fachliche HUMAN interface | Kernel invariants 218–219; agent chat model | `test_platform_not_factory_or_operating_model_owns_chat` | Implemented |
| HUMAN `GO` is exclusive subagent trigger | `agent-bootstrap-model.json`; Agent Workspace/Scheduler | `test_human_go_is_the_only_agent_activation` | Implemented |
| Git/automation never wakes agent | same | positive/negative activation assertions | Implemented |
| One-time identity bootstrap and fail-closed rebind | Bootstrap model, identity schema and template | identity schema test | Implemented |
| Stable ID plus memorable display name | identity/registry schemas | identity schema and migration checks | Implemented |
| Identity → personal index → job → pinned inputs | Agent Workspace + Job Contract | existing workspace/job suites plus rc.8 tests | Implemented |
| Complete explicit Job Contract | `v0.13.0/schemas/agent-job.schema.json` | `test_job_requires_domain_response_and_chat_contracts` | Implemented |
| Role/skill/domain/right validation | Agent Workspace/Job/Scheduler | validator, existing agent tests and skill-mismatch negative path | Implemented |
| Product and control writes separately authorized | Job schema and response contract | validator and conformance assertion | Implemented |
| Exact Response Template per job | Job schema, template catalog | template catalog test | Implemented |
| Result/Error/Clarification/Mismatch/Improvement types | response schema/model/templates | `test_all_five_response_types_validate` | Implemented |
| Invalid response fails closed | response validator | `test_invalid_response_fails_closed` | Implemented |
| Subagent chat is minimal status only | agent chat model/schema/governor | chat governor negative test | Implemented |
| Subagent does not discuss domain work with HUMAN | kernel/agent chat routing | schema/governor/conformance checks | Implemented |
| MASTER status from compact indexes | master status index model/schema/runtime | `test_master_status_index_is_compact_and_start_aware` | Implemented |
| History preserved on conflict/rework | Job Contract and kernel invariant 223 | conformance/legacy policy | Implemented |
| Factory/OM cannot control communication | platform governor + kernel invariant 224 | cross-domain tests | Implemented |
| All domain distributions contain the contracts | reproducible builders | `test_all_domain_distributions_embed_rc8_contracts` | Implemented |

## External truth boundary

SAFOR's JSON contracts are normative product behavior. They do not create connector permissions or force a nonconforming LLM host. Actual Git/provider rights, readback, CI, reviews and branch governance remain external evidence. This boundary does not introduce a customer-runtime installation requirement.

## Reference-project migration

The non-destructive `safomwebsite` migration is complete in `empishaj/safor-memory` at merge commit `85e08eab15b18a86868090d7b18573b9e2484aea` (PR #4). The authoritative projection is `projects/safomwebsite/state/current.json`; the complete nine-agent registry, HUMAN-GO identity overlays, response-template binding and compact MASTER status index are present. Historical jobs, AWC objects, legacy identities and evidence remain read-only history.

This closes the reference-project migration acceptance item for rc.9. It does not close cross-host, provider, commercial-delivery or General Availability acceptance items.
