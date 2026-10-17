# Release Checklist

## Required before every SAFOR release

- [ ] `VERSION` matches the intended release.
- [ ] `CHANGELOG.md` contains the release.
- [ ] `RELEASE-MANIFEST.json` matches the canonical repository and artifact.
- [ ] `python tools/build_bundle.py --check` passes.
- [ ] `python tools/validate_safor.py` passes.
- [ ] CI is green on the exact release commit.
- [ ] `SAFOR-MASTER-COMPLETE-v0.11.0-rc.1.json` is rebuilt from canonical `v0.11.0/` overlay plus pinned `v0.10.0/` baseline.
- [ ] `SAFOR-MASTER-COMPLETE.json` exactly matches the versioned release artifact.
- [ ] All embedded module references resolve.
- [ ] Runtime memory requirement is exactly `{OWNER}/safor-memory`.
- [ ] Missing/read-only `safor-memory` still results in STOP.
- [ ] Creation type remains mandatory.
- [ ] Software/Website Factory contracts pass.
- [ ] Book Factory contracts pass.
- [ ] Self-healing safety invariants pass.
- [ ] Every embedded module has exactly one recovery profile.
- [ ] No recovery profile targets an unknown module key.
- [ ] Every embedded module and integrity-manifest entry carries the matching selfHealingProfileId.
- [ ] All module recovery profiles validate against the recovery-profile schema.
- [ ] IMMUTABLE_VALIDATE_ONLY profiles cannot auto-rewrite semantics.
- [ ] RESTORE_FROM_VERIFIED_SOURCE profiles require expected version/blob evidence.
- [ ] REGENERATE_DERIVED_ONLY profiles mutate only declared derived artifacts.
- [ ] REBIND_EXTERNAL_CAPABILITY profiles never elevate provider rights.
- [ ] Self-healing controls fail closed when their own integrity cannot be proven.
- [ ] Module-aware repair records include profile decision and verification evidence.
- [ ] Chat-native-only UI policy passes.
- [ ] HUMAN Cognitive Load Policy validates for all lifecycle phases.
- [ ] HUMAN Decision Gate defaults to DO_NOT_ASK and exposes only legitimate HUMAN reasons.
- [ ] Discovery permits HIGH necessary load while post-plan Scheduling/Agent Coordination default VERY_LOW and Execution/Recovery default LOW.
- [ ] Every HUMAN decision action carries an explicit interaction reason/load contract.
- [ ] SAFOR derives from approved state/evidence before asking.
- [ ] Unchanged decisions, mandates and persistent identities are reused without redundant approval.
- [ ] Deterministic K10 package binding requires no second approval; K10A is exceptional only.
- [ ] Internal job/branch/lease/dispatch/readback/evidence mechanics are never delegated to HUMAN.
- [ ] Default SUMMARY uses HUMAN-domain language and hides internal IDs/terms.
- [ ] Primary action labels are domain-specific; fallback is `Weiter`.
- [ ] Cognitive-load score is explicitly treated as a non-psychometric governance heuristic.
- [ ] Agent registry/identity/job/state/result schemas validate.
- [ ] Agent workspace ownership boundaries validate.
- [ ] MASTER-authoritative agent job lifecycle validates.
- [ ] Agent result cannot self-accept.
- [ ] Canonical Agent Job Contract validates.
- [ ] Every job has UUIDv7 jobId, jobKey and package/work-item/sequence lineage.
- [ ] MASTER provenance/timestamps are explicit.
- [ ] Agent identity revision and explicit role contract are bound.
- [ ] Mandatory skills are versioned/described and pinned to immutable source blobs.
- [ ] Inputs are immutable READ_ONLY references.
- [ ] Provider/repository/write/branch/merge/deploy rights are explicit.
- [ ] Result/HUMAN-result/evidence/audit return routes are fixed before dispatch.
- [ ] `inbox/{jobId}.md` projection is generated, blob-pinned and read back before READY.
- [ ] Rework uses a new jobId.
- [ ] Agent Workspace scenarios F–H in `ACCEPTANCE-TESTS.md` are recorded.
- [ ] Multi-Agent Scheduler schemas/model validate.
- [ ] Work packages enforce ATOMIC/COMPOSITE decomposition and resource declarations.
- [ ] Agent scheduling capacity and conflict-free dispatch-wave rules validate.
- [ ] Resource leases reconcile before reassignment.
- [ ] Mutating agent jobs use dedicated Git branches from immutable bases.
- [ ] Every agent result has machine JSON plus HUMAN-readable Markdown.
- [ ] Mutating results include provider-verifiable Git trace.
- [ ] Acceptance scenarios I–K are recorded.
- [ ] Canonical explicit Job Contract scenario L is recorded.
- [ ] Module-wide Self-Healing scenario M is recorded.
- [ ] HUMAN Cognitive Load scenario N is recorded.
- [ ] No secrets or credentials exist in release files.
- [ ] HUMAN has approved any change to license/distribution terms.

- [ ] Deterministic reducer tests pass: same inputs -> same hash, replay equivalence, idempotency, divergent duplicate rejection, pause/resume, STOP mandate revocation and reconcile-on-unknown-effect.
- [ ] All transition predicates resolve to the closed registry and all effects use the closed operation set.
- [ ] 54 embedded modules map exactly to 54 recovery profiles.

## Additional gates for General Availability

- [ ] GitHub blank-chat end-to-end acceptance passes according to `ACCEPTANCE-TESTS.md`.
- [ ] GitLab blank-chat end-to-end acceptance passes according to `ACCEPTANCE-TESTS.md`.
- [ ] Agent Workspace end-to-end acceptance passes according to scenarios F–H.
- [ ] Six-agent scheduling, conflict serialization and HUMAN-readable/Git-trace acceptance pass according to scenarios I–K.
- [ ] Canonical explicit Job Contract acceptance passes according to scenario L.
- [ ] Module-wide Self-Healing acceptance passes according to scenario M.
- [ ] HUMAN Cognitive Load/communication acceptance passes according to scenario N.
- [ ] License/distribution decision is explicit.
- [ ] Public repository slug is final and stable.

- [ ] Deterministic Control end-to-end acceptance passes according to scenario O.
- [ ] Full governance transition migration is completed or the remaining non-executable boundary is explicitly accepted for GA scope.
