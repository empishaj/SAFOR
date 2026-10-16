# Release Checklist

## Required before every SAFOR release

- [ ] `VERSION` matches the intended release.
- [ ] `CHANGELOG.md` contains the release.
- [ ] `RELEASE-MANIFEST.json` matches the canonical repository and artifact.
- [ ] `python tools/build_bundle.py --check` passes.
- [ ] `python tools/validate_safor.py` passes.
- [ ] CI is green on the exact release commit.
- [ ] `SAFOR-MASTER-COMPLETE-v0.7.0-rc.1.json` is rebuilt from canonical `v0.7.0/` source.
- [ ] `SAFOR-MASTER-COMPLETE.json` exactly matches the versioned release artifact.
- [ ] All embedded module references resolve.
- [ ] Runtime memory requirement is exactly `{OWNER}/safor-memory`.
- [ ] Missing/read-only `safor-memory` still results in STOP.
- [ ] Creation type remains mandatory.
- [ ] Software/Website Factory contracts pass.
- [ ] Book Factory contracts pass.
- [ ] Self-healing safety invariants pass.
- [ ] Chat-native-only UI policy passes.
- [ ] Agent registry/identity/job/state/result schemas validate.
- [ ] Agent workspace ownership boundaries validate.
- [ ] MASTER-authoritative agent job lifecycle validates.
- [ ] Agent result cannot self-accept.
- [ ] Agent Workspace scenarios F–H in `ACCEPTANCE-TESTS.md` are recorded.
- [ ] Multi-Agent Scheduler schemas/model validate.
- [ ] Work packages enforce ATOMIC/COMPOSITE decomposition and resource declarations.
- [ ] Agent scheduling capacity and conflict-free dispatch-wave rules validate.
- [ ] Resource leases reconcile before reassignment.
- [ ] Mutating agent jobs use dedicated Git branches from immutable bases.
- [ ] Every agent result has machine JSON plus HUMAN-readable Markdown.
- [ ] Mutating results include provider-verifiable Git trace.
- [ ] Acceptance scenarios I–K are recorded.
- [ ] No secrets or credentials exist in release files.
- [ ] HUMAN has approved any change to license/distribution terms.

## Additional gates for General Availability

- [ ] GitHub blank-chat end-to-end acceptance passes according to `ACCEPTANCE-TESTS.md`.
- [ ] GitLab blank-chat end-to-end acceptance passes according to `ACCEPTANCE-TESTS.md`.
- [ ] Agent Workspace end-to-end acceptance passes according to scenarios F–H.
- [ ] Six-agent scheduling, conflict serialization and HUMAN-readable/Git-trace acceptance pass according to scenarios I–K.
- [ ] License/distribution decision is explicit.
- [ ] Public repository slug is final and stable.
