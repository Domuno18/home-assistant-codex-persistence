# Native Codex remote startup

HACP uses the **original OpenAI Codex CLI**. It does not build a fork, distribute
another CLI, copy or pin the remote executable, select a model, or replace native
remote lifecycle logic. Model availability, including Astra where provided by
the account and client, remains controlled by OpenAI. HACP never promises model
availability from a file or version check.

Remote startup is opt-in and separate from persistence. A successful persistence
audit does not prove that remote transport is connected. `status` reads the
native local control endpoint and prints only daemon and connection states;
it never starts a daemon, refreshes authentication, or prints machine identity.

## Setup

1. Install and authenticate the official Codex CLI using OpenAI's supported
   procedure. Start native remote control once with `codex remote-control start`.
   This lets OpenAI create its managed package directory and native service.
2. Install HACP using [INSTALLATION.md](INSTALLATION.md). Keep its persistence
   boot command first in Studio Code Server `init_commands`.
3. Ensure `procps` and `python3` are available through the add-on's supported
   package configuration. HACP does not install packages in its boot script.
4. Explicitly configure remote startup from the repository. Substitute the
   actual persistent runtime root in both arguments:

```sh
python3 scripts/hacp_remote.py configure --enable \
  --runtime-root /data/codex-persistence \
  --cli /data/codex-persistence/current/codex-home/packages/standalone/current/bin/codex
```

Configuration verifies ownership, the existing official managed CLI and its
native remote-start command, then installs the Python launcher and records
opt-in. It adds `procps` and `python3` to the add-on package list and inserts its
own remote command immediately after HACP boot. Unrelated options are preserved.
Concurrent Supervisor changes and failed read-back prevent activation. A failed
read-back restores the previous helper and leaves active state unchanged; it
does not blindly overwrite concurrent Supervisor options.

```sh
python3 scripts/hacp_remote.py status --runtime-root /data/codex-persistence
python3 scripts/hacp_remote.py start --runtime-root /data/codex-persistence
```

The launcher delegates to the existing official `remote-control start --json`
command with a 45-second timeout. Existing reachable daemons are preserved,
including when transport is connecting or errored. A stale socket left by a
crash is checked against the kernel socket table; native Codex owns reclamation.
HACP never deletes a chat lock, kills an unrelated process, or replaces an
unreachable service. Boot warnings return success so the editor remains usable.

## Native updates and models

HACP persistence boot remains offline. The separate, explicitly enabled native
remote phase uses network connectivity and **retains OpenAI's own package and
auto-update behavior**. The launcher follows the official managed `current`
selection at every start. It does not force a historical CLI or extension
version and passes no model, feature, sandbox or approval overrides.

The reference check used official Codex CLI 0.154.0 and Studio Code Server 7.1.1.
A future CLI without the supported remote-start command needs a new compatibility
check; HACP will report a warning rather than synthesize a replacement CLI.
A successful CLI start alone is not evidence of connectivity or Astra access.

## Disable and rollback

```sh
python3 scripts/hacp_remote.py configure --disable --runtime-root /data/codex-persistence
```

Disable removes only HACP's remote init command and disables its startup state.
It preserves packages, native packages, sign-ins, sessions, memories and the
currently running service. Use the official `codex remote-control stop` command
if the operator also wants to stop that service. Restore an earlier HACP source
release through its documented installation procedure; never downgrade or
replace the native CLI as part of HACP rollback. Before an upgrade, retain a
private backup of the previous HACP bootstrap and add-on options. These backups
must stay outside Git and release artifacts.
