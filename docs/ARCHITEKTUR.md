# Architektur

## Architekturziele

1. native Codex- und GitHub-CLI-Daten direkt außerhalb des austauschbaren
   Containers führen,
2. eine einmalige, vollständig verifizierte Installation ermöglichen,
3. bei jedem Add-on-Start vor `code-server` nur bekannte Links wiederherstellen,
4. bei Widersprüchen ohne Merge, Überschreiben oder leere Neuerzeugung
   blockieren,
5. die Add-on-eigene persistente Git-Konfiguration erhalten und darin nur zwei
   ausdrücklich bekannte GitHub-Credential-Helper binden,
6. Runtime-Geheimnisse strikt von Quellcode, Projekten und neutraler
   Memory-Vorlage trennen.

## Systemkontext

Das Studio-Code-Server-Add-on verwaltet Studio-Code-Einstellungen und
Erweiterungen bereits persistent unter `/data/vscode`. Ebenso verwaltet es
Git-Konfiguration, SSH-Daten und Shell-History in eigenen `/data`-Bereichen.
Diese Lösung ergänzt den bislang nicht vom Add-on verwalteten Zustand von Codex
CLI und GitHub CLI sowie bei Bedarf ihre ausführbaren Dateien. Die bestehende
Git-Konfiguration wird nicht in die Projekt-Runtime übernommen und ihr
Gesamtinhalt wird nicht ersetzt; nur ihre zwei Helper-Schlüssel für `github.com`
und `gist.github.com` werden atomar an die persistente GitHub CLI gebunden.

```text
Home Assistant Supervisor
        │ entfernt gh-Bootstrap und setzt boot zuerst
        ▼
install ──> persistente Runtime ──> init_commands: boot
                    │                         │
                    │                         ▼ vor code-server
                    └────────────────────── boot
                                              │
                 /root/.codex <───────────────┤
             /root/.config/gh <───────────────┤
        vorgesehene CLI-Pfade <───────────────┘

/root/.gitconfig ─ Add-on ─> /data/git/.gitconfig
                         └─ nur zwei GitHub-Helper ─> persistentes gh

audit ── nur lesend ──> Runtime, Links, Helper, Rechte und optionale Anmeldung
```

## Speicherentscheidung

Der generische Standard ist `/data/codex-persistence`, weil `/data` der native
private Persistenzbereich eines Home-Assistant-Add-ons ist. Der Zielpfad ist
über `HACP_RUNTIME_ROOT` konfigurierbar und muss absolut, kanonisch und sicher
unter `/data`, `/config` oder `/share` liegen. Die Referenzinstallation nutzt
`/config/Codex/.runtime`, damit sie zum vorhandenen persistenten Workspace
passt. Beide Varianten erfüllen denselben Vertrag.

```text
RUNTIME_ROOT/
├── current/
│   ├── codex-home/              native Sessions, Auth, Konfiguration
│   ├── gh/                      GitHub-CLI-Konfiguration und Auth
│   ├── tools/
│   │   ├── bin/codex
│   │   ├── bin/gh
│   │   └── SHA256SUMS
│   └── meta/                    verifizierte Baummanifeste
├── state/
│   ├── ready-generation           verifiziert, Hook-Cutover noch nicht bestätigt
│   └── active-generation          für boot freigegebene Generation
├── locks/                       Schutz vor parallelen Operationen
└── bootstrap/
    └── ha-codex-persistence.sh  persistenter boot-/audit-Einstieg
```

Alle privaten Runtime-Verzeichnisse sind reguläre Verzeichnisse mit Modus
`0700`. Die aktive Generation wird erst nach erfolgreicher Prüfung markiert.
Temporäre Arbeitsverzeichnisse dürfen ausschließlich unter dem Runtime-Root
liegen und werden nur über eng begrenzte Pfadmuster entfernt.

Die globale Git-Konfiguration ist kein Bestandteil von `RUNTIME_ROOT`.
`/root/.gitconfig` muss auf eine reguläre persistente Datei unter `/data`,
`/config` oder `/share` auflösbar sein; im Add-on ist das Ziel
`/data/git/.gitconfig`. Die Datei bleibt Add-on-eigen. Das Projekt verwendet
`git config --file` nur für zwei exakt benannte Credential-Helper-Schlüssel.

## Komponenten

| ID | Komponente | Verantwortung | Abhängigkeiten | Ausfallverhalten |
|---|---|---|---|---|
| ARC-001 | Installationscontroller | Voraussetzungen, stabile Kopien, Programme, Links, Marker und Add-on-Option atomar geordnet einrichten | Dateisystem, Codex CLI, GitHub CLI, Supervisor API | bricht mit Diagnose ab; keine konkurrierenden Daten mischen |
| ARC-002 | Persistente Generation | hält Codex-Home, GitHub-CLI-Home, Werkzeuge, Prüfsummen und Marker als Konsistenzgrenze | persistenter Home-Assistant-Pfad | unmarkierter oder beschädigter Bestand ist nicht aktivierbar |
| ARC-003 | Boot-Adapter | prüft die Generation und rekonstruiert Links vor `code-server` | `init_commands`, ARC-002 | blockiert Add-on-Start bei Abweichung |
| ARC-004 | Audit-Adapter | bewertet Zustand, Links, Rechte, Sitzungsanzahl und optional beide Anmeldungen | ARC-002, lokale CLI-Programme | meldet `OK` oder `BLOCK`, schreibt nichts |
| ARC-005 | Workspace-/Memory-Grenze | trennt persistente Projekte und reale Memory-Datei von privater Runtime und öffentlicher Vorlage | persistenter Workspace, `examples/memory` | keine automatische Kopie realer Inhalte ins Repository |
| ARC-006 | Git-Helper-Adapter | bindet ausschließlich GitHub und Gist in der Add-on-eigenen Git-Konfiguration an die persistente `gh`-Binary | `/root/.gitconfig`, `/data/git/.gitconfig`, ARC-002 | migriert nur bekannte Werte; fremder Helper bleibt erhalten und blockiert |

## Ablauf `install`

1. Eine ausdrückliche Installationsbestätigung, Root-Rechte, sichere Pfade und
   benötigte Werkzeuge prüfen.
2. Sicherstellen, dass kein Codex-Prozess läuft und beide CLIs installiert sind.
   Codex muss vor `install` per Gerätecode und
   `cli_auth_credentials_store="file"` angemeldet sein; sein Statusbefehl
   erkennt nur den Cache. Ein externer `sqlite_home` oder Codex-Keyring
   blockiert. GitHub CLI muss ohne vorrangige Umgebungs-Tokens ein
   dateibasiertes Credential in `/root/.config/gh/hosts.yml` führen; ein
   Keyring-only-Zustand blockiert.
3. `/root/.gitconfig` auf die persistente reguläre Zieldatei auflösen und die
   vorhandenen Werte der zwei GitHub-Helper prüfen. Fehlende, leere und bekannte
   alte `!…/gh auth git-credential`-Werte sind migrierbar; jeder fremde Wert
   bleibt unverändert und blockiert vor dem Cutover.
4. Ausschließlich fehlende Memory-Dateien atomar anlegen und vorhandene
   Dateien bytegenau erhalten. Die wirksame globale
   `$CODEX_HOME/AGENTS.override.md`, andernfalls `$CODEX_HOME/AGENTS.md`, erhält
   genau einen verwalteten Block mit absoluten Pfaden. Damit wirkt die Logik in
   verschachtelten Git-Repositories; der Workspace liegt nicht im
   Installationsrepository.
5. Codex-Home und GitHub-CLI-Home jeweils mehrfach inventarisieren, kopieren
   und auf Quellruhe sowie Inhaltsgleichheit prüfen. Nur der flüchtige native
   Socket `ipc/ipc.sock` wird ausgelassen; andere Spezialdateien blockieren.
6. Aufgelöste Codex- und GitHub-CLI-Programme stabil kopieren,
   SHA-256-Prüfsummen schreiben und die Programme per `--version` prüfen.
7. Den verifizierten Bestand atomar als `current` ablegen, die persistente
   Bootstrap-Kopie schreiben und mit `ready-generation` als wiederanlauffähig
   markieren.
8. Über die Supervisor API in einem Update ausschließlich das einmalige
   Bootstrap-Paket `gh` und den veralteten Alias `github-cli` aus `packages`
   entfernen und den eindeutig markierten `boot`-Befehl als ersten
   `init_commands`-Eintrag setzen. Fremde Pakete, Optionen und Startbefehle
   bleiben unverändert und in ihrer bisherigen Reihenfolge erhalten.
9. Unmittelbar vor dem Cutover erneut Prozessruhe und Inhaltsgleichheit prüfen,
   nur konfliktfreie Containerpfade und Werkzeugpfade verlinken und anschließend
   ausschließlich die zwei GitHub-Helper auf je zwei geordnete Werte setzen:
   leerer Reset und danach
   `!GH_CONFIG_DIR=/root/.config/gh /usr/local/bin/gh auth git-credential`.
   Erst nach exakter Verifikation der Wertepaare wird `active-generation`
   veröffentlicht.

`install` wird einmal nach Installation und Anmeldung beider CLIs ausgeführt.
Ein erneuter Aufruf auf einer gültigen aktiven Generation erneuert
idempotent Bootstrap und Add-on-Starteintrag und prüft die Links. Eine nach
Unterbrechung vollständig verifizierte Ready-Generation kann ohne neue Kopie
fortgesetzt werden; es gibt dafür keinen zusätzlichen Benutzerbefehl.

## Paket-Lifecycle und Offline-Grenze

Das Add-on verarbeitet jede nicht leere `packages`-Liste vor den
`init_commands`: zuerst werden die Paketindizes aktualisiert, danach die
Pakete installiert. Deshalb darf `gh` nach erfolgreichem `install` nicht als
dauerhaftes Add-on-Paket verbleiben. Andernfalls würde jeder Wiederanlauf trotz
vorhandener persistenter Binary von APT, DNS und Paketservern abhängen.

Der Zielzustand ist:

```text
einmalig: packages enthält gh -> lokale gh-Binary verfügbar
install:  Binary + SHA-256 + Version persistent und geprüft
          Supervisor-Update entfernt nur gh/github-cli und setzt boot zuerst
danach:   boot verwendet current/tools/bin/gh ohne Paketinstallation oder Netz
```

Eine leere `packages`-Liste löst keinen Paketlauf aus. Fremde Pakete werden
nicht entfernt, verursachen aber weiterhin vor dem Boot-Hook einen APT-Lauf
und liegen damit außerhalb der Offline-Garantie dieses Projekts. Ein Upgrade
der persistierten Programme ist eine bewusste, geprüfte Betriebsänderung und
kein Bestandteil von `boot`; der Upgrade-Ablauf bleibt in BL-005.

## Ablauf `boot`

`boot` läuft automatisch als erster Eintrag aus `init_commands`, bevor
`code-server` startet. Es prüft Marker, private Rechte, Struktur,
Werkzeugprüfsummen, Prozesszustand und die Migrierbarkeit der zwei GitHub-
Helper. Nach einer unterbrochenen Installation darf es ausschließlich eine
vollständig verifizierte `ready-generation` automatisch übernehmen. Danach
setzt es nur fehlende erwartete Links und verifiziert beziehungsweise migriert
die zwei Helper:

```text
/root/.codex       -> RUNTIME_ROOT/current/codex-home
/root/.config/gh   -> RUNTIME_ROOT/current/gh
/usr/local/bin/codex -> RUNTIME_ROOT/current/tools/bin/codex
/usr/local/bin/gh    -> RUNTIME_ROOT/current/tools/bin/gh

/root/.gitconfig     -> /data/git/.gitconfig       vom Add-on bereitgestellt
GitHub-/Gist-Helper  -> persistentes /usr/local/bin/gh
```

Bereits korrekte Links bleiben unverändert. Nicht leere neue Containerpfade,
unerwartete Links oder vorhandene reguläre Dateien an den Werkzeugpfaden
führen zum sicheren Abbruch. Die Git-Konfigurationsdatei wird nicht in die
Projekt-Runtime übernommen und ihr semantischer Gesamtinhalt nicht ersetzt.
Nur die beiden Helper-Schlüssel werden über eine private Geschwisterkopie
atomar veröffentlicht; alle übrigen Werte sowie Modus und Eigentümer bleiben
erhalten. Ein fremder Wert in einem der beiden Helper-Schlüssel bleibt erhalten
und blockiert; fehlende, leere und bekannte alte `gh`-Werte werden gezielt
migriert. Erst danach wird eine Ready-Generation aktiv markiert.

## Ablauf `audit`

`audit` prüft ausschließlich lesend:

- Konfiguration und aktive Generationskennung,
- Runtime-Struktur und Werkzeugprüfsummen,
- alle vier Kompatibilitätslinks,
- Eigentümer und Modus aller privaten Runtime-Verzeichnisse,
- Anzahl nativer `sessions`-Dateien,
- Vorhandensein der neutralen Memory-Regeln und der wirksamen globalen Referenz,
- kanonische persistente Git-Konfiguration und je zwei exakt geordnete Werte für
  den GitHub- und Gist-Credential-Helper: leerer Reset, danach persistentes `gh`,
- optional Erkennung des Codex-Anmeldecaches und
  `gh auth status --active --hostname github.com`; der Codex-Status ist keine
  serverseitige Gültigkeitsprüfung. Ohne diese Option wird Auth als `WARN` markiert.

Der Audit repariert keinen Befund. Maschinenlesbare Ausgaben besitzen vier
tabulatorgetrennte Felder: Level, Check, Ziel und Detail.

## Workspace und Memory

Projekte liegen unabhängig von der Runtime in einem persistenten Workspace;
dieser darf nicht innerhalb des Installationsrepository-Checkouts liegen. Das
Repository liefert unter `examples/memory` nur neutrale Pflege- und Startregeln.
`install` legt fehlende Memory-Dateien atomar an und lässt vorhandene Dateien
bytegenau unverändert. Die wirksame globale
`$CODEX_HOME/AGENTS.override.md`, andernfalls `$CODEX_HOME/AGENTS.md`, enthält
genau einen verwalteten Block mit absoluten Pfaden. Bereits vorhandener fremder
Inhalt wird nicht ersetzt; die Startlogik gilt dadurch auch in verschachtelten
Git-Repositories.

Eine reale, befüllte `MEMORY.md` verbleibt im persistenten Workspace.
Fortsetzbare Chats bleiben ausschließlich im nativen
`codex-home/sessions`-Bereich.

## Datenverantwortung

| Datenobjekt | Erzeuger | Führende Quelle | Änderungsrecht | Aufbewahrung |
|---|---|---|---|---|
| native Codex-Sitzungen | Codex CLI | `current/codex-home` | Codex CLI | solange vom Betreiber benötigt |
| Codex-Anmeldung und -Konfiguration | Codex CLI | `current/codex-home` | Codex CLI und Betreiber | bis Abmeldung, Rotation oder Löschung |
| GitHub-CLI-Anmeldung | GitHub CLI | `current/gh` | GitHub CLI und Betreiber | bis Abmeldung, Rotation oder Löschung |
| globale Git-Konfiguration | Studio Code Server Add-on | `/data/git/.gitconfig` | Add-on und Betreiber; Projekt nur für zwei Helper | gemäß Add-on- und Betreiberkonfiguration |
| GitHub-/Gist-Credential-Helper | `install` und `boot` | zwei Schlüssel in `/data/git/.gitconfig` | Git-Helper-Adapter | solange diese Lösung aktiv ist |
| persistierte CLI-Programme | `install` | `current/tools` | Installationscontroller | bis zu einem bewusst geprüften Upgrade gemäß BL-005 |
| Add-on-Starteintrag | `install` | Supervisor-Optionen | Betreiber und Installationscontroller | solange die Lösung aktiv ist |
| gh-Bootstrap-Paket | Betreiber vor `install` | Add-on-Optionen | Installationscontroller entfernt nur bekannte Namen | ausschließlich bis zur verifizierten persistenten Übernahme |
| Projekte | Nutzer und Git | persistenter Workspace | Nutzer und Git-Werkzeuge | gemäß jeweiligem Projekt |
| reale Memory-Datei | Codex und Nutzer | persistenter Workspace | gemäß lokalen Memory-Regeln | bis bestätigte Aussagen ersetzt werden |
| neutrale Memory-Vorlage | Projekt | Git-Repository | Projektpflege | versioniert |

## Architekturgrenzen

- Keine zusätzliche Datenbank, kein Hintergrunddienst und kein Importformat.
- Kein Wiederherstellen nativer Sitzungen aus Markdown.
- Kein automatisches Upgrade der persistierten CLI-Programme während `boot`.
- Keine Verwaltung von `/data/vscode`, Add-on-Erweiterungen oder
  Add-on-eigener SSH-Konfiguration. Die Add-on-eigene Git-Konfiguration wird
  nicht in die Projekt-Runtime übernommen und ihr Gesamtinhalt nicht ersetzt;
  ausschließlich die zwei dokumentierten GitHub-Credential-Helper werden
  atomar veröffentlicht.
- Persistenz schützt vor Containerwechsel, ersetzt aber kein geprüftes,
  vertrauliches Backup des persistenten Speichers.
