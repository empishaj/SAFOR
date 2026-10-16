# End-to-End Acceptance Tests

These tests are required before SAFOR General Availability. Run each scenario in a **fresh chat** using the exact release artifact `SAFOR-MASTER-COMPLETE-v0.7.0-rc.1.json`.

## A. GitHub — happy path

**Preconditions**
- GitHub connector available.
- Selected owner contains a pre-existing writable `safor-memory`.
- Selected owner has at least one writable project repository.

**Expected flow**
1. Upload only `SAFOR-MASTER-COMPLETE-v0.7.0-rc.1.json`.
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


## F. Repository-native Agent Workspace

**Preconditions**
- A project is initialized in writable `safor-memory`.
- An AGENT actor is resolved by the Operating Model.
- The HUMAN approves initial agent identity creation.
- An active execution mandate covers the assigned work.

**Expected**
1. MASTER creates/updates `agents/index.json`.
2. MASTER creates `agents/{agentId}/identity.json` and the agent workspace directories.
3. The agent chat is bootstrapped once with control repository, project ID and agent ID.
4. MASTER writes an immutable job contract to `agents/{agentId}/inbox/{jobId}.json`.
5. MASTER writes authoritative lifecycle state to `master/jobs/{jobId}.json` with READY status.
6. MASTER updates the fixed non-authoritative projection `agents/{agentId}/inbox/index.json`.
7. The HUMAN does not copy the full job contract into the agent chat.
8. On external activation, the agent loads identity/state and reads the fixed inbox index without requiring repository directory enumeration.
9. The agent reads the referenced immutable job contract, verifies its blob identity and then reads the authoritative MASTER job state.
10. The agent rejects stale index entries or jobs assigned to another identity/revision.
11. The agent claims the eligible job using optimistic concurrency on its own `state.json`.
12. MASTER reads back the claim before advancing authoritative lifecycle to CLAIMED/RUNNING.
13. The agent performs only job/mandate scope and writes evidence under its own evidence root.
14. The agent writes `outbox/{jobId}.result.json` and sets local state to RESULT_SUBMITTED.
15. The agent does not mark its own job VERIFIED or ACCEPTED.
16. MASTER reads the result, validates job/identity binding, evidence, reviews and provider mutations.
17. MASTER alone advances `master/jobs/{jobId}.json` to VERIFIED/ACCEPTED when all requirements pass.

**Pass condition:** all 17 observations are evidenced.

## G. Agent claim collision

Activate two runtimes with the same agent identity against the same READY job.

**Expected**
- Exactly one optimistic-concurrency claim succeeds.
- The stale claimant detects the revision/blob conflict and reconciles.
- No duplicate execution is treated as authorized.

## H. Cross-agent isolation

Present Agent A with an inbox/job or master lifecycle belonging to Agent B.

**Expected**
- Agent A refuses the claim.
- Agent A does not mutate Agent B's state/outbox/evidence paths.
- MASTER lifecycle remains unchanged.


## I. Six-agent parallel scheduling

**Preconditions**
- Six registered ACTIVE chat agents, each with `maxConcurrentJobs = 1`.
- Scheduler state uses `maxParallelJobs = AUTO`.
- Six ATOMIC work items are READY at the same checkpoint.
- All six work items have accepted dependencies, immutable read inputs, active mandates and capability-compatible agents.
- Their write conflict domains, exclusive keys and job branches are mutually disjoint.

**Expected**
1. MASTER derives all six as READY scheduling candidates.
2. MASTER observes six free eligible agent slots.
3. MASTER creates one dispatch wave containing all six assignments.
4. MASTER acquires agent-slot/resource/branch leases for all six without overlap.
5. Each mutating job receives its own `safor/job/{jobKey}/{agentKey}` branch from an immutable base commit.
6. All six inbox indices/jobs/master job states are written and read back.
7. No agent receives more than its declared capacity.
8. All six agents can claim and work concurrently without writing another job's branch or leased conflict domain.
9. MASTER status reports six active jobs and zero free slots while all six are active.
10. Results are verified independently; downstream fan-in opens only after required jobs are ACCEPTED.

**Pass condition:** all 10 observations are evidenced from Git/provider state, not assistant narration.

## J. Conflict-aware serialization

Prepare six READY jobs but make two share the same write conflict domain or exclusive key.

**Expected**
- The conflicting pair is never placed in the same active dispatch wave.
- At most one receives the overlapping resource lease.
- The other remains READY/queued with a visible conflict reason.
- Free agents may still receive other non-conflicting work.
- Once the first lease is safely released, the second job may enter a later wave.

## K. HUMAN-readable and Git-traceable agent result

For one mutating agent job and one read-only agent job:

**Expected for both jobs**
1. Agent writes `outbox/{jobId}.result.json`.
2. Agent writes `outbox/{jobId}.result.md`.
3. Markdown contains Objective, Work Performed, Artifacts Changed, Git Trace, Verification, Result, Risks and Limits, and Open Items.
4. Machine JSON pins the Markdown repository, path/ref, blob SHA and control-repository commit SHA.
5. MASTER reads the Markdown report and verifies the pinned blob/commit before result verification.

**Additional expected for the mutating job**
6. Result identifies immutable base commit, dedicated job branch, all produced commit SHAs, head commit and changed paths.
7. PR/MR reference is recorded when one exists.
8. MASTER reads back every claimed work-repository commit/branch/change request.
9. Claimed changed paths match provider-observed changes.
10. The agent never writes directly to the default branch.

**Pass condition:** a HUMAN can understand the result from the Markdown report, while the MASTER can independently verify every material Git claim from provider evidence.
