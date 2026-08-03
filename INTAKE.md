# Bestätigter Projekt-Intake

## Kurzfassung

| Frage | Bestätigte Antwort |
|---|---|
| Was soll entstehen? | Eine wiederverwendbare Persistenzlösung für Codex CLI und GitHub CLI im Home-Assistant-Add-on Studio Code Server. |
| Welches Problem wird gelöst? | Der austauschbare Container darf nicht länger die einzige Kopie nativer Codex-Chats, Anmeldungen, Konfiguration und benötigter CLI-Programme enthalten. |
| Wer nutzt das Ergebnis? | Home-Assistant-Betreiber, die Studio Code Server mit Codex und GitHub CLI verwenden. |
| Woran ist Erfolg erkennbar? | Nach Neustart oder Container-Neuerstellung sind native Chats fortsetzbar, beide Anmeldungen gültig, HTTPS-Git-Zugriffe an die persistente GitHub-Anmeldung gebunden, Projekte und Memory vorhanden und der Audit meldet keinen `BLOCK`. |
| Welche Systeme sind beteiligt? | Home Assistant Supervisor, Studio Code Server, Codex-Erweiterung und Codex CLI, GitHub CLI, persistenter Add-on-Speicher und persistenter Workspace. |
| Was ist vertraulich? | Anmeldedateien, native Sessions, Datenbanken, private Konfiguration und reale Memory-Inhalte. |

## Bestätigte Installationsfolge

1. Studio Code Server als Home-Assistant-Add-on installieren.
2. Codex-Erweiterung in Studio Code installieren.
3. GitHub CLI einmalig als Bootstrap-Paket `gh` über die
   Add-on-Konfiguration installieren.
4. Codex und GitHub CLI anmelden und beide Statusprüfungen erfolgreich
   ausführen.
5. `home-assistant-codex-persistence` persistent unter `/config` klonen,
   Codex-Prozesse schließen und genau einmal `install` aus einem normalen
   Terminal ausführen.

Nach erfolgreichem `install` läuft `boot` bei jedem Add-on-Start automatisch
vor `code-server`. `audit` bleibt ein rein lesender Prüfbefehl.
Nach Prüfung der persistenten `gh`-Kopie und Synchronisierung der
Ready-Generation entfernt dasselbe Supervisor-Update nur `gh` und
`github-cli` aus `packages`, erhält fremde Pakete und Befehle und setzt den
verwalteten Bootbefehl an die erste Stelle. Der Normalstart von `gh` benötigt
danach weder APT noch Netzwerk; fremde verbleibende Pakete begrenzen diese
Offline-Garantie für den gesamten Add-on-Start.

## Speicherentscheidung

- Generischer Standard: `/data/codex-persistence`
- Konfigurierbare Alternative: sicherer absoluter Pfad unter `/data`, `/config`
  oder `/share`
- Referenzbeispiel: `/config/Codex/.runtime`
- Studio Code und Erweiterungen: bereits durch das Add-on unter `/data/vscode`
  persistent
- globale Git-Konfiguration: bereits durch das Add-on unter
  `/data/git/.gitconfig` persistent; das Projekt veröffentlicht darin nur die
  zwei geordneten GitHub-/Gist-Reset-plus-Helper-Wertepaare
- Projekte und reale Memory-Datei: separater persistenter Workspace unter
  `/config`
- GitHub-Repository: ausschließlich Ablage und Verteilung des versionierten
  Installationsprojekts; niemals Runtime-Persistenz oder Backup

## Schutz- und Abgrenzungsentscheidungen

- Der vollständige Codex-Home wird als eine Zustandsgrenze behandelt; dazu
  gehören native Sessions, Anmeldung, Konfiguration und Datenbanken.
- Die vollständige GitHub-CLI-Konfiguration wird gemeinsam persistent geführt.
- Die Add-on-eigene globale Git-Konfiguration wird nicht in die Projekt-Runtime
  übernommen und nicht im semantischen Gesamtinhalt ersetzt. Nur die Helper für
  GitHub und Gist werden atomar auf je einen leeren Resetwert und den
  persistenten `gh auth git-credential`-Befehl gesetzt; fremde Helper blockieren
  unverändert.
- Codex- und GitHub-CLI-Programme werden bei `install` geprüft und persistent
  abgelegt, damit ein neuer Container nicht von ihrer bisherigen Lage abhängt.
- `gh` ist nur Bootstrap-Paket. Seine Paket-Aliasse werden erst nach
  verifizierter Persistenz selektiv entfernt; fremde Pakete und Befehle bleiben
  unverändert. `boot` installiert oder aktualisiert keine Programme.
- Ein flüchtiger nativer IPC-Socket wird nicht kopiert; andere Spezialdateien
  blockieren die Installation.
- Zwei gefüllte oder widersprüchliche Zustände werden niemals automatisch
  zusammengeführt.
- Das Repository enthält nur eine neutrale Memory-Vorlage. Eine real befüllte
  Memory-Datei verbleibt im persistenten Workspace.
- Die private Runtime liegt ausschließlich unter `HACP_RUNTIME_ROOT`; Git und
  GitHub erhalten davon keine Kopie.
- Native Chats werden nicht aus Markdown wiederhergestellt; ihre führende
  Quelle bleibt `codex-home/sessions`.
- Echte Anmeldedaten, Sessions und Memory-Inhalte gelangen weder in Git noch in
  normale ungeschützte Spiegelungen.

## Modellierungsumfang

| Bereich | Entscheidung | Begründung |
|---|---|---|
| Domänenmodell | erforderlich | Installation, aktive Generation, Links und Blockierungen besitzen feste Invarianten. |
| Schnittstellen | erforderlich | Dateisystem, Supervisor API, `init_commands` und beide CLIs müssen klar getrennt sein. |
| Zustands- und Sicherheitslogik | erforderlich | Unsichere Zustände müssen fail-closed enden. |
| Mathematik und Regelung | nicht anwendbar | Es gibt keine fachliche Berechnung oder Regelung. |
| ISA-95 | nicht anwendbar | Das Projekt besitzt keinen Produktions- oder Anlagenbezug. |

## Annahmen und Risiken

- `ANN-001`: Der gewählte Zielpfad bleibt über Neustart, Update und
  Container-Neuerstellung persistent.
- `ANN-002`: `init_commands` laufen mit den nötigen Rechten vor `code-server`.
- `ANN-003`: Studio Code und Erweiterungen bleiben unabhängig unter
  `/data/vscode` persistent.
- `ANN-004`: Eine nicht leere `packages`-Liste wird vom Add-on über APT vor
  `init_commands` verarbeitet; eine leere Liste überspringt diesen Schritt.
- `RISK-001`: Ein Neustart vor erfolgreichem `install` kann den einzigen
  nativen `/root`-Bestand verlieren.
- `RISK-002`: Eine veränderliche Quelle kann keine konsistente Kopie liefern
  und muss blockieren.
- `RISK-003`: Runtime oder reale Memory-Inhalte können versehentlich in Git,
  Logs oder Spiegelungen gelangen.
- `RISK-004`: Anbieter können Anmeldungen serverseitig widerrufen oder ablaufen
  lassen; Persistenz allein garantiert keine dauerhafte Kontogültigkeit.
- `RISK-005`: Persistenz schützt vor Containerwechsel, ersetzt aber kein
  verschlüsseltes Backup des persistenten Speichers.
- `RISK-006`: Fremde verbleibende Add-on-Pakete können vor `init_commands` APT
  oder Netzwerk benötigen und einen Offline-Start verhindern.
- `RISK-007`: Persistierte CLI-Programme können veralten oder mit einem
  späteren Container inkompatibel werden; der Upgrade-Ablauf bleibt BL-005.

## Noch ausstehender Nachweis

Die isolierten Basistests sind erfolgreich und die dokumentierte
Pakettransition ist im Skript umgesetzt. Ihr automatisierter
Supervisor-Nachweis TC-016 bleibt in BL-014 offen. Danach wird die reale
Installation mit Add-on-Neustart und Container-Neuerstellung als TC-012 auf dem
Referenzsystem abgenommen, bevor eine öffentliche Freigabe erwogen wird.

## Rückverfolgbarkeit

```text
Intake -> US/REQ/AC -> DOM/ARC -> AP -> TC -> Abnahme
```

Die vollständige Zuordnung steht in `docs/NACHWEISMATRIX.md`.
