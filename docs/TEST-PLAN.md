# Test concept and test cases

## Strategy

Automated tests use artificial isolated roots and test doubles. Real lifecycle
acceptance is recorded separately because simulation cannot prove behavior on
the Home Assistant reference system.

## Automated integration and failure tests

| ID | Covers | Action and expected result | Status |
|---|---|---|---|
| TC-001 | REQ-F-001, REQ-F-002, REQ-F-005, REQ-I-002, REQ-I-004 | install artificial native state, replace the container tree, boot and audit; sessions, auth, tools, links, and helpers persist | automated |
| TC-002 | REQ-I-002, REQ-Q-003, DOM-R-003 | run `boot` without installation; return `BLOCK` and create nothing | automated |
| TC-003 | REQ-Q-001, AC-006 | repeat `boot` and container replacement; active state remains unchanged | automated |
| TC-004 | REQ-Q-003, DOM-R-004 | create a non-empty conflicting path; preserve it and block all managed links | automated |
| TC-005 | REQ-F-005, DOM-R-005 | alter a persisted executable; checksum failure blocks activation | automated |
| TC-006 | REQ-Q-002, AC-009 | add an unsupported special file or mutate source during install; preserve source and block | automated |
| TC-007 | REQ-O-001, AC-002 | remove Codex authentication before install; block without activation | automated |
| TC-008 | REQ-F-002, AC-003 | test missing and keyring-only GitHub credentials; both block | automated |
| TC-009 | REQ-O-002, DOM-R-008 | remove authentication after boot; auth audit reports failure without mutation | automated |
| TC-010 | REQ-O-001, REQ-O-002 | invoke an unsupported lifecycle command; return usage error | automated |
| TC-011 | REQ-F-004, DOM-R-006, AC-011 | create missing neutral memory files, preserve existing files and approved legacy block, reject ambiguous blocks | automated and reviewed |
| TC-013 | REQ-I-002, DOM-R-002 | activate a fully verified ready generation after container replacement | automated |
| TC-014 | REQ-O-001, REQ-Q-003 | configure unsupported external credential stores; block before `current` | automated |
| TC-015 | REQ-O-002, DOM-R-008 | compare complete runtime-tree manifests before and after audit | planned under BL-007 |
| TC-016 | REQ-I-001, DOM-R-009 | verify Supervisor comparison, selective update, concurrency abort, read-back, and persisted `gh` after replacement | automated |
| TC-017 | REQ-I-003, REQ-I-004, DOM-R-010 | migrate only supported helper values and preserve unrelated Git configuration | automated |
| TC-DOM-001 | DOM-R-001–DOM-R-010 | evaluate all positive and negative invariant cases together | automated; real TC-012 evidence recorded separately |
| TC-SEC-001 | REQ-S-001, REQ-S-002 | scan working tree and history and test ownership, path, link, mode, and output boundaries | automated |

## TC-012 — Real restart and container acceptance

- **Prerequisites:** automated tests and security scan pass; Codex and GitHub
  CLI are installed with file-backed sign-ins; installation and authenticated
  audit pass; Supervisor packages, startup command, and Git helpers match the
  documented contract.
- **Action:** record a non-sensitive baseline, restart the add-on, perform a
  controlled add-on update/container replacement, restart the replacement
  container, and separately perform a Home Assistant host reboot.
- **Expected:** sessions resume; both sign-ins remain valid; projects, memory,
  Studio Code state, extensions, tools, helpers, and unrelated configuration
  remain unchanged; audits return no `BLOCK`.
- **Tolerance:** no missing session, changed project state, repeated sign-in,
  helper setup, or manual link repair.
- **Status:** installation and add-on restart passed; update `6.0.1` to
  `7.0.0`, container replacement, subsequent container restart, and complete
  Home Assistant host cold start passed.

## Execution

```sh
./scripts/validate.sh
```
