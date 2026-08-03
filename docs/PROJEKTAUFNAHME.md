# Projektaufnahme

## Ausgangslage

Studio Code Server muss in Home Assistant als Add-on und damit in einem
Container laufen. Studio-Code-Einstellungen und Erweiterungen sind bereits
unter `/data/vscode` persistent. Der zusätzlich installierte Zustand von Codex
und GitHub CLI liegt dagegen standardmäßig teilweise unter `/root` und kann bei
einem Containerwechsel verloren gehen.

Betroffen sind insbesondere:

- native, fortsetzbare Codex-Sitzungen unter `/root/.codex/sessions`,
- Codex-Anmeldung und -Konfiguration im vollständigen `/root/.codex`,
- GitHub-CLI-Anmeldung und -Konfiguration unter `/root/.config/gh`,
- ausführbare Codex- und GitHub-CLI-Programme, falls ihre ursprüngliche Lage
  nicht containerübergreifend besteht.

Projekte und ein lesbares Langzeitgedächtnis sollen ebenfalls persistent sein,
aber getrennt von den geheimen Runtime-Daten in einem Workspace unter
`/config` liegen.

## Verstandener Auftrag

Das Repository `home-assistant-codex-persistence` stellt eine allgemein
nutzbare Lösung mit genau drei öffentlichen Betriebsbefehlen bereit:

- `install`: einmal nach Installation und Anmeldung beider CLIs ausführen,
- `boot`: danach automatisch vor `code-server` ausführen,
- `audit`: den Zustand jederzeit rein lesend prüfen.

Der generische Runtime-Standard ist `/data/codex-persistence`; die
Referenzinstallation verwendet `/config/Codex/.runtime`.

## Bestätigte Installationsfolge

1. Studio Code Server installieren.
2. Codex-Erweiterung installieren.
3. GitHub CLI einmalig als Add-on-Bootstrap-Paket `gh` installieren.
4. Codex und GitHub CLI anmelden.
5. Installationsprojekt unter `/config` klonen, Codex-Prozesse schließen und
   einmal `install` ausführen.

Danach werden bei einem Neustart keine Chats exportiert oder importiert. Codex
und GitHub CLI verwenden über Symlinks direkt den persistenten Zustand.
Sobald `install` die persistente `gh`-Kopie geprüft und die Ready-Generation
synchronisiert hat, entfernt dasselbe Supervisor-Update nur `gh` und
`github-cli` aus `packages`, erhält alle fremden Pakete und Befehle und setzt
den verwalteten Bootbefehl an die erste Stelle. Damit benötigt `gh` im
Normalstart weder APT noch Netzwerk. Verbleibende fremde Pakete werden vom
Add-on weiterhin vor `init_commands` verarbeitet und bleiben ein dokumentiertes
Restrisiko für einen vollständig offlinefähigen Start.

Git und GitHub dienen nur als versionierte Ablage des Installationsprojekts.
Sie persistieren und sichern weder Chats noch Anmeldungen: Die private Runtime
liegt ausschließlich unter `HACP_RUNTIME_ROOT`, die reale lokale `MEMORY.md`
im persistenten Workspace.

## Erfolg

- AC-001: Eine vorhandene native Codex-Sitzung bleibt fortsetzbar.
- AC-002 und AC-003: Beide Anmeldungen bleiben gültig.
- AC-004: Projektpfade und Git-Zustände bleiben unverändert.
- AC-005 und AC-006: Links stimmen und wiederholte Starts sind idempotent.
- AC-010: Neustart und Container-Neuerstellung benötigen keine manuelle
  Wiederherstellung.
- AC-011: Die private Memory-Datei bleibt im Workspace und wird beim
  Sitzungsstart geladen; native Chats bleiben unter `codex-home/sessions`.

## Schutzbedarf

Anmeldedateien, native Sitzungen, Datenbanken, private Laufzeitprofile und
reale Memory-Inhalte sind vertraulich oder geheim. Sie bleiben in den dafür
vorgesehenen lokalen persistenten Bereichen und dürfen nicht in Repository,
Logs, Beispiele oder normale ungeschützte Spiegelungen gelangen.

Die Projektdateien enthalten nur generische Pfade, künstliche Testdaten und
eine leere neutrale Memory-Vorlage.

## Status

Projektverständnis und Hybrid-Lifecycle sind dokumentiert. Die bestehende
Basisimplementierung und ihre isolierten Tests sind abgeschlossen; die
Pakettransition ist im Skript umgesetzt, ihr automatisierter
Supervisor-Nachweis TC-016 bleibt als BL-014 offen. Die reale Referenzabnahme
TC-012 steht vor einer öffentlichen Freigabe noch aus.
