# Release Checklist

Use this checklist for every SAFOR release candidate. Current values come from `VERSION`, `RELEASE-FACTS.json` and `RELEASE-MANIFEST.json`; do not duplicate release numbers or package versions here.

## Canonical release facts

- [ ] `VERSION`, `RELEASE-FACTS.targetVersion`, `RELEASE-MANIFEST.version` and traceability `releaseTarget` are identical.
- [ ] `RELEASE-MANIFEST.distributable`, release evidence, release notes and checksum file match the current version.
- [ ] `SAFOR-FRAMEWORK.json` is byte-identical to the current versioned generic Framework.
- [ ] Root contains only the current versioned generic Framework artifact.
- [ ] Current release evidence and checksum file cover all seven distributed/evaluation artifacts.

## Framework build

- [ ] `python tools/build_bundle.py --check` passes.
- [ ] `python tools/build_domain_framework.py --check` passes.
- [ ] `python tools/validate_safor.py` passes.
- [ ] `python tools/validate_audit_remediation.py` passes.
- [ ] `python tools/validate_release_facts.py` passes.
- [ ] `python tools/validate_traceability.py` passes.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] SHA-256 verification of the current checksum file passes.

## Domain distributions

- [ ] Website, SaaS and Book Framework distributions embed the same current SAFOR kernel.
- [ ] Website defaults equal the canonical FREE_PUBLIC package versions from `RELEASE-FACTS.json`.
- [ ] SaaS and Book public files remain evaluation-only and never imply production authorization.
- [ ] Test-access bundles match exactly one domain distribution and keep `productionAuthorization=false`.
- [ ] Cross-domain Factory/Operating-Model or access-bundle combinations are rejected.
- [ ] Factory and Operating Model remain independently replaceable only when access, integrity and bidirectional compatibility pass.

## Agent orchestration

- [ ] MASTER dispatches jobs through `agents/{agentId}/inbox/{jobId}.json` plus the personal inbox index.
- [ ] Normal chat agents require explicit HUMAN `GO`; Git/automation does not activate them.
- [ ] Agent execution identity is bound to pinned identity, identityRevision, personal inbox assignment and dispatchRevision—not host session attestation.
- [ ] Provider CAS/readback remains required for an authoritative claim.
- [ ] Typed OUTBOX responses and MASTER readback/verification remain enforced.

## Documentation

- [ ] `README.md`, `START-HIER.md` and `QUICKSTART.md` contain the current release and package versions.
- [ ] Manual acceptance examples use different artifacts for positive and negative cases.
- [ ] Historical examples are explicitly marked historical.
- [ ] Open evidence/GA gates remain open unless backed by the required evidence.

## Repository hygiene

- [ ] No obsolete one-time materialization workflow remains on `main`.
- [ ] No obsolete release artifacts from older candidates remain in the repository root.
- [ ] Old source baselines required by compatibility/audit tests remain preserved.
- [ ] Superseded pull requests are closed.
