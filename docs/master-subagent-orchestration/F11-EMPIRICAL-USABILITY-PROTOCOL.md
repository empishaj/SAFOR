# SAFOR F-11 Empirical Usability & Cognitive-Load RC Pilot

## Status

**Protocol ready. Empirical acceptance remains OPEN until real HUMAN runs satisfy this protocol.**

This protocol closes the methodological gap behind audit finding F-11. It does **not** claim that SAFOR's internal 0–100 load heuristic is a validated psychometric measure, and it does not establish population-level scientific usability.

## Purpose

F-11 requires empirical evidence that SAFOR's HUMAN interaction model behaves as designed:

- genuine Discovery may demand substantial HUMAN contribution;
- repeated or safely derivable questions are suppressed;
- after Planning and authorization, orchestration complexity is absorbed by SAFOR;
- Scheduling and Agent Coordination require almost no routine HUMAN workflow operation;
- Execution remains low-friction;
- material scope/risk/authority changes may temporarily increase HUMAN involvement;
- after the material decision, routine load returns to the phase target;
- technical identifiers and internal workflow mechanics stay off the default SUMMARY surface;
- unsafe recovery escalates clearly rather than inferring approval.

The normative basis is:
- `HUMAN-COGNITIVE-LOAD.md`;
- `v0.14.0/interaction-model.json`;
- `v0.14.0/human-decision-gate-model.json`;
- `v0.14.0/schemas/human-cognitive-load-policy.schema.json`;
- Scenario N in `ACCEPTANCE-TESTS.md`.

## Evidence boundary

The pilot evaluates observable product behavior and subjective HUMAN experience in controlled fresh-chat runs.

It must never claim:
- that SAFOR's internal 0–100 heuristic measures psychological cognitive load;
- clinical, neurological or psychometric validity;
- statistical generalization to all users;
- cross-host acceptance unless the cross-host gate is separately satisfied.

Subjective 1–7 ratings in this protocol are simple product-feedback ratings, not validated psychometric instruments.

## Minimum pilot design

F-11 may move from OPEN to RC-PILOT-PASS only when all of the following exist:

1. At least **6 eligible fresh-chat runs**.
2. At least **3 pseudonymous HUMAN participants**.
3. At least **1 participant not involved in SAFOR design/implementation**.
4. At least **2 experience profiles** represented: `TECHNICAL`, `NONTECHNICAL`, or `MIXED`.
5. The run set covers all three scenario classes:
   - `DISCOVERY_HEAVY`;
   - `POST_PLAN_EXECUTION`;
   - `RECOVERY_ESCALATION`.
6. Every run uses an exact immutable SAFOR Framework artifact reference.
7. Every run retains a transcript/evidence reference and evaluator decision.
8. No participant name, email address, account identifier or other unnecessary personal data is stored in the evidence record.

A single run may cover more than one scenario class, but the aggregate evidence set must contain at least two observations of each class.

## Required behavioral observations

Every eligible run records the following hard behavioral metrics.

### Decision discipline

- `maxNewDecisionContextsPerTurn <= 1`.
- `repeatedUnchangedApprovalCount == 0`.
- `safelyDerivableQuestionViolationCount == 0`.
- `internalOrchestrationQuestionCountAfterPlan == 0`.

Questions about job IDs, agent selection when deterministic, branches, leases, dispatch waves, provider readbacks, evidence collection or internal state transitions count as internal orchestration questions.

### Default-surface abstraction

- `rawInternalIdentifierExposureViolationCount == 0`.
- `technicalMechanicsExposureViolationCount == 0`.
- Every routine SUMMARY tells the HUMAN what happened, what it means, whether action is required and what happens next.

Technical identifiers are allowed when the HUMAN explicitly requests Details/Evidence or when a material technical decision actually requires them; those cases are not violations.

### Phase-load behavior

For a Discovery-heavy run:
- at least one question must concern genuinely non-derivable HUMAN intent/context;
- Discovery must not be artificially suppressed merely to lower question count.

For post-plan execution:
- `executionUnnecessaryHumanQuestionCount == 0`;
- unchanged active decisions/mandates are reused;
- routine Scheduling/Agent Coordination proceeds without HUMAN workflow operation.

For temporary material escalation:
- the escalation reason must be one of the declared Decision-Gate reasons;
- at most one new decision context is introduced;
- `returnedToPhaseTargetAfterEscalation == true`.

### Recovery behavior

For a safely repairable failure:
- no HUMAN decision is requested merely to operate the recovery mechanism.

For a non-repairable/unsafe failure:
- exactly one clear blocker/decision context is presented;
- no approval is inferred;
- recovery internals remain behind Details unless materially necessary.

### Measurement integrity

- `internalHeuristicPresentedAsScientificMeasure == false`.
- Any 0–100 internal heuristic value remains governance metadata and is not shown as validated HUMAN cognitive-load measurement.

## Subjective pilot feedback

At the end of an eligible run, the participant may provide simple 1–7 product ratings:

- `clarityRating`: how clear was the interaction?
- `controlRating`: how clear was when HUMAN action was actually required?
- `discoveryEffortRating`: perceived effort during genuine Discovery.
- `executionEffortRating`: perceived effort after Planning/authorization.

These ratings are product feedback only.

## Aggregate RC pilot acceptance

F-11 may be marked `RC_PILOT_PASS` only when:

1. All hard behavioral observations pass in every eligible run.
2. Median `clarityRating >= 5` across runs with subjective feedback.
3. Median `controlRating >= 5`.
4. In at least 80% of paired Discovery→Execution observations, `executionEffortRating <= discoveryEffortRating - 1`.
5. No run records a safety-critical approval inference, scope expansion, hidden authority expansion or required-human-decision suppression.
6. All FAIL runs are retained; no failed run may be deleted from the evidence set.
7. The aggregate report explicitly states the sample size, participant count, host(s), scenario coverage and limitations.

If any hard gate fails, F-11 remains OPEN regardless of subjective ratings.

## Run procedure

1. Start a fresh compatible chat.
2. Load the exact immutable Framework artifact used by the run.
3. Record `runId`, pseudonymous `participantId`, host, framework commit/blob and scenario class.
4. Execute the assigned realistic scenario without coaching the participant on expected SAFOR wording.
5. Retain the transcript reference and emitted SAFOR evidence references.
6. An evaluator records behavioral metrics from observable interaction evidence.
7. Collect optional 1–7 product ratings.
8. Persist one immutable run record using `F11-EMPIRICAL-RUN.template.json`.
9. Do not alter a run record after evaluation. Corrections create a superseding record with lineage.
10. Aggregate only immutable eligible runs.

## Current disposition

Until qualifying HUMAN runs exist:

- Audit finding F-11 = **OPEN_EMPIRICAL_USABILITY_EVIDENCE**.
- `V014_COGNITIVE_LOAD_EMPIRICAL_ACCEPTANCE` remains a GA blocker.
- Automated tests may verify the protocol and interaction contracts, but may not substitute for HUMAN empirical evidence.
