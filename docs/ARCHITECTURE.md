# Architecture overview

## Goal

The add-on container is disposable; the engineering workspace is not. The
project keeps private Codex and GitHub state in persistent Home Assistant
storage while preserving the standard paths expected by the existing tools.

## Storage model

```text
Home Assistant persistent storage
├── private runtime
│   ├── codex-home       sessions, sign-in, config, native state
│   ├── gh               GitHub CLI sign-in
│   ├── tools            verified codex and gh executables
│   ├── bootstrap        startup/audit script
│   └── state            ownership, generation, and checksums
└── workspace
    ├── projects
    └── Memories         optional human-maintained context

disposable add-on container
├── /root/.codex      -> private runtime/codex-home
├── /root/.config/gh  -> private runtime/gh
├── /usr/local/bin/codex -> private runtime tool
└── /usr/local/bin/gh    -> private runtime tool
```

Studio Code and extensions remain under the add-on's existing `/data/vscode`
storage. The add-on also continues to own `/data/git/.gitconfig`.

## Lifecycle

### Install

`install` is the only one-time migration step. It requires explicit
confirmation, rejects active Codex processes, verifies stable sources, copies
the private state, records checksums, registers startup integration, and
activates only a fully verified generation.

### Startup

The managed add-on startup command restores the four standard container paths
before `code-server` starts. Startup is idempotent, performs no tool upgrade,
and blocks unknown conflicting state.

### Audit

`audit` is read-only. It verifies the active generation, paths, permissions,
checksums, session presence, memory guidance, Git credential helpers, and
optionally the two CLI authentication states.

## Memory mechanisms

The standard mechanism is manual file-based memory. Installation creates only missing `Memories/AGENTS.md` and `Memories/MEMORY.md` files and adds one managed block to the effective global Codex `AGENTS` file. This setup is disabled only when installation explicitly uses `HACP_MEMORY_SETUP=NO`. Codex discovers the global guidance at session start; the block instructs Codex to read the two manual files. The bootstrap itself does not read them, and the project implements no memory engine or technical include mechanism.

The installer does not enable `[features] memories = true`. If an operator enables Codex-managed local Memories separately, their configuration and state remain persistent because the complete Codex home is preserved. The two mechanisms have no synchronization, deduplication, conflict resolution, import, or merge logic.

## GitHub credential integration

The project does not replace the global Git configuration. It atomically
manages only the credential helpers for `github.com` and `gist.github.com` so
HTTPS Git operations use the persistent GitHub CLI sign-in. Unknown custom
helpers cause a fail-closed result.

## Failure model

Potentially destructive ambiguity always results in `BLOCK`. The project does
not merge unknown directories, replace foreign symlinks, trust unstable source
data, activate programs with mismatched checksums, or silently overwrite custom
Git helpers.

## Repository boundary

The Git repository contains the installer, tests, documentation, and neutral
templates only. The private runtime, real sessions, credentials, projects, and
populated memories are never copied into the repository.

For the detailed engineering architecture and traceability records, see the
remaining documents in this directory. Their English migration is part of the
public-beta release gate.
