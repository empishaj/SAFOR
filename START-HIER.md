# SAFOR testen – Start hier

Diese Anleitung ist für Menschen gedacht, die SAFOR **verwenden**. Du musst die JSON-Dateien weder bearbeiten noch technisch verstehen. Die genaue Release-Candidate-Version steht in [`VERSION`](VERSION).

## Die wichtigste Produktgrenze

SAFOR ist eine JSON-basierte Arbeits- und Orchestrierungsanleitung für einen kompatiblen LLM-Chat. Du lädst das passende Domain-Framework in einen normalen Chat. Das Sprachmodell interpretiert die eingebetteten Verträge und nutzt ausschließlich die Werkzeuge, die der Chat tatsächlich bereitstellt.

Für diese normale Nutzung musst du **keine zusätzliche SAFOR-Runtime, keinen Daemon und keine separate Benutzeroberfläche installieren**.

Die Python-Module unter `runtime/` sind optionale Referenzimplementierungen für CI, Tests und Hosts, die Regeln zusätzlich maschinell erzwingen wollen. Ein normaler Chat führt diese Module nicht automatisch aus. Deshalb gilt weiterhin:

- JSON kann keine Providerrechte erzeugen.
- Ein Chat muss die benötigten Git-/Dateiwerkzeuge tatsächlich besitzen.
- Branch-Protection, CI, Reviews und optionale Hostadapter können die deklarativen Regeln technisch verstärken.
- Fehlende maschinelle Erzwingung darf nie als vorhandene technische Sperre ausgegeben werden.

## 1. Wähle genau einen Produktpfad

| Pfad | Dateien, die du in denselben Chat lädst | Anzahl | Zugriffsart |
|---|---|---:|---|
| Website | `SAFOR-FRAMEWORK-WEBSITE.json` | 1 | kostenlos |
| Software / SaaS testen | `SAFOR-FRAMEWORK-SAAS.json` **und** `SAFOR-TEST-ACCESS-SAAS.json` | 2 | öffentlicher Testzugang |
| Buch testen | `SAFOR-FRAMEWORK-BOOK-CREATION.json` **und** `SAFOR-TEST-ACCESS-BOOK-CREATION.json` | 2 | öffentlicher Testzugang |

Das Domain-Framework enthält den SAFOR-Kern, die passende Factory und das passende Operating Model. Beim SaaS- und Buch-Test ist die zweite Datei ausschließlich der Test-Zugriffsnachweis. Sie ist weder eine weitere Factory noch ein weiteres Operating Model.

Lade nicht gleichzeitig Website-, SaaS- und Buch-Frameworks. SAFOR soll genau eine aktive Domain besitzen.

## 2. Sende den Startauftrag

```text
Arbeite mit dem geladenen SAFOR-Domain-Framework.
Prüfe zuerst Framework, eingebettete Factory, Operating Model und – falls vorhanden – den Test-Zugriffsnachweis.
Verwende die durch die Datei bereits festgelegte Domain und frage mich nicht erneut, ob ich Website, SaaS oder Buch erstellen möchte.
Führe mich danach in verständlicher Sprache Schritt für Schritt durch die Einrichtung meines eigenen Git-Projekts und die fachliche Discovery.
Verändere nichts im öffentlichen SAFOR-Repository.
```

Danach beschreibst du dein Ziel in normaler Sprache. Beispiele:

```text
Ich möchte eine SaaS-Anwendung entwickeln, mit der kleine Unternehmen ihre Wartungsverträge verwalten können.
```

```text
Ich möchte ein Fachbuch über systemische KI-Integration für Engineering-Führungskräfte erstellen.
```

## 3. MASTER und Subagenten

Der **MASTER** ist deine einzige fachliche und organisatorische Schnittstelle. Mit ihm besprichst du Ziel, Planung, Roadmap, Status, Risiken, Freigaben und Konfliktentscheidungen.

Für einen neuen Subagenten erstellt der MASTER einmalig einen Initialisierungsprompt. Diesen fügst du einmal in einen eigenen, fortgeführten Agenten-Chat ein. Danach gilt für jeden Folgejob:

```text
GO
```

Nur dieses bewusste HUMAN-`GO` startet einen normalen Agenten-Chat. Ein Git-Push, ein Scheduler, Polling, eine Automation oder ein Host-Ereignis startet ihn nicht.

Der Subagent lädt nach `GO` selbst:

1. seine gepinnte Identität,
2. seinen kleinen persönlichen Inbox-Index,
3. den konkret zugewiesenen Job,
4. den autoritativen MASTER-Jobstatus,
5. nur die im Job referenzierten Eingaben.

Er erhält keinen neuen Fachprompt vom HUMAN. Fachliche Rückfragen, Fehler, Konflikte und Ergebnisse schreibt er als typisierte Git-Responses an den MASTER. Im Agenten-Chat zeigt er nur eine kurze Start-, Abschluss-, Blocker- oder Reidentifikationsmeldung.

## 4. Daran erkennst du einen korrekten Projektstart

SAFOR muss:

1. die bereits ausgewählte Domain aus der Domain-Datei erkennen;
2. Factory und Operating Model auf Integrität und Kompatibilität prüfen;
3. beim SaaS- oder Buch-Test ausschließlich den exakt passenden Testzugang binden;
4. ausdrücklich erklären, dass der Testzugang keine Produktionsberechtigung erteilt;
5. nicht erneut nach Website, SaaS oder Buch fragen;
6. ein eigenes Remote-Git- oder – bei real vorhandenen lokalen Werkzeugen – Local-Git-Projekt verwenden;
7. das öffentliche Repository `empishaj/SAFOR` niemals als dein Arbeitsprojekt verwenden;
8. tatsächliche Provider- und Schreibrechte prüfen, statt sie aus JSON abzuleiten;
9. erst nach erfolgreicher Workspace-Prüfung mit der fachlichen Discovery beginnen;
10. nur Informationen erfragen, die nicht sicher aus dem vorhandenen Kontext ableitbar sind;
11. Stopps, Blocker und den kleinsten notwendigen nächsten Schritt verständlich erklären.

Beim erfolgreichen öffentlichen SaaS- oder Buch-Test ist der technische Übergang:

```text
PUBLIC_EVALUATION_ACCESS_RESOLVED
→ SELECT_PROJECT_WORKSPACE_TYPE
```

Diese technischen Bezeichner dürfen im normalen Dialog hinter einer verständlichen Zusammenfassung verborgen bleiben.

## 5. Daran erkennst du einen korrekten Agentenlauf

Nach `GO` erscheint höchstens eine kurze Meldung wie:

```text
GO bestätigt | Agent: Nova Dev (agent-dev-003) | Job: WP-014-IMPL | Status: RUNNING | Zielbranch: safor/job/wp-014/agent-dev-003
```

Bei Abschluss:

```text
Job WP-014-IMPL abgeschlossen | Status: SUBMITTED | Ergebnis: <Git-Referenz>
```

Bei Blockierung:

```text
Job WP-014-IMPL blockiert | Status: BLOCKED | Meldung: <Git-Referenz> | MASTER-Klärung erforderlich
```

Ein Subagent darf nicht im Chat mit dir über fachliche Details verhandeln. Du fragst den MASTER nach Status und Entscheidungen.

## 6. Schnelle Akzeptanztests

### Test A – korrekter SaaS-Pfad

Lade `SAFOR-FRAMEWORK-SAAS.json` und `SAFOR-TEST-ACCESS-SAAS.json`.

Erwartung: SAFOR akzeptiert ausschließlich die vorgesehenen SaaS-Testpakete, kennzeichnet den Zugriff als Test und wechselt zur Workspace-Auswahl.

### Test B – fehlender Testzugang

Lade nur `SAFOR-FRAMEWORK-SAAS.json`.

Erwartung: SAFOR startet die bezahlten Module nicht stillschweigend. Es fordert den passenden Testzugang an und bleibt in einem sicheren Wartezustand.

### Test C – falscher Testzugang

Lade `SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-BOOK-CREATION.json`.

Erwartung: SAFOR lehnt die Kombination wegen Domain-, Creation-Type-, Distribution- und Paketversionskonflikten ab.

### Test D – unpassender Modulaustausch

Starte den Buch-Pfad und versuche anschließend, ein SaaS-Operating-Model als Ersatz zu laden.

Erwartung: SAFOR lehnt den Austausch ab und behält die letzte gültige Buch-Bindung.

### Test E – Agent ohne `GO`

Öffne einen initialisierten Agenten-Chat, aber sende nicht `GO`.

Erwartung: Der Agent claimt keinen Job und verändert kein Repository.

### Test F – Agent mit Rollen- oder Rechtekonflikt

Sende `GO`, während Rolle, Skill, gepinnter Input oder tatsächliches Schreibrecht nicht passt.

Erwartung: Der Agent stoppt vor unzulässiger Produktmutation, schreibt eine typisierte Response an den MASTER und zeigt nur den knappen `BLOCKED`-Status.

## 7. Typische Fehler vermeiden

- Verwende als Endanwender das Domain-Framework, nicht die generische Engineering-Distribution.
- Bearbeite die JSON-Dateien nicht; Änderungen können Integritätsprüfungen ungültig machen.
- Verwende dein eigenes Git-Projekt. Das SAFOR-Repository ist Produktquelle, nicht dein Arbeitsbereich.
- Interpretiere den öffentlichen Testzugang nicht als Kauf- oder Produktionsnachweis.
- Lade genau eine Domain und gegebenenfalls deren passenden Zugriffsnachweis.
- Kopiere keine Jobtexte zwischen MASTER- und Agenten-Chats. Nach der einmaligen Initialisierung reicht `GO`.

## 8. Kaufversion und technische Durchsetzung

Die öffentlichen Testdateien setzen ausdrücklich:

```text
productionAuthorization = false
```

Sie können keine Produktionslizenz ersetzen. Eine spätere Kaufversion verwendet verifizierte Entitlement- und Liefernachweise für die exakte Paketversion.

Optionale Hostadapter können Lizenz-, Integritäts-, Claim- und Zustandsregeln zusätzlich maschinell erzwingen. Diese Verstärkung ändert nicht das Endkundenerlebnis: SAFOR bleibt im normalen kompatiblen Chat über die geladenen JSON-Verträge nutzbar.
