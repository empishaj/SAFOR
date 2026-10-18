# SAFOR 0.14.0-rc.2 – Audit-Delta und Integrationsauftrag

## Gepinnte Basis

- rc.9 `main`: `29a9bcc5c84fe348f94c63b08852fda28135fe50`
- auditierter v0.14-Quellstand: `cd6aa12605d208b96c4d19c95b7eb9756624c113`
- Integrationszweig: `safor/integrate-v0.14.0-rc.2`

## Integrationsregel

Der v0.14-Quellzweig wird nicht blind gemergt. Vorhandene rc.8/rc.9-Verträge bleiben Ausgangsbasis; v0.14-Modelle, Schemas, Referenzcode und Tests werden selektiv übernommen und gegen die Auditbefunde F-01 bis F-12 gehärtet.

## Freigabe

Die aktuelle HUMAN-Anweisung autorisiert die schrittweise Implementierung. Ein Release-Merge bleibt an den exakten grünen Head, nachvollziehbare Evidence und die ausgewiesenen Review-/Governance-Gates gebunden.
