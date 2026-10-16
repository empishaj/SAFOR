# SAFOR

**Systemic AI Factory Orchestration Runtime**

This repository is the canonical product repository for SAFOR.

## Separation of concerns

- **This repository (`empishaj/SAFOR`)** contains the SAFOR product, runtime definition, factories, operating models, provider adapters, schemas and distributable JSON.
- **`{OWNER}/safor-memory`** is a mandatory, project-scoped runtime/control-memory repository used by a HUMAN after loading SAFOR. It is not the SAFOR product repository.

## Current distribution

- `SAFOR-MASTER-COMPLETE.json` — self-contained single-file distribution.
- `v0.4.0/` — modular source baseline.

The HUMAN runtime must verify a pre-existing writable `{OWNER}/safor-memory`. Missing or read-only memory means **STOP**.
