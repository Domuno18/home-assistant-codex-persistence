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

## 5. Enable full Codex use inside the protected add-on container

Use this only when Studio Code Server provides the outer container boundary and
Codex reports that its nested Linux sandbox cannot start. This keeps Home
Assistant add-on protection enabled. It does not disable approvals.

Activate the exact persistent profile:

```sh
HACP_CODEX_CONTAINER_ACCESS=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh configure-access
```

For a custom runtime, use its bootstrap path and set `HACP_RUNTIME_ROOT`.
The command requires the explicit acknowledgement above, changes only these
top-level Codex settings, and preserves unrelated configuration:

```toml
sandbox_mode = "danger-full-access"
approval_policy = "on-request"
approvals_reviewer = "user"
```

The protected add-on container is the outer isolation boundary. HACP writes
persistent defaults; it does not change a running chat's effective permission
profile. Treat project instructions and shell commands as trusted-code inputs.

### Required Codex access level: local and remote

For this container workaround, the active execution profile must permit
unrestricted filesystem access: **Full access** (or **unrestricted access**,
depending on the client), corresponding to `danger-full-access`. A restricted
`workspace-write` profile still attempts the unavailable nested sandbox.
This is a permission setting, not a model, reasoning level, or subscription tier.

| Entry point | Operator action | What proves the setting took effect |
|---|---|---|
| Codex IDE chat in Studio Code Server | Select Full access in the active chat's permission control. | A normal command and the file-edit tool both work in that chat. |
| Remote chat connected to the same host | Select Full access for the existing remote task/chat in the controlling client. A host default alone is insufficient evidence. | The next response uses unrestricted access and passes the same tool checks. |
| Codex CLI | Use `codex --sandbox danger-full-access --ask-for-approval on-request`, or the explicitly configured defaults. | The running session reports the intended permissions and tools succeed. |

Finish the current response after changing the permission setting, then send
"Test access" in the **same chat**. Keep its conversation and context. Neither a
new conversation nor a container restart is a prerequisite for this procedure.
The reference remote chat applied the operator's change on its next response.
Other client versions must be checked rather than assumed to behave identically.
If the profile remains restricted, inspect the client selection and any managed
requirements; restarting the container does not prove those overrides changed.

Filesystem access and approval behavior are separate. HACP sets `on-request`
and `approvals_reviewer = "user"`, not `never`. These settings do not guarantee
a confirmation before every command: commands already allowed by Full access
can run directly. A client permission preset can also change approval behavior.
In the reference remote check, the client supplied unrestricted access with
`approval_policy = "never"`; this was the operator's client selection, not an
HACP setting or a demonstrated requirement. Record the effective profile and
approval policy separately. Broad technical access does not expand the task
the operator authorized.

Official background: [Codex approvals and container sandboxing](https://learn.chatgpt.com/docs/agent-approvals-security).

### Verify the running chat, not only the configuration file

Ask the agent in the same chat to:

1. Run `python3 -c 'print("CODEX_ACCESS_TEST_OK")'` through its normal command
   tool, without a per-command escalation.
2. Use its normal file-edit tool to create and modify a uniquely named temporary
   test file; read it back and check the content.
3. Remove its own test file and verify cleanup.

An approved command running outside the sandbox, or a simple command allowed
by an existing rule, is not sufficient evidence that normal tooling works.
A `bwrap: Failed to make / slave: Permission denied` result means the command
path is still trying the unavailable nested sandbox. Report that path as
unresolved even if another tool succeeds.

Separately verify the persistent configuration without changing state:

```sh
HACP_CHECK_CODEX_ACCESS=YES \
HACP_CHECK_ADDON_CONFIG=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
```
The add-on check confirms exactly one managed HACP boot command and rejects the
retired HACP `rm -rf` command. Audit never repairs Supervisor options; rerun a
confirmed installation to apply that narrow cleanup.

The access-profile audit reads the stored configuration. It does not inspect
the active remote turn or execute its command/file tools; a successful audit
must not be described as end-to-end chat access acceptance.

### Service access is checked separately

Full access permits tools to use the container's available files and network.
Each service still validates its own credentials and permissions. GitHub
sign-in and repository permissions are checked independently. File access
under the workspace is verified through the tool checks above.

## 6. Audit

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

A normal installation creates missing `core-knowledge/AGENTS.md` and
`core-knowledge/MEMORY.md` files and adds the managed startup instruction to the
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
- Studio Code Server update from `7.0.0` to `7.1.0`, containing
  `code-server 4.137.0` and including container recreation;
- a subsequent container restart;
- a complete Home Assistant host cold start.

Codex sessions, manual memory, both sign-ins, persisted CLI programs, Git
credential helpers, projects, and the managed startup entry remained
available. Authenticated runtime and network cold-start audits passed after the
host returned.

During the `7.1.0` update, the existing Codex conversation resumed and
projects, GitHub access, sessions, and manual memory remained available. The
authenticated persistence audit passed afterward. See
[the recorded update evidence](REFERENCE-UPDATE-7.1.0.md).

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

## Beta.4 remote startup and memory paths

New installations use Core Knowledge in `<workspace>/core-knowledge`. Existing
safe `<workspace>/Memories` stores remain unchanged. Native Codex Memories are
separate; see [MEMORY-COMPATIBILITY.md](MEMORY-COMPATIBILITY.md) before combining
workspace tools. Enable native remote startup explicitly using
[REMOTE-STARTUP.md](REMOTE-STARTUP.md). HACP restores persistence first, then the
separate native remote phase runs. No custom CLI or model override is installed.
