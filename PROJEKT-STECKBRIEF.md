# Projekt-Steckbrief: home-assistant-codex-persistence

## Identität

| Feld | Wert |
|---|---|
| Projekt | Home Assistant Codex Persistence |
| Repository | `home-assistant-codex-persistence` |
| Nutzer | Home-Assistant-Betreiber mit Studio Code Server, Codex und GitHub CLI |
| Auftrag und Prioritäten | Repository-Projektpflege |
| Fachliche Abnahme | Betreiber des Home-Assistant-Referenzsystems |
| Zieltermin der ersten Version | 2026-07-30 |
| Status | Runtime migriert und Add-on-Neustart bestätigt; direkter init_commands-Vertrag in `9102b34`; Host-Neustart und Add-on-Update als weitere reale Abnahme offen |
| Sichtbarkeit | privat bis zur dokumentierten Veröffentlichungsfreigabe |

## Ziel und Nutzen

Codex-Home, native Chats, Codex-Anmeldung und -Konfiguration sowie die
GitHub-CLI-Anmeldung werden außerhalb des austauschbaren Studio-Code-Containers
geführt. Nach einer einmaligen Installation stellt ein automatischer
Startbefehl alle benötigten Links und die zwei GitHub-Credential-Helper wieder
her. Projekte und das verdichtete Langzeitgedächtnis liegen unabhängig davon in
einem persistenten Workspace.

Damit bleiben nach Neustart, Add-on-Update und Container-Neuerstellung
erhalten:

- fortsetzbare Codex-Sitzungen,
- Codex- und GitHub-Anmeldung,
- Codex-Konfiguration,
- benötigte CLI-Programme,
- HTTPS-Git-Zugriff über die persistente GitHub-Anmeldung,
- Studio Code und Erweiterungen über die vorhandene Add-on-Persistenz,
- Projekte und private Memory-Datei im persistenten Workspace.

## Installationsfolge

1. Studio Code Server installieren.
2. Codex-Erweiterung installieren.
3. GitHub CLI einmalig als Add-on-Bootstrap-Paket `gh` installieren.
4. Codex und GitHub CLI anmelden.
5. Repository unter `/config` klonen und einmal `install` ausführen.

Danach läuft `boot` automatisch vor `code-server`; `audit` bleibt jederzeit
read-only verfügbar.
Nach verifizierter Persistenz entfernt dasselbe Supervisor-Update nur
`gh`/`github-cli` aus `packages`, erhält fremde Pakete und Befehle und setzt
den verwalteten Bootbefehl zuerst. Dadurch startet das persistierte `gh` ohne
APT oder Netzwerk. Fremde verbleibende Pakete bleiben ein dokumentiertes
Offline-Restrisiko.

Git und GitHub enthalten ausschließlich das Installationsprojekt. Sie sind
weder Persistenzmechanismus noch Backup; die private Runtime liegt unter
`HACP_RUNTIME_ROOT`, die reale lokale `MEMORY.md` im persistenten Workspace.

## Speicherorte

| Bereich | Generischer Standard | Referenzbeispiel |
|---|---|---|
| private Runtime | `/data/codex-persistence` | `/config/Codex/.runtime` |
| Studio Code und Erweiterungen | `/data/vscode` | `/data/vscode` |
| globale Git-Konfiguration | Add-on-eigene `/data/git/.gitconfig` | `/data/git/.gitconfig`; Projekt verwaltet nur zwei Helper |
| Projekte und reale Memory-Datei | persistenter Workspace unter `/config` | `/config/Codex` |

## Umfang

**Im Projekt:**

- portable Shell-Implementierung für `install`, `boot` und `audit`,
- persistente Codex-/GitHub-CLI-Daten und geprüfte Programme,
- automatische Einbindung über `init_commands`,
- atomare, selektive Entfernung der einmaligen `gh`-Bootstrap-Pakete bei
  unverändertem Erhalt fremder Add-on-Optionen,
- gezielte Verwaltung nur der GitHub-/Gist-Credential-Helper in der
  Add-on-eigenen persistenten Git-Konfiguration,
- neutrale Memory-Vorlage,
- Tests, Security-, Betriebs- und Abnahmedokumentation.

**Nicht im Projekt:**

- Installation oder interne Persistenz von Studio Code und Erweiterungen,
- echte Anmeldedaten, Sitzungen oder befüllte Memory-Dateien im Repository,
- automatische Programm-Upgrades während `boot`,
- unverschlüsselte Sicherung der privaten Runtime,
- Wiederherstellung nativer Chats aus Markdown-Exporten.

## Modellierungsbedarf

| Bereich | Status | Dokument |
|---|---|---|
| Domänenmodell | erforderlich | `docs/DOMAENENMODELL.md` |
| Schnittstellen und Startreihenfolge | erforderlich | `docs/SCHNITTSTELLEN.md` |
| Zustands- und Sicherheitslogik | erforderlich | `docs/DOMAENENMODELL.md`, `docs/SECURITY.md` |
| ISA-95 | nicht anwendbar | `docs/ISA95-MODELL.md` |
| Mathematik oder Regelung | nicht anwendbar | `docs/MATHEMATISCHES-MODELL.md` |

## Freigabestand

- [x] Projektverständnis und Schutzbedarf dokumentiert
- [x] Anforderungen, Architektur und Domänenregeln rückverfolgbar
- [x] neutrale Memory-Vorlage ohne private Inhalte vorhanden
- [x] isolierte Container-, Fehler- und Security-Tests erfolgreich
- [x] Pakettransition im Skript umgesetzt
- [x] Git-Helper-Migration und Konfliktfall durch TC-017 automatisiert
- [x] automatisierter Supervisor-Test TC-016 abgeschlossen
- [x] reale Installation und Add-on-Neustart gemäß TC-012 bestätigt
- [ ] Host-Neustart; Add-on-Update/Container-Neuerstellung als zukünftiger Regressionstest gemäß TC-012 abgenommen
- [ ] Public-Release-Check ausdrücklich freigegeben
