# Requirements

## Functional requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-F-001 | Persist the complete Codex home, including native sessions, configuration, and file-backed sign-in, outside the disposable container. | AC-001, AC-002, AC-005, AC-009 |
| REQ-F-002 | Persist GitHub CLI configuration and provide authenticated HTTPS Git access through the persistent sign-in. | AC-003, AC-005, AC-009, AC-012 |
| REQ-F-003 | Leave projects and Studio Code add-on-owned persistence outside the project runtime and unchanged. | AC-004, AC-010 |
| REQ-F-004 | Create and preserve the standard manual file-based memory setup unless explicitly disabled. | AC-011 |
| REQ-F-005 | Persist verified Codex and GitHub CLI executable files with checksums and architecture compatibility. | AC-005, AC-010 |

## Integration requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-I-001 | Update Supervisor options atomically, remove only the one-time `gh` bootstrap package, preserve unrelated options, and install the managed boot command first. | AC-009, AC-010 |
| REQ-I-002 | Restore standard container paths from the active persistent generation before `code-server` starts. | AC-005, AC-010 |
| REQ-I-003 | Keep the persistent workspace and add-on-owned storage outside `HACP_RUNTIME_ROOT`. | AC-010, AC-012 |
| REQ-I-004 | Manage only the GitHub and Gist credential-helper keys and preserve all unrelated Git configuration. | AC-007, AC-009, AC-010, AC-012 |

## Quality and security requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-Q-001 | `boot` is idempotent. | AC-006 |
| REQ-Q-002 | Installation copies stable regular files only and detects source changes. | AC-009 |
| REQ-Q-003 | Unknown ownership, paths, helpers, special files, or integrity failures block without destructive mutation. | AC-007 |
| REQ-S-001 | Repository content, history, examples, logs, and artifacts contain no credentials, native sessions, private runtime, or populated memory. | AC-008 |
| REQ-S-002 | Publication requires explicit approval and completed security and license review. | AC-008, AC-011 |

## Operational requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-O-001 | `install` validates prerequisites, supported credential storage, programs, paths, and process state before activation. | AC-002, AC-003, AC-009 |
| REQ-O-002 | `audit` is read-only and reports runtime, integrity, helper, and optional authentication state without exposing secrets. | AC-002, AC-003, AC-007, AC-008, AC-011, AC-012 |
| REQ-O-003 | Default and custom runtime roots are documented and constrained to persistent storage. | AC-005, AC-009 |
| REQ-O-004 | Real lifecycle acceptance records installation, restart, update, container replacement, and host-reboot evidence separately. | AC-001 through AC-006, AC-010, AC-012 |

## Constraints

- Normal startup performs no package download or executable upgrade.
- The runtime root must be a narrow persistent path below `/data`, `/config`,
  or `/share`, outside every Git checkout.
- All Codex processes must be closed during installation or upgrade.
- Home Assistant host-reboot evidence remains open; the add-on update and
  container restart evidence is complete.
