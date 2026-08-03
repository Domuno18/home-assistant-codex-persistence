# Security model and safe publication

## Protected assets

| Asset | Classification | Allowed storage | Never allowed |
|---|---|---|---|
| Codex sign-in and native sessions | secret/confidential | private persistent `codex-home` | Git, public documentation, ordinary mirrors, diagnostic output |
| GitHub CLI sign-in | secret | private persistent `gh` directory | Git, examples, logs, unencrypted backup |
| global Git configuration | internal | add-on-owned `/data/git/.gitconfig` | full copy in the project runtime or replacement by this project |
| real manual memory | internal to confidential | operator's persistent workspace | this repository or its neutral template |
| persisted CLI programs | internal | verified private `tools` directory | unverified activation or silent replacement |
| neutral memory template | public | repository and workspace | real people, projects, credentials, or chat content |
| project code and generic documentation | public after approval | repository | runtime files or identifying private metadata |

## Trust boundaries

```text
public/private Git repository
        │ project code, tests, docs, neutral examples only
        X no runtime data
        │
persistent workspace
        │ projects and operator-maintained memory
        X no automatic publication
        │
private persistent runtime
        │ sessions, authentication, configuration, tools
        X no ordinary mirror or unprotected backup
        │
disposable add-on container
        └─ standard paths linked to persistent state

add-on-owned persistent Git configuration
        └─ two managed GitHub helper keys -> persistent gh and gh sign-in
```

## Installation protections

- `HACP_INSTALL_OK=YES` explicitly confirms the mutating installation.
- Installation requires root and a narrow absolute path below `/data`,
  `/config`, or `/share`; broad roots are rejected.
- The runtime must be outside every Git checkout and carry the exact project
  ownership marker. Unknown non-empty targets and symlinked path components
  are rejected before permission or content changes.
- Running Codex processes block installation so sessions and databases cannot
  change during migration.
- Codex must use file-backed credentials. External SQLite homes and
  container-local keyrings are rejected.
- GitHub CLI credentials must exist below `GH_CONFIG_DIR` after higher-priority
  environment tokens are removed. Tokens are never printed with
  `--show-token`.
- Source trees are inventoried repeatedly. Only a stable, identical copy can
  become active.
- Sockets, devices, and FIFOs block migration except for the explicitly
  excluded volatile Codex IPC socket.
- Persisted programs require a matching SHA-256 digest and successful version
  output before activation.
- After a verified persistent `gh` copy exists, installation removes only the
  `gh` or `github-cli` bootstrap package. Unrelated add-on packages and startup
  commands remain unchanged.
- The managed startup command is placed before `code-server` and its option
  update is verified through Supervisor read-back.
- Existing unknown tools, links, Git credential helpers, or unclaimed runtime
  data are never overwritten automatically.

## Git credential protections

The add-on owns `/data/git/.gitconfig`; this project does not copy or replace
the file. It atomically manages only:

```text
credential.https://github.com.helper
credential.https://gist.github.com.helper
```

Each key must contain an empty reset value followed by the persistent GitHub
CLI credential command. Missing, empty, and known older `gh auth
git-credential` values can be migrated. Any unknown custom helper is preserved
and causes `BLOCK` pending an operator decision.

The private sibling copy used for an atomic update retains every unrelated
setting, file mode, and owner. Concurrent changes prevent publication.

## Startup protections

- Startup requires the installation's active or fully verified ready
  generation. It never creates a new empty state.
- Codex and `code-server` must not already be running.
- Correct links remain untouched. Unknown non-empty paths, conflicting links,
  or unverified program files cause `BLOCK`.
- A checksum mismatch blocks activation before any new container link is set.
- Startup performs no package installation, tool update, or network download.
- The two GitHub credential-helper keys are verified before `code-server`
  starts; unrelated Git configuration remains unchanged.

## Read-only audit

`audit` checks markers, metadata, directories, links, permissions, program
checksums, session count, memory guidance, and Git credential helpers without
mutating them. `HACP_CHECK_AUTH=YES` additionally invokes the two CLI status
checks.

Diagnostics include only a level, check name, path or logical target, and a
short result. They must never include file contents, credentials, chat text,
memory content, or the Supervisor token.

## Permissions, backups, and exclusions

- Runtime root, `current`, `state`, `locks`, and `bootstrap` are regular
  directories with mode `0700` and, in production, owner `root:root`.
- Checksums and state markers are not group- or world-readable.
- A runtime below `/config` must be explicitly excluded from unprotected NAS
  or filesystem mirrors.
- Backups containing sign-ins or sessions must be encrypted, access
  controlled, and covered by documented restore and deletion rules.
- The repository must never contain real session formats, databases, logs,
  populated memory files, or runtime archives.

## Memory safety

`examples/memory` contains only neutral structure and maintenance rules.
Installation creates missing workspace files atomically and preserves existing
`AGENTS.md` and `MEMORY.md` byte-for-byte.

This manual memory setup is part of standard installation and is skipped only
when the operator explicitly uses `HACP_MEMORY_SETUP=NO`.

One managed global instruction block instructs Codex to read the persistent manual rules and memory file. Codex discovers the global guidance at session start; the bootstrap does not read either manual file and no technical include mechanism is implemented. Existing unrelated instructions are preserved. There is no copy-back path from the real workspace memory into this repository.

Codex-managed local Memories are a separate optional feature. The installer does not enable them. If the operator enables them separately, their state remains inside the persistent Codex home. There is no synchronization, deduplication, conflict resolution, import, or merge with the manual `MEMORY.md`.

## Credential incident response

1. Revoke or rotate the affected credential at its provider.
2. Inspect reachable Git history, releases, CI output, logs, mirrors, and
   backups.
3. Remove exposed material without printing it again.
4. If it reached Git, clean the reachable history and re-check every copy.
5. Repeat the full security scan and authentication audit.
6. Document the cause and remediation without the secret value.

Deleting a value from only the latest working-tree file is not sufficient.

## Public-release checklist

- [x] Working tree, complete reachable history, and tags are clean.
- [x] No runtime directory, native session, database, or populated memory file
      is tracked.
- [x] Examples contain artificial values and neutral templates only.
- [x] Documentation, tests, screenshots, and artifacts contain no private
      accounts, addresses, credentials, or identifying metadata.
- [x] Shell output and test artifacts contain no secrets.
- [x] Upstream relationship and license review is documented in
      `THIRD_PARTY.md`; this repository uses MIT.
- [x] The real reference runtime and workspace remain local.
- [x] Version and release decision are consistent with `docs/RELEASES.md`.
- [x] English public user documentation review is complete; supplementary
      internal engineering records may remain in German.
- [x] The owner has explicitly approved public repository visibility.
- [ ] The owner has explicitly approved the beta tag and GitHub Release.

The repository is public. A tag and GitHub Release remain blocked until the remaining release evidence and explicit release approval exist.
