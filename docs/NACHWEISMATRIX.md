# Nachweismatrix

> Durchgängige Kette: Nutzerziel und Akzeptanz → Anforderung → Domänenregel →
> Architektur → Arbeitspaket → Test beziehungsweise Abnahme.

| Anforderung | Quelle und Akzeptanz | Domäne | Architektur | Arbeitspaket | Test/Nachweis | Status |
|---|---|---|---|---|---|---|
| REQ-F-001 | US-001; AC-001, AC-002, AC-005, AC-009 | DOM-R-001, DOM-R-002 | ARC-001, ARC-002, ARC-003 | AP-300, AP-400 | TC-001, TC-DOM-001, TC-012 | isoliert automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-F-002 | US-001; AC-003, AC-005, AC-009, AC-012 | DOM-R-002, DOM-R-010 | ARC-001, ARC-002, ARC-003, ARC-006 | AP-300, AP-400 | TC-001, TC-008, TC-017, TC-012 | isoliert automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-F-003 | US-001; AC-004, AC-010 | DOM-R-007 | ARC-005 | AP-100, AP-400, AP-500 | TC-012 | Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-F-004 | US-003; AC-011 | DOM-R-006 | ARC-005 | AP-100, AP-500 | TC-011, TC-012 | Vorlage geprüft; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-F-005 | US-001; AC-005, AC-010 | DOM-R-005 | ARC-001, ARC-002, ARC-003 | AP-300, AP-400 | TC-001, TC-005, TC-012 | isoliert automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-I-001 | US-001; AC-009, AC-010 | DOM-R-002, DOM-R-009 | ARC-001, ARC-003 | AP-200, AP-300, AP-400 | TC-016, TC-012 | automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-I-002 | US-001; AC-005, AC-010 | DOM-R-003, DOM-R-004 | ARC-002, ARC-003 | AP-300, AP-400 | TC-001 bis TC-005, TC-012 | isoliert automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-I-003 | US-001; AC-010, AC-012 | DOM-R-007, DOM-R-010 | ARC-005, ARC-006 | AP-200, AP-300, AP-400 | Architekturreview, TC-017, TC-012 | gezielte Ausnahme automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-I-004 | US-001, US-002; AC-007, AC-009, AC-010, AC-012 | DOM-R-010 | ARC-001, ARC-003, ARC-004, ARC-006 | AP-200, AP-300, AP-400, AP-500 | TC-001, TC-017, TC-012 | automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-Q-001 | US-002; AC-006 | DOM-R-003 | ARC-003 | AP-300, AP-400 | TC-003 | automatisiert |
| REQ-Q-002 | US-001; AC-009 | DOM-R-001, DOM-R-002 | ARC-001, ARC-002 | AP-200, AP-300, AP-400 | TC-001, TC-006, TC-DOM-001 | automatisiert |
| REQ-Q-003 | US-002; AC-007 | DOM-R-003, DOM-R-004, DOM-R-005, DOM-R-008, DOM-R-010 | ARC-001 bis ARC-004, ARC-006 | AP-200, AP-300, AP-400 | TC-002, TC-004, TC-005, TC-006, TC-009, TC-017, TC-DOM-001 | automatisiert |
| REQ-S-001 | US-001, US-002; AC-008 | DOM-R-005, DOM-R-008 | ARC-001 bis ARC-004 | AP-200, AP-300, AP-400 | TC-005, TC-SEC-001 | automatisiert |
| REQ-S-002 | US-003; AC-008, AC-011 | DOM-R-006 | ARC-004, ARC-005 | AP-200, AP-400, AP-500 | TC-011, TC-SEC-001 | geprüft |
| REQ-O-001 | US-001; AC-002, AC-003, AC-009 | DOM-R-002, DOM-R-008 | ARC-001 | AP-300, AP-400 | TC-001, TC-007, TC-008, TC-010 | automatisiert |
| REQ-O-002 | US-002; AC-002, AC-003, AC-007, AC-008, AC-011, AC-012 | DOM-R-008, DOM-R-010 | ARC-004, ARC-006 | AP-300, AP-400, AP-500 | TC-009, TC-015, TC-017 | Auth- und Helper-Fehler automatisiert; vollständiger Mutationsnachweis geplant |
| REQ-O-003 | US-001; AC-005, AC-009 | DOM-O-001, DOM-O-002 | ARC-001, ARC-002 | AP-200, AP-300, AP-500 | Konfigurationsprüfung, TC-001, TC-012 | Standard automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |
| REQ-O-004 | US-001; AC-001 bis AC-006, AC-010, AC-012 | DOM-R-003, DOM-R-005, DOM-R-007, DOM-R-009, DOM-R-010 | ARC-002, ARC-003, ARC-005, ARC-006 | AP-300, AP-400, AP-500 | TC-001, TC-003, TC-016, TC-017, TC-012 | automatisiert; Add-on-Neustart bestätigt; Host-Neustart ausstehend; Add-on-Update ist ein zukünftiger Regressionstest |

## Akzeptanzabdeckung

| Akzeptanzkriterium | Nachweis |
|---|---|
| AC-001 | TC-001, TC-012 |
| AC-002 | TC-001, TC-007, TC-009, TC-012 |
| AC-003 | TC-001, TC-008, TC-009, TC-012 |
| AC-004 | TC-012 |
| AC-005 | TC-001, TC-003, TC-012 |
| AC-006 | TC-003 |
| AC-007 | TC-002, TC-004 bis TC-006, TC-009, TC-017, TC-DOM-001 |
| AC-008 | TC-005, TC-SEC-001 |
| AC-009 | TC-006 bis TC-008, TC-016, TC-017, TC-012 |
| AC-010 | TC-001, TC-003, TC-016, TC-017, TC-012 |
| AC-011 | TC-011, TC-012 |
| AC-012 | TC-001, TC-017, TC-012 |

## Regeln

- IDs bleiben stabil und werden nicht wiederverwendet.
- Entfernte Einträge werden als verworfen markiert, nicht umnummeriert.
- Keine Muss-Anforderung ohne Arbeitspaket und objektiven Nachweis.
- Automatisierte Container-Simulation und reale Add-on-Abnahme werden getrennt
  ausgewiesen.
- Ein `BLOCK` ist ein erfolgreicher Sicherheitsnachweis, wenn der jeweilige
  Fehlerfall genau diese Reaktion fordert.
