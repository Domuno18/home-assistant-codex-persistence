# Backlog

> Operative Restarbeit und spätere Verbesserungen. Verbindlicher Umfang und
> Traceability stehen im Projektstrukturplan und in der Nachweismatrix.

## In Arbeit

- [ ] BL-001 — Host-Neustart; Add-on-Update/Container-Neuerstellung als zukünftiger Regressionstest als
      Rest der TC-012-Abnahme durchführen. Der Add-on-Neustart ist bestätigt.
      Quellen: REQ-O-004, AC-001 bis AC-012.
## Erledigt

- [x] BL-015 — SemVer-Strategie, private Beta und separate
      Veröffentlichungsentscheidung dokumentiert. Quelle: REQ-S-002.
- [x] BL-014 — TC-016 automatisiert: gehärteter Supervisor-Transport,
      selektive Pakettransition, Erhalt fremder Optionen, Konkurrenzabbruch und
      Read-back vor `ACTIVE`. Quellen: REQ-I-001, REQ-O-004, DOM-R-009,
      AC-009, AC-010.
## Nach der realen Abnahme

- [x] BL-003 — Betriebsstatus und bisherigen TC-012-Nachweis dokumentiert, ohne Chats,
      Anmeldedaten oder reale Memory-Inhalte aufzunehmen.
- [x] BL-004 — Public-Release-Check vollständig durchgeführt; sauberes
      öffentliches Repository und `v0.9.0-beta.1`-Prerelease nach ausdrücklicher
      Freigabe veröffentlicht. Quelle: REQ-S-001, REQ-S-002.

## Spätere Verbesserungen

- BL-005 — Geprüften, atomaren Upgrade- und Rollback-Ablauf für persistierte
  Codex- und GitHub-CLI-Programme entwerfen. Version, Prüfsumme, Architektur
  und Kompatibilität werden vor Aktivierung geprüft; ein temporäres
  Bootstrap-Paket wird anschließend wieder entfernt. `boot` bleibt netz- und
  upgradefrei. Quelle: RISK-007.
- BL-006 — Optionalen verschlüsselten Backup-/Restore-Nachweis für die private
  Runtime untersuchen. Quelle: RISK-005.
- BL-007 — TC-015 zum maschinellen Nachweis eines vollständig mutationsfreien
  Audit-Laufs automatisieren. Quelle: REQ-O-002.

## Erledigt

- [x] BL-002 — Privates GitHub-Repository
      `home-assistant-codex-persistence` erstellt, validierten Stand gepusht und
      private Sichtbarkeit technisch geprüft. Quelle: REQ-S-002.
- [x] BL-008 — Projekt aus Projektvorlage_20 initialisiert.
- [x] BL-009 — Anforderungen, Domänenmodell, Architektur, Schnittstellen,
      Security, Betrieb und Traceability projektspezifisch dokumentiert.
- [x] BL-010 — `install`, automatisches `boot` und read-only `audit`
      implementiert.
- [x] BL-011 — Container-Neuerstellung, Konflikte, beschädigte Programme,
      Spezialdateien und fehlende Anmeldungen isoliert getestet.
- [x] BL-012 — Neutrale Memory-Vorlage ohne reale Inhalte erstellt.
- [x] BL-013 — Working Tree auf Secrets geprüft und Projektvalidierung
      erfolgreich ausgeführt.
