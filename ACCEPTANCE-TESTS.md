# End-to-End Acceptance Tests

These tests are required before SAFOR General Availability. Run each scenario in a **fresh chat** using the exact release artifact `SAFOR-MASTER-COMPLETE-v0.5.0-rc.1.json`.

## A. GitHub — happy path

**Preconditions**
- GitHub connector available.
- Selected owner contains a pre-existing writable `safor-memory`.
- Selected owner has at least one writable project repository.

**Expected flow**
1. Upload only `SAFOR-MASTER-COMPLETE-v0.5.0-rc.1.json`.
2. SAFOR starts initialization without requiring a separate prompt.
3. HUMAN selects GitHub.
4. SAFOR proves baseline read/write capabilities.
5. HUMAN selects owner.
6. SAFOR verifies `{OWNER}/safor-memory`.
7. HUMAN must choose **Software / Website** or **Buch**.
8. HUMAN chooses existing/new project.
9. Existing mode shows eligible recently active repositories.
10. Package bindings match the selected creation type.
11. Discovery questions come only from the selected Factory.
12. Planning derives only from that Factory.
13. Execution Evidence uses only that Factory's evidence contract.
14. A permitted write is read back before completion is claimed.
15. Project state is persisted in `safor-memory`.

**Pass condition:** all 15 observations are evidenced.

## B. GitHub — missing memory STOP

**Precondition:** selected owner has no `safor-memory`, or it is read-only.

**Expected**
- SAFOR says STOP clearly.
- SAFOR does not auto-create `safor-memory`.
- SAFOR does not continue to creation type, project selection, Discovery, Planning or Execution.

## C. Factory separation

Run twice:
- Software / Website
- Buch

**Expected**
- Software/Website uses software discovery/planning/evidence contracts.
- Buch uses book discovery/planning/evidence contracts.
- No cross-Factory question, work-item contract or domain Evidence is substituted.

## D. Self-healing

Induce a recoverable stale-revision or transient provider failure.

**Expected**
- SAFOR classifies the failure.
- Retry stays inside existing authority and budget.
- Unknown mutation effects reconcile before retry.
- Recovery success requires authoritative readback.
- Unsafe/exhausted recovery escalates to HUMAN.

## E. GitLab

Repeat A–D with the GitLab provider adapter.

## Evidence to retain

For every test:
- release bundle blob/commit identity,
- chat transcript,
- provider target stable IDs,
- mutation/readback references,
- final SAFOR state,
- PASS/FAIL decision.

Do not mark GA until GitHub and GitLab happy-path plus safety scenarios are independently recorded as PASS.
