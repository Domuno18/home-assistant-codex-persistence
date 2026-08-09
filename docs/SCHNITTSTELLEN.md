# Schnittstellen

## Übersicht

| ID | Quelle | Ziel | Zweck | Vertrag | Fehlerverhalten |
|---|---|---|---|---|---|
| IF-001 | Installationsskript | lokales Dateisystem | native Laufzeitbäume und Programme persistent ablegen | POSIX-Dateien, Verzeichnisse, Symlinks, Modi und SHA-256 | instabile Quelle, Spezialdatei oder Konflikt blockiert |
| IF-002 | Installationsskript | Home Assistant Supervisor | einmaliges gh-Bootstrap-Paket entfernen und automatischen `boot`-Befehl zuerst eintragen | lokale HTTP-API mit JSON | fremde Optionen und Pakete erhalten; API-Fehler lässt `install` fehlschlagen |
| IF-003 | Add-on `init_commands` | persistenter Bootstrap | `boot` vor `code-server` ausführen | absoluter Shell-Befehl mit expliziter Bestätigung | Exitcode ungleich null blockiert Add-on-Initialisierung |
| IF-004 | Installations- und Audit-Skript | Codex CLI | Installation, Version und Anmeldung prüfen | Prozessaufruf und Exitcode | ungültige Anmeldung oder Programmdatei blockiert |
| IF-005 | Installations- und Audit-Skript | GitHub CLI | Installation, Version und Anmeldung prüfen | Prozessaufruf und Exitcode | ungültige Anmeldung oder Programmdatei blockiert |
| IF-006 | globale Codex-Startanweisung | Memory-Regeln und private Memory-Datei im Workspace | verdichteten Kontext bei Sitzungsstart laden und nach bestätigten Entscheidungen pflegen | wirksame `$CODEX_HOME/AGENTS.override.md` oder `$CODEX_HOME/AGENTS.md` mit absoluten Pfaden zu `Memories/AGENTS.md` und `Memories/MEMORY.md` | fehlende oder vertrauliche Inhalte nicht durch Chatkopien ersetzen |
| IF-007 | Installations-, Boot- und Audit-Skript | Add-on-eigene globale Git-Konfiguration | HTTPS-Git-Zugriffe mit persistenter GitHub-Anmeldung verbinden | ausschließlich zwei Credential-Helper-Schlüssel mit je einem geordneten Reset-plus-`gh`-Wertepaar | fremder Helper bleibt erhalten und blockiert fail-safe |

## IF-001 — Persistentes Dateisystem

### Eingaben

- Codex-Quelle `/root/.codex`,
- GitHub-CLI-Quelle `/root/.config/gh`,
- mit `command -v` aufgelöste Codex- und GitHub-CLI-Programme,
- `HACP_RUNTIME_ROOT`, standardmäßig `/data/codex-persistence`.

### Ausgaben

```text
RUNTIME_ROOT/current/codex-home
RUNTIME_ROOT/current/gh
RUNTIME_ROOT/current/tools
RUNTIME_ROOT/state/active-generation
RUNTIME_ROOT/bootstrap/ha-codex-persistence.sh
```

Die Quelle wird vor, unmittelbar nach und nach einer Ruhephase inventarisiert.
Quelle und Kopie müssen in Typ, Modus, Eigentümer, Linkziel und Dateiprüfsumme
übereinstimmen. Der flüchtige Codex-Socket `ipc/ipc.sock` ist die einzige
bewusst ausgeschlossene Datei.

### Aktivierung

```text
/root/.codex       -> RUNTIME_ROOT/current/codex-home
/root/.config/gh   -> RUNTIME_ROOT/current/gh
/usr/local/bin/codex -> RUNTIME_ROOT/current/tools/bin/codex
/usr/local/bin/gh    -> RUNTIME_ROOT/current/tools/bin/gh
```

Ein vorhandener fremder Link, eine reguläre Datei am Werkzeugpfad oder ein
nicht leerer konkurrierender Quellpfad wird niemals überschrieben.

## IF-002 — Supervisor-Optionen

`install` liest über eine gegen Curl-Konfiguration, Proxy und Redirects
gehärtete lokale Supervisor-Verbindung die vollständigen aktuellen
Add-on-Optionen. Nachdem die persistente GitHub-CLI-Binary und die
Ready-Generation verifiziert und synchronisiert sind, liest es die Basis erneut,
bricht bei Konkurrenz ab, führt genau einen Options-Update aus und vergleicht
danach den zurückgelesenen Zustand:

- ausschließlich `gh` und den veralteten Alias `github-cli` aus `packages`
  entfernen,
- alle fremden Pakete unverändert und in ihrer Reihenfolge erhalten,
- alte eigene Starteinträge entfernen,
- genau einen aktuellen verwalteten Befehl als ersten `init_commands`-Eintrag
  setzen,
- alle sonstigen Optionen und fremden Startbefehle unverändert zurücksenden.

Der generische Starteintrag lautet:

```sh
HACP_MANAGED=home-assistant-codex-persistence HACP_RUNTIME_ROOT=/data/codex-persistence HACP_GIT_CONFIG_SOURCE=/root/.gitconfig HACP_BOOT_OK=YES sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh boot
```

Authentifizierung erfolgt ausschließlich mit dem vom Add-on bereitgestellten
Supervisor-Laufzeittoken. Das Skript gibt diesen Wert nicht aus und speichert
ihn nicht.

## IF-003 — Add-on-Start

Studio Code Server führt `init_commands` bei jedem Start vor `code-server`
aus. Add-on-Pakete werden noch vor diesen Befehlen verarbeitet. Der verwaltete
Befehl ruft die persistente `boot`-Schnittstelle auf. Sie validiert die aktive
Generation und stellt Codex-, GitHub-CLI- und Werkzeuglinks nur nach
erfolgreicher Konflikt- und Integritätsprüfung wieder her.

Der Aufruf ist bei jedem neuen Container gleich. Ein Fehlercode verhindert bewusst den Start mit
einem leeren, beschädigten oder konkurrierenden Zustand. Weil `gh` nach
erfolgreichem `install` nicht mehr in `packages` steht, benötigt dieser
Wiederanlauf für GitHub CLI weder APT noch eine Netzverbindung. Fremde
verbleibende Pakete können weiterhin vor dem Hook einen APT-Lauf auslösen.

## IF-004 — Codex CLI

### Installation

- `codex` muss auflösbar und als reguläre ausführbare Datei lesbar sein.
- Vor `install` muss der Device-Code-Login in ChatGPT erlaubt sein und mit
  `CODEX_HOME=/root/.codex codex -c 'cli_auth_credentials_store="file"' login --device-auth`
  erfolgen.
- Codex gibt Link und Einmalcode aus; der Nutzer bestätigt sie im Browser.
- `CODEX_HOME=/root/.codex codex -c 'cli_auth_credentials_store="file"' login status`
  muss den dateibasierten Anmeldecache erkennen. Das ist keine eigenständige
  serverseitige Gültigkeitsprüfung.
- Das aufgelöste Programm wird kopiert, gehasht und per `--version` geprüft.
- Das vollständige Codex-Home wird einschließlich `sessions`, Anmeldung,
  Konfiguration und Datenbanken persistent geführt.

### Audit

Mit `HACP_CHECK_AUTH=YES` wird `codex login status` über das persistierte
Programm ausgeführt. Bewertet werden ausschließlich Erkennung und Methode des
lokalen Anmeldecaches sowie der Exitcode, nicht die serverseitige Gültigkeit.
Inhalte der Anmeldedatei werden nicht ausgegeben.

## IF-005 — GitHub CLI

### Installation

- Das Add-on-Paket `gh` stellt genau einmal vor `install` den ersten
  ausführbaren Befehl bereit.

Der Login-Vertrag lautet:

```sh
(
  unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN
  GH_CONFIG_DIR=/root/.config/gh \
    gh auth login --hostname github.com --git-protocol https --web --insecure-storage
  GH_CONFIG_DIR=/root/.config/gh \
    gh auth status --active --hostname github.com
)
```

GitHub CLI gibt einen Gerätecode aus. Falls kein Browser startet, öffnet der
Nutzer `https://github.com/login/device`, gibt den Code ein und bestätigt
**Continue** sowie **Authorize GitHub CLI**.

`--insecure-storage` ist für diese Architektur bewusst erforderlich: Das
Credential liegt so in `hosts.yml` statt in einem flüchtigen Container-Keyring
und wird durch die private persistente Runtime mit Eigentümer `root:root` und
Modus `0700` geschützt. `--show-token` ist unzulässig.

- `GH_CONFIG_DIR=/root/.config/gh gh auth status --active --hostname github.com`
  muss für das aktive Konto erfolgreich sein.
- Das aufgelöste Programm wird kopiert, gehasht und per `--version` geprüft.
- Die vollständige GitHub-CLI-Konfiguration wird persistent geführt.
- Nach erfolgreicher persistenter Übernahme entfernt der Supervisor-Update nur
  `gh` beziehungsweise `github-cli`; der Betriebsbefehl kommt danach aus
  `current/tools/bin/gh`.

### Steady State

`boot` installiert und aktualisiert keine Pakete. Die gespeicherte
GitHub-CLI-Binary wird offline per Prüfsumme und Versionsaufruf verifiziert und
über `/usr/local/bin/gh` eingebunden. Fremde Add-on-Pakete bleiben erhalten,
liegen wegen der Add-on-Startreihenfolge aber außerhalb der Offline-Garantie.
Ein geplanter Upgrade-Ablauf für persistierte Programme ist BL-005.

HTTPS-Git-Aufrufe verwenden nicht einen containerlokalen Helper-Pfad, sondern
den in IF-007 definierten absoluten `/usr/local/bin/gh`-Aufruf mit festem
`GH_CONFIG_DIR`.

### Audit

Mit `HACP_CHECK_AUTH=YES` wird `gh auth status --active --hostname github.com`
über das persistierte Programm ausgeführt. Es werden keine
Authentifizierungswerte in die Projektausgabe übernommen.

## IF-006 — Workspace und Memory

Das Repository liefert unter `examples/memory` eine leere neutrale Vorlage.
`install` erzeugt daraus ausschließlich fehlende `Memories/AGENTS.md` und
`Memories/MEMORY.md`; vorhandene Dateien bleiben vollständig bytegenau.
Wirksame globale Startdatei ist die nicht leere
`$CODEX_HOME/AGENTS.override.md`, falls vorhanden, sonst
`$CODEX_HOME/AGENTS.md`. Genau ein verwalteter Block verweist mit absoluten
Pfaden zuerst auf die lokalen Memory-Regeln und danach auf die private
`MEMORY.md`. Vorhandener fremder Inhalt wird nicht ersetzt. Dadurch gilt die
Startlogik auch in verschachtelten Git-Repositories.

Der persistente Workspace darf weder das Installationsrepository selbst sein
noch innerhalb seines Checkouts liegen. Eine reale Memory-Datei wird niemals
in das Repository zurückgeschrieben. Fortsetzbare Chats bleiben im nativen
`codex-home/sessions`-Format.

## IF-007 — Add-on-Git-Konfiguration

Das Studio-Code-Server-Add-on persistiert die globale Git-Konfiguration unter
`/data/git/.gitconfig`; `/root/.gitconfig` verweist darauf. Das Projekt kopiert
oder übernimmt diese Datei nicht in die Projekt-Runtime und ersetzt ihren
semantischen Gesamtinhalt nicht. Der generische Quellpfad kann über
`HACP_GIT_CONFIG_SOURCE` gesetzt werden, muss sich aber kanonisch als reguläre
Datei unter `/data`, `/config` oder `/share` auflösen.

Nur diese Schlüssel gehören zum Projektvertrag:

```text
credential.https://github.com.helper
credential.https://gist.github.com.helper
```

Jeder Schlüssel besitzt im Zielzustand genau zwei geordnete Werte:

```text
<leer>
!GH_CONFIG_DIR=/root/.config/gh /usr/local/bin/gh auth git-credential
```

Der leere erste Wert setzt niedriger priorisierte beziehungsweise System-Helper
zurück; der zweite delegiert an die persistente GitHub-CLI-Konfiguration.

`install` prüft vor jeder anderen Aktivierung alle vorhandenen Werte. Fehlende
Schlüssel, leere Werte, der aktuelle Sollwert und bekannte alte Befehle der Form
`!gh auth git-credential` beziehungsweise `!<Pfad>/gh auth git-credential` sind
migrierbar. Ein anderer benutzerdefinierter Wert wird nicht überschrieben und
führt zu `BLOCK`.

Nach dem Verlinken der persistenten `gh`-Binary erzeugen `install` und `boot`
unter dem üblichen `.gitconfig.lock` eine private Geschwisterkopie, verändern
darin ausschließlich diese beiden Schlüssel und veröffentlichen sie atomar mit
einem `mv`. Danach prüfen sie je Schlüssel das exakte geordnete Wertepaar. Alle
anderen Git-Konfigurationswerte sowie Modus und Eigentümer bleiben erhalten.
`audit` führt nur die kanonische Pfad-, Reihenfolge- und Exaktwertprüfung aus
und schreibt nichts.

## Diagnoseformat

Alle Skriptmeldungen verwenden:

```text
LEVEL    CHECK    TARGET    DETAIL
```

Die vier Felder sind jeweils durch einen Tabulator getrennt.

Zulässige Level sind `OK`, `WARN` und `BLOCK`. Diagnosefelder enthalten keine
Chattexte, Memory-Inhalte, Dateiinhalte oder Anmeldedaten.
