# User-Storys

## US-001 — Containerwechsel ohne Verlust

**Als** Home-Assistant-Betreiber mit Studio Code Server, Codex und GitHub CLI
**möchte ich** den vollständigen Codex- und GitHub-CLI-Zustand einmal
persistent installieren
**damit** Chats, Anmeldungen, Konfiguration, HTTPS-Git-Zugriff und benötigte Programme nach
Neustart, Update oder Container-Neuerstellung ohne manuelle Wiederherstellung
verfügbar sind und die persistierte GitHub CLI keinen erneuten APT- oder
Netzzugriff benötigt.

### Akzeptanzkriterien

- AC-001: Eine vorhandene native Codex-Sitzung bleibt fortsetzbar.
- AC-002: Codex-Anmeldung und -Konfiguration bleiben gültig.
- AC-003: GitHub-CLI-Anmeldung und read-only Repository-Zugriff bleiben gültig.
- AC-004: Projekte im persistenten Workspace bleiben unverändert.
- AC-005: Container- und CLI-Pfade zeigen auf die aktive persistente
  Generation.
- AC-006: Wiederholte Starts sind idempotent.
- AC-009: `install` meldet erst nach vollständiger Prüfung und Einrichtung
  Erfolg; dabei wird nur das einmalige gh-Bootstrap-Paket entfernt und der
  Boot-Hook zuerst gesetzt.
- AC-010: Reale Neustarts und Container-Neuerstellung benötigen keine erneute
  Anmeldung, manuelle Linkreparatur oder gh-bedingte Paketinstallation.
  Fremde Add-on-Pakete bleiben erhalten und werden als separates
  Offline-Risiko ausgewiesen.
- AC-012: Die Add-on-eigene globale Git-Konfiguration bleibt erhalten; nur die
  beiden GitHub- und Gist-Credential-Helper erhalten jeweils das exakte
  geordnete Paar aus leerem Resetwert und persistenter GitHub CLI. Fremde
  Helper-Werte werden nicht überschrieben und blockieren.

## US-002 — Sicher prüfen und blockieren

**Als** Betreiber
**möchte ich** Installation und aktiven Zustand jederzeit rein lesend prüfen
**damit** ein beschädigter oder konkurrierender Zustand erkannt wird, bevor
Codex oder `code-server` damit startet.

### Akzeptanzkriterien

- AC-007: Jeder widersprüchliche oder nicht verifizierbare Zustand blockiert,
  ohne vorhandene Daten zu überschreiben oder zusammenzuführen.
- AC-008: Runtime-Rechte und Repository-Ausschlüsse schützen Sessions,
  Anmeldungen und private Inhalte.

## US-003 — Verdichtetes Langzeitgedächtnis

**Als** Codex-Nutzer
**möchte ich** eine kleine private Memory-Datei in meinem persistenten
Workspace führen
**damit** bestätigte dauerhafte Zusammenhänge bei einer neuen Sitzung wieder
verfügbar sind, ohne native Chats zu kopieren oder Secrets zu veröffentlichen.

### Akzeptanzkriterium

- AC-011: Die private Memory-Datei wird beim Sitzungsstart über lokale Regeln
  gelesen, bleibt persistent und getrennt vom Repository sowie von
  `codex-home/sessions`.
