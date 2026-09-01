# Backlog

> Remaining operational evidence and later improvements. The project structure
> plan and evidence matrix define the binding scope and traceability.

## In progress

- [ ] BL-001 — Complete the remaining TC-012 evidence with a Home Assistant
      host reboot. Installation, add-on restart, the real Studio Code Server
      update from `6.0.1` to `7.0.0`, container replacement, and the
      subsequent container restart are already accepted. Sources: REQ-O-004,
      AC-001 through AC-012.

## Later improvements

- [ ] BL-017 — Obtain an independent installation report; until then, treat
      the documented reference environment as the only proven environment.
- [ ] BL-018 — Collect additional CPU architecture, Home Assistant version,
      and persistent-storage layout reports from community testers.
- [ ] BL-005 — Design a verified, atomic upgrade and rollback workflow for the
      persisted Codex and GitHub CLI programs. Verify version, checksum,
      architecture, and compatibility before activation; remove any temporary
      bootstrap package afterward. `boot` remains network- and upgrade-free.
      Source: RISK-007.
- [ ] BL-006 — Investigate optional encrypted backup and restore evidence for
      the private runtime. Source: RISK-005.
- [ ] BL-007 — Automate TC-015 to prove that a complete audit run is
      mutation-free. Source: REQ-O-002.

## Done

- [x] BL-002 — Repository created, validated, pushed, and publication controls
      verified. Source: REQ-S-002.
- [x] BL-003 — Operational status and TC-012 evidence documented without
      recording chats, credentials, or real memory content.
- [x] BL-004 — Public-release review completed and approved prereleases
      published. Sources: REQ-S-001, REQ-S-002.
- [x] BL-008 — Project initialized from Projektvorlage_20.
- [x] BL-009 — Requirements, domain model, architecture, interfaces, security,
      operations, and traceability documented for the project.
- [x] BL-010 — `install`, automatic `boot`, and read-only `audit`
      implemented.
- [x] BL-011 — Container replacement, conflicts, damaged programs, special
      files, and missing sign-ins tested in isolation.
- [x] BL-012 — Neutral manual-memory template created without real content.
- [x] BL-013 — Working tree scanned for secrets and project validation passed.
- [x] BL-014 — TC-016 automated for hardened Supervisor transport, selective
      package transition, preservation of unrelated options, concurrency
      rejection, and read-back before `ACTIVE`. Sources: REQ-I-001,
      REQ-O-004, DOM-R-009, AC-009, AC-010.
- [x] BL-015 — Semantic-versioning strategy, beta stage, and separate
      publication approval documented. Source: REQ-S-002.
- [x] BL-016 — Real Studio Code Server update from `6.0.1` to `7.0.0`,
      container replacement, and subsequent container restart accepted under
      TC-012.
