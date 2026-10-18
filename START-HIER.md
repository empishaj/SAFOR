# SAFOR testen – Start hier

Diese Anleitung ist für Menschen gedacht, die SAFOR **verwenden**, nicht technisch analysieren wollen. Du musst keine JSON-Datei öffnen, bearbeiten oder verstehen.

> Produktstatus: **SAFOR v0.14.0-rc.2 ist ein Release Candidate.** Die öffentlichen SaaS- und Buch-Dateien dienen ausschließlich dem Produkttest und sind keine Produktionslizenz.

## Ausführungsmodell

SAFOR ist ein **deklaratives JSON-Produkt für gewöhnliche kompatible LLM-Chats**. Du lädst das passende Domain-Framework in den Chat; eine zusätzlich auf deinem Rechner oder beim Endkunden zu installierende SAFOR-Runtime ist **nicht erforderlich**.

Ein normaler Chat führt den Python-Referenzcode nicht automatisch aus. Das ist keine Installationsvoraussetzung: Der Chat interpretiert den eingebetteten SAFOR-Vertrag und nutzt ausschließlich die Werkzeuge und Git-Rechte, die der Host tatsächlich bereitstellt. Die Python-Module unter `runtime/` sind optionale Referenz-, Prüf- und Hostintegrationsimplementierungen. Sie dürfen technische Durchsetzung verstärken, sind aber keine Voraussetzung für den normalen Chatbetrieb.

Die Grenze bleibt transparent: JSON kann keine fehlenden Connector-Rechte erzeugen und keinen nichtkonformen Chat-Host technisch zwingen. SAFOR verlangt deshalb Provider-Readback, Git-Nachweise, Reviews und fail-closed Stopps, ohne daraus eine Installationspflicht abzuleiten.

## 1. Entscheide, was du erstellen möchtest

| Pfad | Dateien, die du in denselben Chat lädst | Anzahl | Zugriffsart |
|---|---|---:|---|
| Website | `SAFOR-FRAMEWORK-WEBSITE.json` | 1 | kostenlos |
| Software / SaaS testen | `SAFOR-FRAMEWORK-SAAS.json` **und** `SAFOR-TEST-ACCESS-SAAS.json` | 2 | öffentlicher Testzugang |
| Buch testen | `SAFOR-FRAMEWORK-BOOK-CREATION.json` **und** `SAFOR-TEST-ACCESS-BOOK-CREATION.json` | 2 | öffentlicher Testzugang |

Die Domain-Framework-Datei enthält bereits das SAFOR-Framework, die passende Factory und das passende Operating Model. Bei den bezahlten Pfaden ist die zweite Datei **nur der Test-Zugriffsnachweis**. Sie ist keine weitere Factory und kein weiteres Operating Model.

## 2. Lade nur die Dateien deines gewählten Pfades

Für einen SaaS-Test lädst du gemeinsam hoch:

- `SAFOR-FRAMEWORK-SAAS.json`
- `SAFOR-TEST-ACCESS-SAAS.json`

Für einen Buch-Test lädst du gemeinsam hoch:

- `SAFOR-FRAMEWORK-BOOK-CREATION.json`
- `SAFOR-TEST-ACCESS-BOOK-CREATION.json`

Für eine Website lädst du nur `SAFOR-FRAMEWORK-WEBSITE.json` hoch.

Lade nicht gleichzeitig Website-, SaaS- und Buch-Frameworks. SAFOR soll genau eine aktive Domain besitzen.

## 3. Sende diesen Startauftrag

Kopiere nach dem Hochladen der Datei oder Dateien folgenden Text in den Chat:

```text
Arbeite mit dem geladenen SAFOR-Domain-Framework.
Prüfe zuerst Framework, eingebettete Factory, Operating Model und – falls vorhanden – den Test-Zugriffsnachweis.
Verwende die durch die Datei bereits festgelegte Domain und frage mich nicht erneut, ob ich Website, SaaS oder Buch erstellen möchte.
Führe mich danach in verständlicher Sprache Schritt für Schritt durch die Einrichtung meines eigenen Git-Projekts und die fachliche Discovery.
Verändere nichts im öffentlichen SAFOR-Repository.
```

Danach beschreibst du dein Vorhaben in normaler Sprache, zum Beispiel:

```text
Ich möchte eine SaaS-Anwendung entwickeln, mit der kleine Unternehmen ihre Wartungsverträge verwalten können.
```

oder:

```text
Ich möchte ein Fachbuch über systemische KI-Integration für Engineering-Führungskräfte erstellen.
```

Die sichtbare Kommunikation wird zentral durch die SAFOR-Plattform verdichtet. Factory und Operating Model liefern fachliche Fakten, dürfen aber weder die Antwortlänge noch Menüs oder technische Detailtiefe bestimmen. Reine Statusmeldungen wie eine erkannte Framework-Änderung bleiben kurz; Details erscheinen nur auf Nachfrage oder bei einer echten Entscheidung.

## 4. Daran erkennst du einen korrekten Start

SAFOR muss sich in dieser Reihenfolge verhalten:

1. Es erkennt die bereits ausgewählte Domain aus der Domain-Framework-Datei.
2. Es prüft die Integrität der eingebetteten Factory und des eingebetteten Operating Models.
3. Beim SaaS- oder Buch-Test bindet es ausschließlich den exakt passenden Test-Zugriffsnachweis.
4. Es bestätigt ausdrücklich, dass der Testzugang **keine Produktionsberechtigung** erteilt.
5. Es fragt nicht erneut nach Website, SaaS oder Buch.
6. Es fragt, ob dein Projekt in einem eigenen Remote-Git-Repository oder in einem lokalen Git-Projekt liegen soll.
7. Es verwendet das öffentliche Repository `empishaj/SAFOR` niemals als dein Projekt-Repository.
8. Erst nach erfolgreicher Workspace-Prüfung beginnt die fachliche Discovery.
9. Es stellt nur Fragen, die es nicht sicher aus deinen bisherigen Angaben ableiten kann.
10. Es erklärt Stopps und notwendige nächste Schritte in verständlicher Sprache.

Beim erfolgreichen öffentlichen SaaS- oder Buch-Test lautet der technische Übergang:

```text
PUBLIC_EVALUATION_ACCESS_RESOLVED
→ SELECT_PROJECT_WORKSPACE_TYPE
```

Diese technischen Bezeichner dürfen im normalen Dialog hinter einer verständlichen Zusammenfassung verborgen bleiben.

## 5. Vier schnelle Akzeptanztests

### Test A – korrekter SaaS-Pfad

Lade `SAFOR-FRAMEWORK-SAAS.json` und `SAFOR-TEST-ACCESS-SAAS.json`.

Erwartung: SAFOR akzeptiert ausschließlich die Factory `safor.factory.software-delivery@1.7.0-test.1` und das Operating Model `safor.om.saas-engineering@1.7.0-test.1`, kennzeichnet den Zugriff als Test und wechselt zur Workspace-Auswahl.

### Test B – fehlender Testzugang

Lade nur `SAFOR-FRAMEWORK-SAAS.json`.

Erwartung: SAFOR startet nicht stillschweigend mit den bezahlten Modulen. Es fordert konkret `SAFOR-TEST-ACCESS-SAAS.json` an und bleibt bis dahin in einem sicheren Wartezustand.

### Test C – falscher Testzugang

Lade `SAFOR-FRAMEWORK-SAAS.json` zusammen mit `SAFOR-TEST-ACCESS-SAAS.json`.

Erwartung: SAFOR lehnt die Kombination wegen Domain-, Creation-Type-, Distribution- und Paketversionskonflikten ab. Es darf den Buch-Zugriff niemals für SaaS verwenden.

### Test D – unpassender Modulaustausch

Starte den Buch-Pfad und versuche anschließend, ein SaaS-Operating-Model als Ersatz zu laden.

Erwartung: SAFOR lehnt den Austausch ab und behält die letzte gültige Buch-Bindung. Ein Modulwechsel darf weder die aktive Domain stillschweigend ändern noch die Gegenstelle automatisch ersetzen.

## 6. Typische Fehler vermeiden

- Verwende als Endanwender die Domain-Datei und nicht `SAFOR-FRAMEWORK.json` oder `SAFOR-FRAMEWORK-v0.14.0-rc.2.json`. Diese generischen Dateien sind für Framework-Engineering und fortgeschrittene Auswahlabläufe gedacht.
- Bearbeite die JSON-Dateien nicht. Jede Änderung kann Integritäts- oder Zugriffsprüfungen ungültig machen.
- Verwende dein eigenes Git-Projekt. Das SAFOR-Repository ist Produktquelle, nicht Arbeitsbereich deines Vorhabens.
- Interpretiere den öffentlichen Testzugang nicht als Kauf- oder Produktionsnachweis.
- Lade für einen Test genau eine Domain und den dazugehörigen Zugriffsnachweis.

## 7. Unterschied zur späteren Kaufversion

Die Produktstruktur bleibt gleich: ein Domain-Framework enthält Framework, Factory und Operating Model. In der Kaufversion stammt der Zugriffs- und Liefernachweis jedoch aus einem geschützten, verifizierten kommerziellen Kanal und ist an den Käufer beziehungsweise die Organisation sowie an die exakte Paketversion gebunden.

Die öffentlichen Dateien `SAFOR-TEST-ACCESS-SAAS.json` und `SAFOR-TEST-ACCESS-BOOK-CREATION.json` setzen ausdrücklich:

```text
productionAuthorization = false
```

Sie können daher niemals eine produktive Lizenz ersetzen.
