# Deployment

## Zielumgebungen

| Umgebung | Zweck | Daten | Freigabe |
|---|---|---|---|
| isolierter Test | automatisierte Container-, Fehler- und Security-Tests | ausschließlich künstliche Daten | `./scripts/validate.sh` erfolgreich |
| Home-Assistant-Referenzsystem | reale Installation, Neustart und Container-Neuerstellung | private lokale Runtime | Betreiber bestätigt TC-012 |
| weitere Home-Assistant-Systeme | wiederverwendbare Installation | jeweilige private lokale Runtime | lokale Betriebs- und Sicherheitsfreigabe |

Das GitHub-Repository bleibt privat, bis der Public-Release-Check in
`docs/SECURITY.md` vollständig und ausdrücklich freigegeben wurde.

## Installationsreihenfolge

### 1. Studio Code Server installieren

Das Home-Assistant-Add-on Studio Code Server installieren und einmal starten.
Studio-Code-Einstellungen und Erweiterungen werden vom Add-on bereits unter
`/data/vscode` persistent gehalten. Seine globale Git-Konfiguration liegt
bereits persistent unter `/data/git/.gitconfig` und wird von diesem Projekt
nicht in die eigene Runtime übernommen. Das Projekt ersetzt ihren Gesamtinhalt
nicht und veröffentlicht nur zwei gezielte Helper-Schlüssel atomar.

### 2. Codex-Erweiterung installieren

Die Codex-Erweiterung in der Studio-Code-Erweiterungsansicht installieren und
prüfen, dass der Befehl `codex` in einem neuen Terminal verfügbar ist.

### 3. GitHub CLI einmalig als Bootstrap-Paket installieren

In der Add-on-Konfiguration das Paket `gh` ergänzen. Eine minimale sichere
Konfiguration steht in `config/config.example.yaml`. Anschließend das Add-on
neu starten und prüfen:

```sh
gh --version
```

Das Paket ist nur die Quelle für die einmalige persistente Übernahme der
Programmdatei. Nach erfolgreichem `install` wird die geprüfte persistente
Programmdatei verwendet.

### 4. Beide Programme anmelden

Falls der Device-Code-Login für ChatGPT noch deaktiviert ist, muss er zuerst in
den Sicherheitseinstellungen oder durch den Workspace-Admin freigeschaltet
werden. Codex schreibt den Anmeldecache bei diesem Aufruf ausdrücklich in sein
Home:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login --device-auth
```

Den von Codex ausgegebenen Link im Browser öffnen, den einmaligen Code eingeben
und die Freigabe bestätigen. Danach erkennt folgender Befehl den lokalen Cache:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login status
```

`codex login status` ist eine Cache- und Methodenprüfung, kein eigenständiger
Nachweis der serverseitigen Gültigkeit.

GitHub CLI wird mit festem Konfigurationspfad und bewusst dateibasierter
Credential-Ablage angemeldet:

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

GitHub CLI zeigt einen einmaligen Gerätecode. Öffnet sich der Browser nicht,
`https://github.com/login/device` aufrufen, den Code eingeben, **Continue** und
danach **Authorize GitHub CLI** wählen. `--insecure-storage` ist hier bewusst
nötig: Der geheime Wert muss statt in einem flüchtigen Container-Keyring in der
privaten persistenten Runtime liegen. Deren Verzeichnisse gehören `root:root`
und besitzen Modus `0700`. Niemals `gh auth status --show-token` verwenden.

Keine Ausgabe mit Anmeldedaten oder Gerätecodes in Logs, Issues oder
Dokumentation übernehmen.

### 5. Installationsprojekt unter `/config` klonen und einmal installieren

```sh
GH_CONFIG_DIR=/root/.config/gh \
gh repo clone Domuno18/home-assistant-codex-persistence /config/home-assistant-codex-persistence
cd /config/home-assistant-codex-persistence
./scripts/validate.sh
```

Danach alle Codex-Chats und Codex-Prozesse schließen. In einem normalen
Studio-Code-Terminal ausführen:

```sh
cd /config/home-assistant-codex-persistence
HACP_INSTALL_OK=YES sh ./scripts/ha-codex-persistence.sh install
```

Das Standardziel ist `/data/codex-persistence`. `install` prüft beide
Anmeldungen, erstellt stabile verifizierte Kopien, persistiert die aufgelösten
CLI-Programme, setzt die Kompatibilitätslinks und ergänzt den automatischen
`boot`-Befehl in den bestehenden Add-on-Optionen. Erst nachdem die persistente
`gh`-Kopie geprüft und die Ready-Generation synchronisiert ist, entfernt
dasselbe Supervisor-Update ausschließlich `gh` beziehungsweise `github-cli`
aus `packages`, erhält fremde Pakete und Befehle in ihrer Reihenfolge und setzt
den verwalteten Bootbefehl an die erste Stelle. Vor der Erfolgsmeldung setzt
`install` außerdem ausschließlich die beiden Git-Credential-Helper für
`github.com` und `gist.github.com` auf die persistente `gh`-Binary.

Für die Referenzinstallation wird nur der Installationsbefehl angepasst:

```sh
cd /config/Codex/Projekte/home-assistant-codex-persistence
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

Git und GitHub verteilen dabei ausschließlich das versionierte
Installationsprojekt mit Skript, Tests und Dokumentation. Sie sind weder
Persistenzmechanismus noch Backup: Die private Runtime liegt ausschließlich
unter `HACP_RUNTIME_ROOT`, die reale lokale `MEMORY.md` im persistenten
Workspace unter `/config`.

## Einmalige Installationsabnahme

Standardpfad:

```sh
HACP_CHECK_AUTH=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
```

Referenzpfad:

```sh
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_CHECK_AUTH=YES \
sh /config/Codex/.runtime/bootstrap/ha-codex-persistence.sh audit
```

Der Audit muss ausschließlich `OK` und abschließend `OK result active`
melden. Außerdem wird in den Add-on-Optionen geprüft, dass alle bisherigen
`init_commands` erhalten sind, genau ein persistenter `boot`-Befehl an erster
Stelle vorhanden ist, `packages` weder `gh` noch `github-cli` enthält und alle
fremden Pakete unverändert geblieben sind.

Zusätzlich muss `audit` den exakten persistenten GitHub- und Gist-Helper als
`OK` melden. Die Add-on-eigene `/data/git/.gitconfig` bleibt erhalten; es werden
nur die beiden ausdrücklich verwalteten Schlüssel geändert.

Diese Abnahme kontrolliert die einmalige Übernahme. Sie ist kein Chat-Backup
und kein Prepare-Schritt für spätere Neustarts. Nach erfolgreichem `install`
werden neue Zustände direkt persistent geschrieben; normale Neustarts
benötigen keine vorherige Sicherung, keinen Export und keinen manuellen
Skriptaufruf.

## Gezielte Git-Credential-Helper

Der normale Add-on-Pfad `/root/.gitconfig` verweist auf die persistente
`/data/git/.gitconfig`. Weder `install` noch `boot` übernimmt diese Datei in die
eigene Runtime oder ersetzt ihren Gesamtinhalt. Beide veröffentlichen atomar
ausschließlich:

```text
credential.https://github.com.helper
credential.https://gist.github.com.helper
```

Für jeden Schlüssel müssen danach genau zwei Werte in dieser Reihenfolge
vorhanden sein:

```text
1. <leer>  (Reset niedriger priorisierter beziehungsweise System-Helper)
2. !GH_CONFIG_DIR=/root/.config/gh /usr/local/bin/gh auth git-credential
```

Fehlende, leere und bekannte alte `!…/gh auth git-credential`-Einträge werden
migriert. Alle sonstigen Git-Einstellungen bleiben erhalten. Ein fremder
benutzerdefinierter Wert in einem der beiden verwalteten Schlüssel wird niemals
automatisch ersetzt und führt vor der Aktivierung zu `BLOCK`. Der persistente
Bootbefehl prüft denselben Vertrag bei jedem Containerstart automatisch; es ist
kein Prepare-Schritt vor späteren Neustarts erforderlich. Die atomare
Veröffentlichung erhält alle übrigen Werte sowie Modus und Eigentümer.

## Offline-Steady-State

Nach der erfolgreichen Installation benötigt der Normalstart des persistenten
`gh` weder APT noch Netzwerkzugriff. `boot` installiert und aktualisiert keine
Programme. Verbleiben fremde Einträge in `packages`, verarbeitet das Add-on
diese weiterhin vor `init_commands`; deren Paketquellen bleiben deshalb ein
dokumentiertes Restrisiko für einen vollständig offlinefähigen Add-on-Start.
Upgrades persistierter Programme erfolgen später nur über den geprüften Ablauf
aus BL-005, niemals während `boot`.

## Einmaliger Neustart-Nachweis

Für die einmalige reale TC-012-Abnahme werden vor dem Testneustart ohne private
Inhalte Vergleichswerte erfasst:

- Anzahl nativer Codex-Sitzungsdateien,
- eine gezielt fortsetzbare Sitzung,
- beide Login-Status,
- Projektpfade, Git-HEADs und Working-Tree-Status,
- Prüfsumme der privaten Memory-Datei,
- installierte Studio-Code-Erweiterungen.

Danach das Add-on kontrolliert neu starten. `boot` läuft automatisch vor
`code-server`; kein manueller Chatimport und keine erneute Anmeldung sind
vorgesehen. Nach dem Start werden Audit und Baseline-Vergleich wiederholt.

Diese Vergleichswerte dienen nur dem Projektnachweis. Im späteren Normalbetrieb
ist vor einem Neustart keine Baseline, Sicherung oder Vorbereitung erforderlich.

Für die vollständige TC-012-Abnahme folgt anschließend eine kontrollierte
Container-Neuerstellung beziehungsweise ein Add-on-Update mit demselben
Nachweis.

## Memory einbinden

`install` erzeugt aus `examples/memory` ausschließlich fehlende
`Memories/AGENTS.md` und `Memories/MEMORY.md`. Vorhandene Dateien bleiben
bytegenau unangetastet. Als globale Startdatei verwendet Codex die nicht leere
`$CODEX_HOME/AGENTS.override.md`, falls sie existiert, andernfalls
`$CODEX_HOME/AGENTS.md`. Ein verwalteter Block verweist mit absoluten Pfaden
zuerst auf die Memory-Regeln und danach auf die private `MEMORY.md`; vorhandener
fremder Inhalt wird nicht ersetzt. Die globale Lage und absoluten Pfade wirken
auch beim Start in verschachtelten Git-Repositories.

Der persistente Workspace darf nicht das Installationsrepository selbst sein
und nicht unter dessen Checkout liegen. Die befüllte Arbeitskopie wird niemals
in dieses Repository zurückkopiert. Native Chats bleiben unter
`codex-home/sessions`.

## Fehlgeschlagenes Deployment

- Bei `BLOCK` weder Quell- noch Zielpfade löschen, verschieben oder mischen.
- Einen fehlenden oder falschen Link nicht manuell über einen gefüllten Pfad
  legen.
- Add-on-Logs und Audit-Ausgabe ohne Geheimniswerte sichern.
- Wenn die Supervisor-Option erst im letzten Installationsschritt scheiterte,
  den Zustand auditieren, Supervisor-Zugriff klären und denselben
  `install`-Aufruf wiederholen. Bis das atomare Optionsupdate erfolgreich war,
  kann `gh` noch als Bootstrap-Paket konfiguriert und damit von APT oder dem
  Netzwerk abhängig sein.
- Bei ungültiger Programmprüfsumme das Programm nicht ausführen.
- Bei ungültiger Anmeldung das betroffene Konto rotieren oder erneut anmelden
  und danach den Auth-Audit wiederholen.
- Bei `BLOCK git-helper` den gemeldeten vorhandenen Helper nicht löschen oder
  überschreiben. Seine Herkunft und gewünschte Funktion klären; erst danach
  bewusst auf den dokumentierten Sollwert migrieren oder die Projektinstallation
  unverändert abgebrochen lassen.

Es gibt keinen automatischen Daten-Merge und kein automatisches
Programm-Upgrade während `boot`.

## Rücknahme und Wiederherstellung

Vor einer Rücknahme wird der persistente Runtime-Bereich unverändert erhalten.
Eine Löschung ist kein Rollback. Soll die Lösung außer Betrieb genommen werden,
müssen zuerst Add-on-Starteintrag, erwartete Links, benötigte Arbeitsdaten und
ein verschlüsselter Wiederherstellungspunkt einzeln geprüft werden.

Nach einer Wiederherstellung aus einem vertraulichen Backup werden Eigentümer,
Modi, Marker, Programmprüfsummen und Links per read-only Audit geprüft, bevor
Codex oder GitHub CLI gestartet werden.
