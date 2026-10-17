# SAFOR 0.13.0 — Composable Domain Package Contract

## Ziel

SAFOR selbst bleibt das öffentliche, in einen Chat ladbare Framework. Factory und Operating Model sind davon unabhängige, jeweils eigenständig ladbare JSON-Produkte.

Das Produktmodell lautet damit:

`SAFOR Framework JSON + genau eine ausgewählte Factory JSON + genau ein ausgewähltes Operating Model JSON + optional externe Entitlement-Evidenz + HUMAN-Projektworkspace`.

## Zentrale Produktregeln

1. Eine Factory ist ein eigenständiges JSON-Artefakt.
2. Ein Operating Model ist ein eigenständiges JSON-Artefakt.
3. Beide können unabhängig voneinander kostenlos oder kostenpflichtig sein.
4. Der Besitz einer kostenpflichtigen JSON-Datei ist kein Lizenznachweis.
5. Entitlement-Evidenz wird nicht in das Package eingebettet, sondern separat verifiziert.
6. Die kostenlose Website-Erstellung nutzt standardmäßig die öffentliche Starter-Factory und das öffentliche Starter-Operating-Model.
7. Der HUMAN darf später nur die Factory, nur das Operating Model oder beide ersetzen.
8. Ein gemischtes Paar aus kostenlosem und kostenpflichtigem Package ist zulässig.
9. Jeder ausgewählte Package-Zugriff wird separat geprüft.
10. Vor Bindung muss die Factory/Operating-Model-Kombination deterministisch als kompatibel bewertet werden.
11. Package-Quellen sind niemals Projekt-Workspaces.
12. Projektartefakte verbleiben ausschließlich im HUMAN-kontrollierten Remote- oder Local-Git-Workspace.

## Warum die 0.12-Struktur nicht genügte

0.12 koppelte einen Creation Type faktisch an ein festes Factory/Operating-Model-Paar und an einen gemeinsamen Access Mode. Das ist für ein späteres Produktportfolio zu eng: Eine kostenlose Website-Factory könnte beispielsweise mit einem gekauften Enterprise Operating Model kombiniert werden oder ein kostenloses Operating Model mit einer Premium Factory.

0.13 verschiebt deshalb die Zugriffsentscheidung vom Creation Profile auf jedes einzelne Package.

## Domain-Package-Artefakt

Jedes Package verwendet `format = SAFOR_DOMAIN_PACKAGE` und enthält:

- Identität: `packageId`, `packageKind`, `version`.
- Commercial Contract: Access Mode, SKU und die Festlegung, dass Entitlement extern bleibt.
- Framework-Kompatibilität: minimale und exklusive maximale Framework-Version.
- Creation-Type-Unterstützung.
- Counterpart-Anforderungen: benötigte Capabilities und Authorities.
- Exporte.
- Dependencies.
- Model Payload.
- Integritätsdaten.

Der Digest `contentDigest` wird über den **DECLARED_DOMAIN_CONTRACT** gebildet. Diese Projektion besteht aus:
`packageId`, `packageKind`, `version`, `commercial`, `compatibility`, `exports`, `dependencies` und `model`.
Die Serialisierung ist `SAFOR_CANONICAL_JSON_V1`: UTF-8 JSON, Objekt-Keys rekursiv lexikografisch sortiert, keine unnötigen Whitespaces.

## Lizenzgrenze

Ein PAID-Package enthält keine selbstbehauptete Freischaltung. SAFOR benötigt zusätzlich eine verifizierte Entitlement-Evidenz, die exakt `packageId` und Version abdeckt. Das Entitlement verändert keine Rollen, keine organisatorischen Entscheidungsrechte, keine Provider-Rechte und keinen Projekt-Scope.

## Komposition

Creation Profiles definieren nur noch Default-Packages. Sie dürfen kompatible Alternativen zulassen. Die Auflösung erfolgt separat:

`Factory auswählen -> Factory-Zugriff prüfen -> Operating Model auswählen -> OM-Zugriff prüfen -> Integrität prüfen -> Framework-Kompatibilität prüfen -> Pair-Kompatibilität prüfen -> immutable Binding`.

Damit wird das von SAFOR angestrebte Produktmodell explizit unterstützt: kostenlose Einstiegspfade plus unabhängig kaufbare, höherwertige oder spezialisierte Factory- und Operating-Model-Pakete.
