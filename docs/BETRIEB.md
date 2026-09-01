# Operations

## Operational objective

After one guarded installation, Studio Code Server may restart, update, or
replace its container without a prepare, export, restore, package download,
manual link repair, or repeated sign-in step.

## Responsibilities

| Activity | Owner |
|---|---|
| installation, add-on options, lifecycle, and backup | Home Assistant operator |
| runtime, integrity, and authentication audit | operator or technical reviewer |
| account authorization and credential rotation | account owner |
| program and project upgrades | project maintainer with review |

## Existing add-on persistence

The project does not copy or replace `/data/vscode` or the complete
`/data/git/.gitconfig`. It manages only the two documented GitHub credential
helper keys. Projects and real manual memory remain in an operator-owned
persistent workspace outside `HACP_RUNTIME_ROOT`.

## One-time installation

1. Back up the Home Assistant system and use non-critical infrastructure.
2. Install Studio Code Server and the Codex extension.
3. Add `gh` to add-on `packages`, restart once, and sign in to Codex and
   GitHub CLI with file-backed credentials.
4. Clone the project below persistent storage.
5. Close all Codex chats and processes.
6. Run:

```sh
HACP_INSTALL_OK=YES sh ./scripts/ha-codex-persistence.sh install
```

For the documented reference layout:

```sh
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_WORKSPACE_ROOT=/config/Codex \
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

Installation must finish successfully before any lifecycle operation. Never
force past `BLOCK` and never delete an unknown conflicting path.

## Post-installation check

```sh
HACP_CHECK_AUTH=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
```

A healthy audit contains only `OK` checks and ends with
`OK result active`. Custom roots use their own bootstrap path.

## Normal startup

The managed Supervisor command runs `boot` before `code-server`. Repeated
successful boot is normal and idempotent. A `BLOCK` stops startup so that
unexpected state can be investigated without deletion.

## Git credential helpers

The project preserves the add-on-owned Git configuration and manages only the
GitHub and Gist helper keys. Each must contain an empty reset value followed by
the persistent `gh auth git-credential` helper. Any unknown custom helper is
left unchanged and blocks automatic migration.

## Manual memory

The standard setup creates missing neutral memory files and adds one managed
global startup block. Existing real memory content remains local and
byte-identical. Codex-managed local Memories are a separate optional Codex
feature; this project only persists their storage when enabled.

## Lifecycle acceptance

Record a baseline of sessions, sign-in status, tool versions, helper values,
project paths and Git state, memory checksum, and extensions. After the
lifecycle event, run authenticated runtime and network cold-start audits and
compare the baseline without printing confidential content.

Accepted evidence:

- initial installation and add-on restart;
- Studio Code Server update from `6.0.1` to `7.0.0` with container
  replacement;
- subsequent container restart.

Still open:

- Home Assistant host reboot.

## Troubleshooting

- **Not installed:** do not create links manually; complete the guarded install
  or restore a verified encrypted backup.
- **Conflicting path or symlink:** inventory it, determine ownership, and keep
  it unchanged until a deliberate resolution is approved.
- **Invalid executable checksum:** do not run the tool; use the future verified
  upgrade/rollback workflow under BL-005.
- **Startup still needs APT/network:** inspect unrelated configured packages;
  HACP removes only the one-time `gh` package.
- **Invalid authentication:** close active processes and reauthenticate only
  the affected CLI through its documented file-backed flow.
- **Unknown Git helper:** preserve it and decide explicitly whether migration
  is appropriate.
- **Supervisor write failure:** keep the runtime unactivated and resolve API,
  permission, or concurrent-option changes first.

## Backup and restore

The private runtime contains credentials and native sessions. Never place it in
Git or an unencrypted mirror. Backup and restore require a separately reviewed
encrypted workflow and a successful audit before use.
