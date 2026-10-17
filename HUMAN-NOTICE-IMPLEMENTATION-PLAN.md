# SAFOR HUMAN Notice – verbindlicher Umsetzungsplan

Stand: 17. Oktober 2026  
Zielrelease: `0.13.0-rc.8`  
Ausgangscommit: `bce845305c886b2b78065d1a21f0823775614975`

## Ziel

Dieser Plan setzt die verbindlichen HUMAN-Anforderungen zur Git-basierten MASTER–Subagent-Orchestrierung minimal-invasiv auf Basis der vorhandenen SAFOR-Architektur um. Historische Artefakte bleiben unverändert nachvollziehbar. Neue und aktive Projektinstanzen verwenden danach einen einheitlichen Vertrag.

## Abnahmegrundsatz

Ein Arbeitspaket ist erst abgeschlossen, wenn:

1. die kanonische Quelle geändert wurde,
2. die Single-File- und Domain-Distributionen reproduzierbar neu gebaut wurden,
3. Schema-, Validator-, Unit- und Regressionstests erfolgreich sind,
4. ein negativer Test die relevante Fehlanwendung fail-closed abweist,
5. die Änderung in der Traceability-Matrix der HUMAN-Anforderungen nachgewiesen ist.

## WP-01 – Deklaratives Chat-Produkt ohne Installationspflicht

**Ziel:** SAFOR bleibt JSON-basiert und in einem gewöhnlichen kompatiblen LLM-Chat nutzbar. Eine beim Endkunden installierte SAFOR-Runtime ist keine Produktvoraussetzung.

**Änderungen:**

- expliziter `executionEnvironmentContract` im Kernel,
- normale Chat-Ausführung als primärer Produktmodus,
- Python-Module nur als optionale Referenz-, Prüf- und Hostintegrationsimplementierungen,
- Korrektur von `START-HIER.md`, `SUPPORT.md`, `README.md` und Product-Readiness,
- Verbot, fehlende optionale Runtime als Produktblocker auszugeben.

**Akzeptanz:**

- `customerInstalledRuntimeRequired == false`,
- Domain-Frameworke bleiben direkt hochladbar,
- Dokumentation enthält keine Pflichtbehauptung für Host-/Runtime-Installation,
- technische Grenzen deklarativer Verträge bleiben ehrlich dokumentiert.

## WP-02 – Persistente Agentenidentität und ausschließlich HUMAN-`GO`

**Ziel:** Ein Agenten-Chat wird einmalig gebunden und danach ausschließlich durch ein bewusstes `GO` des HUMAN aktiviert.

**Änderungen:**

- Agent-Bootstrap-Modell und Schema,
- dauerhafte Agenten-ID plus eigenständiger Anzeigename,
- `activationMode = HUMAN_GO_ONLY`,
- Git-Push, Polling, Automation und Host-Ereignisse dürfen keinen Agentenlauf starten,
- fail-closed Rebind bei fehlender/unsicherer Chatbindung,
- keine erneute Übertragung fachlicher Jobprompts.

**Akzeptanz:**

- `GO` ist der einzige gültige Startintent für Subagentenarbeit,
- ein Agent ohne sichere Identitätsbindung schreibt nichts,
- ein Git-Ereignis erzeugt weder Claim noch RUNNING-Status,
- Folgejob wird über Identität → Index → Job gefunden.

## WP-03 – Kanonischer Jobvertrag mit vollständigem Response Contract

**Ziel:** Jeder neue Agentenjob enthält vor Dispatch alle geforderten Identitäts-, Rollen-, Skill-, Kontext-, Git-, Rechte-, Qualitäts- und Rückgabeverträge.

**Änderungen:**

- aktuelles Agent-Job-Schema auf SAFOR 0.13,
- verpflichtender Domain-/Factory-/Operating-Model-Kontext,
- expliziter Produkt- und Control-Write-Scope,
- konkreter Response-Template-Index,
- genaue Repository-, Branch-, Pfad-, Schema- und Blob-Referenzen,
- unveränderlicher Job nach Dispatch und versionierter Supersede-/Rework-Pfad.

**Akzeptanz:**

- unvollständige Jobs sind nicht dispatchfähig,
- jeder Job ist exklusiv an Agent und Identity Revision gebunden,
- Jobrechte sind nur Obergrenze und ersetzen keine realen Providerrechte,
- Produkt- und Response-Schreibziele sind getrennt autorisiert.

## WP-04 – Typisierte Agent-to-MASTER-Response-Familie

**Ziel:** Ergebnisse, Fehler, Klärungen, Capability-Mismatches und Verbesserungsvorschläge sind eigenständige, validierbare Antworttypen.

**Antworttypen:**

- `JOB_RESULT`,
- `JOB_ERROR`,
- `CLARIFICATION_REQUEST`,
- `CAPABILITY_MISMATCH`,
- `IMPROVEMENT_PROPOSAL`.

**Änderungen:**

- gemeinsames Response-Envelope-Schema mit typabhängigen Payloads,
- eingebetteter Template-Katalog,
- Response-Zuordnung zu Job, Agent, Projekt, Work Package und Identity Revision,
- Conflict-/Error-Lifecycle mit MASTER-Entscheidungsreferenz,
- verpflichtende Evidence- und Git-Referenzen nach Antworttyp.

**Akzeptanz:**

- unbekannter oder unpassender Antworttyp wird abgelehnt,
- Blocker stoppt weitere schreibende Agentenarbeit,
- MASTER kann jede Response ohne Chat-Historie einordnen,
- Nacharbeit erzeugt neuen Job beziehungsweise neue Dispatch Revision und überschreibt keine Historie.

## WP-05 – Minimale Subagenten-Chat-Kommunikation

**Ziel:** Subagenten führen kein fachliches Gespräch mit dem HUMAN. Alle substanziellen Inhalte werden in Git abgelegt.

**Änderungen:**

- Plattformvertrag und Schema für `STARTED`, `SUBMITTED`, `BLOCKED`, `REBIND_REQUIRED`,
- deterministische, einzeilige Statusprojektion,
- Verbot von Menüs, Fachdetails, Entscheidungsvorlagen und technischen Dumps im Agenten-Chat,
- MASTER bleibt einzige fachliche/organisatorische HUMAN-Schnittstelle.

**Akzeptanz:**

- Status enthält Agent, Job, Zustand und Git-Referenz beziehungsweise Zielbranch,
- fachliche Payloads im Chatstatus sind ungültig,
- HUMAN-Entscheidungen werden ausschließlich an den MASTER geroutet.

## WP-06 – Kompakter MASTER-Status und Pointer-Ökonomie

**Ziel:** Der MASTER beantwortet Statusfragen aus kleinen, autoritativen Indizes und lädt Details nur gezielt nach.

**Änderungen:**

- Master-Status-Index-Modell und Schema,
- vollständige Agentenregistrierung inklusive Zustand und Rückmeldestatus,
- Job-/Review-/Blocker-/PR-Pointer,
- eine explizite autoritative Control-State-Referenz,
- Verbot globaler Vollscans im Normalpfad.

**Akzeptanz:**

- Statusfragen erfordern nur Registry, Master-Index und betroffene Einzelreferenzen,
- alle registrierten Agenten sind im Status sichtbar,
- veraltete oder widersprüchliche Pointer blockieren statt zu raten,
- Aktualität wird über Revision und Provider-Readback gekennzeichnet.

## WP-07 – Konformität, Regression und Release

**Ziel:** Jede verbindliche HUMAN-Anforderung wird maschinenprüfbar und in den rc.8-Distributionen ausgeliefert.

**Änderungen:**

- Kernel-Invarianten und Conformance Assertions,
- genaue Self-Healing-Abdeckung aller neuen Module,
- positive und negative Unit-/Regressionstests,
- Human-Notice-Traceability-Matrix,
- Release-Dokumentation und rc.8-Bundles.

**Akzeptanz:**

- Bundle- und Domain-Distributionen sind bytegenau reproduzierbar,
- Validator und vollständige Testsuite sind grün,
- jede HUMAN-Anforderung besitzt mindestens einen Quell- und Testnachweis,
- keine Domain-Factory und kein Operating Model kontrolliert die Plattformkommunikation.

## WP-08 – Nichtdestruktive Migration des Referenzprojekts `safomwebsite`

**Ziel:** Aktive Projektsteuerung wird auf rc.8 und die neuen Verträge gehoben, ohne historische AWC-/Job-/Evidence-Artefakte umzuschreiben.

**Änderungen:**

- rc.8-Bindung und Migrationsentscheidung,
- autoritativer Current-State-Pointer,
- vollständiges Agentenregister mit eindeutigen Anzeigenamen,
- aktualisierte aktive Identitäten und Launch-Prompts,
- materialisierte Response-Templates und Master-Status-Index,
- Legacy-Artefakte als read-only Historie markieren,
- bestehende Blocker und akzeptierte Arbeit unverändert übernehmen.

**Akzeptanz:**

- kein akzeptierter historischer Job wird verändert,
- aktive Agenten verwenden HUMAN-`GO` und neue Response-Verträge,
- MASTER kann alle Agenten/Jobs/Reviews/Blocker aus dem kompakten Index berichten,
- das Produktrepository bleibt von Control-Artefakten frei,
- Migration wird durch Provider-Readback und Projekt-Konformitätstest belegt.

## End-to-End-Abnahme

Der Abschlusslauf muss folgenden Pfad nachweisen:

1. Domain-Framework in normalen kompatiblen Chat laden.
2. Projekt und Memory über vorhandene Git-Werkzeuge binden.
3. MASTER erstellt beziehungsweise migriert Agentenidentität, Inbox-Index und vollständigen Job.
4. HUMAN initialisiert einen neuen Agenten-Chat einmalig.
5. HUMAN sendet nur `GO`.
6. Agent validiert Identität, Index, Job, Rolle, Skill, Inputs, Rechte und Schreibziele.
7. Agent schreibt Produktbeitrag und typisierte Git-Response oder stoppt mit typisiertem Blocker.
8. Agenten-Chat zeigt nur Minimalstatus.
9. MASTER liest kompakten Statusindex und Response, veranlasst unabhängige Prüfung und aktualisiert den Lifecycle.
10. Rework, Supersede, Review und Acceptance bleiben vollständig historisiert.

## Freigabe

Die HUMAN-Anweisung vom 17. Oktober 2026 autorisiert die Umsetzung dieses Plans. Merges, produktive Deployments und kommerzielle Aktivierungen bleiben von den jeweils vorhandenen SAFOR-/Repository-Gates abhängig.
