# Quellcode

Empfohlene minimale Struktur, erst bei Bedarf anlegen:

```text
<projekt>/
├── domain/          fachliche Objekte, Regeln und Ereignisse
├── application/     Anwendungsfälle und Ports
├── adapters/        Protokolle, Datenbanken, UI und externe Systeme
└── bootstrap/       Konfiguration und Verdrahtung
```

Kleine Projekte dürfen diese Struktur in wenige Module zusammenfassen. Die
Abhängigkeitsrichtung zur Domäne bleibt trotzdem verbindlich.
