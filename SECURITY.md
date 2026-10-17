# Security Policy

## SAFOR security model

SAFOR is deny-by-default and evidence-driven.

### Non-negotiable rules
- Never paste passwords, personal access tokens, private keys, recovery codes, or other secrets into chat.
- Provider permissions come from the actual GitHub/GitLab connection, never from JSON declarations.
- `{OWNER}/safor-memory` must be readable and writable before SAFOR proceeds.
- External mutations require authoritative provider readback before they are treated as completed.
- Website Factory 1.6 requires security requirements before implementation, threat assessment during design, secure-build evidence, post-release vulnerability response and fail-closed conditional risk authorities.
- Dependency inventory and build provenance are required; SBOM evidence is required when third-party components are present.
- Unknown mutation effects transition to reconciliation before any retry.
- Self-healing may not bypass HUMAN gates, reviews, separation of duties, or active mandate scope.
- Force-push, history rewrite, destructive repository deletion, and invented evidence are forbidden automatic repairs.

## Reporting a vulnerability

Do not post secrets or exploitable details in a public issue. Contact the repository owner through a private GitHub channel before public disclosure.

## Supported version

Security hardening currently targets SAFOR v0.13.0-rc.2 and the free Website Factory/Operating Model 1.6.0 pair.
