# Changelog

All notable public changes are documented here. Versions follow Semantic Versioning.

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
- A future add-on update or container recreation remains a regression test.
- Persisted CLI upgrade/rollback and encrypted runtime backup/restore are not implemented.
