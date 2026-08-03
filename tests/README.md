# Tests

- `domain/`: Fachregeln, Wertobjekte und Invarianten
- `model/`: Einheiten, Gleichungen, Referenz- und Grenzfälle
- `unit/`: kleine technische Einheiten
- `integration/`: Adapter, Verträge und Ausfallverhalten
- `architecture/`: erlaubte Abhängigkeitsrichtungen
- `acceptance/`: bestätigte Auftraggeber-Szenarien

Ein Test zählt nur mit konkretem Prüforakel und Bezug zu `REQ-*`, `DOM-*`,
`AC-*` oder `RISK-*` als Nachweis.
