# Release Checklist

## Required before every SAFOR release

- [ ] `VERSION` matches the intended release.
- [ ] `CHANGELOG.md` contains the release.
- [ ] `RELEASE-MANIFEST.json` matches the canonical repository and artifact.
- [ ] `python tools/build_bundle.py --check` passes.
- [ ] `python tools/validate_safor.py` passes.
- [ ] CI is green on the exact release commit.
- [ ] `SAFOR-MASTER-COMPLETE-v0.5.0-rc.1.json` is rebuilt from canonical `v0.5.0/` source.
- [ ] `SAFOR-MASTER-COMPLETE.json` exactly matches the versioned release artifact.
- [ ] All embedded module references resolve.
- [ ] Runtime memory requirement is exactly `{OWNER}/safor-memory`.
- [ ] Missing/read-only `safor-memory` still results in STOP.
- [ ] Creation type remains mandatory.
- [ ] Software/Website Factory contracts pass.
- [ ] Book Factory contracts pass.
- [ ] Self-healing safety invariants pass.
- [ ] Chat-native-only UI policy passes.
- [ ] No secrets or credentials exist in release files.
- [ ] HUMAN has approved any change to license/distribution terms.

## Additional gates for General Availability

- [ ] GitHub blank-chat end-to-end acceptance passes according to `ACCEPTANCE-TESTS.md`.
- [ ] GitLab blank-chat end-to-end acceptance passes according to `ACCEPTANCE-TESTS.md`.
- [ ] License/distribution decision is explicit.
- [ ] Public repository slug is final and stable.
