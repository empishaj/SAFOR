# SAFOR 200-Scenario Hardening Suite

This directory contains the formal scenario-driven hardening campaign for SAFOR.

- `scenarios/`: exactly 200 immutable scenario definitions (`SC-001.json` .. `SC-200.json`)
- `manifest.json`: suite manifest and category/priority counts
- `status/status-index.json`: current status projection
- `status/status-log.json`: append-only execution/status history
- `status/status-protocol.json`: verdict semantics and update rules
- `schemas/`: JSON Schemas for scenario and status records

All scenarios start as `NOT_RUN`. Existing historical evidence may be referenced when a scenario is formally executed, but the campaign does not pre-label scenarios as PASS.

The intended learning loop is:

Scenario -> Execution -> Evidence -> Verdict -> Finding -> Root Cause -> Remediation -> Regression -> Retest -> Learned Rule.

A failure must be preserved. A PASS without sufficient evidence is invalid.
