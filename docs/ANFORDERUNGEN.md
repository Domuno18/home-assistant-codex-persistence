# Anforderungen

## Nutzerziele

- **US-001:** Als Betreiber des Studio-Code-Server-Add-ons möchte ich Codex
  und GitHub CLI einmal persistent einrichten, damit native Chats,
  Anmeldungen, Konfiguration, HTTPS-Git-Zugriff und benötigte Programme nach
  einem Containerwechsel ohne erneute Einrichtung verfügbar sind.
- **US-002:** Als Betreiber möchte ich den Zustand jederzeit rein lesend
  prüfen und bei einem unsicheren Zustand eine eindeutige Blockierung erhalten.
- **US-003:** Als Codex-Nutzer möchte ich ein kleines Langzeitgedächtnis in
  meinem persistenten Workspace führen, ohne native Chats oder private
  Memory-Inhalte im Projekt-Repository abzulegen.

## Funktionale Anforderungen

| ID | Anforderung | Quelle | Priorität | Akzeptanz |
|---|---|---|---|---|
| REQ-F-001 | Vor `install` muss Codex per Gerätecode und erzwungenem Dateispeicher angemeldet sein. `install` muss den vollständigen nativen Codex-Home aus `/root/.codex` einschließlich `sessions`, Anmeldecache und Konfiguration stabil und verifiziert unter dem persistenten Ziel ablegen und den ursprünglichen Pfad damit verbinden. | US-001 | Muss | AC-001, AC-002, AC-005, AC-009 |
| REQ-F-002 | Vor `install` muss GitHub CLI ohne vorrangige Umgebungs-Tokens mit festem `GH_CONFIG_DIR`, HTTPS-Gerätecode-Webflow (`gh auth login --web`) und bewusstem Klartext-Dateispeicher angemeldet sein. `install` muss die vollständige GitHub-CLI-Konfiguration einschließlich des dateibasierten Credentials aus `/root/.config/gh` stabil und verifiziert unter dem persistenten Ziel ablegen und den ursprünglichen Pfad damit verbinden; ein Keyring-only-Zustand ist unzulässig. | US-001 | Muss | AC-003, AC-005, AC-009, AC-012 |
| REQ-F-003 | Projekte müssen in einem persistenten Workspace liegen; die Lösung darf vorhandene Projekt-Worktrees weder verschieben noch inhaltlich verändern. | US-001 | Muss | AC-004, AC-010 |
| REQ-F-004 | Das Repository muss eine neutrale Memory-Vorlage bereitstellen. `install` muss fehlende Memory-Dateien atomar anlegen, vorhandene Memory-Dateien bytegenau erhalten und genau einen verwalteten Block mit absoluten Memory-Pfaden in der wirksamen globalen `$CODEX_HOME/AGENTS.override.md`, andernfalls `$CODEX_HOME/AGENTS.md`, ergänzen, ohne fremden Inhalt zu ersetzen. Die Startlogik muss auch in verschachtelten Git-Repositories wirken; der Workspace darf nicht im Installationsrepository liegen. | US-003 | Muss | AC-011 |
| REQ-F-005 | `install` muss die aufgelösten ausführbaren Dateien von Codex CLI und GitHub CLI samt Prüfsummen persistent ablegen; `boot` muss die vorgesehenen Kompatibilitätslinks wiederherstellen. | US-001 | Muss | AC-005, AC-010 |

## Integrationsanforderungen

| ID | Anforderung | Quelle | Priorität | Akzeptanz |
|---|---|---|---|---|
| REQ-I-001 | Das Add-on-Paket `gh` dient nur der einmaligen Bereitstellung vor `install`. Nachdem die GitHub-CLI-Binary persistent kopiert und verifiziert sowie die Ready-Generation synchronisiert wurde, muss `install` im selben Supervisor-Update ausschließlich `gh` und den veralteten Alias `github-cli` aus `packages` entfernen und den eindeutig verwalteten `boot`-Befehl genau einmal als ersten `init_commands`-Eintrag setzen. Fremde Pakete, Optionen und Startbefehle müssen unverändert und in ihrer bisherigen Reihenfolge erhalten bleiben. | US-001 | Muss | AC-009, AC-010 |
| REQ-I-002 | `boot` muss vor `code-server` ausschließlich eine aktive oder nach Installationsunterbrechung vollständig verifizierte Ready-Generation verwenden und die Codex-, GitHub-CLI- und Werkzeuglinks wiederherstellen. | US-001 | Muss | AC-005, AC-010 |
| REQ-I-003 | Die Lösung darf die vom Add-on bereits persistent verwalteten Bereiche für Studio Code, Erweiterungen, globale Git-Konfiguration, SSH und Shell-History nicht in die eigene Runtime übernehmen oder in ihrem Gesamtinhalt ersetzen. In der Add-on-eigenen Git-Konfiguration ist ausschließlich die in REQ-I-004 definierte atomare Veröffentlichung zweier Credential-Helper-Schlüssel zulässig; alle anderen Git-Einstellungen sowie Modus und Eigentümer müssen erhalten bleiben. | US-001 | Muss | AC-010, AC-012 |
| REQ-I-004 | `/root/.gitconfig` muss auf eine reguläre persistente Datei unter `/data`, `/config` oder `/share` auflösbar sein; im Studio-Code-Server-Add-on ist dies `/data/git/.gitconfig`. `install` und `boot` dürfen ausschließlich `credential.https://github.com.helper` und `credential.https://gist.github.com.helper` atomar auf je zwei geordnete Werte setzen: zuerst einen leeren Helper zum Zurücksetzen niedriger priorisierter beziehungsweise System-Helper, danach `!GH_CONFIG_DIR=/root/.config/gh /usr/local/bin/gh auth git-credential`. Fehlende, leere und bekannte alte `!…/gh auth git-credential`-Werte dürfen migriert werden. Jeder fremde benutzerdefinierte Wert muss unverändert bleiben und die automatische Aktivierung fail-safe blockieren. | US-001, US-002 | Muss | AC-007, AC-009, AC-010, AC-012 |

## Qualitäts- und Sicherheitsanforderungen

| ID | Anforderung | Quelle | Priorität | Akzeptanz |
|---|---|---|---|---|
| REQ-Q-001 | Wiederholte `boot`-Aufrufe müssen idempotent sein und dürfen Inhalt oder Generation der persistenten Runtime nicht verändern. | US-002 | Muss | AC-006 |
| REQ-Q-002 | Die einmalige Installationskopie darf erst aktiviert werden, wenn Quelle vor und nach der Kopie stabil blieb, die Kopie inhaltsgleich ist und die benötigten Programme ihre Versionsprüfung bestehen. | US-001 | Muss | AC-009 |
| REQ-Q-003 | Fehlende Installation, unerwartete Spezialdateien, konkurrierende nicht leere Pfade, falsche Symlinks, beschädigte Programme, ungültige Zustandsmarker oder ein fehlender beziehungsweise falscher Runtime-Eigentumsmarker müssen mit `BLOCK` und einem Fehlercode enden; vorhandene Bestände dürfen dabei nicht überschrieben oder zusammengeführt werden. | US-002 | Muss | AC-007 |
| REQ-S-001 | Der persistente Runtime-Bereich muss außerhalb jedes Git-Checkouts liegen, durch einen exakten privaten Eigentumsmarker beansprucht und als reguläres Verzeichnis mit Eigentümer `root:root` und Modus `0700` geführt werden; sensible Runtime-Inhalte dürfen nicht in Git, normale Spiegelungen oder ungeschützte Backups gelangen. | US-001, US-002 | Muss | AC-008 |
| REQ-S-002 | Quellcode, Tests, Beispiele, Dokumentation und Diagnoseausgaben dürfen keine echten Anmeldedaten, nativen Sitzungsinhalte oder real befüllte Memory-Dateien enthalten. | US-003 | Muss | AC-008, AC-011 |

## Betriebsanforderungen

| ID | Anforderung | Quelle | Priorität | Akzeptanz |
|---|---|---|---|---|
| REQ-O-001 | Der einmalige `install`-Aufruf darf nur mit installierten Programmen, erkanntem dateibasiertem Codex-Anmeldecache, gültiger aktiver dateibasierter GitHub-Anmeldung sowie ohne laufenden Codex-Prozess erfolgreich sein. `codex login status` ist dabei ausschließlich Cache- und Methodenerkennung. | US-001 | Muss | AC-002, AC-003, AC-009 |
| REQ-O-002 | `audit` muss ohne Schreibzugriff Installation, Generation, Verzeichnisse, Symlinks, Programmintegrität, Rechte, native Sitzungsdateien, wirksame globale Memory-Startlogik und die exakten geordneten Reset-plus-Helper-Wertepaare beider Git-Credential-Helper prüfen. Die optionale Authentifizierungsprüfung erkennt den Codex-Anmeldecache und validiert die aktive GitHub-Anmeldung; der Codex-Status darf nicht als serverseitige Gültigkeitsprüfung bezeichnet werden. Ohne Auth-Prüfung muss der ungeprüfte Status als `WARN` erscheinen. | US-002 | Muss | AC-002, AC-003, AC-007, AC-008, AC-011, AC-012 |
| REQ-O-003 | Ohne Konfiguration muss `/data/codex-persistence` verwendet werden; ein absoluter kanonischer Pfad unter `/data`, `/config` oder `/share`, außerhalb jedes Git-Checkouts und mit eindeutigem HACP-Eigentumsmarker muss konfigurierbar sein. Ein nicht leerer unbeanspruchter Bestand wird vor jeder Mutation blockiert. Die Referenzinstallation verwendet `/config/Codex/.runtime`. | US-001 | Muss | AC-005, AC-009 |
| REQ-O-004 | Nach erfolgreichem `install` müssen Neustart, Add-on-Update und Container-Neuerstellung durch automatisches `boot` ohne erneute Anmeldung, Chatimport, manuelle Git-Helper-Einrichtung oder eine durch `gh` verursachte Paketinstallation beziehungsweise Netzverbindung überstanden werden. Fremde, bewusst erhaltene Add-on-Pakete bleiben außerhalb dieser Offline-Garantie, weil das Add-on sie vor `init_commands` über APT verarbeitet. | US-001 | Muss | AC-001 bis AC-006, AC-010, AC-012 |

## Akzeptanzkriterien

| ID | Beobachtbares Ergebnis |
|---|---|
| AC-001 | Eine vor der Installation vorhandene native Codex-Sitzung bleibt nach Container-Neuerstellung unter `codex-home/sessions` vorhanden, wird von Codex gefunden und ist fortsetzbar. |
| AC-002 | Der dateibasierte Codex-Anmeldecache und die Codex-Konfiguration bleiben nach Neustart erhalten; `codex login status` erkennt Cache und Methode ohne erneute Anmeldung, gilt aber nicht als serverseitige Gültigkeitsprüfung. |
| AC-003 | `GH_CONFIG_DIR=/root/.config/gh gh auth status --active --hostname github.com` bleibt nach Neustart ohne erneute Anmeldung erfolgreich und ein rein lesender Repository-Zugriff funktioniert. |
| AC-004 | Pfad, Git-HEAD und Working-Tree-Status jedes Projekts im persistenten Workspace sind vor und nach dem Neustart identisch. |
| AC-005 | `/root/.codex`, `/root/.config/gh` sowie die vorgesehenen CLI-Links zeigen auf die installierte persistente Generation; neue Laufzeitdaten werden direkt dort geschrieben. |
| AC-006 | Ein zweiter und jeder weitere `boot`-Aufruf endet erfolgreich und lässt Sitzungen, Prüfsummen und aktive Generation unverändert. |
| AC-007 | Jeder widersprüchliche oder nicht verifizierbare Zustand wird ohne Überschreiben oder Zusammenführen vorhandener Daten blockiert. |
| AC-008 | Runtime und Metadaten besitzen die festgelegten privaten Rechte; Secret-Scan und Repository-Prüfung finden keine privaten Runtime-Inhalte. |
| AC-009 | `install` meldet erst Erfolg, nachdem beide Laufzeitbäume und Programme verifiziert, im selben Supervisor-Update ausschließlich `gh` beziehungsweise `github-cli` aus den Add-on-Paketen entfernt, der automatische Startbefehl als erster Eintrag eingerichtet, die Generation aktiv markiert, alle Kompatibilitätslinks konfliktfrei gesetzt und die geordneten Wertepaare beider GitHub-Credential-Helper exakt verifiziert wurden. Fremde Pakete, Startbefehle und nicht verwaltete Git-Einstellungen bleiben erhalten. |
| AC-010 | Nach einem realen Add-on-Neustart und einer Container-Neuerstellung sind Codex, GitHub CLI, Studio Code, Erweiterungen, Projekte und der HTTPS-Git-Zugriff ohne manuelle Wiederherstellung verfügbar. Die GitHub CLI startet aus der persistenten verifizierten Binary und verursacht dabei keinen APT- oder Netzzugriff; verbleibende fremde Add-on-Pakete werden als gesondertes Offline-Risiko ausgewiesen. |
| AC-011 | Fehlende neutrale Memory-Dateien werden beim einmaligen `install` atomar angelegt und vorhandene Dateien bytegenau erhalten. Genau ein verwalteter Block in der wirksamen globalen `$CODEX_HOME/AGENTS.override.md`, andernfalls `$CODEX_HOME/AGENTS.md`, verweist absolut auf Regeln und Inhalt, ohne fremden Inhalt zu ersetzen; die Dateien werden dadurch auch aus verschachtelten Git-Repositories geladen und bleiben vom Installationsrepository sowie von `codex-home/sessions` getrennt. |
| AC-012 | Nach `install` und jedem `boot` enthalten `credential.https://github.com.helper` und `credential.https://gist.github.com.helper` in der Add-on-eigenen persistenten Git-Konfiguration jeweils genau zwei geordnete Werte: zuerst leer als Reset niedriger priorisierter beziehungsweise System-Helper, danach `!GH_CONFIG_DIR=/root/.config/gh /usr/local/bin/gh auth git-credential`. Alle anderen Git-Einstellungen sowie Modus und Eigentümer bleiben erhalten. Ein fremder Wert in einem der beiden Schlüssel bleibt unverändert und führt zu `BLOCK`; `audit` erkennt jede Abweichung rein lesend. |
