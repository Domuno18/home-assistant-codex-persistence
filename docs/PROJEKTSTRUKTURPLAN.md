# Projektstrukturplan

## Struktur

```text
AP-100 Auftrag, Anforderungen und Domänenmodell
AP-200 Architektur, Schnittstellen und Sicherheit
AP-300 Implementierung und Add-on-Integration
AP-400 Verifikation und reale Abnahme
AP-500 Dokumentation, Übergabe und Betrieb
```

ISA-95 und mathematische Modellierung sind für dieses Projekt nicht
anwendbar. Es gibt keine zusätzlichen Modellierungspakete.

## Arbeitspakete

| AP-ID | Ergebnis | Verantwortliche Rolle | Abhängigkeit | Deckt ab | Abnahme | Status |
|---|---|---|---|---|---|---|
| AP-100 | bestätigter Intake, Projektauftrag, User-Storys, Anforderungen und Domänenmodell | Repository-Projektpflege | keine | US-001 bis US-003, REQ-F-001 bis REQ-O-004 | Dokumentreview und Traceability-Prüfung | abgeschlossen |
| AP-200 | Architektur für Standard- und Referenzpfad, dokumentierte Schnittstellen, fail-closed Regeln und Security-Konzept | Repository-Projektpflege | AP-100 | REQ-I-001 bis REQ-I-004, REQ-Q-001 bis REQ-S-002, RISK-001 bis RISK-007 | Architektur- und Security-Review | abgeschlossen |
| AP-300 | portable Shell-Implementierung für `install`, `boot`, `audit`, persistente Programme, Git-Helper und Supervisor-Integration einschließlich selektiver `gh`-Pakettransition | Projektentwicklung | AP-200 | REQ-F-001, REQ-F-002, REQ-F-005, REQ-I-001, REQ-I-002, REQ-I-004, REQ-Q-001 bis REQ-O-004 | TC-001 bis TC-010, TC-016, TC-017 und TC-DOM-001 | einschließlich Pakettransition und Git-Helper-Bindung implementiert |
| AP-400 | automatisierte Nachweise, Secret-Scan, Supervisor-Vertrag und reale Neustart-/Container-Abnahme | technischer Prüfer und Referenzbetreiber | AP-300 | alle Muss-Anforderungen und AC-001 bis AC-012 | TC-SEC-001, TC-016, TC-017 sowie TC-012 | isolierte Tests einschließlich TC-016 und TC-017 abgeschlossen; TC-012 ausstehend |
| AP-500 | README, Installations-, Deployment-, Betriebs-, Memory- und Übergabedokumentation | Repository-Projektpflege und Betreiber | AP-100 bis AP-400 | REQ-F-003, REQ-F-004, REQ-I-003, REQ-I-004, REQ-O-002 bis REQ-O-004 | Dokumentreview und Betriebsfreigabe | Dokumentation abgeschlossen; Betriebsfreigabe folgt TC-012 |

## Liefergegenstände

### AP-100

- `project-definition.json`, `INTAKE.md` und Projekt-Steckbrief,
- Projektauftrag und User-Storys,
- atomare REQ-/AC-Anforderungen,
- Domänenobjekte, Invarianten und Zustände.

### AP-200

- Systemkontext und Schnittstellen,
- Architektur für `/data/codex-persistence` und `/config/Codex/.runtime`,
- Datenschutz-, Secret- und Fehlersicherheitsregeln,
- klare Grenze zu `/data/vscode`, Projekten und realer Memory-Datei.

### AP-300

- `scripts/ha-codex-persistence.sh`,
- einmalige stabile und geprüfte Übernahme durch `install`,
- automatischer idempotenter `boot`,
- read-only `audit`,
- persistente Bootstrap- und CLI-Programme,
- selektive Entfernung nur der `gh`-/`github-cli`-Bootstrap-Pakete bei Erhalt
  fremder Pakete und Befehle,
- deduplizierter, an erster Stelle stehender Eintrag in Add-on-`init_commands`.
- gezielte, idempotente Bindung nur der zwei GitHub-Credential-Helper bei Erhalt
  aller anderen Git-Einstellungen.

### AP-400

- isolierte Integrationstests mit künstlichen Daten,
- Konflikt-, Spezialdatei-, Prüfsummen- und Authentifizierungsfehlerfälle,
- TC-017 für bekannte Git-Helper-Migration und fail-safe Blockierung fremder
  Helper,
- Struktur-, Traceability- und Secret-Scan,
- Supervisor-Test für Pakettransition, Befehlsreihenfolge und Offline-Start von
  persistentem `gh`,
- reale TC-012-Abnahme nach Neustart und Container-Neuerstellung.

### AP-500

- einfache Fünf-Schritte-Installation,
- sichere Beispielkonfiguration,
- Betriebs- und Störungsanleitung,
- neutrale Memory-Vorlage,
- Deployment-, Release- und Veröffentlichungsgrenzen.

## Vollständigkeitsprüfung

- [x] jedes Lieferergebnis einem Arbeitspaket zugeordnet
- [x] jede Muss-Anforderung durch mindestens ein Arbeitspaket abgedeckt
- [x] Verantwortliche Rollen und Abhängigkeiten geklärt
- [x] isolierte Tests und Security-Scan erfolgreich
- [x] selektive Pakettransition im Skript implementiert
- [x] gezielte Git-Helper-Bindung und TC-017 automatisiert
- [x] automatisierter Supervisor-Nachweis TC-016 erfolgreich
- [ ] TC-012 auf dem realen Referenzsystem abgeschlossen
- [ ] Betriebs- und öffentliche Freigabe erteilt
