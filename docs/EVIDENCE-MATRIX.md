# Evidence matrix

> Continuous chain: user goal and acceptance → requirement → domain rule →
> architecture → work package → test or real evidence.

| Requirement | Source and acceptance | Domain | Architecture | Work package | Test/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-F-001 | US-001; AC-001, AC-002, AC-005, AC-009 | DOM-R-001, DOM-R-002 | ARC-001, ARC-002, ARC-003 | AP-300, AP-400 | TC-001, TC-DOM-001, TC-012 | automated and complete real lifecycle acceptance passed |
| REQ-F-002 | US-001; AC-003, AC-005, AC-009, AC-012 | DOM-R-002, DOM-R-010 | ARC-001, ARC-002, ARC-003, ARC-006 | AP-300, AP-400 | TC-001, TC-008, TC-017, TC-012 | automated and complete real lifecycle acceptance passed |
| REQ-F-003 | US-001; AC-004, AC-010 | DOM-R-007 | ARC-005 | AP-100, AP-400, AP-500 | TC-012 | complete real lifecycle acceptance passed |
| REQ-F-004 | US-003; AC-011 | DOM-R-006 | ARC-005 | AP-100, AP-500 | TC-011, TC-012 | template reviewed and real update/container evidence passed |
| REQ-F-005 | US-001; AC-005, AC-010 | DOM-R-005 | ARC-001, ARC-002, ARC-003 | AP-300, AP-400 | TC-001, TC-005, TC-012 | automated plus real update/container evidence |
| REQ-I-001 | US-001; AC-009, AC-010 | DOM-R-002, DOM-R-009 | ARC-001, ARC-003 | AP-200, AP-300, AP-400 | TC-016, TC-012 | automated plus real update/container evidence |
| REQ-I-002 | US-001; AC-005, AC-010 | DOM-R-003, DOM-R-004 | ARC-002, ARC-003 | AP-300, AP-400 | TC-001–TC-005, TC-012 | automated plus real update/container evidence |
| REQ-I-003 | US-001; AC-010, AC-012 | DOM-R-007, DOM-R-010 | ARC-005, ARC-006 | AP-200, AP-300, AP-400 | architecture review, TC-017, TC-012 | reviewed, automated, and accepted on reference system |
| REQ-I-004 | US-001, US-002; AC-007, AC-009, AC-010, AC-012 | DOM-R-010 | ARC-001, ARC-003, ARC-004, ARC-006 | AP-200, AP-300, AP-400, AP-500 | TC-001, TC-017, TC-012 | automated plus real update/container evidence |
| REQ-Q-001 | US-002; AC-006 | DOM-R-003 | ARC-003 | AP-300, AP-400 | TC-003 | automated |
| REQ-Q-002 | US-001; AC-009 | DOM-R-001, DOM-R-002 | ARC-001, ARC-002 | AP-200, AP-300, AP-400 | TC-001, TC-006, TC-DOM-001 | automated |
| REQ-Q-003 | US-002; AC-007 | DOM-R-003, DOM-R-004, DOM-R-005, DOM-R-008, DOM-R-010 | ARC-001–ARC-004, ARC-006 | AP-200, AP-300, AP-400 | TC-002, TC-004–TC-006, TC-009, TC-017, TC-DOM-001 | automated |
| REQ-S-001 | US-001, US-002; AC-008 | DOM-R-005, DOM-R-008 | ARC-001–ARC-004 | AP-200, AP-300, AP-400 | TC-005, TC-SEC-001 | automated |
| REQ-S-002 | US-003; AC-008, AC-011 | DOM-R-006 | ARC-004, ARC-005 | AP-200, AP-400, AP-500 | TC-011, TC-SEC-001 | reviewed and automated |
| REQ-O-001 | US-001; AC-002, AC-003, AC-009 | DOM-R-002, DOM-R-008 | ARC-001 | AP-300, AP-400 | TC-001, TC-007, TC-008, TC-010 | automated |
| REQ-O-002 | US-002; AC-002, AC-003, AC-007, AC-008, AC-011, AC-012 | DOM-R-008, DOM-R-010 | ARC-004, ARC-006 | AP-300, AP-400, AP-500 | TC-009, TC-015, TC-017 | auth/helper failures automated; full mutation proof planned |
| REQ-O-003 | US-001; AC-005, AC-009 | DOM-O-001, DOM-O-002 | ARC-001, ARC-002 | AP-200, AP-300, AP-500 | configuration review, TC-001, TC-012 | automated plus real update/container evidence |
| REQ-O-004 | US-001; AC-001–AC-006, AC-010, AC-012 | DOM-R-003, DOM-R-005, DOM-R-007, DOM-R-009, DOM-R-010 | ARC-002, ARC-003, ARC-005, ARC-006 | AP-300, AP-400, AP-500 | TC-001, TC-003, TC-016, TC-017, TC-012 | complete real lifecycle acceptance passed |

## Acceptance coverage

| Criterion | Evidence |
|---|---|
| AC-001 | TC-001, TC-012 |
| AC-002 | TC-001, TC-007, TC-009, TC-012 |
| AC-003 | TC-001, TC-008, TC-009, TC-012 |
| AC-004 | TC-012 |
| AC-005 | TC-001, TC-003, TC-012 |
| AC-006 | TC-003 |
| AC-007 | TC-002, TC-004–TC-006, TC-009, TC-017, TC-DOM-001 |
| AC-008 | TC-005, TC-SEC-001 |
| AC-009 | TC-006–TC-008, TC-016, TC-017, TC-012 |
| AC-010 | TC-001, TC-003, TC-016, TC-017, TC-012 |
| AC-011 | TC-011, TC-012 |
| AC-012 | TC-001, TC-017, TC-012 |

## Rules

- IDs remain stable and are never reused.
- Removed entries are marked rejected rather than renumbered.
- Every mandatory requirement has a work package and objective evidence.
- Automated container simulation and real lifecycle acceptance are reported
  separately.
- A `BLOCK` is successful security evidence when the test expects rejection.
