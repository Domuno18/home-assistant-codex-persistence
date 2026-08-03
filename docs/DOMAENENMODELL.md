# Domänenmodell

## Domänengrenze

**Innerhalb** sind die einmalige Installation einer persistenten
Codex-/GitHub-CLI-Runtime, ihre automatische Aktivierung beim Add-on-Start,
der rein lesende Zustandsaudit, die gezielte Bindung zweier GitHub-Credential-
Helper und die klare Abgrenzung eines optionalen Langzeitgedächtnisses im
persistenten Workspace.

**Außerhalb** sind die Persistenz von Studio Code und Erweiterungen unter
`/data/vscode`, die vom Add-on verwaltete Git-/SSH-/Shell-Konfiguration mit
Ausnahme der zwei ausdrücklich gebundenen GitHub-Credential-Helper,
Home-Assistant-Backups, die Installation der Programme vor dem ersten Aufruf,
die fachliche Pflege einzelner Projekte sowie der Inhalt realer Memory-Dateien.

## Gemeinsame Sprache

| Begriff | Fachliche Bedeutung | Abgrenzung | Beispiel |
|---|---|---|---|
| Wegwerfcontainer | Dateisystemschicht, die bei Update oder Neuerstellung ersetzt werden kann | nicht der persistente Add-on- oder Home-Assistant-Speicher | `/root` vor der Verlinkung |
| persistenter Runtime-Bereich | privater Speicher für native Codex-/GitHub-Daten, Werkzeuge und Bootstrap | kein Git-Repository und kein lesbares Chatarchiv | `/data/codex-persistence` |
| Referenz-Runtime | alternative, im Referenzsystem verwendete Runtime-Lage | ändert nicht den fachlichen Vertrag | `/config/Codex/.runtime` |
| native Codex-Sitzung | von Codex selbst erzeugte, fortsetzbare Sitzung | keine Markdown-Chatkopie | `codex-home/sessions/.../*.jsonl` |
| Codex-Home | vollständige native Codex-Zustandsgrenze | nicht nur der Unterordner `sessions` | Anmeldung, Konfiguration, Sessions, Datenbanken |
| GitHub-CLI-Konfiguration | vollständiger Zustand der GitHub CLI | nicht die globale Git-Konfiguration des Add-ons | `gh/hosts.yml` und zugehörige Dateien |
| globale Git-Konfiguration | vom Add-on persistent geführte Benutzerkonfiguration | wird nicht in die Projekt-Runtime übernommen oder im Gesamtinhalt ersetzt | `/root/.gitconfig` → `/data/git/.gitconfig` |
| GitHub-Credential-Helper | zwei gezielt verwaltete Schlüssel für HTTPS-Git-Zugriffe | keine Verwaltung anderer Git-Einstellungen | Helper für `github.com` und `gist.github.com` |
| gh-Bootstrap-Paket | einmalige containerlokale Quelle der ersten GitHub-CLI-Binary | kein Bestandteil des dauerhaften Wiederanlaufs | Add-on-Option `packages: [gh]` vor `install` |
| persistente GitHub-CLI-Binary | verifizierte, zur lokalen Architektur passende Betriebsbinary | kein automatischer Paket- oder Upgrade-Mechanismus | `current/tools/bin/gh` |
| aktive Generation | verifizierter persistenter Bestand, den `boot` verlinken darf | kein unmarkierter oder teilweise kopierter Bestand | Marker plus `current/` |
| Kompatibilitätslink | gewohnter Pfad im Container, der direkt auf persistenten Zustand zeigt | kein Export-/Importmechanismus | `/root/.codex` als Symlink |
| Workspace | persistenter Arbeitsbereich für Projekte und lesbare Dokumente | nicht Teil der privaten Runtime | Home-Assistant-Konfigurations- oder Share-Pfad |
| Langzeitgedächtnis | kurze, bestätigte und menschenlesbare Kontextverdichtung | keine native Chathistorie, keine Anmeldung | private Arbeitskopie von `MEMORY.md` |
| Blockierung | sicherer Abbruch mit Diagnose und Fehlercode | keine automatische Reparatur | konkurrierender nicht leerer Quellpfad |

## Domänenobjekte

| ID | Objekt | Art | Verantwortung | Identität und wichtige Werte |
|---|---|---|---|---|
| DOM-O-001 | Persistente Runtime | Aggregat | schützt alle gemeinsam aktivierten Runtime-Bestandteile | absoluter kanonischer Root-Pfad |
| DOM-O-002 | Aktive Generation | Entität | kennzeichnet genau einen vollständig verifizierten Bestand | unveränderliche Generations-ID und Marker |
| DOM-O-003 | Codex-Home | Aggregat | hält native Sessions, Anmeldung, Konfiguration und Datenbanken zusammen | `current/codex-home` |
| DOM-O-004 | GitHub-CLI-Home | Aggregat | hält die GitHub-CLI-Anmeldung und -Konfiguration zusammen | `current/gh` |
| DOM-O-005 | Werkzeugpaket | Wertobjekt | hält geprüfte Codex- und GitHub-CLI-Programme | Programmpfad und SHA-256-Prüfsumme |
| DOM-O-006 | Kompatibilitätslink | Wertobjekt | verbindet einen erwarteten Containerpfad mit genau einem Ziel | Linkpfad und absolutes Ziel |
| DOM-O-007 | Persistenter Workspace | Aggregat | hält Projekte und die reale Memory-Datei außerhalb des Containers | vom Betreiber gewählter persistenter Pfad |
| DOM-O-008 | Memory-Vorlage | Wertobjekt | beschreibt neutrale Struktur und Pflegeregeln | `examples/memory` ohne reale Einträge |
| DOM-O-009 | GitHub-Helper-Bindung | Wertobjekt | verbindet ausschließlich GitHub und Gist mit der persistenten `gh`-Binary | zwei Schlüssel mit je einem geordneten Reset-plus-Helper-Wertepaar |

## Beziehungen und Verantwortungsgrenzen

```text
Studio Code Server Add-on
├── /data/vscode                         vom Add-on persistent verwaltet
├── /data/git/.gitconfig                 vom Add-on persistent verwaltet
│   └── zwei GitHub-Helper               gezielt durch DOM-O-009 gebunden
├── persistenter Workspace               Projekte und reale Memory-Datei
└── persistenter Runtime-Bereich
    ├── current/codex-home               DOM-O-003
    ├── current/gh                       DOM-O-004
    ├── current/tools                    DOM-O-005
    ├── state/ready-generation           verifizierter Zwischenzustand
    ├── state/active-generation          DOM-O-002
    ├── locks                            Parallelitätsschutz
    └── bootstrap                        persistenter boot-/audit-Einstieg

Wegwerfcontainer
├── /root/.codex        ───────────────> current/codex-home
├── /root/.config/gh    ───────────────> current/gh
├── /root/.gitconfig    ───────────────> /data/git/.gitconfig
└── vorgesehene CLI-Pfade ─────────────> current/tools/bin
```

## Fachliche Regeln und Invarianten

| ID | Regel | Quelle | Nachweis |
|---|---|---|---|
| DOM-R-001 | Das Codex-Home wird vollständig als eine Konsistenzgrenze behandelt; native Sessions, Anmeldung, Konfiguration und Datenbanken werden nicht getrennt aktiviert. | REQ-F-001 | TC-001, TC-DOM-001 |
| DOM-R-002 | Nur `install` darf aus einem vorhandenen nativen Quellbestand eine Ready-Generation erzeugen, und erst nach stabiler Inhaltsprüfung. Erst der registrierte automatische Startbefehl erlaubt den Active-Marker und den Cutover. | REQ-Q-002, REQ-O-001 | TC-001, TC-006 |
| DOM-R-003 | `boot` darf niemals einen leeren Runtime-Bestand erzeugen. Es verwendet eine aktive Generation oder stuft ausschließlich eine vollständig verifizierte Ready-Generation nach einer Installationsunterbrechung hoch. | REQ-I-002 | TC-002, TC-013, TC-DOM-001 |
| DOM-R-004 | Ein vorhandener nicht leerer oder unerwartet verlinkter Containerpfad wird niemals überschrieben oder mit der Runtime zusammengeführt. | REQ-Q-003 | TC-004, TC-DOM-001 |
| DOM-R-005 | Die persistierten Programme gehören zur aktiven Generation und müssen vor jeder Aktivierung ihre gespeicherten Prüfsummen erfüllen. | REQ-F-005, REQ-Q-003 | TC-001, TC-005 |
| DOM-R-006 | Eine reale Memory-Datei bleibt im persistenten Workspace; das Repository enthält nur die neutrale Vorlage und native Chats bleiben in `codex-home/sessions`. | REQ-F-004, REQ-S-002 | TC-011 |
| DOM-R-007 | Projekt-Worktrees und Add-on-eigene Persistenzbereiche werden von `install`, `boot` und `audit` nicht in die Projekt-Runtime übernommen oder im Gesamtinhalt ersetzt. Die einzige gezielte Inhaltsänderung ist DOM-R-010. | REQ-F-003, REQ-I-003 | TC-012, TC-017 |
| DOM-R-008 | Jeder mutierende Befehl benötigt eine ausdrückliche Bestätigung über seine vorgesehene Umgebungsvariable; `audit` bleibt rein lesend. | REQ-O-002, REQ-Q-003 | TC-002, TC-013 |
| DOM-R-009 | `gh` ist nur ein Bootstrap-Paket. Sobald die persistente Binary und Ready-Generation verifiziert und synchronisiert sind, entfernt dasselbe Supervisor-Update ausschließlich `gh` beziehungsweise `github-cli`, setzt den verwalteten Bootbefehl zuerst und erhält alle fremden Pakete. Fremde Pakete bleiben ein ausdrücklich ausgewiesenes APT-/Offline-Risiko. | REQ-I-001, REQ-O-004 | TC-016, TC-012 |
| DOM-R-010 | Nur die beiden Git-Credential-Helper für `github.com` und `gist.github.com` dürfen atomar auf je zwei geordnete Werte migriert werden: leerer Reset, danach der exakte persistente `gh`-Befehl. Fehlende, leere oder bekannte alte `gh`-Werte sind migrierbar; ein fremder Wert bleibt unverändert und blockiert. | REQ-I-003, REQ-I-004 | TC-017, TC-012 |

## Zustände und Übergänge

Es gibt nur die öffentlich dokumentierten Befehle `install`, `boot` und
`audit`.

| Ausgangszustand | Befehl oder Ereignis | Vorbedingung | Folgezustand | Unzulässiger Fall |
|---|---|---|---|---|
| nicht installiert | `install` | Codex und GitHub CLI installiert, angemeldet, Git-Helper fehlend oder sicher migrierbar und kein Codex-Prozess aktiv | installiert und im aktuellen Container aktiv; `gh`-Bootstrap-Paket entfernt; beide Helper exakt gebunden | Quelle fehlt, Anmeldung ungültig, fremder Helper, instabile Kopie oder Supervisor-Transition unvollständig: blockieren |
| Ready nach Unterbrechung | `boot` | Ready-Marker, Runtime, Programme und Prüfsummen vollständig gültig; Aufruf vor `code-server` | aktiv | beschädigter oder konkurrierender Zustand: blockieren |
| installiert, Containerpfade fehlen | `boot` | Active-Marker, Runtime, Programme und Prüfsummen gültig; Aufruf vor `code-server` | aktiv | fehlender, beschädigter oder konkurrierender Zustand: blockieren |
| aktiv | `boot` | Links zeigen bereits auf die aktive Generation | aktiv, unverändert | abweichender Link: blockieren |
| installiert oder aktiv | `audit` | keine | Zustand unverändert, Diagnose ausgegeben | Prüfabweichung melden, nichts reparieren |
| aktiv | Container wird ersetzt | persistenter Speicher bleibt erhalten | Containerpfade fehlen, Generation bleibt installiert | automatisches `boot` stellt Links wieder her |

## Domänenereignisse

- `RuntimeBereit`: beide Laufzeitbäume und Programme wurden geprüft und der
  automatische Add-on-Start kann die Generation sicher übernehmen.
- `GhBootstrapAbgeschlossen`: die persistente GitHub-CLI-Binary ist geprüft;
  das Supervisor-Update hat nur die bekannten Bootstrap-Paketnamen entfernt,
  fremde Pakete erhalten und den Bootbefehl zuerst gesetzt.
- `RuntimeInstalliert`: der Bootbefehl wurde registriert, die Generation aktiv
  markiert und konfliktfrei verknüpft.
- `RuntimeVerknüpft`: die Containerpfade zeigen auf die aktive Generation.
- `RuntimeGeprüft`: ein Audit hat den aktuellen Zustand ohne Mutation bewertet.
- `GitHelperGebunden`: ausschließlich die beiden GitHub-Helper besitzen das
  exakte geordnete Reset-plus-Helper-Wertepaar zur persistenten GitHub CLI;
  andere Git-Einstellungen sowie Modus und Eigentümer blieben erhalten.
- `AktivierungBlockiert`: eine Invariante war verletzt; vorhandene Daten
  blieben erhalten.
- `MemoryGepflegt`: eine bestätigte dauerhafte Aussage wurde in der privaten
  Workspace-Datei aktualisiert, nicht im Repository.
