# Changelog

All notable public changes are documented here. Versions follow Semantic Versioning.

## Unreleased

### Documentation

- Converted all remaining public engineering documentation below `docs/` to
  English and removed the obsolete mixed-language disclaimer.
- Consolidated the backlog, leaving only the Home Assistant host reboot open
  under TC-012 and recording the completed add-on update, container
  replacement, and subsequent restart as done.
- Added regression tests for the English-only public documentation gate and
  lifecycle-backlog status.
- Consolidated each topic into one canonical document, renamed engineering
  records to clear English filenames, removed duplicate guides, obsolete
  publication checklists, and empty non-applicable model/template files, and
  added regression checks for obsolete paths and broken relative links.
- Folded unique operational guidance into `docs/INSTALLATION.md`, assumptions
  into the project charter, and release-note maintenance into the changelog;
  removed the superseded intake, deployment, and release-note documents.

## 0.9.0-beta.2 — 2026-08-09

### Fixed

- Replaced the direct `rm -rf` startup entry with the guarded persistent
  bootstrap `boot` command.
- Preserved unexpected container state by failing closed while still allowing
  narrowly defined disposable fresh-container paths.
- Allowed explicitly confirmed repeated installation to update an existing
  bootstrap and managed Supervisor startup entry without remigrating private
  runtime data or persisted executables.
- Added exact compatibility for the official legacy manual-memory startup
  block while continuing to reject modified or ambiguous managed blocks.

### Verified

- Added regression coverage for the generated safe startup command and a
  sealed legacy-memory installation upgraded in place.
- Upgraded the reference installation and passed authenticated runtime and
  network cold-start audits before and after a real restart.
- Passed a real Studio Code Server update from `6.0.1` to `7.0.0`, including
  container replacement and a subsequent container restart, with sessions,
  manual memory, both sign-ins, persisted CLI programs, Git credential
  helpers, and the managed startup entry intact.

## 0.9.0-beta.1 — 2026-08-03

### Added

- Restart-safe persistence for Codex sessions, sign-in, configuration, and local state inside the Home Assistant Studio Code Server add-on.
- Persistent GitHub CLI sign-in, HTTPS Git credentials, and verified CLI executables.
- Automatic startup integration after one guarded installation.
- Read-only runtime and authentication audit.
- Standard manual file-based memory through `AGENTS.md` and `MEMORY.md`, with explicit opt-out through `HACP_MEMORY_SETUP=NO`.
- Persistence for separately enabled Codex-managed local Memories.
- English public installation, architecture, security, release, and memory documentation.
- Automated integration, conflict, integrity, authentication, Supervisor, and credential-helper tests.

### Security

- Credentials, native sessions, databases, populated memories, and private runtime data are excluded from Git, examples, diagnostics, and ordinary mirrors.
- Runtime ownership markers, strict permissions, stable-copy verification, SHA-256 checks, and fail-closed conflict handling.
- Unrelated Git configuration, add-on packages, and startup commands remain unchanged.

### Verified

- Installation and a real Studio Code Server add-on restart succeeded on the documented reference environment.
- Sessions, both sign-ins, and persisted CLI programs survived the restart.
- Repository, reachable-history, and staged-content security scans passed.
- The automated validation suite passes 51 tests.

### Known limitations

- Independent installation feedback is still pending.
- Home Assistant host-reboot evidence is still pending.
- Additional add-on updates and container recreations remain regression tests.
- Persisted CLI upgrade/rollback and encrypted runtime backup/restore are not implemented.
