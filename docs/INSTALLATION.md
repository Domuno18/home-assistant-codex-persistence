# Installation and operation

This guide is for beta testers who already run the Home Assistant Studio Code
Server community add-on.

This is the canonical installation, normal-operation, troubleshooting, and
recovery guide. The README provides only a concise project introduction.

## Before you start

- Use a non-critical Home Assistant system or make an appropriate backup.
- Confirm that `/data`, `/config`, or `/share` is persistent on your setup.
- Do not place the private runtime inside this or any other Git checkout.
- Do not run the installer while any Codex chat or process is open.
- Never paste authentication files, session data, or a populated memory file
  into an issue.

## 1. Install the existing components

1. Install and start the Studio Code Server community add-on.
2. Install the OpenAI Codex IDE extension in Studio Code.
3. Add `gh` to the add-on's `packages` option and restart the add-on once.

The package is needed only to bootstrap GitHub CLI. The installer later removes
only `gh` or `github-cli` after a verified persistent executable exists.

## 2. Sign in with device authentication

Use a file-backed Codex credential cache:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login --device-auth

CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login status
```

Use a file-backed GitHub CLI credential:

```sh
(
  unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN
  GH_CONFIG_DIR=/root/.config/gh \
    gh auth login \
      --hostname github.com \
      --git-protocol https \
      --web \
      --insecure-storage
  GH_CONFIG_DIR=/root/.config/gh \
    gh auth status --active --hostname github.com
)
```

GitHub's device flow uses <https://github.com/login/device>. Never run
`gh auth status --show-token` when collecting diagnostics.

## 3. Clone the project

```sh
GH_CONFIG_DIR=/root/.config/gh \
gh repo clone Domuno18/home-assistant-codex-persistence \
  /config/home-assistant-codex-persistence

cd /config/home-assistant-codex-persistence
```

## 4. Close Codex and install once

Close every Codex chat and process, then use a normal Studio Code terminal:

```sh
HACP_INSTALL_OK=YES sh ./scripts/ha-codex-persistence.sh install
```

The default runtime is `/data/codex-persistence`. To use a different narrow
persistent location:

```sh
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

Installation copies stable local state, verifies it, activates persistent
links, stores verified CLI programs, binds the two GitHub HTTPS credential
helpers, and registers the automatic startup command.

If installation reports `BLOCK`, do not force it and do not delete the
reported path blindly. Read the check name and inspect the conflicting state.

## 5. Audit

For the default runtime:

```sh
HACP_CHECK_AUTH=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
```

A healthy result ends with `OK result active`.

For a custom runtime, invoke the bootstrap script below that root. Audit is
read-only and can be repeated after a restart, host reboot, or add-on update.

## Normal operation

After successful installation:

- restart the add-on normally;
- do not run a prepare script;
- do not export or restore chats;
- do not rerun installation before each restart;
- use audit only when you want a health check.

Codex and GitHub CLI continue to use their usual `/root` paths, which now point
to the private persistent runtime.

## Standard manual file-based memory

A normal installation creates missing `Memories/AGENTS.md` and
`Memories/MEMORY.md` files and adds the managed startup instruction to the
effective global Codex `AGENTS` file. Existing memory files are preserved.

Only operators who explicitly do not want this standard setup should add
`HACP_MEMORY_SETUP=NO` to the one-time installation command.

## Optional Codex-managed local Memories

The included manual file-based memory works without enabling the Codex Memories feature. The installer does not add `[features] memories = true`.

An operator may enable that separate Codex feature after installation in the persistent `/root/.codex/config.toml`:

```toml
[features]
memories = true
```

If a `[features]` table already exists, add the key to that table instead of creating a duplicate table. The complete Codex home is persistent, so Codex-managed memory state remains available across container restarts. It is not synchronized or merged with the manual `Memories/MEMORY.md`.

## Beta feedback

When reporting a result, include only:

- hardware architecture and general hardware model;
- Home Assistant OS and Studio Code Server add-on versions;
- tested lifecycle event;
- final audit status and redacted check names;
- whether sessions and both sign-ins remained usable.

Do not attach the runtime, authentication files, sessions, databases, or real
memory content.

## Verified lifecycle evidence

The reference system has passed:

- initial installation and add-on restart;
- Studio Code Server update from `6.0.1` to `7.0.0`, including container
  replacement;
- a subsequent container restart;
- a complete Home Assistant host cold start.

Codex sessions, manual memory, both sign-ins, persisted CLI programs, Git
credential helpers, projects, and the managed startup entry remained
available. Authenticated runtime and network cold-start audits passed after the
host returned.

## Troubleshooting

### `boot` reports not installed

Do not create links manually. Complete the guarded installation or restore a
separately verified encrypted backup.

### A path or symlink conflicts

Do not delete it blindly. Inventory the path, determine its owner and origin,
and keep it unchanged until a deliberate resolution is approved.

### A persisted executable fails its checksum

Do not run it. Normal startup never upgrades tools; use the future verified
upgrade and rollback workflow tracked as BL-005.

### Startup still requires APT or network access

Inspect unrelated packages in the add-on configuration. The installer removes
only the one-time `gh` or `github-cli` bootstrap package.

### Authentication is invalid

Close affected processes and reauthenticate only the affected CLI through the
documented file-backed device flow.

### `git-helper` reports an unknown value

The project preserves custom helper configuration and blocks automatic
migration. Review the value and decide explicitly whether it may be replaced.

### Supervisor options cannot be updated

Resolve API availability, permission, or concurrent configuration changes
before retrying. The installer must not activate a runtime until read-back
matches the intended narrow update.

## Backup and recovery

The private runtime contains credentials and native sessions. Never place it in
Git or an unencrypted mirror. Backup and restore require a separately reviewed
encrypted workflow, followed by a successful authenticated audit.
