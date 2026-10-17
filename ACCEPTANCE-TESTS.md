# End-to-End Acceptance Tests

These tests are required before SAFOR General Availability. Run each scenario in a **fresh chat** using the exact Framework artifact `SAFOR-FRAMEWORK-v0.13.0-rc.7.json`.

## A. GitHub REMOTE_GIT — free Website happy path

**Preconditions**
- GitHub connector available.
- HUMAN controls a writable project repository.
- The selected owner contains a pre-existing writable `safor-memory`.

**Expected flow**
1. Upload only `SAFOR-FRAMEWORK-v0.13.0-rc.7.json`.
2. SAFOR verifies Framework/recovery/deterministic-control integrity.
3. HUMAN selects **Website**.
4. SAFOR resolves `safor.factory.website-delivery@1.1.0` and `safor.om.website-team@1.1.0` from public SAFOR Git at immutable revision/blob without asking for a paid entitlement.
5. SAFOR verifies Factory/Operating Model compatibility.
6. HUMAN selects **In meinem Git-Repository**.
7. HUMAN selects GitHub and the HUMAN-controlled owner/project repository.
8. SAFOR proves actual project read/write and Git capabilities.
9. SAFOR verifies separate HUMAN-controlled `{OWNER}/safor-memory`.
10. SAFOR persists immutable package pins/access metadata in project control.
11. Discovery questions come only from the resolved Factory.
12. Planning derives only from that Factory and approved Operating Model.
13. Execution Evidence uses only that Factory's evidence contract.
14. Domain project writes occur only in the HUMAN project repository and are read back before completion claims.
15. SAFOR control state persists in `safor-memory`; domain work artifacts do not.

**Pass condition:** all 15 observations are evidenced.

## B. REMOTE_GIT — missing/read-only control workspace

**Precondition:** package resolution has succeeded, but the selected remote owner has no usable `safor-memory` or it is read-only.

**Expected**
- SAFOR enters `WAITING_HUMAN_CONTROL_WORKSPACE`.
- SAFOR does not auto-create remote `safor-memory`.
- SAFOR does not materialize project execution/control or begin Discovery until a valid HUMAN-controlled control workspace exists.
- Package entitlement/access state is not changed or invented as a recovery shortcut.

## C. Free/Paid package separation

Run two package-resolution paths.

### C1 — Website
- Access mode is `FREE_PUBLIC`.
- The default Factory/OM may resolve from the public canonical SAFOR repository.
- Exact provider revision/blob is pinned before use.

### C2 — Buch
- Access mode is `PAID_ENTITLEMENT_REQUIRED`.
- No Book model content is read from the public canonical package source.
- Without paid package artifacts + independently verified entitlement, SAFOR returns `PACKAGE_ACCESS_REQUIRED` or `PACKAGE_ENTITLEMENT_UNVERIFIED`.
- With HUMAN-loaded/entitled packages and valid entitlement evidence, SAFOR continues to technical integrity/compatibility checks.
- Entitlement does not grant any Operating Model authority.

**Pass condition:** public/free and commercial paths remain strictly separated.

## D. Self-healing

Induce a recoverable stale-revision/provider/package-observation failure.

**Expected**
- SAFOR classifies the failure.
- Retry stays inside existing authority and budget.
- Unknown mutation effects reconcile before retry.
- Recovery success requires authoritative readback.
- SAFOR never invents entitlement, reads paid content from the public package source, changes HUMAN project location, bypasses Local Git, or grants workers access to `.safor/`.
- Unsafe/exhausted recovery escalates to HUMAN.

## E. GitLab REMOTE_GIT

Repeat Scenario A with GitLab as the HUMAN project provider. Free Website packages still resolve from the public SAFOR package source independently of the project provider.

## Evidence to retain

For every test:
- Framework blob/commit identity,
- resolved package IDs/versions/source revisions/blob identities,
- entitlement verification evidence when applicable,
- HUMAN workspace binding,
- chat transcript,
- project/control target stable IDs or local Git identity,
- mutation/readback references,
- final SAFOR state,
- PASS/FAIL decision.

Do not mark GA until remote-provider, Local Git and commercial entitlement scenarios are independently recorded as PASS.


## F. Repository-native Agent Workspace

**Preconditions**
- A project is initialized with a verified control workspace: remote `safor-memory` or local MASTER-only `.safor/`.
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
- Load the exact v0.13.0-rc.2 Framework bundle.
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
6. Simulate a pinned external Factory/Operating Model package mismatch while preserving the approved package identity/access evidence.
7. SAFOR restores/re-resolves only the expected version/blob from an allowed source, revalidates entitlement when required, and revalidates bindings.
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
- Start a fresh chat with the exact v0.13.0-rc.2 Framework artifact.
- Use a realistic project where Discovery requires genuine HUMAN intent and priorities.
- Retain the interaction transcript plus emitted interaction-menu metadata.

**Expected — initialization and Discovery**
1. Initialization asks one HUMAN decision context at a time.
2. HUMAN-controlled choices such as creation type and remote/local project location may create MEDIUM load; package access is derived when possible.
3. Discovery may reach HIGH load because SAFOR asks meaningful questions about goal, users, value, scope, priorities and constraints.
4. Discovery does not expose internal IDs, leases, dispatch waves, READY/CLAIMED states or provider-readback mechanics on the default surface.
5. Every Discovery question carries the legitimate reason `NON_DERIVABLE_HUMAN_INTENT_OR_CONTEXT` or another valid Decision-Gate reason.
6. SAFOR does not ask a Discovery question when the answer is already safely derivable from approved state/evidence.

**Expected — planning transition**
7. Planning presents a summarized interpretation and material tradeoffs before technical detail.
8. The HUMAN approves the plan once for the pinned plan/scope.
9. Re-reading or resuming the unchanged plan does not trigger the same approval again.
10. FREE_PUBLIC package resolution and deterministic compatible package binding after creation-type selection do not create redundant approval requests.
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

## Scenario O — Deterministic Control Kernel

Goal: demonstrate that the executable rc.1 transition slice behaves reproducibly and fails closed around integrity/authority boundaries.

1. Load the exact `SAFOR-FRAMEWORK-v0.13.0-rc.7.json` artifact and verify K00 then K00A complete before provider/project work.
2. Create or load a project with a PLANNED work item whose dependency is ACCEPTED, required input object is resolvable, resource declaration is complete and an active execution mandate covers the work item/capability.
3. Submit a typed `WORK_ITEM_READINESS_REEVALUATION_REQUESTED` event with the next contiguous sequence.
4. Verify the deterministic transition is `WORK_ITEM_BECOMES_READY`, the work item becomes READY, `execution.readySince` comes from the event timestamp and the resulting canonical state hash is recorded.
5. Replay the same genesis projection set and ordered events; the replayed state hash must equal the stored state hash.
6. Re-submit the identical eventId/canonical event; verify `IDEMPOTENT_NO_OP` and unchanged state hash.
7. Re-submit the same eventId with different payload; verify `INTEGRITY_FAILURE` and no state change.
8. Remove or revoke the covering mandate and retry readiness from a valid genesis/next event sequence; verify no READY transition occurs.
9. Submit `PAUSE_PROJECT_REQUESTED`; verify Control mode becomes PAUSED, status WAITING_HUMAN and prior mode is retained in resumeMode.
10. Submit `RESUME_PROJECT_REQUESTED`; verify the prior nonterminal mode is restored and guards are re-evaluated before further execution.
11. Submit `STOP_PROJECT_REQUESTED`; verify all active mandates are revoked with revokedAt derived from the triggering event and Control mode becomes STOPPED.
12. Submit RESUME after STOP; verify Control moves to AWAITING_AUTHORIZATION and execution authority is not restored.
13. Submit `EXTERNAL_MUTATION_OUTCOME_UNKNOWN`; verify Control becomes RECOVERING/RECONCILE_REQUIRED and a PROVIDER_READBACK effect intent is emitted without retrying the mutation.
14. Inject an unknown predicate identifier or duplicate an otherwise applicable transition so two authoritative transitions match; verify fail-closed CONTROL_FAILURE.
15. Verify no transition JSON contains executable code fields and the reference reducer imports no provider/network/LLM/random/time execution facility.

Pass criteria: identical canonical inputs and pinned model revision produce identical logical transition outputs/state hashes; replay reproduces the stored hash; integrity/authority ambiguities never auto-advance state.

## Scenario P — Deterministic Acceptance

Goal: prove that Work Item ACCEPTED is derived only from the approved Acceptance Contract and authoritative typed evidence/review/authority records.

1. Use the exact `SAFOR-FRAMEWORK-v0.13.0-rc.7.json` artifact.
2. Create an executable Work Item with three approved criteria: pinned contribution evidence, independent technical review and explicit risk authority approval.
3. Verify Planning materializes an ACTIVE Acceptance Contract preserving all three criterion texts and mapping each to typed requirements.
4. Verify the contractHash matches canonical contract content and P03 approval binds the contract set.
5. Record pinned contribution evidence with matching subject/evidenceType/revisionRef.
6. Record a PASS review from a reviewer different from the performer and with the required capability.
7. Record APPROVED for the exact required authorityId.
8. Request acceptance reevaluation; verify only `WORK_ITEM_ACCEPTED` changes the Work Item to ACCEPTED.
9. Repeat without evidence; acceptance must not occur.
10. Attempt approving self-review under `PERFORMER_MUST_DIFFER_FROM_APPROVING_REVIEWER`; the review record must not satisfy acceptance.
11. Record CHANGES_REQUIRED; Work Item must deterministically transition to CHANGES_REQUIRED.
12. Repeat without required authority approval; acceptance must not occur.
13. Record REJECTED for the required authority; acceptance must remain blocked for the current contract revision.
14. Tamper with approved criterion text after contract hash creation; contract registration must fail closed.
15. Replay the full accepted sequence from genesis; the resulting state hash must exactly match sequential execution.
16. Attempt to reuse the same evidenceId/reviewId/decisionId under a different eventId; the duplicate record must not be appended.
17. Provide an assistant claim or Agent acceptanceSelfCheck in place of required provider evidence/review/authority; acceptance must not occur.

Pass criteria: ACCEPTED is reproducible, replayable and authority-safe; no probabilistic actor can directly self-accept work.


## Q. Commercial Package Entitlement

**Goal:** prove that paid Factory/Operating Model use is licensed independently from organizational authority.

1. Load the exact `SAFOR-FRAMEWORK-v0.13.0-rc.7.json`.
2. Select **Buch**.
3. With no commercial package artifacts, verify `PACKAGE_ACCESS_REQUIRED`.
4. Supply Book Factory/OM as HUMAN-loaded package artifacts but no independently verified entitlements; verify `PACKAGE_ENTITLEMENT_UNVERIFIED`.
5. Attempt to resolve Book package content from `PUBLIC_CANONICAL_REPOSITORY`; verify fail-closed rejection.
6. Supply valid package artifacts and one verified entitlement per required package/version.
7. Verify entitlement evidence uses an allowed verifier method and exact package/version coverage.
8. Verify Factory/OM integrity and technical compatibility are evaluated separately after entitlement.
9. Verify purchasing/loading the package does not create an Operating Model authority, execution mandate, provider permission, review approval or project scope.
10. Revoke/expire entitlement before a new binding and verify the paid package cannot be newly bound.
11. Verify Self-Healing does not fabricate or extend entitlement.
12. Verify the public Framework integrity manifest contains no paid Factory/OM model module.

**Pass condition:** commercial access is enforceable as a package-binding gate and never becomes organizational authority.

## R. LOCAL_GIT HUMAN Project Workspace

**Goal:** prove that the project can remain on the HUMAN local disk without remote project storage.

1. Load the exact `SAFOR-FRAMEWORK-v0.13.0-rc.7.json`.
2. Select **Website** and resolve the FREE_PUBLIC Factory/OM.
3. Select **Lokal auf meinem Rechner**.
4. Verify the host exposes actual local filesystem read/write plus Git repository/history/branch/commit capabilities.
5. Select a HUMAN-controlled local Git project path.
6. With a plain non-Git directory, verify mutating execution is blocked until Git is initialized/selected through explicit setup.
7. Verify the project workspace binding records `LOCAL_GIT`, Git root and capability evidence.
8. Verify no remote `safor-memory` is required.
9. Verify SAFOR creates/binds a Git-tracked `.safor/` control root only after setup approval.
10. Verify `.safor/` is MASTER-only and absent from all worker write scopes.
11. Execute one mutating worker job on a dedicated Git branch and verify domain changes remain inside the local HUMAN project repository.
12. Attempt to redirect project work to `empishaj/SAFOR` or a package-source repository; verify rejection.
13. Verify Git trace, readback and deterministic state/replay evidence still work.
14. Verify stopping/resuming does not move the project or control state to a remote service implicitly.

**Pass condition:** all project/domain bytes remain in the HUMAN local Git workspace and SAFOR retains its governance/evidence guarantees.




## S. Free Website Product Boundary

**Goal:** prove that the free path is a Website creation product rather than a free Software/SaaS product.

1. Load `SAFOR-FRAMEWORK-v0.13.0-rc.7.json`.
2. Select **Website**.
3. Verify `safor.factory.website-delivery@1.1.0` and `safor.om.website-team@1.1.0` resolve as FREE_PUBLIC.
4. Verify the Website Factory covers audience/purpose, content/information architecture, experience design, web implementation, accessibility/responsive/performance verification, publishing, observation and outcome.
5. Verify public discoverability adds search-visibility evidence conditionally.
6. Present a request that requires application logic, SaaS/service lifecycle or broader software operations.
7. Verify the Website Factory returns `CREATION_TYPE_CHANGE_REQUIRED` targeting `SOFTWARE_SAAS` rather than silently expanding free scope.
8. Verify Website publishing is not treated as website outcome success.

**Pass condition:** free Website scope stays narrow, useful and explicit.

## T. Commercial Software/SaaS Pair

**Goal:** prove that Software/SaaS requires both a paid Factory and a paid Operating Model.

1. Load `SAFOR-FRAMEWORK-v0.13.0-rc.7.json`.
2. Select **Software / SaaS**.
3. With no commercial artifacts, verify `PACKAGE_ACCESS_REQUIRED`.
4. Supply only the Software Factory plus valid entitlement; verify initialization still blocks because the SaaS Operating Model is missing.
5. Supply both artifacts but only one entitlement; verify `PACKAGE_ENTITLEMENT_UNVERIFIED` for the uncovered package.
6. Supply a FREE_PUBLIC Factory or Operating Model override supporting SOFTWARE_SAAS; verify `CREATION_PROFILE_REQUIRES_BOTH_PAID_PACKAGES`.
7. Supply both paid artifacts and one valid independent entitlement per exact package/version.
8. Verify access resolves, then integrity and Factory/Operating-Model compatibility are evaluated.
9. Verify public canonical SAFOR Git is not used to resolve current commercial model content.
10. Verify historical public Software/SaaS 1.6 bytes do not satisfy current commercial package resolution.

**Pass condition:** Software/SaaS cannot initialize until both commercial product modules are licensed and verified.


## U. Strict Commercial Entitlement and Protected Delivery

**Goal:** prove the paid package chain from commercial basis through protected delivery and digest verification.

1. Load `SAFOR-FRAMEWORK-v0.13.0-rc.7.json`.
2. Select **Software / SaaS**.
3. Provide both paid package artifacts but no verification context; verify paid binding does not succeed.
4. Verify a `REVOKED`, `SUSPENDED` or `EXPIRED` entitlement cannot authorize package use.
5. Verify a future `validFrom` or elapsed `validUntil` blocks use at explicit `evaluatedAt`.
6. Verify entitlement subject must equal the active HUMAN/organization subject.
7. Verify issuer ID and entitlement verifier ID must belong to externally configured trusted sets; identities inside the entitlement do not establish trust.
8. Verify commercial-basis evidence exists and its SKU equals the grant SKU.
9. For `ENTITLED_PACKAGE_SOURCE`, omit delivery evidence and verify `COMMERCIAL_PACKAGE_DELIVERY_EVIDENCE_REQUIRED`.
10. Supply delivery evidence with wrong entitlementId/packageId/version and verify fail-closed rejection.
11. Supply delivery evidence with wrong artifactDigest and verify `COMMERCIAL_PACKAGE_DELIVERY_DIGEST_MISMATCH`.
12. Supply expired or future-issued delivery evidence and verify rejection.
13. Supply delivery evidence from an untrusted delivery verifier and verify rejection.
14. Supply valid active entitlements plus valid delivery evidence for both Software Factory and SaaS Operating Model.
15. Verify each delivered package digest matches the package declared-contract digest before compatibility/binding.
16. Verify final package resolutions persist entitlement ID plus delivery ID/verifier/digest evidence.
17. Repeat with `HUMAN_LOADED_PACKAGE`; verify delivery-source evidence is not required, but all entitlement status/time/subject/trust rules remain mandatory.
18. Verify Self-Healing never invents commercial basis, restores revoked entitlement, trusts a self-declared verifier, fabricates delivery evidence or rewrites a digest to pass.

**Pass condition:** no paid package reaches binding without a valid entitlement trust chain; protected-source delivery is additionally bound to immutable package identity and digest.


## V. Domain Framework Distribution and Premium Replacement

**Goal:** prove that one domain-specific Framework file contains its default modules yet remains safely modular.

1. Start a fresh chat with only `SAFOR-FRAMEWORK-WEBSITE.json`.
2. Verify the artifact declares `WEBSITE_CREATION` / `WEBSITE` and embeds Website Factory 1.1.0 plus Website Operating Model 1.1.0.
3. Verify SAFOR does not ask the HUMAN to choose Website/SaaS/Book again.
4. Verify the embedded default pair passes same-domain and bidirectional compatibility.
5. Load a Premium Website Factory with a different packageId but family `safor.factory.website`, domain `WEBSITE_CREATION` and compatible counterpart contract; verify it can replace only the Factory.
6. Restore defaults, then load a Premium Website Operating Model with a different packageId but family `safor.om.website`; verify it can replace only the Operating Model.
7. Load a Website-domain Operating Model from a family not allowed by the Factory; verify replacement rejection.
8. Load a Website-domain Factory from a family not allowed by the Operating Model; verify replacement rejection.
9. Remove a Factory work-item type required by the Operating Model; verify bidirectional compatibility fails.
10. Attempt Book Factory + SaaS Engineering Operating Model; verify domain mismatch rejection.
11. Attempt a SaaS Factory in the Website Framework; verify active-domain mismatch rejection.
12. After each failed replacement, verify the previously valid pair remains bound and SAFOR does not silently replace the counterpart or change the domain.
13. Build the public Website distribution with `python tools/build_domain_framework.py --check`; verify byte-equivalent reproducibility.
14. Verify `SAFOR-FRAMEWORK-SAAS.json` and `SAFOR-FRAMEWORK-BOOK-CREATION.json` are reproducibly built from explicit public test/evaluation package paths and retain paid access mode.

**Pass condition:** domain-specific distribution simplifies startup without sacrificing independent modular replacement or domain safety.


## W. Public Paid-Domain Evaluation

**Goal:** test the two paid domains end to end before the production licensing backend exists.

### SaaS
1. Load `SAFOR-FRAMEWORK-SAAS.json`.
2. Verify publication mode is `PUBLIC_TEST_EVALUATION`, domain is `SAAS_ENGINEERING`, and both embedded modules remain `PAID_ENTITLEMENT_REQUIRED`.
3. Without access evidence, verify paid package access does not silently become free.
4. Load `SAFOR-TEST-ACCESS-SAAS.json`.
5. Verify its subject/trust context and the two exact `1.7.0-test.1` entitlements satisfy the paid test modules.
6. Verify `productionAuthorization=false`.
7. Verify Factory/Operating Model domain, package-family and bidirectional compatibility before project binding.

### Book
8. Load `SAFOR-FRAMEWORK-BOOK-CREATION.json`.
9. Verify publication mode is `PUBLIC_TEST_EVALUATION`, domain is `BOOK_CREATION`, and both embedded modules remain `PAID_ENTITLEMENT_REQUIRED`.
10. Load `SAFOR-TEST-ACCESS-BOOK-CREATION.json`.
11. Verify its exact `1.0.0-test.1` entitlements resolve the embedded Book Factory and Operating Model.
12. Verify `productionAuthorization=false`.
13. Verify a SaaS Factory/OM cannot replace Book modules and vice versa.
14. Verify the production package catalog still exposes no public model path for paid package identities.

**Pass condition:** both paid domain Frameworks can be tested from public Git without weakening paid-mode semantics or redefining the production distribution source.

## S. Platform-owned HUMAN response governor

**Preconditions**
- An existing Website project is bound to an older SAFOR Framework.
- `SAFOR-FRAMEWORK-WEBSITE.json` from the current release is loaded.

**Expected**
1. The platform recognizes the new Framework and begins safe migration analysis without delegating technical comparison or plan drafting to the HUMAN.
2. The first visible notice contains at most two sentences and thirty words.
3. The notice does not expose versions, blob/digest values, package IDs, value-stream mappings or a migration-option menu.
4. Factory and Operating Model contribute facts/evidence only and cannot override visible wording, length, structure or menu behavior.
5. Full comparison, mapping and evidence remain retained and are available through Details/Evidence.
6. A HUMAN decision is requested only if scope, authority, material risk, irreversible action or a genuine alternative requires it.

**Canonical default notice**

```text
Neues Website-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.
```
