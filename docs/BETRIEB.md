# Betrieb

## Betriebsziel

Nach einer einmaligen Installation arbeitet Codex weiterhin über
`/root/.codex` und GitHub CLI über `/root/.config/gh`; beide Pfade zeigen
jedoch direkt auf persistenten Speicher. Bei jedem Add-on-Start stellt der
automatische `boot`-Befehl diese Links und die zwei GitHub-Credential-Helper vor
`code-server` wieder her. Ein Chatimport, erneutes Anmelden oder manuelles
`gh auth setup-git` nach einem normalen Containerwechsel ist nicht vorgesehen.

## Zuständigkeiten

| Aufgabe | Verantwortliche Rolle | Vertretung | Eskalation |
|---|---|---|---|
| Installation und Add-on-Optionen | Home-Assistant-Betreiber | administrativer Betreiber | Projektpflege bei reproduzierbarem Skriptfehler |
| Runtime-Audit und Neustartabnahme | Home-Assistant-Betreiber | technischer Prüfer | kein Neustart bei `BLOCK` |
| Codex- und GitHub-Anmeldung | jeweiliger Kontoinhaber | keine automatische Vertretung | Anbieter-Support bei serverseitigem Kontoproblem |
| Credential-Rotation | jeweiliger Kontoinhaber | Sicherheitsverantwortlicher | Anmeldung sofort sperren und Vorfallprozess starten |
| verschlüsseltes Backup und Restore | Home-Assistant-Betreiber | Backup-Verantwortlicher | Wiederherstellung nur aus geprüftem Stand |
| Memory-Pflege | Codex gemäß globaler Startanweisung und lokaler Memory-Regeldatei, bestätigt durch Nutzer | Nutzer | widersprüchliche Aussage an führender Quelle klären |
| Programm- und Projektpflege | jeweilige Projektpflege | technischer Prüfer | Update bei fehlender Kompatibilität stoppen |

## Bestehende Add-on-Persistenz

Diese Bereiche werden bereits durch Studio Code Server selbst persistent
verwaltet und von diesem Projekt weder kopiert noch ersetzt:

- Studio-Code-Einstellungen und Erweiterungen unter `/data/vscode`,
- globale Git-Konfiguration unter `/data/git`,
- SSH-Konfiguration unter `/data/.ssh`,
- Shell-History unter `/data/.zsh_history`.

Für `/data/git/.gitconfig` gilt eine eng begrenzte Ausnahme: Das Projekt
verwaltet ausschließlich die Credential-Helper-Schlüssel für `github.com` und
`gist.github.com`. Alle anderen Git-Einstellungen bleiben in der Verantwortung
des Add-ons und Betreibers.

Projekte und eine reale Memory-Datei müssen zusätzlich in einem persistenten
Workspace unter `/config`, `/share` oder einem gleichwertigen eingebundenen
Pfad liegen. Inhalte unter einem beliebigen sonstigen `/root`-Pfad gehören
nicht zum Schutzumfang.

## Einmalige Installation

### Voraussetzungen

1. Codex CLI ist über die Erweiterung verfügbar. GitHub CLI wurde einmalig als
   Add-on-Paket `gh` installiert; dieses Paket dient nur als Quelle für die
   einmalige persistente Übernahme der Programmdatei.
2. Der dateibasierte Codex-Anmeldecache wird erkannt; die aktive, ebenfalls
   dateibasiert gespeicherte GitHub-Anmeldung besteht
   `GH_CONFIG_DIR=/root/.config/gh gh auth status --active --hostname github.com`.
3. Bestehende native Codex-Sitzungen befinden sich unter
   `/root/.codex/sessions`.
4. Alle Codex-Chats und Codex-Prozesse sind geschlossen. Der Aufruf erfolgt aus
   einem normalen Studio-Code-Terminal; `code-server` selbst darf laufen.
5. Der gewünschte persistente Zielpfad ist vorhanden oder sein reguläres
   Elternverzeichnis ist beschreibbar.
6. `/root/.gitconfig` verweist auf die reguläre persistente
   `/data/git/.gitconfig`; vorhandene Werte der zwei GitHub-Helper sind fehlend,
   leer oder ein bekannter alter `gh auth git-credential`-Befehl. Ein fremder
   Helper wird nicht automatisch überschrieben und blockiert.
7. Der Betreiber hat die Add-on-Optionen gesichert und kontrolliert, welche
   `init_commands` bereits bestehen.

### Gerätecode-Anmeldung

Der Device-Code-Login muss in ChatGPT gegebenenfalls zuerst in den
Sicherheitseinstellungen oder durch den Workspace-Admin erlaubt werden. Codex
wird danach mit festem Home und dateibasiertem Cache angemeldet:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login --device-auth
```

Den ausgegebenen Link im Browser öffnen, den einmaligen Code eingeben und die
Freigabe bestätigen. Danach den Cache erkennen lassen:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login status
```

`codex login status` erkennt Cache und Methode; er beweist nicht selbst die
serverseitige Gültigkeit.

GitHub CLI wird ohne vorrangige Umgebungs-Tokens und mit festem Dateispeicher
angemeldet:

```sh
(
  unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN
  GH_CONFIG_DIR=/root/.config/gh \
    gh auth login \
      --hostname github.com \
      --git-protocol https \
      --web \
      --insecure-storage
  GH_CONFIG_DIR=/root/.config/gh \
    gh auth status --active --hostname github.com
)
```

GitHub CLI zeigt einen einmaligen Gerätecode. Falls kein Browser geöffnet wird,
`https://github.com/login/device` aufrufen, Code eingeben, **Continue** und
**Authorize GitHub CLI** bestätigen. Der Klartext-Dateispeicher ist bewusst
nötig, damit kein flüchtiger Container-Keyring Teil des Zustands wird. Die
private persistente Runtime schützt die Datei mit Eigentümer `root:root` und
Modus `0700`. `--show-token` darf niemals verwendet werden.

### Codex-Unterstützung vor der Installation

Codex kann die Voraussetzungen prüfen und den passenden Terminalbefehl nennen.
Dafür genügt: „Lies die README dieses Projekts, prüfe nur die Voraussetzungen
für die einmalige Installation und führe `install` nicht aus, solange dieser
Chat geöffnet ist.“ Anschließend müssen alle Codex-Chats geschlossen werden;
der einmalige Installer läuft dann direkt im normalen Studio-Code-Terminal.

### Standardinstallation

Im Root dieses Projekt-Repositories ausführen:

```sh
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

Ohne weitere Konfiguration lautet das Ziel `/data/codex-persistence`.
`install` führt alle Kopier- und Inhaltsprüfungen aus, persistiert die
aufgelösten Codex- und GitHub-CLI-Programme und synchronisiert die
Ready-Generation. Danach entfernt derselbe Supervisor-Update ausschließlich
`gh` beziehungsweise `github-cli` aus den Add-on-Paketen und setzt den
verwalteten `boot`-Befehl als ersten Startbefehl. Fremde Pakete und
Startbefehle bleiben erhalten. Anschließend aktiviert `install` die
verifizierte Generation, stellt die Links im aktuellen Container her und setzt
ausschließlich die zwei GitHub-Credential-Helper auf die persistente
`/usr/local/bin/gh`-Binary.

### Referenzinstallation

Für den dokumentierten Referenzpfad:

```sh
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

Der gewählte `HACP_RUNTIME_ROOT` ist für `install`, `boot` und `audit`
identisch. Ein Wechsel des Pfads ist keine normale Betriebsoperation und darf
nicht durch Kopieren oder Zusammenführen zweier gefüllter Runtime-Bestände
improvisiert werden.

### Einmalige Kontrolle der Add-on-Optionen

Direkt nach `install` sind die Add-on-Optionen einmalig zu kontrollieren:

- `packages` enthält weder `gh` noch `github-cli`,
- falls `gh` das einzige Bootstrap-Paket war, ist `packages` leer,
- alle fremden Pakete sind unverändert und in derselben Reihenfolge vorhanden,
- der verwaltete `boot`-Befehl ist der erste `init_commands`-Eintrag,
- alle fremden Startbefehle sind unverändert erhalten,
- `audit` meldet den exakten GitHub- und Gist-Credential-Helper als `OK`.

Das Studio-Code-Server-Add-on verarbeitet eine nicht leere `packages`-Liste
vor den `init_commands` durch `apt update` und Paketinstallation. Deshalb ist
der Steady State nur bezüglich GitHub CLI offlinefähig: `gh` kommt aus der
persistenten verifizierten Binary und benötigt beim Neustart kein APT und kein
Netz. Bewusst beibehaltene fremde Pakete bleiben ein separates
Offline-Risiko des Betreibers.

### Einmalige Erfolgsprüfung nach `install`

Für den Standardpfad:

```sh
HACP_CHECK_AUTH=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
```

Für die Referenzinstallation:

```sh
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_CHECK_AUTH=YES \
sh /config/Codex/.runtime/bootstrap/ha-codex-persistence.sh audit
```

Erwartet werden ausschließlich `OK`-Zeilen und abschließend `OK result
active`. Vor diesem Ergebnis wird kein Neustart zur einmaligen Abnahme
ausgelöst. Die Prüfung ist kein Backup und kein Prepare-Schritt. Nach
erfolgreicher Installation sind vor normalen späteren Neustarts keine
Sicherung, kein Export und kein manueller Skriptaufruf nötig.

## Automatischer Start

`install` trägt einen absoluten, explizit bestätigten Bootstrap-Aufruf in
`init_commands` ein. Für den Standardpfad entspricht er diesem Vertrag:

```sh
HACP_MANAGED=home-assistant-codex-persistence HACP_RUNTIME_ROOT=/data/codex-persistence HACP_GIT_CONFIG_SOURCE=/root/.gitconfig HACP_BOOT_OK=YES sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh boot
```

Der Befehl läuft bei jedem Add-on-Start vor `code-server`. Er kopiert keine
Sessions und importiert keine Chats. `boot` prüft Eigentumsmarker, Generation,
Manifeste, Programme, Prozesszustand, GitHub-Helper und jeden Quellpfad, bevor
es fehlende Links wiederherstellt. Unerwarteter Zustand wird nicht gelöscht,
sondern blockiert den Start. `boot` installiert weder `gh` noch andere Pakete
und führt kein Programm-Upgrade aus.

Eine bereits aktive Installation wird mit demselben ausdrücklich bestätigten
`install`-Aufruf kontrolliert aktualisiert. Dabei bleiben die versiegelte
Runtime-Generation, Sessions, Anmeldungen und Programme unverändert; ersetzt
werden nur die persistente Bootstrap-Kopie und der verwaltete Starteintrag.

Ein erfolgreicher wiederholter `boot` ist normal. Eine Blockierung beendet die
Add-on-Initialisierung bewusst, damit kein leerer oder konkurrierender Zustand
gestartet wird.

## Git-Credential-Helper im persistenten Add-on-Bereich

Das Add-on persistiert die globale Git-Konfiguration selbst:

```text
/root/.gitconfig -> /data/git/.gitconfig
```

Das Projekt übernimmt die Datei nicht in `RUNTIME_ROOT` und ersetzt ihren
semantischen Gesamtinhalt nicht. `install` und `boot` veröffentlichen atomar
nur die Werte dieser beiden Schlüssel:

```text
credential.https://github.com.helper
credential.https://gist.github.com.helper
```

Jeder Schlüssel muss genau diese zwei geordneten Werte besitzen:

```text
<leer>
!GH_CONFIG_DIR=/root/.config/gh /usr/local/bin/gh auth git-credential
```

Der erste, leere Wert setzt niedriger priorisierte beziehungsweise
System-Helper zurück. Für eine Änderung wird unter dem üblichen
`.gitconfig.lock` eine private Geschwisterdatei erstellt und mit genau einem
`mv` veröffentlicht. Alle anderen Werte sowie Modus und Eigentümer der Datei
bleiben erhalten.

Fehlende, leere und bekannte alte `!gh auth git-credential`- beziehungsweise
`!<Pfad>/gh auth git-credential`-Werte werden idempotent migriert. Eine
vorhandene fremde Benutzerkonfiguration außerhalb dieser zwei Schlüssel bleibt
erhalten. Auch ein fremder Helper-Wert bleibt erhalten, führt aber bewusst zu
`BLOCK`, weil das Projekt die Betreiberentscheidung nicht errät.

Nach erfolgreichem `install` erfolgt diese Prüfung und gegebenenfalls Migration
bei jedem Add-on-Start automatisch. Vor einem normalen Neustart ist kein
Prepare-, Login- oder Helper-Befehl nötig. `audit` prüft Pfad, Reihenfolge und
Exaktwerte rein lesend.

## Memory im persistenten Workspace

Das Verzeichnis `examples/memory` ist eine neutrale Vorlage. Beim einmaligen
`install` werden nur fehlende `Memories/AGENTS.md` und `Memories/MEMORY.md`
atomar angelegt; vorhandene Dateien bleiben vollständig bytegenau erhalten.
Wirksame globale Startdatei ist eine vorhandene nicht leere
`$CODEX_HOME/AGENTS.override.md`, sonst `$CODEX_HOME/AGENTS.md`. `install`
ergänzt darin genau einen verwalteten Block mit den absoluten Pfaden zu den
beiden Memory-Dateien. Bereits vorhandener fremder Inhalt wird nicht ersetzt;
unvollständige oder abweichende HACP-Marker blockieren. Die globale Datei und
absoluten Pfade funktionieren auch aus verschachtelten Git-Repositories.

`HACP_WORKSPACE_ROOT` darf weder das Installationsrepository selbst sein noch
innerhalb seines Checkouts liegen. Die private `MEMORY.md` wird nach bestätigten
dauerhaften Entscheidungen kurz gepflegt. Sie enthält keine Chatkopien oder
Anmeldedaten und wird nicht in dieses Repository zurückkopiert. Native,
fortsetzbare Chats verbleiben unter
`RUNTIME_ROOT/current/codex-home/sessions`.

## Regelmäßiger Audit

Der Audit wird mindestens in diesen Situationen ausgeführt:

- unmittelbar nach `install`,
- nach Add-on-Neustart, Add-on-Update oder Container-Neuerstellung,
- vor und nach einer Wiederherstellung des persistenten Speichers,
- bei fehlenden Chats, Anmeldeproblemen oder unerwarteten CLI-Pfaden.

Ohne `HACP_CHECK_AUTH=YES` prüft er Struktur, Integrität und die zwei Git-
Credential-Helper. Mit der Variable
prüft er zusätzlich die Erkennung des Codex-Anmeldecaches und die aktive
GitHub-Anmeldung. Der Codex-Status ist dabei keine serverseitige
Gültigkeitsprüfung. Der Audit ist read-only und nimmt keine Reparatur vor.

## Einmalige Neustart- und Update-Abnahme

Für TC-012 werden vor dem kontrollierten Testeingriff ohne Geheimnisinhalte
Vergleichswerte erfasst:

- Anzahl nativer Sitzungsdateien und eine gezielt fortsetzbare Sitzung,
- Erkennung des dateibasierten Codex-Anmeldecaches,
- `gh auth status --active --hostname github.com`,
- beide exakten GitHub-/Gist-Credential-Helper und eine unveränderte fremde
  Git-Einstellung,
- Add-on-Paketliste ohne `gh` beziehungsweise `github-cli` sowie unveränderte
  fremde Pakete,
- Pfade, Git-HEADs und Working-Tree-Status der Projekte,
- Prüfsumme der privaten Memory-Datei,
- installierte Studio-Code-Erweiterungen.

Nach Neustart beziehungsweise Container-Neuerstellung werden dieselben Werte
verglichen. Zusätzlich müssen alle erwarteten Symlinks stimmen und der
Authentifizierungs-Audit ohne `BLOCK` enden. Erst dann ist TC-012 erfüllt.

Diese Baseline dient nur der einmaligen Projektabnahme. Der spätere
Normalbetrieb benötigt vor einem Neustart keine Baseline, Sicherung oder
Vorbereitung; `boot` bindet den bereits persistenten Zustand automatisch ein.

## Störungen

### `boot` meldet nicht installiert

Nicht manuell leere Zielordner oder Links erzeugen. Bestehende Pfade und
Add-on-Logs sichern. Wenn die ursprünglichen angemeldeten `/root`-Bestände noch
vorhanden sind, die Installationsvoraussetzungen wiederherstellen und
`install` kontrolliert ausführen. Sind sie verloren, ist eine erneute Anmeldung
oder ein geprüftes vertrauliches Backup erforderlich.

### Nicht leerer Containerpfad oder unerwarteter Symlink

Nicht löschen, verschieben oder zusammenführen. Beide Pfade getrennt
inventarisieren und ihre Herkunft klären. Bis zu einer bewussten Entscheidung
bleibt der Add-on-Start blockiert.

### Programmprüfsumme ungültig

Das betroffene persistente Programm nicht ausführen. Runtime und Quelle der
Programmdatei untersuchen. `boot` führt absichtlich kein automatisches
Programm-Upgrade durch. Ein Upgrade benötigt eine geprüfte Projektänderung
oder eine dokumentierte Neuinstallation, die den Laufzeitzustand erhält. Der
atomare Upgrade- und Rollback-Ablauf für persistierte Programme bleibt BL-005.

### Neustart benötigt weiterhin APT oder Netz

Prüfen, ob in den Add-on-Optionen noch fremde Einträge unter `packages`
vorhanden sind. `install` entfernt absichtlich nur `gh` und `github-cli`, weil
andere Pakete dem Betreiber gehören. Solange mindestens ein fremdes Paket
konfiguriert ist, kann dessen APT-Verarbeitung vor dem Boot-Hook den
Add-on-Start offline blockieren. Das Paket nur nach eigener Betriebsprüfung
entfernen oder anderweitig persistent bereitstellen.

### Anmeldung ungültig

Persistenz garantiert Aufbewahrung, nicht die serverseitige Gültigkeit eines
Kontos. Nach Rotation oder Ablauf wird die jeweilige CLI erneut angemeldet;
wegen des Symlinks schreibt sie den neuen Zustand direkt in die persistente
Runtime. Danach Auth-Audit wiederholen.

### `git-helper` meldet einen fremden Wert

Den gemeldeten Helper nicht automatisch löschen oder ersetzen. Der Wert bleibt
absichtlich erhalten. Seine Herkunft und Funktion prüfen und bewusst
entscheiden, ob er weiterhin Vorrang haben soll oder auf den dokumentierten
Sollwert migriert werden darf. Bis dahin bleiben `install` und `boot` sicher
blockiert; andere Git-Einstellungen werden nicht verändert.

### `install` kann Add-on-Optionen nicht schreiben

Die verifizierte Runtime kann bereits mit `ready-generation` vorliegen, obwohl
die Supervisor API scheiterte. Nicht neu kopieren oder löschen. Den
Supervisor-Zugriff klären und denselben `install`-Aufruf erneut starten. Eine
vollständig gültige Ready-Generation wird idempotent fortgesetzt; falls der
Startbefehl bereits wirksam war, kann auch `boot` sie nach einer Unterbrechung
automatisch übernehmen.

## Backup und Restore

Container-Persistenz ersetzt kein Backup des Home-Assistant-Speichers. Eine
Sicherung der Runtime enthält Sessions und Anmeldungen und muss deshalb
verschlüsselt und zugriffsbeschränkt sein. Vor der Sicherung sind Codex und
GitHub CLI zu beenden; nach Restore werden Rechte, Prüfsummen, Marker und Links
zuerst per Audit geprüft.

Eine normale lesbare Workspace- oder NAS-Spiegelung darf den Runtime-Root
nicht enthalten. Die private Memory-Datei wird nur entsprechend ihrer lokalen
Datenklassifikation gesichert.
