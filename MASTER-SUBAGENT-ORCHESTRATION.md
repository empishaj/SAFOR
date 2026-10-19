# MASTER–Subagent-Orchestrierung

Dieses Dokument beschreibt den verbindlichen v0.14-Zielbetrieb zwischen HUMAN, MASTER und persistenten Subagenten.

## Rollen

### HUMAN

Der HUMAN:

- formuliert Ziele und Anforderungen im MASTER-Chat;
- entscheidet über Scope, Prioritäten, Risiken und Freigaben;
- fragt MASTER nach Roadmap und Status;
- fügt einmalig einen MASTER-erzeugten Initialisierungsprompt in einen neuen Agenten-Chat ein;
- startet spätere Agentenjobs dort ausschließlich mit `GO`;
- transportiert keine Jobtexte, Skills, Eingaben oder Ergebnisformate zwischen Chats.

### MASTER

MASTER ist die einzige fachliche und organisatorische HUMAN-Schnittstelle. Er:

- klärt Ziel und Kontext;
- plant Work Packages und Abhängigkeiten;
- löst Factory-/Operating-Model-Rollen auf konkrete Agenten auf;
- erstellt und pflegt Identitäten, Anzeigenamen, Inboxen und kompakte Statusindizes;
- erzeugt immutable Jobs mit Rolle, Skills, Inputs, Branches, Rechten, Outputs und Response-Verträgen;
- plant konfliktfreie Dispatch Waves;
- veröffentlicht Chatjobs als `WAITING_HUMAN_GO`;
- liest Responses, Evidence und Provider-Readback;
- organisiert unabhängige Reviews;
- verifiziert, akzeptiert und integriert Ergebnisse getrennt;
- löst Blocker oder erstellt historisch verkettete Ersatzjobs.

### Subagent

Ein normaler Subagent ist ein persistenter, an einen fortgeführten Chat gebundener `CHAT_AGENT`. Er:

- kennt seine technische ID und seinen separaten Anzeigenamen;
- startet nur nach direktem HUMAN-`GO`;
- liest selektiv Identität, eigenen Index, Job, MASTER-State und gepinnte Inputs;
- validiert Rolle, Skills, Domain, Versionen, Rechte, Branch und Schreibziele;
- arbeitet nur im Jobscope;
- schreibt Produktartefakte und Control-Responses in getrennte Ziele;
- hält Details dauerhaft in Git fest;
- zeigt im Chat nur einen Minimalstatus;
- fragt nicht den HUMAN nach fachlicher Klärung;
- übernimmt keinen fremden Job und wechselt nicht eigenmächtig Rolle oder Auftrag.

## Einmalige Agenteninitialisierung

MASTER erzeugt:

```text
agents/{agentId}/identity.json
agents/{agentId}/initialization.json
agents/{agentId}/state.json
agents/{agentId}/inbox/index.json
agents/{agentId}/outbox/index.json
```

Die Initialisierung bindet:

- `projectId`;
- `masterId`;
- `agentId`;
- `displayName`;
- `identityRevision`;
- Control Repository;
- Workspace Root;
- persönliche INBOX-Bindung;
- Kommunikationsvertrag.

Der HUMAN fügt den gerenderten Prompt einmal ein. Der Agent liest die referenzierten Artefakte zurück und meldet `READY`.

Bei fehlender, veralteter oder widersprüchlicher Identität/INBOX-Bindung:

```text
REIDENTIFICATION_REQUIRED
```

Kein Job wird geclaimt und keine Produktmutation ausgeführt.

## Jobvorbereitung

MASTER darf einen Job erst veröffentlichen, wenn:

- Work Item atomar und dependency-ready ist;
- Mandat und HUMAN-Entscheidungen aktiv sind;
- Rollen- und Skillquellen immutable gepinnt sind;
- Agent aktiv, an seine persönliche INBOX gebunden, capability-kompatibel und kapazitiv frei ist;
- Inputversionen auflösbar sind;
- Produktbranch und Pfade feststehen;
- Produkt- und Response-Rechte getrennt sind;
- alle fünf Response-Templates gepinnt sind;
- Review- und Acceptance-Regeln definiert sind;
- Leases und Konfliktbereiche reserviert sind;
- JSON und HUMAN-Projektion per Provider-Readback bestätigt wurden.

Danach lautet der Lifecycle:

```text
PREPARED → WAITING_HUMAN_GO
```

## HUMAN-Start

MASTER zeigt:

```text
Agent: Nova Dev (agent-dev-003)
Job: WP-014-IMPL
Agenten-Chat: <initialisierter Agenten-Chat>
Start: GO
```

Der HUMAN sendet im Agenten-Chat ausschließlich:

```text
GO
```

Zusätzlicher Fachtext ist nicht Teil des Aktivierungsvertrags.

## Agenten-Preflight

Nach `GO` prüft der Agent:

1. gepinnte Identity und persönliche INBOX-Bindung;
2. persönlichen Inbox-Index;
3. Job- und Projektion-Blob;
4. MASTER-Jobstatus und Dispatch Revision;
5. single-use GO-Evidence;
6. Mandat;
7. Rolle, Skills, Domain und Technologie;
8. immutable Inputs;
9. Produktbranch und erlaubte Pfade;
10. getrennte Response-Ziele;
11. tatsächliche Providerrechte;
12. aktive Leases und Konfliktfreiheit;
13. STOP, PAUSE, stale refs oder ungültige Identity/INBOX-Bindung.

Erst danach erfolgt der Claim.

Der Claim schreibt **nicht** in `master/jobs/{jobId}.json`. Der Agent führt einen providerseitigen Compare-and-Swap ausschließlich auf seinem eigenen `agents/{agentId}/state.json` aus. Der Jobvertrag muss diesen `claimStateTarget` vorab binden. Erst exakter Provider-Readback macht den Claim autoritativ; danach darf der Agent innerhalb des bereits erteilten Mandats arbeiten. MASTER reconciliert seinen Job-Lifecycle später aus Claim- und Response-Evidence.

## Rückgabeobjekte

| Typ | Auslöser | Wirkung |
|---|---|---|
| `JOB_RESULT` | Arbeit abgeschlossen | MASTER verifiziert und plant Review/Acceptance |
| `JOB_ERROR` | technische Ausführung fehlgeschlagen | Job stoppt; MASTER plant Repair/Rework |
| `CLARIFICATION_REQUEST` | Job unklar oder widersprüchlich | Job stoppt; MASTER klärt oder ersetzt ihn |
| `CAPABILITY_MISMATCH` | Rolle/Skill/Domain/Identität passt nicht | Job stoppt; MASTER korrigiert Zuordnung |
| `IMPROVEMENT_PROPOSAL` | nicht blockierender Vorschlag | MASTER entscheidet separat; Jobscope bleibt unverändert |

Alle Responses sind immutable. Resolutionen liegen separat unter:

```text
master/response-resolutions/{responseId}.json
```

## Minimalstatus im Agenten-Chat

Zulässig sind nur:

```text
READY
STARTED
SUBMITTED
BLOCKED
REIDENTIFICATION_REQUIRED
```

Die Meldung bleibt eine Zeile. Sie enthält bei `SUBMITTED` oder `BLOCKED` eine Git-Referenz. Es folgen keine fachlichen Erläuterungen im selben Turn.

## MASTER-Status

Routinefragen werden aus kompakten Indizes beantwortet:

- Welche Agenten brauchen jetzt `GO`?
- Welche Jobs laufen?
- Welche Responses sind eingegangen?
- Welche Reviews sind offen?
- Welche Jobs sind blockiert?
- Haben sich alle erwarteten Agenten zurückgemeldet?
- Was ist die nächste HUMAN-Aktion?

MASTER lädt Detailobjekte nur über exakte Pointer bei Stale State, Konflikt, Audit, Risiko oder ausdrücklicher Nachfrage.

## Qualität und Integration

```text
RESPONSE_SUBMITTED
→ VERIFIED
→ ACCEPTED
→ INTEGRATED
```

- Agent submission is not acceptance.
- Provider mutation is not complete without readback.
- Author self-review does not satisfy independent review.
- Acceptance does not imply merge.
- Delivery does not prove business outcome.

## Rework und Konfliktlösung

Ein blockierender Response bleibt unverändert. MASTER schreibt eine Resolution und erzeugt bei Bedarf einen neuen Job mit:

- neuer UUIDv7-ID;
- `supersedesJobId`;
- `triggerConflictRef`;
- neuem Versuch/Rework-Zyklus;
- aktualisierten, erneut gepinnten Inputs und Rechten.

Der HUMAN startet den Ersatzjob wieder mit `GO`.

## Endkunden- und Runtimegrenze

Diese Arbeitsweise ist als JSON-Vertrag im normalen kompatiblen Chat nutzbar. Der HUMAN installiert keine zusätzliche SAFOR-Runtime. Optionale Referenzmodule, CI, Branch-Protection und Hostadapter können dieselben Regeln technisch verstärken, ersetzen aber weder tatsächliche Providerrechte noch die bewusste HUMAN-Autorität.
