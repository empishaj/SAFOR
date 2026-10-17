# SAFOR 0.12.0-rc.2 — Agent Runtime Modes and HUMAN Activation Governance

## Objective

Close the governance gap exposed by the free-Website E2E exercise:

- SAFOR must distinguish schema/product design, validation/test execution and real project execution.
- Agent execution must be abstracted behind an Agent Runtime Adapter rather than implicitly delegated to the HUMAN.
- Manual HUMAN chat activation may exist only as an explicit validation harness, never as normal production orchestration.
- Job prompts remain repository-native; runtime activation must never reintroduce copied job contracts as authority.

## New architecture

### Operation modes

- DESIGN — SAFOR Framework / schema / package architecture work.
- VALIDATION — isolated machine/E2E/test-harness validation with no production project authority.
- EXECUTION — real HUMAN project Value Creation Stream execution.

Mode is governance state, not presentation style.

### Agent Runtime Adapter

Separates agent activation/execution from repository Provider Adapters.

Provider Adapter answers how SAFOR reads/writes repositories, branches, PRs/MRs, checks and evidence.
Agent Runtime Adapter answers how an AGENT runtime is activated; whether continuation/wakeup can happen automatically; how the runtime observes job availability; whether a one-time identity bootstrap is needed; and how results become observable.

## Activation capabilities

- HOST_NATIVE_AUTOMATIC
- EXTERNAL_AUTOMATION
- HUMAN_MANUAL_TEST_ONLY
- UNAVAILABLE

HUMAN_MANUAL_TEST_ONLY is permitted only in VALIDATION with an isolated test harness. It is incompatible with EXECUTION.

## HUMAN governance

The HUMAN is never asked to:
- open/wake routine agent chats for production execution;
- copy a job prompt or job contract;
- poll an agent inbox;
- transport agent results;
- keep dispatch sequencing alive manually.

If EXECUTION requires AGENT work and no runtime with automatic or external-automation activation is bound, SAFOR returns AGENT_RUNTIME_AUTOMATION_UNAVAILABLE.

The only legitimate HUMAN escalation is a material choice such as selecting/configuring a different runtime adapter when no safe deterministic alternative exists.

## Mode semantics

### DESIGN
- May mutate SAFOR Framework/schema/package development targets under normal Git governance.
- Must not mutate a HUMAN project Value Creation Stream as if work were being executed.
- E2E evidence produced in DESIGN does not count as production execution evidence.
- If agents are used, their runtime activation still follows the bound Agent Runtime Adapter.

### VALIDATION
- Requires an explicit isolated test target/harness.
- May use HUMAN_MANUAL_TEST_ONLY when the test itself is specifically validating manual-host behavior.
- Validation jobs/evidence are marked non-production.
- Validation evidence cannot silently satisfy production mandates, acceptance or business outcome authority.

### EXECUTION
- Targets a HUMAN-controlled project workspace.
- AGENT dispatch requires HOST_NATIVE_AUTOMATIC or EXTERNAL_AUTOMATION.
- HUMAN_MANUAL_TEST_ONLY and UNAVAILABLE block automatic agent execution.
- SAFOR must not convert this capability gap into manual HUMAN workflow operation.

## Hard invariants

1. Operation mode is resolved before any mutating effect.
2. Mode cannot silently downgrade from EXECUTION to VALIDATION to bypass runtime limitations.
3. Manual test harness activation cannot satisfy production execution.
4. Agent runtime capability is observed/evidenced; never inferred from a prompt.
5. Background wakeup is false unless actual host/runtime evidence proves support.
6. Agent Runtime Adapter grants no repository rights, role authority, mandate, package entitlement or acceptance authority.
7. Provider Adapter and Agent Runtime Adapter remain separate bindings.
8. Repository-native Job Contract remains authoritative regardless of runtime adapter.
9. Identity bootstrap may never carry the full job contract as authority.
10. Missing automation in EXECUTION produces a capability gap, not a HUMAN copy/paste instruction.

## rc.2 acceptance criteria

- Operation Mode model and binding schema validate.
- Agent Runtime model and binding schema validate.
- EXECUTION rejects HUMAN_MANUAL_TEST_ONLY.
- VALIDATION permits manual test harness only on isolated test targets.
- DESIGN is explicitly distinct from project Value Creation execution.
- HUMAN Decision Gate forbids routine agent activation/wakeup/job transport requests.
- Agent Workspace activation contract binds to Agent Runtime Adapter.
- Self-Healing cannot fabricate runtime capability or switch mode to bypass missing automation.
- Machine policy tests cover mode/runtime combinations.
- Existing deterministic-control, acceptance, package and workspace tests remain green.
