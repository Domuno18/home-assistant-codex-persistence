# Projektauftrag

> Status: Runtime-Migration und Add-on-Neustart sind bestätigt;
> Host-Neustart; Add-on-Update/Container-Neuerstellung als zukünftiger Regressionstest der TC-012 bleiben offen.

## Auftrag

Für Home-Assistant-Nutzer mit dem Add-on Studio Code Server wird eine
wiederverwendbare Lösung bereitgestellt, die den vollständigen nativen
Codex-Zustand, die GitHub-CLI-Konfiguration und benötigte CLI-Programme
außerhalb des austauschbaren Containers persistent hält.

Die Bedienung bleibt einfach:

1. Studio Code Server installieren.
2. Codex-Erweiterung installieren.
3. GitHub CLI einmalig als Add-on-Bootstrap-Paket `gh` installieren.
4. Beide Programme anmelden.
5. Installationsprojekt unter `/config` klonen und genau einmal `install`
   ausführen.

Danach übernimmt `boot` den automatischen Wiederanlauf vor `code-server`.
`audit` prüft den Zustand rein lesend.

Nach erfolgreicher Prüfung und Ready-Synchronisierung entfernt `install` im
selben Supervisor-Update ausschließlich `gh` beziehungsweise `github-cli` aus
`packages`, erhält fremde Pakete und Befehle und setzt den verwalteten
Bootbefehl an die erste Stelle. Der Normalstart des persistenten `gh` benötigt
dadurch weder APT noch Netzwerkzugriff. Fremde Add-on-Pakete bleiben davon
unberührt und begrenzen gegebenenfalls die vollständige Offline-Fähigkeit.

Git und GitHub sind ausschließlich Ablage und Verteilweg des versionierten
Installationsprojekts. Sie sind weder Runtime-Persistenz noch Backup. Die
private Runtime liegt unter `HACP_RUNTIME_ROOT`; die reale lokale `MEMORY.md`
liegt getrennt im persistenten Workspace.

## Ziel und Nutzen

Nach Neustart, Add-on-Update oder Container-Neuerstellung sollen ohne erneute
Anmeldung und ohne Chatimport verfügbar sein:

- native, fortsetzbare Codex-Sitzungen,
- Codex-Anmeldung und -Konfiguration,
- GitHub-CLI-Anmeldung und -Konfiguration,
- geprüfte Codex- und GitHub-CLI-Programme,
- Projekte und private Memory-Datei im persistenten Workspace,
- Studio Code und Erweiterungen über die bereits vorhandene
  Add-on-Persistenz.

## Rollen

| Rolle | Verantwortliche Gruppe | Verantwortung |
|---|---|---|
| Auftrag und Prioritäten | Repository-Projektpflege | Umfang, Anforderungen und Releases |
| Nutzer | Home-Assistant-Betreiber | lokale Installation und Nutzung |
| Betrieb | Home-Assistant-Betreiber | Add-on-Optionen, Audit, Neustart und Backup |
| Konto und Credentials | jeweiliger Kontoinhaber | Anmeldung, Rotation und Sperrung |
| Abnahme | Betreiber des Referenzsystems | TC-012 und Freigabe des Betriebszustands |
| Memory-Pflege | Codex nach lokaler Regel, bestätigt durch Nutzer | verdichteten Kontext aktuell und secret-frei halten |

## Umfang

### Im Projekt

- Anforderungen REQ-F-001 bis REQ-O-004,
- Shell-Implementierung für `install`, `boot` und `audit`,
- automatische, deduplizierte Integration in `init_commands`,
- atomare Supervisor-Transition für das einmalige `gh`-Bootstrap-Paket bei
  unverändertem Erhalt fremder Pakete und Befehle,
- Standardziel `/data/codex-persistence`,
- Referenzbeispiel `/config/Codex/.runtime`,
- neutrale Memory-Vorlage ohne reale Inhalte,
- isolierte Integrations-, Konflikt-, Integritäts- und Security-Tests,
- Betriebs-, Deployment- und Abnahmedokumentation.

### Nicht im Projekt

- Persistenzimplementierung für Studio Code und Erweiterungen; sie besteht
  bereits unter `/data/vscode`,
- automatische Installation oder Anmeldung von Benutzerkonten,
- echte Anmeldedaten, Sessions, Datenbanken oder reale Memory-Inhalte im
  Repository,
- automatischer Merge konkurrierender Runtime-Bestände,
- automatisches Upgrade persistierter CLI-Programme während `boot`,
- unverschlüsselte Runtime-Sicherung,
- Chatwiederherstellung aus Markdown-Exporten.

## Erfolgskriterien

Die fachliche Abnahme verwendet AC-001 bis AC-012 aus
`docs/ANFORDERUNGEN.md`. Der zentrale Systemnachweis TC-012 umfasst einen
realen Add-on-Neustart und eine Container-Neuerstellung. Kein fehlender Chat,
kein geänderter Projektzustand, keine erneute Anmeldung und kein manueller
Startbefehl sind zulässig. Nach `install` sind `gh` und `github-cli` nicht mehr
als Add-on-Paket konfiguriert, der verwaltete Bootbefehl steht zuerst und das
persistierte `gh` startet ohne APT- oder Netzwerkzugriff. Die persistente
Add-on-Git-Konfiguration enthält für GitHub und Gist jeweils das festgelegte
Reset-plus-Helper-Paar, ohne andere Einstellungen zu verlieren.

## Annahmen

| ID | Aussage | Nachweis |
|---|---|---|
| ANN-001 | Der konfigurierte Zielpfad bleibt über Neustart, Update und Container-Neuerstellung persistent. | reale TC-012-Abnahme |
| ANN-002 | `init_commands` laufen vor `code-server` mit den benötigten Rechten. | Add-on-Quellcode und reale Startabnahme |
| ANN-003 | Studio Code und Erweiterungen bleiben unabhängig unter `/data/vscode` persistent. | Add-on-Vertrag und TC-012 |
| ANN-004 | Das Add-on verarbeitet eine nicht leere `packages`-Liste über APT vor `init_commands`; eine leere Liste überspringt diesen Schritt. | gepinnter Add-on-Quellcode, TC-016 und TC-012 |

## Risiken

| ID | Risiko | Maßnahme |
|---|---|---|
| RISK-001 | Neustart vor erfolgreichem `install` verliert möglicherweise den einzigen `/root`-Bestand. | Vor Neustart erfolgreichen Auth-Audit verlangen. |
| RISK-002 | Aktive Codex-Prozesse verändern Sessions oder Datenbanken während der Kopie. | Codex-Prozess blockiert `install`; stabile Mehrfachprüfung. |
| RISK-003 | Runtime oder reale Memory-Inhalte gelangen in Git oder Spiegelungen. | strikte Speichergrenzen, Ausschlüsse und Security-Scan. |
| RISK-004 | Persistierte Anmeldung läuft serverseitig ab. | Status prüfen und betroffene CLI kontrolliert erneut anmelden. |
| RISK-005 | Persistenter Home-Assistant-Speicher wird beschädigt. | verschlüsseltes Backup und geprüfter Restore außerhalb des Containervertrags. |
| RISK-006 | Ein fremdes verbleibendes Add-on-Paket benötigt vor `init_commands` APT oder Netzwerk und verhindert einen Offline-Start. | fremde Pakete nie automatisch verändern; Restrisiko anzeigen und Betreiberentscheidung dokumentieren. |
| RISK-007 | Persistierte CLI-Programme veralten oder werden mit einem späteren Container inkompatibel. | expliziter geprüfter Upgrade-/Rollback-Ablauf gemäß BL-005; kein Upgrade in `boot`. |

## Ausstehender Nachweis

Die technische Basis,
Pakettransition und der gehärtete Supervisor-Vertrag sind einschließlich
TC-016 isoliert validiert. Runtime-Migration und Add-on-Neustart sind bestätigt; Host-Neustart; Add-on-Update/Container-Neuerstellung als zukünftiger Regressionstest bleiben offen.

## Freigabe

- [x] Auftrag, Umfang und Nicht-Ziele bestätigt
- [x] Anforderungen und Akzeptanzkriterien prüfbar dokumentiert
- [x] Schutzbedarf und Sicherheitsgrenzen bestätigt
- [x] Basisimplementierung und bisherige isolierte Tests erfolgreich
- [x] Pakettransition im Skript implementiert
- [x] automatisierter Supervisor-Nachweis TC-016 erfolgreich
- [ ] reale Referenzabnahme TC-012 erfolgreich
- [ ] öffentliche Freigabe nach Public-Release-Check erteilt
