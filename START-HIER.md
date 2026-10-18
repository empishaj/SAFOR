# SAFOR – einfache Anleitung

> Aktuelle Version: **0.14.0-rc.5 (Release Candidate)**  
> Du musst keine JSON-Datei öffnen oder verstehen. Wenn SAFOR Dateien in Git speichern soll, braucht dein Chat lediglich Zugriff auf dein Git-Projekt.

## 1. Wähle, was du machen willst

| Dein Ziel | Diese Datei(en) lädst du in **einen** Chat |
|---|---|
| Website erstellen | `SAFOR-FRAMEWORK-WEBSITE.json` |
| Software / SaaS testen | `SAFOR-FRAMEWORK-SAAS.json` + `SAFOR-TEST-ACCESS-SAAS.json` |
| Buch testen | `SAFOR-FRAMEWORK-BOOK-CREATION.json` + `SAFOR-TEST-ACCESS-BOOK-CREATION.json` |

**Wichtig:** SaaS und Buch sind aktuell öffentliche Testpfade. Die Testdateien sind keine Produktionslizenz.

## 2. Lade nur die passenden Dateien hoch

Lade nicht Website, SaaS und Buch gleichzeitig.

Du musst die Dateien nicht bearbeiten. Lade sie unverändert in den Chat.

## 3. Sende diesen Starttext

Kopiere nach dem Hochladen genau diesen Text:

```text
Arbeite mit dem geladenen SAFOR-Framework.
Führe mich in einfacher Sprache Schritt für Schritt.
Nutze den bereits gewählten Bereich und frage mich nicht noch einmal, ob ich Website, SaaS oder Buch erstellen möchte.
Frage mich nur Dinge, die du nicht sicher aus meinen Antworten ableiten kannst.
Erkläre mir einen Stopp kurz und verständlich.
```

Danach beschreibst du dein Vorhaben ganz normal in deinen eigenen Worten.

## 4. Beantworte nur die Fragen des MASTER

Der **MASTER** ist dein Hauptchat und dein einziger Ansprechpartner für fachliche Fragen.

Du musst keine technischen Rollen, Dateien oder Arbeitsaufträge selbst koordinieren. SAFOR soll diese Dinge aus deinen Angaben ableiten.

Wenn der MASTER eine echte Entscheidung von dir braucht, beantwortest du sie. Wenn keine Entscheidung nötig ist, soll SAFOR weiterarbeiten, ohne dich mit Technik zu belasten.

## 5. Wenn SAFOR einen Subagenten braucht

Manche Aufgaben kann der MASTER an einen Hilfs-Chat, einen sogenannten Subagenten, geben.

Dann läuft es so:

1. Der MASTER richtet den Agenten einmal ein.
2. Falls nötig, gibt dir der MASTER einen Initialisierungstext für einen neuen Agenten-Chat.
3. Diesen Text fügst du **einmal** in den neuen Agenten-Chat ein.
4. Der MASTER legt spätere Jobs selbst in die persönliche **INBOX** dieses Agenten.
5. Wenn der MASTER dir sagt, dass der Agent startbereit ist, schreibst du im Agenten-Chat nur:

```text
GO
```

6. Der Agent holt seinen Job selbst aus seiner INBOX und arbeitet daran.
7. Das fachliche Ergebnis geht zurück an den MASTER. Du musst den Job nicht zwischen Chats kopieren.

**Merksatz:**  
**MASTER schreibt den Job in die INBOX. Du schreibst nur GO. Der Agent holt den Job selbst ab.**

## 6. Wenn SAFOR stoppt

Ein Stopp ist nicht automatisch ein Fehler.

SAFOR soll stoppen, wenn zum Beispiel:

- ein benötigter Git-Zugriff fehlt,
- eine Datei nicht zur gewählten Domain passt,
- ein Agent nicht eindeutig zu seinem Job passt,
- eine notwendige Freigabe von dir fehlt.

Dann gehst du zurück zum **MASTER** und lässt dir in normaler Sprache sagen, was fehlt und was du als Nächstes tun sollst.

## 7. Diese Dinge musst du nicht tun

Du musst **nicht**:

- JSON lesen oder bearbeiten,
- Jobtexte zwischen Chats kopieren,
- technische IDs verstehen,
- Prüfsummen vergleichen,
- Git-Zustände selbst auswerten,
- mit Subagenten fachlich diskutieren.

Wenn SAFOR dich dazu zwingt, obwohl es die Information selbst ableiten kann, ist das ein Produkt- oder Usability-Problem.

## Kurzfassung

**Website:** eine Website-Datei hochladen.  
**SaaS-Test:** SaaS-Framework + SaaS-Testzugang hochladen.  
**Buch-Test:** Buch-Framework + Buch-Testzugang hochladen.  
**Dann:** Starttext senden, Fragen des MASTER beantworten.  
**Subagent:** Initialisierung einmal einfügen, danach bei freigegebenem Job nur `GO`.  
**Bei Problemen:** zurück zum MASTER.
