# SAFOR v0.14.0-rc.2 – Umsetzungsplan Master–Subagent-Orchestrierung

**Status:** zur Umsetzung freigegeben durch den HUMAN im aktuellen MASTER-Chat  
**Basis:** `empishaj/SAFOR@29a9bcc5c84fe348f94c63b08852fda28135fe50`  
**Umsetzungsbranch:** `safor/master-subagent-orchestration-v0.14.0-rc.2`  
**Ziel:** vollständige normative Abdeckung der HUMAN NOTICE vom 17. Oktober 2026, ohne bestehende Domain-/Lizenzarchitektur zu brechen.

## 0. Integrationskorrektur für rc.2

Der auditierte rc.1-Zweig bleibt unverändert als Herkunftsnachweis. rc.2 wird selektiv auf `main@29a9bcc5c84fe348f94c63b08852fda28135fe50` integriert. Reales Git-E2E muss vor einer Migration des Referenzprojekts bestehen; Unit- und Bundle-PASS werden nicht als Fremdhost- oder GA-PASS ausgegeben.

## 1. Nicht verhandelbare Zielinvarianten

1. SAFOR bleibt eine direkt in kompatiblen LLM-Chats nutzbare JSON-Distribution.
2. Für normale Endkundennutzung ist keine zusätzlich zu installierende Runtime Voraussetzung.
3. Der MASTER ist die einzige fachliche und organisatorische HUMAN-Schnittstelle.
4. Ein normaler Agenten-Chat beginnt Arbeit ausschließlich nach einem bewussten HUMAN-`GO`.
5. Git-Push, Polling, Scheduler oder ein Host-Trigger dürfen einen normalen Chat nicht automatisch zur Ausführung bringen.
6. Agenten werden einmalig identifiziert; Folgejobs benötigen keinen Fachprompt-Transport.
7. Unsichere Identität, fehlende Historie, stale refs, fehlende Skills oder Rechte führen fail-closed zu einer typisierten Response.
8. Ein Agent liest im Normalpfad nur seine Identität, seinen kleinen Index, den konkreten Job und gepinnte Eingaben.
9. Jeder Job bindet Rolle, Skills, Inputs, Branch, Pfade, Operationen, Qualität und alle Response-Templates.
10. Produktartefakte und Memory-Responses besitzen getrennte Schreibziele und Rechte.
11. Ergebnisse, Fehler, Klärungen, Capability-Mismatch und Verbesserungsvorschläge sind getrennte Response-Typen.
12. Der Agenten-Chat enthält nur minimale Start-, Abschluss-, Blocker- oder Reidentifikationsmeldungen.
13. `SUBMITTED`, `VERIFIED`, `ACCEPTED` und `INTEGRATED` sind getrennte Zustände.
14. Rework oder substanzielle Änderung erzeugen neue, historisch verkettete Jobobjekte.
15. Bestehende Website-/SaaS-/Book-Paket-, Lizenz- und Kompatibilitätsregeln bleiben unverändert wirksam.
16. Normative Regeln liegen im JSON-Framework; Python bleibt Referenzvalidator und CI-Harness, nicht Endkundenvoraussetzung.

## 2. Lieferstrategie

Die Umsetzung erfolgt in elf getrennten Arbeitspaketen. Jedes Paket endet mit:

- Git-Readback des erzeugten Commits und der geänderten Pfade;
- Syntax-/Schema-/Unit-Test-Prüfung in GitHub Actions;
- Abgleich gegen die paketbezogenen Akzeptanzkriterien;
- Aktualisierung der Traceability;
- keinem Merge, solange der Gesamtstand nicht vollständig geprüft ist.

### WP-00 – Baseline und Traceability

**Zweck:** Den Implementierungsumfang eindeutig festschreiben und jede HUMAN-Anforderung prüfbar machen.

**Lieferobjekte**

- dieser Umsetzungsplan;
- `requirements-traceability-v0.14.0.json`;
- 33 eindeutig nummerierte normative Anforderungen;
- Abhängigkeiten und Akzeptanzkriterien je Arbeitspaket.

**Akzeptanz**

- 33/33 Anforderungen besitzen mindestens ein Arbeitspaket;
- JSON ist syntaktisch gültig;
- keine Repository- oder Produktmigration wird vorgezogen.

### WP-01 – HUMAN-`GO` und Agenteninitialisierung

**Zweck:** Einmalige, stabile Chatidentität mit ausschließlich bewusstem HUMAN-Start.

**Lieferobjekte**

- Agent Activation Model 0.14;
- Identity-, Registry-, State-, Inbox-Index- und Initialisierungs-Schemas 0.14;
- eingebettetes Initialisierungstemplate;
- Anzeigename zusätzlich zur technischen ID;
- Chat-Binding, Reidentification Policy und GO-Evidence-Vertrag.

**Akzeptanz**

- `activationMode == HUMAN_GO_REQUIRED`;
- `backgroundWakeupAssumed == false`;
- Automations-/Host-Aktivierung eines normalen Chats ist verboten;
- Claim ohne gültige GO-Evidence schlägt fehl;
- unsichere Chatbindung erzeugt keinen Claim und keine Mutation;
- `displayName != agentId`.

### WP-02 – Typisierte Response-Familie

**Zweck:** Alle fachlichen Rückmeldungen standardisiert und maschinenlesbar an den MASTER übergeben.

**Lieferobjekte**

- Response Contract Model 0.14;
- diskriminiertes `agent-response.schema.json`;
- Response-Index-Schema;
- Templates für:
  - `JOB_RESULT`,
  - `JOB_ERROR`,
  - `CLARIFICATION_REQUEST`,
  - `CAPABILITY_MISMATCH`,
  - `IMPROVEMENT_PROPOSAL`.

**Akzeptanz**

- jeder Typ besitzt Job-, Agent-, Identity- und Contract-Bindung;
- Konflikte enthalten ID, Typ, Severity, Schritt, Refs, Lösungsvorschlag und Status;
- blockierende Typen stoppen vor weiterer Mutation;
- Improvement Proposal erweitert den Jobscope nicht;
- MASTER-Entscheidungsreferenz kann nachträglich gebunden werden, ohne historische Response zu überschreiben.

### WP-03 – Jobvertrag v0.14 und minimale Chat-Ausgabe

**Zweck:** Alle Ausführungs-, Rechte-, Git- und Response-Regeln in einem unveränderlichen Jobvertrag bündeln.

**Lieferobjekte**

- Canonical Agent Job 0.14;
- Job-State 0.14;
- Agent Workspace Model 0.14;
- Agent Job Contract Model 0.14;
- Agent Chat Output Schema und Policy;
- aktualisierte HUMAN-lesbare Jobvorlage.

**Akzeptanz**

- Job bindet alle fünf Response-Templates mit Repo/Ref/Path/Blob;
- Produkt- und Response-Schreibziele sind getrennt;
- mutierender Job besitzt dedizierten Branch und immutable Base Commit;
- Chat-Output erlaubt ausschließlich `STARTED`, `SUBMITTED`, `BLOCKED`, `REIDENTIFICATION_REQUIRED`;
- keine lange fachliche Antwort im Agenten-Chat;
- Rework verwendet neue Job-ID und `supersedesJobId`.

### WP-04 – MASTER-Statusindex und Scheduler-Integration

**Zweck:** Schnelle Statusauskunft und sichere Parallelität ohne Repository-Vollscan.

**Lieferobjekte**

- Project Agent Status Index Schema;
- Response-Index-Aggregation;
- Scheduler-Erweiterung `WAITING_HUMAN_GO`;
- GO-Evidence- und Claim-Gates;
- Review-/Separation-of-Duties-Status;
- kompakte Startliste für den HUMAN.

**Akzeptanz**

- MASTER kann alle Agenten, Jobs, Responses, Reviews und Blocker aus kompakten Indizes berichten;
- Details werden nur über exakte Pointer nachgeladen;
- Scheduler dispatcht, aktiviert aber keinen normalen Chat;
- unbekannte Schreibüberlappung wird serialisiert;
- Lease-Ablauf führt zu `RECONCILE_REQUIRED`, nicht stiller Neuzuweisung.

### WP-05 – Migration und Legacy-Kompatibilität

**Zweck:** Bestehende Projekte ohne Historienverlust auf eine eindeutige aktive Autoritätskette migrieren.

**Lieferobjekte**

- Migration Model und Migration Manifest Schema;
- Legacy-Klassifizierung `ACTIVE`, `LEGACY_SNAPSHOT`, `SUPERSEDED`;
- Regeln für alte `SAF_AGENT_*`, AWC- und v0.10-Agentenobjekte;
- Konfliktfreie Koexistenz während der Migration;
- kanonische Repository-Namensauflösung.

**Akzeptanz**

- kein historisches Artefakt wird gelöscht;
- genau eine aktive Control-/Agenten-Autoritätskette;
- Legacy-Objekte dürfen keine neuen Claims auslösen;
- fehlende Agenten werden registriert oder ausdrücklich als Legacy archiviert;
- keine stille Formatkonvertierung ohne Migration Evidence.

### WP-06 – Produktgrenze und Dokumentation

**Zweck:** Die direkte Chat-Architektur unmissverständlich dokumentieren.

**Lieferobjekte**

- korrigierte Start-, Support-, Architektur- und Agentendokumentation;
- klare Trennung zwischen Chat-Ausführung und optionalem Referenzvalidator;
- Benutzerführung für MASTER und Agenten-Chats;
- Minimalstatus-Beispiele.

**Akzeptanz**

- keine Dokumentation bezeichnet eine zusätzliche Endkunden-Runtime als Pflicht;
- Python-Referenzcode wird als optionale Host-/CI-Enforcement-Implementierung beschrieben;
- tatsächliche Providerrechte bleiben Voraussetzung;
- HUMAN kommuniziert fachlich nur mit MASTER und startet Agenten mit `GO`.

### WP-07 – Framework- und Release-Integration

**Zweck:** Die neuen Verträge in alle Single-File- und Domain-Distributionen integrieren.

**Lieferobjekte**

- v0.14-Kernel-/Initialisierungs-/Self-Healing-/Conformance-Overlay;
- Builder- und Validator-Anpassung;
- vollständige Module-Recovery-Coverage;
- `0.14.0-rc.2` Framework- und Domain-Bundles;
- Release Manifest, Version, Changelog und Readiness.

**Akzeptanz**

- reproduzierbare Bundles;
- Integritätsmanifest und Blob-SHAs stimmen;
- alle Module besitzen Recovery Profile;
- keine bezahlten Produktionspakete leaken in das öffentliche Basisframework;
- alle bisherigen Domain-, Entitlement- und Kompatibilitätstests bleiben grün.

### WP-08 – Referenzprojektmigration

**Zweck:** `safomwebsite` im Control Repository auf den aktiven v0.14-Vertrag migrieren.

**Lieferobjekte**

- neues Bindings-/Migration-Manifest;
- vollständiges Agentenregister einschließlich Legacy-Agenten;
- v0.14-Identitäten und Initialisierungsprompt-Refs;
- kompakte Status- und Response-Indizes;
- Legacy-Snapshots statt konkurrierender aktiver Zustände;
- aktualisierte Framework-Pins.

**Akzeptanz**

- alle bekannten Agenten besitzen eindeutige Disposition;
- aktive Identitäten validieren gegen v0.14;
- aktuelle Jobs/Responses bleiben referenzierbar;
- alte AWC-Artefakte bleiben auditierbar;
- keine Produktrepository- oder Default-Branch-Mutation ist für die Migration erforderlich.

### WP-09 – End-to-End-Abnahme

**Zweck:** Die vollständige Kette deterministisch und mit negativen Fällen prüfen.

**Positive Kette**

`Initialisierung → HUMAN GO → Identity/Index/Job-Read → Preflight → Claim → Arbeit → Response → MASTER-Status → Review → Acceptance`

**Negative Ketten**

- kein GO;
- falscher Agent;
- unsichere Chatbindung;
- stale Job-/Input-Ref;
- Skill-/Rollen-Mismatch;
- fehlendes Schreibrecht;
- falscher Response-Typ;
- Response an falschen Pfad;
- Branchkonflikt;
- Rework ohne neue Job-ID;
- Selbstreview;
- Vollscan-Versuch.

**Akzeptanz**

- positive Kette vollständig grün;
- jeder negative Fall stoppt vor unzulässiger Mutation;
- Minimalstatus entspricht dem Chat-Schema;
- Statusindex meldet alle Rückmeldungen korrekt;
- 33/33 Anforderungen besitzen automatisierte Evidenz.

### WP-10 – Abschlussprüfung und Release-PR

**Zweck:** Gesamtdiff, CI, Traceability und Evidenzgrenzen transparent abnehmen.

**Lieferobjekte**

- finaler Requirements Coverage Report;
- CI- und Commit-Readback;
- PR gegen `main`;
- getrennte Aussagen zu:
  - Implementierungsabdeckung,
  - maschineller Konformität,
  - GitHub-Referenz-E2E,
  - noch nicht empirisch geprüften Fremdhosts.

**Akzeptanz**

- keine ungeklärten P0/P1-Abweichungen;
- 33/33 normative Anforderungen sind implementiert und getestet;
- Standard-CI ist vollständig grün;
- generierte Bundles entsprechen exakt den Quellen;
- kein Merge oder Deployment wird ohne explizite, aktuelle Autorität behauptet.

## 3. Validierungsprinzipien

### 3.1 Nach jedem Arbeitspaket

1. Branch-Head vor dem Schreiben erneut lesen.
2. Änderung als atomaren Commit erzeugen.
3. Branch mit Expected-SHA aktualisieren.
4. Commit und Diff zurücklesen.
5. GitHub Actions auf exakt diesem Commit prüfen.
6. Fehler nicht übergehen, sondern im nächsten Korrekturcommit nachvollziehbar beheben.
7. Erst bei grünem Paketstatus mit dem abhängigen Arbeitspaket fortfahren.

### 3.2 Sicherheits- und Governancegrenzen

- Kein Force-Push.
- Keine direkte Mutation von `main`.
- Keine Löschung historischer Projektartefakte.
- Keine Erfindung von Providerrechten, Testergebnissen oder unabhängigen Reviews.
- Keine automatische Aktivierung normaler Agenten-Chats.
- Keine Vermischung von Produkt- und Control-Repository-Schreibrechten.
- Keine Verringerung bestehender Lizenz-, Entitlement-, Integritäts- oder Domain-Kompatibilitätskontrollen.

### 3.3 Bedeutung von „100 %“

„100 %“ bedeutet in diesem Vorhaben:

- vollständige normative Requirements-Abdeckung,
- vollständige Schema-/Modell- und Test-Traceability,
- grüne GitHub-Referenz- und CI-Abnahme,
- keine bekannte offene P0/P1-Lücke.

Es bedeutet nicht, ohne empirischen Lauf zu behaupten, jeder denkbare LLM-Host oder GitLab-Connector verhalte sich identisch. Solche externen Evidenzgrenzen werden separat und ausdrücklich ausgewiesen; sie dürfen die Implementierungsabdeckung nicht verschleiern.

## 4. Definition of Done

Der Release Candidate ist fertig, wenn:

- alle elf Arbeitspakete abgeschlossen sind;
- alle 33 Anforderungen einen implementierten Vertrag und automatisierten Test besitzen;
- Framework-, Domain-, Lizenz- und Paketkompatibilität regressionsfrei bleibt;
- das Referenzprojekt migriert und validiert ist;
- die End-to-End-Kette einschließlich negativer Fälle grün ist;
- generierte Single-File-Bundles reproduzierbar sind;
- der Abschluss-PR den exakten geprüften Head enthält.
