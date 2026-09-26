# Backlog

> Remaining operational evidence and later improvements. The project structure
> plan and evidence matrix define the binding scope and traceability.

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
- [x] BL-007 — TC-015 now compares complete synthetic runtime manifests
      before/after audit in all memory modes. Source: REQ-O-002.
- [ ] BL-020 — Complete TC-018 on the reference system: activate the exact
      profile, start a new Codex session, confirm Home Assistant/project/GitHub
      tasks and user approval prompts, then run the read-only access audit.

## Done

- [x] BL-001 — Complete TC-012 lifecycle acceptance: installation, add-on
      restart, Studio Code Server update from `6.0.1` to `7.0.0`, container
      replacement, subsequent container restart, and Home Assistant host cold
      start passed. Sources: REQ-O-004, AC-001 through AC-012.
- [x] BL-002 — Repository created, validated, pushed, and publication controls
      verified. Source: REQ-S-002.
- [x] BL-003 — Operational status and TC-012 evidence documented without
      recording chats, credentials, or real memory content.
- [x] BL-004 — Public-release review completed and approved prereleases
      published. Sources: REQ-S-001, REQ-S-002.
- [x] BL-008 — Project initialized from an internal project template.
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
- [x] BL-019 — Add the explicit protected-container Codex access profile,
      user-reviewed on-request approvals, atomic config preservation, optional
      read-only drift audit, and TC-018 automated coverage. Sources: REQ-F-006,
      REQ-I-005, REQ-S-003, REQ-O-005, AC-013.
- [x] BL-021 — Real Studio Code Server update from `7.0.0` to `7.1.0`,
      containing `code-server 4.137.0`, recreated the add-on container while
      preserving Codex sessions, projects, GitHub access, and manual memory.
      The authenticated post-update persistence audit passed under TC-012.

## Beta.4 delivery

- [x] BL-022 — Implement opt-in native remote startup, preserve the original CLI
      and models, and add failure/concurrency/status regressions. REQ-F-007.
- [x] BL-023 — Separate Core Knowledge and Codex Memories, preserve legacy and
      workspace-tool rules, and test both installation orders. REQ-F-008.
- [x] BL-024 — Complete the dated beta.4 live lifecycle and dual-repository
      publication record. See BETA-4-ACCEPTANCE.md. REQ-O-004, REQ-Q-004.
- [x] BL-025 — Synchronize current Studio Code Server `7.1.1` evidence and the
      explicitly authorized native-memory activation across private/public
      documentation, validate both repositories, and clarify the existing
      beta.4 release pages without rebuilding released artifacts.
- [x] BL-026 — Detect persistent access-profile drift read-only, restore the
      exact HACP defaults through the guarded `configure-access` interface,
      pass the authenticated follow-up audit, and document the absent `bwrap`
      boundary without installing packages or rebuilding beta.4.

## Beta.5 and client follow-up

- [x] BL-027 — Complete fresh beta.5 compatibility, security, and release
      verification for REQ-I-006/007 and TC-029/030; record candidate-specific
      results in BETA-5-ACCEPTANCE.md.
- [ ] BL-028 / OPEN-REMOTE-001 — Investigate automatic remote-home selection
      on the reference smartphone. The complete new-chat-in-explicit-folder-
      to-voice workaround and existing-chat voice are operator-confirmed;
      automatic selection still fails. The supplied screenshot shows app
      version `1.2026.258`. An iOS cause is suspected but unproven; record each
      reproduction independently and do not infer other-platform
      behavior or close the issue from server-side checks. REQ-O-007, TC-031.
