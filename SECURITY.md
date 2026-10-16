# Security Policy

## SAFOR security model

SAFOR is deny-by-default and evidence-driven.

### Non-negotiable rules
- Never paste passwords, personal access tokens, private keys, recovery codes, or other secrets into chat.
- Provider permissions come from the actual GitHub/GitLab connection, never from JSON declarations.
- `{OWNER}/safor-memory` must be readable and writable before SAFOR proceeds.
- External mutations require authoritative provider readback before they are treated as completed.
- Unknown mutation effects transition to reconciliation before any retry.
- Self-healing may not bypass HUMAN gates, reviews, separation of duties, or active mandate scope.
- Force-push, history rewrite, destructive repository deletion, and invented evidence are forbidden automatic repairs.

## Reporting a vulnerability

Do not post secrets or exploitable details in a public issue. Contact the repository owner through a private GitHub channel before public disclosure.

## Supported version

Security hardening currently targets the latest v0.4.x release candidate.
