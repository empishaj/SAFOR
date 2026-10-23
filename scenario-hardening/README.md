# SAFOR 200-Scenario Hardening Suite

This directory contains the formal scenario-driven hardening campaign for SAFOR.

- `scenarios/`: exactly 200 immutable scenario definitions (`SC-001.json` .. `SC-200.json`)
- `runs/{scenarioId}/{runId}.json`: immutable execution records for every attempt
- `manifest.json`: suite manifest, baselines, category/priority counts and active runs
- `status/status-index.json`: compact current-status projection using `defaultRecord + overrides`
- `status/status-log.json`: append-only execution/status history
- `status/status-protocol.json`: verdict semantics, resolution and update rules
- `schemas/`: JSON Schemas for scenario and status records

All scenarios begin as `NOT_RUN`. Existing historical evidence may be referenced when a scenario is formally executed, but the campaign does not pre-label scenarios as PASS.

## Current-status resolution

The scenario universe is the 200 IDs declared by `manifest.json`.

1. If `status-index.json#/overrides/{scenarioId}` exists, that record is the current status.
2. Otherwise the scenario inherits `status-index.json#/defaultRecord`.
3. The summary must equal the resolved counts across all 200 scenarios.
4. Prior terminal outcomes remain in `status-log.json` and immutable run records when a retest becomes `RUNNING`.

This model avoids duplicating 199 identical `NOT_RUN` records while retaining an exact current status for all 200 scenarios.

## Learning lifecycle

Scenario -> Execution -> Evidence -> Verdict -> Finding -> Root Cause -> Remediation -> Regression -> Retest -> Learned Rule.

A failure must be preserved. A PASS without sufficient evidence is invalid. A MASTER pre-GO readback must validate both immutable Job inputs and mutable control/status projections before HUMAN activation is requested.
