# Testkonzept und Testfälle

## Ziel und Grundsätze

Die Tests müssen beweisen, dass eine einmal installierte Runtime einen
vollständigen Containerverlust übersteht, ohne dass unsichere Sonderfälle
automatisch repariert werden. Jeder Test verwendet ausschließlich künstliche
Sitzungs-, Anmelde-, Git-Konfigurations- und Memory-Daten.

- Jede Muss-Anforderung besitzt mindestens einen automatisierten Test,
  statischen Nachweis oder realen Abnahmetest.
- Mutierende Tests laufen nur in temporären Verzeichnissen mit explizitem
  Testmodus und berühren keine reale Runtime.
- Fehlerfalltests prüfen zusätzlich, dass Quellen und Konfliktdateien erhalten
  bleiben.
- Ein erfolgreicher Shell-Aufruf benötigt neben Exitcode `0` die erwarteten
  tabulatorgetrennten Diagnosezeilen.
- Ein realer Neustarttest wird erst nach erfolgreichem isoliertem Testlauf,
  Secret-Scan und read-only Audit durchgeführt.

## Testebenen

| Ebene | Inhalt | Umgebung |
|---|---|---|
| Struktur | Projektdateien, Traceability und neutrale Memory-Vorlage | Repository |
| Domäne | Invarianten zu Generation, Links, Konflikten und Befehlsgrenzen | temporäres Dateisystem |
| Integration | `install`, `boot`, `audit`, Programme und simulierte Container-Neuerstellung | Python-Testharness mit Testdoubles |
| Supervisor-Vertrag | atomare Optionsänderung, Paketfilter und Bootreihenfolge | Supervisor-Testdouble und reales Add-on |
| Security | Secret-Scan, Dateirechte, Pfadgrenzen und Prüfsummen | Repository und temporäres Dateisystem |
| System | realer Add-on-Neustart und Container-Neuerstellung | Home-Assistant-Referenzsystem |
| Abnahme | Chats, Anmeldungen, Projekte, Studio Code und Memory aus Nutzersicht | Home-Assistant-Referenzsystem |

## Automatisierte Integrations- und Fehlerfalltests

Die Testimplementierung liegt in `tests/test_codex_persistence.py`.

| ID | Prüft | Aktion | Erwartetes Ergebnis | Status |
|---|---|---|---|---|
| TC-001 | REQ-F-001, REQ-F-002, REQ-F-005, REQ-I-002, REQ-I-004, AC-001 bis AC-003, AC-005, AC-010, AC-012 | künstliche native Sitzung, dateibasierten Codex-Anmeldecache, dateibasiertes GitHub-Credential und persistente Add-on-Git-Konfiguration anlegen, `install` ausführen, gesamten Containerbaum löschen, aus der persistenten Bootstrap-Kopie `boot` und Auth-Audit ausführen | Sitzung, Konfiguration, Codex-Anmeldecache, aktive GitHub-Anmeldung, Programme und exakte geordnete GitHub-/Gist-Helper-Wertepaare sind persistent; Links zeigen auf `current`; der native IPC-Socket wird nicht kopiert | automatisiert |
| TC-002 | REQ-I-002, REQ-Q-003, DOM-R-003, AC-007 | `boot` ohne vorherige Installation aufrufen | Fehlercode mit `BLOCK`, kein `current`-Bestand und keine Links | automatisiert |
| TC-003 | REQ-Q-001, AC-006 | nach erfolgreicher Installation `boot` mehrfach sowie nach erneuter Container-Neuerstellung ausführen | jeder Lauf erfolgreich; Sitzungsinhalt und aktive Generation unverändert | automatisiert |
| TC-004 | REQ-Q-003, DOM-R-004, AC-007 | in einem neuen Container einen nicht leeren konkurrierenden Codex-Pfad anlegen und `boot` ausführen | Blockierung; Konfliktdatei bleibt erhalten; weder Codex- noch GitHub-Link wird gesetzt | automatisiert |
| TC-005 | REQ-F-005, REQ-Q-003, DOM-R-005, AC-007 | persistierte Codex-Programmdatei nach `install` verändern und `boot` ausführen | Prüfsummenfehler blockiert jede Aktivierung und jeden Werkzeuglink | automatisiert |
| TC-006 | REQ-Q-002, REQ-Q-003, AC-007, AC-009 | außerhalb des erlaubten IPC-Sockets eine FIFO in der Codex-Quelle anlegen und `install` ausführen | Installation blockiert; Quelle bleibt unverändert; keine aktive Generation | automatisiert |
| TC-007 | REQ-O-001, AC-002, AC-009 | Codex-Anmeldedatei vor `install` entfernen | Installation blockiert ohne Aktivierung oder Symlink | automatisiert |
| TC-008 | REQ-F-002, REQ-O-001, AC-003, AC-009 | GitHub-CLI-Anmeldedatei entfernen sowie separat ein nicht leeres `hosts.yml` ohne dateibasiertes Credential bei simuliert nutzbarem Container-Keyring bereitstellen | fehlende Datei und Keyring-only-Zustand blockieren jeweils ohne Aktivierung oder Symlink; ein Status über den flüchtigen Keyring genügt nicht | automatisiert |
| TC-009 | REQ-O-002, AC-002, AC-003, AC-007 | nach erfolgreichem `boot` beide Anmeldedateien entfernen und Auth-Audit ausführen | beide Anmeldungen als ungültig gemeldet; Exitcode für fehlende Authentifizierung | automatisiert |
| TC-010 | REQ-O-001, REQ-O-002 | einen nicht unterstützten vierten Lifecycle-Befehl aufrufen | Usage-Fehlercode; nur `install`, `boot`, `audit` und Versionsausgabe sind öffentlich | automatisiert |
| TC-016 | REQ-I-001, REQ-O-004, DOM-R-009, AC-009, AC-010 | Supervisor-Testdouble mit `gh`, Fremdpaket, fremden Optionen und `init_commands` bereitstellen; gehärtete GET/GET/POST/GET-Folge, Konkurrenz vor POST und abweichenden Read-back prüfen; anschließend Container ohne Quell-`gh` neu erzeugen | nur `gh`/`github-cli` verschwinden, Fremdbestand bleibt semantisch gleich, Bootbefehl steht zuerst; Konkurrenz sendet kein POST, abweichender Read-back erzeugt kein `ACTIVE`; persistiertes `gh` funktioniert nach Containerersatz | automatisiert |
| TC-017 | REQ-I-003, REQ-I-004, REQ-Q-003, REQ-O-002, DOM-R-007, DOM-R-010, AC-007, AC-009, AC-010, AC-012 | persistente Add-on-`.gitconfig` mit fremder Benutzerkonfiguration und getrennt mit fehlenden, leeren, bekannten alten sowie fremden benutzerdefinierten Werten für beide GitHub-Helper bereitstellen; `install`, simulierte Container-Neuerstellung, `boot` und `audit` ausführen | ausschließlich fehlende, leere und bekannte alte Werte werden je Schlüssel zum exakten geordneten Paar aus leerem Resetwert und persistentem `gh`-Helper migriert; fremde Git-Einstellungen sowie Modus und Eigentümer bleiben erhalten; ein fremder Helper bleibt unverändert und blockiert fail-safe; `audit` prüft ohne Mutation | automatisiert |

## Struktur-, Domänen- und Security-Tests

| ID | Prüft | Aktion | Erwartetes Ergebnis | Status |
|---|---|---|---|---|
| TC-011 | REQ-F-004, REQ-S-002, DOM-R-006, AC-011 | fehlende Memory-Dateien installieren; vorhandene künstliche Memory-Dateien erneut installieren; eine nicht leere globale `$CODEX_HOME/AGENTS.override.md` mit fremdem Inhalt bereitstellen; eine versiegelte Installation mit dem exakten offiziellen Altblock erneut installieren; Codex aus einem verschachtelten Git-Repository starten | fehlende Dateien entstehen atomar; vorhandene Memory-Dateien bleiben bytegenau; genau ein verwalteter Block mit absoluten Pfaden wird in der wirksamen Override-Datei ergänzt, ohne die vorhandene Bytefolge zu ersetzen; der offizielle Altblock bleibt bytegenau und upgradefähig; abweichende Blöcke werden abgelehnt; verschachtelter Start lädt die Regeln; keine privaten Inhalte gelangen in `examples/memory` | automatisiert und Review bestanden |
| TC-013 | REQ-I-002, REQ-Q-003, DOM-R-002, DOM-R-003 | nach erfolgreicher Installation den Active-Marker kontrolliert in Ready zurücksetzen, Container ersetzen und `boot` ausführen | vollständig verifizierte Ready-Generation wird atomar aktiv; Ready verschwindet; Links werden gesetzt | automatisiert |
| TC-014 | REQ-O-001, REQ-Q-003 | expliziten `sqlite_home` beziehungsweise Keyring-Credential-Store in künstlicher Codex-Konfiguration setzen | beide externen containerlokalen Speicherformen blockieren `install` vor `current` | automatisiert |
| TC-015 | REQ-O-002, DOM-R-008 | vor und nach `audit` vollständige Dateibaum-Manifeste der Runtime vergleichen | Byteinhalt, Links, Modi, Marker und Zeitstempel bleiben unverändert | geplant |
| TC-DOM-001 | DOM-R-001 bis DOM-R-010 | Positiv- und Negativfälle TC-001 bis TC-017 gemeinsam auswerten | nur eine vollständig verifizierte Generation wird aktiviert; jede verletzte Invariante blockiert; Pakettransition und gezielte Git-Helper-Bindung folgen ihren getrennten Verträgen | automatisiert; reale TC-012-Abnahme ausstehend |
| TC-SEC-001 | REQ-S-001, REQ-S-002, AC-008 | Working Tree und Git-Historie scannen; Runtime-Claim, Fremdziel, Symlink-/Checkout-Grenze, Hardlinks, Rechte und Supervisor-Transport im Testharness prüfen | keine Geheimnisse oder privaten Runtime-Dateien; fremde Bestände bleiben unverändert; Runtime-Root und `current` mit Modus `0700`; Token und Optionen fehlen in argv und Ausgabe | automatisiert durch `scripts/validate.sh` und Integrationstests |

## Reale Abnahme

### TC-012 — Neustart- und Container-Abnahme

- **Prüft:** REQ-F-001 bis REQ-F-005, REQ-I-001 bis REQ-I-004,
  REQ-O-003, REQ-O-004 sowie AC-001 bis AC-012.
- **Voraussetzung:** isolierte Tests und Security-Scan erfolgreich; Codex und
  GitHub CLI installiert und angemeldet; Projekte und reale Memory-Datei in
  einem persistenten Workspace; `install` erfolgreich; `packages` enthält
  danach weder `gh` noch `github-cli`, fremde Pakete sind unverändert
  geblieben, der verwaltete Bootbefehl steht an erster Stelle und beide
  Git-Credential-Helper besitzen jeweils das exakte geordnete Paar aus leerem
  Resetwert und persistentem `gh`-Helper.
- **Aktion:** Baseline aus Sitzungsanzahl, ausgewählter fortsetzbarer Sitzung,
  Codex-Cache-Erkennung, aktivem GitHub-Login-Status, beiden Git-Helper-Werten,
  einer unveränderten fremden Git-Einstellung, Projektpfaden, Git-HEADs,
  Working-Tree-Status, Memory-Prüfsumme sowie Erweiterungsliste erfassen. Danach
  Add-on neu starten und anschließend eine Container-Neuerstellung
  beziehungsweise ein kontrolliertes Add-on-Update durchführen.
- **Erwartetes Ergebnis:** Baseline bleibt erhalten; Codex-Sitzung ist
  fortsetzbar; beide Anmeldungen sind gültig; Projekte und Memory sind
  unverändert; Studio Code und Erweiterungen bleiben durch die native
  Add-on-Persistenz verfügbar; das persistierte `gh` startet ohne APT- oder
  Netzwerkzugriff; HTTPS-Git-Zugriffe verwenden die persistente Anmeldung;
  Auth- und Helper-Audit melden keinen `BLOCK`. Verbleibende fremde
  Pakete werden als Einschränkung der vollständigen Offline-Fähigkeit
  protokolliert.
- **Toleranz:** keine fehlende Sitzung, kein geänderter Git-Stand oder fremder
  Git-Konfigurationswert, keine erneute Anmeldung, Helper-Einrichtung oder
  manuelle Linkreparatur.
- **Status:** Add-on-Neustart erfolgreich bestätigt; Host-Neustart steht noch aus; Add-on-Update oder Container-Neuerstellung ist ein zukünftiger Regressionstest.

## Ausführung

```sh
./scripts/validate.sh
```

Die reale Abnahme wird getrennt protokolliert. Ein isolierter Test ersetzt
nicht den Nachweis eines echten Add-on-Neustarts.
