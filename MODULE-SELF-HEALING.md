# SAFOR Module-wide Self-Healing

SAFOR v0.10 includes conservative self-healing to every embedded module.

## Core rule

Every embedded module has exactly one recovery profile.

A repair is executable only when all of these allow it:

```text
failure-class policy
AND module recovery profile
AND active SAFOR authority/policy
AND actual host/provider rights
```

## Attempt and retry semantics

SAFOR distinguishes the first repair execution from a retry.

- **INITIAL** is the first profile-constrained repair execution for one `failureFingerprint`. It is `attemptNumber: 1` and does **not** consume retry budget.
- **RETRY** starts at `attemptNumber: 2`. It consumes `additionalRetryBudget` and requires a reference to the prior attempt plus authoritative readback proving that the prior mutation did **not** take effect.
- **RECONCILIATION** is read-only evidence collection. It is not a repair attempt, does not consume retry budget and may not mutate state.
- If the prior external effect is unknown, the state is `RECONCILE_REQUIRED`; SAFOR may not issue the mutation again.
- If an upstream product mutation is proven applied but response persistence failed, SAFOR may continue only with the missing response/control persistence effect. The proven product mutation is never replayed.

For SAFOR 0.14 every module recovery profile has `initialAutomaticAttemptBudget: 1` and `additionalRetryBudget: 0`. Therefore module-wide self-healing can make one automatic initial repair attempt, but it cannot automatically execute a second repair mutation for the same failure fingerprint.

## Recovery modes

- `IMMUTABLE_VALIDATE_ONLY` — validate or reload the expected pinned blob; never rewrite semantics.
- `RESTORE_FROM_VERIFIED_SOURCE` — restore only the expected version/blob from a verified canonical source.
- `REGENERATE_DERIVED_ONLY` — regenerate only declared derived artifacts from verified authoritative sources.
- `REBIND_EXTERNAL_CAPABILITY` — refresh/reobserve external capabilities; never grant or elevate permissions.

## Coverage

The complete release bundle contains a recovery profile for every module key, including:

- MASTER kernel
- initialization / interaction / self-healing models
- module self-healing model itself
- Agent Workspace
- canonical Agent Job Contract
- Multi-Agent Scheduler
- repository policy and package registry
- GitHub/GitLab provider adapters
- Operating Models
- Factories
- all JSON schemas
- conformance

The bundle builder rejects any mismatch between embedded module keys and recovery-profile keys.

## Fail-closed recovery control

The self-healing model, module-self-healing model and recovery-profile schema cannot heuristically repair their own semantics.

If their expected integrity cannot be proven, SAFOR stops automatic recovery and escalates.

## Examples

### Derived Agent Workspace projection
If `inbox/index.json` is missing or stale, SAFOR may regenerate it from authoritative MASTER job state.

### Canonical job
If `job.md` is missing while `job.json` is valid, SAFOR may regenerate the Markdown projection and verify its blob.

If the dispatched `job.json` contains a wrong role, skill, input or authorization, SAFOR must not rewrite it. The job is blocked/superseded and a new governed job is required.

### Scheduler
SAFOR may recompute READY sets, free capacity and safe dispatch waves from authoritative work/job/lease state.

An expired lease with uncertain external effects requires reconciliation before reassignment.

### Provider adapters
SAFOR may refresh observed capabilities, permissions and remote revisions. It may never fabricate or elevate provider rights.

### Factory / Operating Model
SAFOR may restore the expected pinned package blob and revalidate bindings. It may never automatically change workflow semantics, decision rights, mandates or separation-of-duties policy.

### Schemas
SAFOR may restore an expected schema and revalidate a subject. It may regenerate a subject only when that subject is explicitly derived. Authoritative state is never automatically coerced simply to pass validation.

## Evidence

Every repair record stores:
- module key
- recovery profile ID
- authority type
- repairability
- source reference
- failure class/fingerprint
- pre-state references
- profile-constrained selected action
- attempt kind/number, prior-attempt reference and retry authorization when applicable
- required success evidence
- resulting evidence
- outcome

A repair is successful only after authoritative readback satisfies the module profile success predicate.
