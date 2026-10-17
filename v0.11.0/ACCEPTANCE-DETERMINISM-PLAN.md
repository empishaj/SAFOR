# SAFOR 0.11.0-rc.2 — Deterministic Acceptance / Evidence Plan

## Objective

Extend the 0.11 deterministic control kernel so that a Work Item may enter ACCEPTED only from a pinned, approved Acceptance Contract whose typed requirements are satisfied by replayable Evidence, Review and Authority-Decision records.

The kernel does not decide qualitative truth. Qualitative criteria are converted during approved planning into explicit independent-review or authority-decision requirements.

## Core rule

> Probabilistic actors may produce evidence, reviews and decisions. The deterministic control kernel alone evaluates whether the approved acceptance contract is satisfied and may materialize WORK_ITEM -> ACCEPTED.

## Acceptance Contract

Each approved Work Item receives an immutable Acceptance Contract containing:
- original acceptance criteria;
- typed requirement references;
- Factory/evidence-contract provenance;
- plan/work-item provenance;
- approval decision provenance;
- deterministic contract hash.

Requirement types:
1. EVIDENCE — requires an authoritative evidence record of a declared evidenceType.
2. REVIEW — requires a review decision from the declared capability and independence policy.
3. AUTHORITY — requires an explicit approved authority decision.

Every criterion uses ALL semantics in rc.2. Every criterion must reference at least one typed requirement.

## No semantic shortcut

Free-text or qualitative acceptance criteria MUST NOT be directly interpreted as PASS by the deterministic kernel. If no machine-verifiable evidence requirement captures the criterion, planning must bind it to REVIEW or AUTHORITY.

Agent self-checks are advisory and cannot satisfy independent review or authority requirements.

## Replay ledger

The deterministic projection set gains an `acceptance` ledger containing replayable pinned copies of:
- contracts;
- evidenceRecords;
- reviewDecisions;
- authorityDecisions.

This ledger is a deterministic projection cache, not a replacement for repository-authoritative source artifacts. Each record must carry a stable provider/source revision reference where applicable.

## Event slice

rc.2 adds:
- ACCEPTANCE_CONTRACT_REGISTERED
- EVIDENCE_RECORDED
- REVIEW_APPROVED_RECORDED
- REVIEW_CHANGES_REQUIRED_RECORDED
- AUTHORITY_APPROVED_RECORDED
- AUTHORITY_REJECTED_RECORDED
- ACCEPTANCE_REEVALUATION_REQUESTED

## Transition slice

1. Register one active acceptance contract for a work item.
2. Record authoritative evidence.
3. Record independent review approval or changes required.
4. Record authority approval or rejection.
5. HANDOFF_READY/IN_REVIEW -> ACCEPTED only when the active contract is valid and all typed requirements are satisfied.
6. Review changes required -> CHANGES_REQUIRED.
7. Authority rejection does not permit ACCEPTED and remains explicit evidence for replan/escalation.

## Deterministic acceptance predicate

ACCEPTED iff:

`ACTIVE_CONTRACT_VALID
&& ALL_CRITERIA_HAVE_REQUIREMENTS
&& ALL_REQUIRED_EVIDENCE_SATISFIED
&& ALL_REQUIRED_REVIEWS_SATISFIED
&& REVIEW_INDEPENDENCE_SATISFIED
&& ALL_REQUIRED_AUTHORITIES_SATISFIED
&& NO_REJECTING_ACTIVE_DECISION`

## Integrity rules

- contractHash is canonical SHA-256 excluding contractHash itself;
- one ACTIVE contract per Work Item in rc.2;
- contract mutation after approval is forbidden; revision requires a new contract/event;
- evidence type and subject must match requirement;
- PINNED evidence requires non-null revisionRef;
- review PASS cannot satisfy independence when reviewer == performer under PERFORMER_MUST_DIFFER_FROM_APPROVING_REVIEWER;
- authority approval must match the exact authorityId and Work Item;
- agent acceptanceSelfCheck never satisfies REVIEW or AUTHORITY.

## Deferred

- conditional Factory evidence-rule compiler;
- threshold/quantitative predicates;
- outcome acceptance beyond Work Item acceptance;
- automatic supersession/revision workflow for Acceptance Contracts;
- full Agent Job lifecycle reducer;
- full Scheduler reducer.

## Acceptance tests

rc.2 passes only when:
- full evidence+review+authority path produces ACCEPTED;
- missing evidence blocks acceptance;
- self-review blocks independent-review satisfaction;
- CHANGES_REQUIRED moves the Work Item back to CHANGES_REQUIRED;
- missing authority blocks acceptance;
- rejected authority blocks acceptance;
- duplicate records are idempotent via event identity;
- replay reproduces the accepted-state hash;
- contract hash tampering fails closed;
- no qualitative criterion is accepted without a typed requirement.
