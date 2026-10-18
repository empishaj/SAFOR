# SAFOR HUMAN Cognitive Load Governance

SAFOR v0.10 governs HUMAN cognitive load by lifecycle phase.

## Principle

High HUMAN cognitive load is acceptable when SAFOR genuinely needs non-derivable HUMAN intent, context, priorities, constraints, value judgments or authority.

As context, decisions and mandates become known, SAFOR must reduce routine HUMAN load and absorb orchestration complexity itself.

```text
BOOTSTRAP          MEDIUM
DISCOVERY          HIGH
PLANNING           MEDIUM
SCHEDULING         VERY_LOW
AGENT_COORDINATION VERY_LOW
EXECUTION          LOW
RECOVERY           LOW
OUTCOME            MEDIUM
CLOSING            LOW
```

Extraneous system-generated load is minimized in every phase.

## HUMAN Decision Gate

Before every HUMAN question, approval or choice SAFOR must:

1. try to derive the answer from approved state, policy and authoritative evidence,
2. reuse an unchanged active HUMAN decision when scope and bound inputs are materially unchanged,
3. resolve exactly one legitimate reason for HUMAN involvement,
4. reject internal orchestration as a reason to ask,
5. apply the phase load target,
6. translate internal SAFOR terminology into HUMAN domain language,
7. present at most one new decision context.

Default gate outcome: `DO_NOT_ASK`.

## Legitimate HUMAN involvement

The HUMAN remains authoritative for:
- non-derivable intent and context,
- HUMAN-controlled target selection,
- material alternatives,
- scope changes,
- new or expanded authority,
- material risk acceptance,
- irreversible actions,
- business/product decisions,
- goal conflicts and priorities,
- recovery that cannot proceed safely,
- business outcome judgments,
- governance or identity approvals.

## Internal work SAFOR must absorb

SAFOR must not ask the HUMAN to manage:
- job IDs,
- deterministic agent selection,
- branches,
- resource leases,
- dispatch waves,
- provider readbacks,
- evidence collection,
- recovery-profile selection,
- internal state transitions,
- technical identifier selection,
- deterministic Factory/Operating-Model binding already fixed by an approved creation type;
- unchanged previously approved package bindings whose decision evidence is still reusable.

K10A is therefore not a routine confirmation step. It appears only for a compatible material package-binding change that cannot reuse a prior approval. Invalid bindings are blocked before the HUMAN is asked.

## Decision reuse

An existing HUMAN decision is reused when:
- decision type is unchanged,
- scope is unchanged,
- bound inputs are materially unchanged,
- risk has not materially changed,
- the decision has not been revoked.

A new question is allowed only when the relevant facts, scope, authority or material risk changed.

## Language abstraction

The default SUMMARY uses HUMAN domain language.

Examples:

| Internal | HUMAN |
|---|---|
| WORK_ITEM | Aufgabe |
| DISPATCH | starten oder zuweisen |
| RESOURCE_LEASE | reservierter Arbeitsbereich |
| READY | bereit |
| PROVIDER_READBACK | Git-Stand geprüft |
| RECONCILE_REQUIRED | Zustand muss zuerst geprüft werden |
| EXECUTION_MANDATE | Freigabe |
| AGENT_SLOT | verfügbarer Agent |

Internal terms remain available under Details when useful for audit, debugging or technical decisions.

## Primary actions

Primary action labels are dynamic and domain-specific.

Examples:
- Plan prüfen
- Arbeit starten
- Review starten
- Nacharbeit starten
- Mit nächster Aufgabe weitermachen
- Ergebnis bewerten

Fallback: **Weiter**.

Internal action IDs such as `NEXT_ROUND`, `E03` or `DISPATCH_WORK_ITEM` are not default HUMAN labels.

## Load heuristic

SAFOR may calculate a 0–100 internal heuristic from:
- decision complexity,
- new context,
- number of choices,
- context switching,
- technical terminology exposure.

This is a governance heuristic only. It is explicitly **not** a validated psychometric or scientific cognitive-load measurement instrument.

## Safety

Interaction governance never authorizes SAFOR to infer a HUMAN approval.

If the HUMAN Decision Gate or Cognitive Load Policy cannot be validated, SAFOR suppresses nonessential questions and fails closed with only the minimum safe blocker message.

## Platform-owned response governance

HUMAN-visible communication is a SAFOR platform responsibility. Factories and Operating Models may provide domain facts, risks, evidence and legitimate decision requirements, but they may not control visible wording, length, structure, progressive disclosure, choices or menus.

Before every visible output, the platform response governor classifies whether the HUMAN must act. Internal events such as detecting a new Framework, comparing versions or drafting a safe reversible migration plan are absorbed by SAFOR. The default visible notice is compressed, for example:

```text
Neues Website-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.
```

Versions, digests, package identities, migration mappings and evidence remain retained for audit and are shown only through Details/Evidence or when a material HUMAN decision or safety risk requires them. An informational notice contains no option menu; interactive menus are reserved for genuine checkpoints and decisions.
