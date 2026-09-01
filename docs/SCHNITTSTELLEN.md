# Interfaces

## Overview

| ID | Interface | Input | Output | Failure behavior |
|---|---|---|---|---|
| IF-001 | persistent filesystem | runtime root below `/data`, `/config`, or `/share` | claimed runtime and immutable generations | reject broad, linked, checked-out, unknown, or unsafe paths |
| IF-002 | Supervisor options | add-on API GET/POST and expected snapshot | selective package and startup-command update | abort on transport, concurrency, or read-back mismatch |
| IF-003 | add-on startup | managed `init_commands` entry | verified links before `code-server` | `BLOCK` without destructive cleanup |
| IF-004 | Codex CLI | resolved executable and file-backed home | verified persistent executable and optional auth status | reject unsupported store, unstable file, bad version, or missing auth |
| IF-005 | GitHub CLI | resolved `gh` and file-backed config | verified executable, auth status, Git credential helper | reject keyring-only, unstable, unauthenticated, or incompatible state |
| IF-006 | workspace and memory | persistent workspace path | neutral missing files and one managed startup block | preserve existing content; reject ambiguous blocks |
| IF-007 | add-on Git configuration | two GitHub helper keys | exact reset-plus-persistent-helper pair | preserve unknown custom values and block |

## IF-001 — Persistent filesystem

The runtime root must resolve to a narrow persistent directory outside all Git
worktrees. The installer creates a strict ownership marker, mode `0700`,
generation directory, bootstrap copy, manifests, and atomic `current` link.
Special files, hard-link violations, source mutation, or unexpected ownership
block activation.

## IF-002 — Supervisor options

The installer communicates through the supported Supervisor API transport. It
reads a baseline twice, writes only if unchanged, then reads back and compares
the semantic result. It removes only `gh`/`github-cli`, preserves all
unrelated fields, and puts exactly one managed boot command first.

## IF-003 — Add-on startup

The managed command invokes the persistent bootstrap:

```sh
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh boot
```

A custom runtime root uses the corresponding absolute path. Startup performs
no APT operation, download, executable upgrade, project mutation, or memory
merge.

## IF-004 — Codex CLI

Installation requires file-backed credential storage and a valid local status.
The resolved regular executable is copied, hashed, version-checked, and linked
from the active generation. Audit may run the supported login-status command
but never prints authentication files.

## IF-005 — GitHub CLI

`GH_CONFIG_DIR` points to file-backed configuration. Installation requires an
active GitHub login, copies and verifies `gh`, removes only its one-time
Supervisor bootstrap package, and configures HTTPS Git through the persistent
executable. Server-side expiration is handled by controlled reauthentication,
not by startup.

## IF-006 — Workspace and manual memory

The workspace is separate from `HACP_RUNTIME_ROOT`. Unless
`HACP_MEMORY_SETUP=NO`, installation creates missing neutral
`Memories/AGENTS.md` and `Memories/MEMORY.md` files and one exact managed
block in the effective global Codex startup instructions. Existing files and
approved legacy blocks remain byte-identical. Modified, duplicated, or mixed
managed blocks fail closed.

## IF-007 — Add-on Git configuration

The add-on owns `/data/git/.gitconfig`; the project never copies or replaces
the whole file. For GitHub and Gist only, missing, empty, or known legacy helper
values may be migrated to:

```text
helper =
helper = !<persistent-gh> auth git-credential
```

Every unrelated key, file mode, and owner remains unchanged.

## Diagnostic contract

Diagnostics use one line per check:

```text
OK <check> <summary>
WARN <check> <summary>
BLOCK <check> <summary>
```

Output contains paths and non-sensitive state only—never tokens, credential
contents, session contents, or populated memory.
