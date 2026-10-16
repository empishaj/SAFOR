# End-to-End Acceptance Tests

These tests are required before SAFOR General Availability. Run each scenario in a **fresh chat** using the exact release artifact `SAFOR-MASTER-COMPLETE-v0.10.0-rc.1.json`.

## A. GitHub — happy path

**Preconditions**
- GitHub connector available.
- Selected owner contains a pre-existing writable `safor-memory`.
- Selected owner has at least one writable project repository.

**Expected flow**
1. Upload only `SAFOR-MASTER-COMPLETE-v0.10.0-rc.1.json`.
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


## L. Canonical explicit Agent Job Contract

**Preconditions**
- One ATOMIC work item is READY and covered by an active mandate.
- An ACTIVE persistent agent identity and an explicit role assignment exist.
- All required skill sources, inputs and repository/provider rights can be resolved.

**Expected**
1. MASTER allocates a new UUIDv7 `jobId` and separate HUMAN/Git-safe `jobKey`.
2. Job JSON records packageId, workItemId, packageSequence, planSequence, dispatchSequence, attempt and reworkCycle.
3. Job JSON records `createdAt`, `issuedAt`, MASTER ID/version/run/state revision.
4. Job binds agentId, identityRevision and explicit roleId/role definition.
5. Every mandatory skill includes version, description, execution instructions, use, immutable skillRef and skillBlobSha.
6. Every input is READ_ONLY and pinned to immutable commit identity.
7. Authorization explicitly declares provider bounds and repository read/write/branch/commit/push/change-request/merge/deploy permissions.
8. Workspace binds authoritative work-item resource snapshot, read/write sets, conflict domains, exclusive keys and dedicated Git workspace.
9. Scheduling binds dispatch revision/wave, active resource leases and claim/reconciliation rules.
10. Output contract fixes machine result, HUMAN result, evidence root and audit root before execution.
11. Verification contract explicitly contains acceptance criteria, evidence requirements, review/SoD and MASTER acceptance authority.
12. MASTER generates `inbox/{jobId}.md` containing all fourteen HUMAN-readable contract sections.
13. Job JSON pins the Markdown blob SHA and declares it non-authoritative.
14. MASTER provider-readbacks both JSON and Markdown before setting master job state READY and adding it to inbox/index.
15. Agent rejects any role/identity/skill/mandate/right mismatch before claim.
16. Agent cannot mutate job JSON/Markdown, change role, substitute a mandatory skill, expand scope/rights, delegate or self-accept.
17. Rework creates a new jobId and records supersession lineage; the historical jobId is not reused.

**Pass condition:** all 17 observations are evidenced from repository/provider state and the HUMAN can understand the complete assignment from `job.md` without relying on chat history.


## M. Module-wide Self-Healing

**Preconditions**
- Load the exact v0.9 release bundle.
- Confirm the embedded module set and module recovery profiles are intact.
- Use a disposable project/control environment for mutation tests.

**Expected coverage**
1. The bundle contains exactly one recovery profile for every embedded module key.
2. Every embedded module and integrity-manifest entry references the same profile ID.
3. No recovery profile targets an unknown module.

**Validate-only test**
4. Simulate integrity failure for an immutable control module such as Kernel/Conformance.
5. SAFOR does not rewrite semantics; it reloads/verifies the expected pinned module or STOPs/escalates.

**Verified-restore test**
6. Simulate a pinned Factory/Operating Model/Registry module mismatch.
7. SAFOR restores only the expected version/blob from verified source and revalidates bindings.
8. SAFOR does not alter workflow semantics, decision rights or SoD rules.

**Derived-regeneration test**
9. Remove/corrupt a derived artifact such as agent inbox index or HUMAN job projection while the authoritative source remains intact.
10. SAFOR regenerates only the derived artifact from the authoritative source.
11. Provider readback verifies the regenerated artifact and the authoritative source remains byte-identical.

**External-rebind test**
12. Simulate Provider capability drift or revoked permission.
13. SAFOR refreshes/reobserves actual capabilities and never fabricates/elevates rights.
14. If required rights remain unavailable, work remains blocked or escalates to HUMAN.

**Scheduler/job safety**
15. Simulate stale scheduler READY/capacity view; SAFOR recomputes derived scheduling state.
16. Simulate expired lease with uncertain external effect; SAFOR enters reconciliation before reuse/reassignment.
17. Simulate invalid dispatched job role/skill/authorization; SAFOR does not rewrite job.json and instead blocks/supersedes through governed flow.

**Recovery-control fail-closed**
18. Simulate invalid self-healing or module-recovery control integrity.
19. SAFOR performs no heuristic self-modification and STOPs/escalates.

**Repair evidence**
20. Every repair record contains moduleKey, moduleProfileId, authority type, repairability, pre-state refs, profile decision, selected action and evidence.
21. No repair is marked SUCCEEDED before authoritative readback satisfies the profile success predicate.

**Pass condition:** all 21 observations are evidenced from repository/provider state. No authoritative semantic artifact is silently rewritten and no permission is inferred or elevated.


## N. HUMAN Cognitive Load and Communication

**Preconditions**
- Start a fresh chat with the exact v0.10 release artifact.
- Use a realistic project where Discovery requires genuine HUMAN intent and priorities.
- Retain the interaction transcript plus emitted interaction-menu metadata.

**Expected — initialization and Discovery**
1. Initialization asks one HUMAN decision context at a time.
2. HUMAN-controlled choices such as provider/project location/creation type may create MEDIUM load.
3. Discovery may reach HIGH load because SAFOR asks meaningful questions about goal, users, value, scope, priorities and constraints.
4. Discovery does not expose internal IDs, leases, dispatch waves, READY/CLAIMED states or provider-readback mechanics on the default surface.
5. Every Discovery question carries the legitimate reason `NON_DERIVABLE_HUMAN_INTENT_OR_CONTEXT` or another valid Decision-Gate reason.
6. SAFOR does not ask a Discovery question when the answer is already safely derivable from approved state/evidence.

**Expected — planning transition**
7. Planning presents a summarized interpretation and material tradeoffs before technical detail.
8. The HUMAN approves the plan once for the pinned plan/scope.
9. Re-reading or resuming the unchanged plan does not trigger the same approval again.
10. Deterministic Factory/Operating-Model/Provider binding after creation-type selection does not create a second approval request.
11. Only a materially changed/non-standard/conflicting binding may invoke K10A.

**Expected — execution load reduction**
12. After plan approval and a covering execution mandate, Scheduling and Agent Coordination proceed without HUMAN questions for job IDs, agent selection when deterministic, branches, resource leases, dispatch waves, readbacks, evidence collection or internal state transitions.
13. Scheduling and Agent Coordination report target load `VERY_LOW`; Execution reports `LOW`.
14. An unchanged active execution mandate is reused rather than requested again.
15. An unchanged ACTIVE persistent agent identity is reused without HUMAN reapproval.
16. Routine successful execution uses concise progress/status communication rather than technical confirmations.

**Expected — language and actions**
17. Default SUMMARY communication answers: what happened, what it means for the project, whether HUMAN action is required and what happens next.
18. Internal SAFOR terms and technical IDs are hidden until Details, audit/debug context or a technical decision actually requires them.
19. Primary action labels describe the concrete next domain action when possible; fallback is `Weiter`, never an internal action ID.

**Expected — legitimate temporary re-escalation**
20. Introduce a material scope change, new risk or authority expansion during Execution.
21. SAFOR temporarily raises HUMAN involvement only for that material decision and records the explicit Decision-Gate reason.
22. The turn still contains at most one new decision context.
23. After the decision is resolved, routine HUMAN load returns to the phase default instead of remaining elevated.

**Expected — recovery**
24. A safely repairable internal failure is handled without a HUMAN decision and summarized only when material.
25. A failure that cannot be repaired safely escalates with one clear blocker/decision and no unnecessary recovery internals on SUMMARY.
26. If the HUMAN Decision Gate/Cognitive Load Policy is invalid, SAFOR suppresses nonessential questions and fails closed; it never infers approval.

**Measurement integrity**
27. The optional 0–100 load value is treated only as an internal governance heuristic.
28. SAFOR never presents that number as a validated psychological/scientific cognitive-load measurement.

**Pass condition:** all 28 observations are evidenced. The transcript must show a deliberately higher HUMAN contribution during genuine Discovery and a clear reduction after planning/authorization, with only temporary, reasoned load increases for material decisions.
