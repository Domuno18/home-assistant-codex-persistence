# Systemkontext

## System und Grenze

`home-assistant-codex-persistence` läuft innerhalb des Studio-Code-Server-
Add-ons, speichert seinen privaten Zustand aber außerhalb der austauschbaren
Containerdateien. Die Systemgrenze umfasst:

- einmaliges `install` nach vorhandener Installation und Anmeldung beider CLIs,
- persistente Runtime-Generation,
- automatisches `boot` über Add-on-`init_commands`,
- read-only `audit`,
- gezielte Bindung der zwei GitHub-Credential-Helper in der bereits
  persistenten Add-on-Git-Konfiguration,
- neutrale Memory-Vorlage und dokumentierte Workspace-Grenze.

Nicht innerhalb der Systemgrenze liegen die native Persistenz von Studio Code
und Erweiterungen unter `/data/vscode`, Home-Assistant-Backuptechnik,
Kontenanbieter, Projektinhalte sowie reale Memory-Inhalte.

## Akteure und Nachbarsysteme

| Akteur oder System | Erwartung an das Projekt | Erwartung des Projekts | Vertrauensgrenze |
|---|---|---|---|
| Home-Assistant-Betreiber | einmalige verständliche Installation und sicherer Wiederanlauf | führt Installation und reale Abnahme bewusst aus | menschliche Freigabegrenze |
| Studio Code Server Add-on | gültiger Startbefehl ohne Zerstörung bestehender Optionen oder Git-Einstellungen | verarbeitet `packages` vor `init_commands`, führt diese vor `code-server` aus und stellt `/data/vscode` sowie `/data/git/.gitconfig` persistent bereit | Add-on-Grenze |
| Home Assistant Supervisor | nur bekannte gh-Bootstrap-Paketnamen entfernen, fremde Optionen erhalten und Boot-Hook zuerst setzen | lokale authentifizierte Options-API und Laufzeittoken | privilegierte lokale API |
| Codex CLI | vollständiges persistentes Home und verfügbarer Befehl | native Zustandsstruktur unter `/root/.codex` und Statusprüfung | private Runtime-Grenze |
| GitHub CLI | persistente Konfiguration und verfügbarer Befehl | Konfigurationsstruktur unter `/root/.config/gh` und Statusprüfung | private Runtime-Grenze |
| GitHub | authentifizierter Zugriff auf das private Projekt-Repository | gültige Benutzeranmeldung | externe Vertrauensgrenze |
| persistenter Home-Assistant-Speicher | private Runtime bleibt über Containerwechsel erhalten | regulärer sicherer Pfad unter `/data`, `/config` oder `/share` | Speichergrenze |
| persistenter Workspace | Projekte und reale Memory-Datei bleiben erhalten | liegt außerhalb der privaten Runtime und des Wegwerfcontainers | Arbeitsbereichsgrenze |
| Projekt-Repository | portable Skripte, Tests, Doku und neutrale Beispiele | enthält keine echten Runtime- oder Memory-Inhalte | Veröffentlichungsgrenze |

## Hauptdatenflüsse

### Einmalige Installation

```text
/root/.codex ── stabile Kopie und Verifikation ──> RUNTIME_ROOT/current/codex-home
/root/.config/gh ─ stabile Kopie und Verifikation > RUNTIME_ROOT/current/gh
aufgelöste CLI-Programme ─ SHA-256 und Version ──> RUNTIME_ROOT/current/tools
/root/.gitconfig ─ nur zwei Helper prüfen/setzen ─> persistentes gh
Installationsskript ─ persistente Kopie ─────────> RUNTIME_ROOT/bootstrap
Installationsskript ─ lokale Supervisor API ─────> gh aus packages entfernen
                                              └─> boot zuerst in init_commands
```

Erst nach erfolgreicher Prüfung werden die gewohnten Containerpfade auf die
persistente Generation verlinkt.

### Automatischer Start

```text
init_commands -> persistenter boot -> Marker und Prüfsummen prüfen
              -> /root- und CLI-Links setzen
              -> zwei GitHub-Helper prüfen/setzen -> code-server startet
```

`boot` kopiert und importiert keine Chats. Er verbindet einen neuen Container
mit dem bereits installierten Zustand. Die GitHub CLI kommt dabei aus der
persistenten verifizierten Binary; `gh` verursacht keinen Paket- oder
Netzzugriff. Die Add-on-eigene Git-Konfiguration bleibt bestehen; nur fehlende,
leere oder bekannte alte GitHub-/Gist-Helper werden gezielt auf je ein
geordnetes Paar aus leerem Resetwert und persistentem `gh`-Helper migriert. Ein
fremder Helper blockiert unverändert. Verbleibende fremde Add-on-Pakete werden
vom Add-on weiterhin vor dem Hook verarbeitet und bleiben ein vom Betreiber
verantwortetes Offline-Risiko.

### Read-only Audit

```text
Betreiber -> audit -> Marker, Runtime, Links, Rechte, Sitzungsanzahl
                   -> exakte GitHub-/Gist-Helper
                   -> optional Codex-/GitHub-Login-Status
                   -> OK oder BLOCK auf Standardausgabe
```

Die Ausgabe enthält keine Datei-, Chat-, Memory- oder Anmeldungsinhalte.

### Workspace und Memory

```text
neutrale Vorlage im Repository -> private Kopie im persistenten Workspace
globale $CODEX_HOME/AGENTS.override.md oder AGENTS.md
                            -> Memory-Regeln -> private MEMORY.md
Codex CLI -> native fortsetzbare Chats -> codex-home/sessions
```

Memory und native Sessions ergänzen einander, ersetzen sich aber nicht.

## Vertrauensannahmen

- `/data` ist der private persistente Standardbereich des Add-ons.
- Die Referenz kann denselben Vertrag unter `/config/Codex/.runtime` nutzen.
- `init_commands` laufen vor `code-server`.
- `/root/.gitconfig` verweist auf die vom Add-on persistent geführte
  `/data/git/.gitconfig`; das Projekt darf dort nur zwei Helper-Schlüssel
  als geordnete Reset-plus-Helper-Wertepaare verwalten und muss alle übrigen
  Werte sowie Modus und Eigentümer erhalten.
- Eine nicht leere fremde `packages`-Liste kann vor `init_commands` einen
  APT- und Netzzugriff erzwingen; die Offline-Zusage gilt nur für die durch
  dieses Projekt entfernte gh-Abhängigkeit.
- Kontenanbieter können Anmeldungen unabhängig vom lokalen Speicher widerrufen.
- Persistenz schützt vor Containerwechsel, nicht vor Verlust des persistenten
  Home-Assistant-Speichers.
