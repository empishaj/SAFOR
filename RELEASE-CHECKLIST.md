# Release Checklist

## Required before every SAFOR release

- [ ] `VERSION` matches the intended release.
- [ ] `CHANGELOG.md` contains the release.
- [ ] `RELEASE-MANIFEST.json` matches the canonical repository and artifact.
- [ ] `python tools/validate_safor.py` passes.
- [ ] CI is green on the exact release commit.
- [ ] `SAFOR-MASTER-COMPLETE.json` is rebuilt from canonical `empishaj/SAFOR` source.
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

- [ ] GitHub blank-chat end-to-end acceptance passes.
- [ ] GitLab blank-chat end-to-end acceptance passes.
- [ ] License/distribution decision is explicit.
- [ ] Public repository slug is final and stable.
