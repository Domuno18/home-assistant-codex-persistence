# Deployment

## Target environments

| Environment | Purpose | Data | Approval |
|---|---|---|---|
| isolated test | automated container, failure, and security tests | artificial data only | `./scripts/validate.sh` succeeds |
| Home Assistant reference system | real installation, restart, and container recreation | private local runtime | operator confirms TC-012 |
| additional Home Assistant systems | reusable installation | each system's private local runtime | local operational and security approval |

The public repository contains the reviewed source snapshot. Release tags and
GitHub Releases remain separate, explicitly approved operations governed by
`docs/SECURITY.md`.

## Installation sequence

### 1. Install Studio Code Server

Install the Home Assistant Studio Code Server add-on and start it once. The
add-on already persists Studio Code settings and extensions under
`/data/vscode`. Its global Git configuration is already persistent under
`/data/git/.gitconfig` and is not copied into this project's runtime. This
project does not replace the complete Git configuration; it atomically updates
only two specific credential-helper keys.

### 2. Install the Codex extension

Install the Codex extension from the Studio Code extensions view and verify
that the `codex` command is available in a new terminal.

### 3. Install GitHub CLI once as a bootstrap package

Add the `gh` package to the add-on configuration. A minimal safe configuration
is provided in `config/config.example.yaml`. Restart the add-on and verify:

```sh
gh --version
```

The package serves only as the source for the one-time persistent copy of the
executable. After a successful `install`, the verified persistent executable is
used instead.

### 4. Sign in to both programs

If device-code sign-in for ChatGPT is disabled, enable it first in the security
settings or ask the workspace administrator to enable it. This invocation
explicitly writes the Codex sign-in cache to the Codex home:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login --device-auth
```

Open the link displayed by Codex in a browser, enter the one-time code, and
approve access. The following command should then recognize the local cache:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login status
```

`codex login status` verifies the cache and authentication method; it is not an
independent check of server-side validity.

Sign in to GitHub CLI with a fixed configuration path and deliberately
file-backed credential storage:

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

GitHub CLI displays a one-time device code. If no browser opens, visit
`https://github.com/login/device`, enter the code, select **Continue**, and then
select **Authorize GitHub CLI**. `--insecure-storage` is deliberately required
for this architecture: the credential must be stored in the private persistent
runtime rather than in a volatile container keyring. These directories are
owned by `root:root` and use mode `0700`. Never use
`gh auth status --show-token`.

Never copy output containing credentials or device codes into logs, issues, or
documentation.

### 5. Clone the installation project under `/config` and install once

```sh
GH_CONFIG_DIR=/root/.config/gh \
gh repo clone Domuno18/home-assistant-codex-persistence /config/home-assistant-codex-persistence
cd /config/home-assistant-codex-persistence
./scripts/validate.sh
```

Then close every Codex chat and Codex process. Run the following command from a
normal Studio Code terminal:

```sh
cd /config/home-assistant-codex-persistence
HACP_INSTALL_OK=YES sh ./scripts/ha-codex-persistence.sh install
```

The default target is `/data/codex-persistence`. `install` verifies both
sign-ins, creates stable verified copies, persists the resolved CLI programs,
creates the compatibility links, and adds the automatic `boot` command to the
existing add-on options. Only after the persistent `gh` copy has been verified
and the ready generation synchronized does the same Supervisor update remove
only `gh` or `github-cli` from `packages`. It preserves unrelated packages and
commands in their original order and places the managed boot command first.
Before reporting success, `install` also sets only the Git credential helpers
for `github.com` and `gist.github.com` to the persistent `gh` binary.

Only the installation command changes for the documented reference setup:

```sh
cd /config/Codex/Projekte/home-assistant-codex-persistence
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

Git and GitHub distribute only the version-controlled installation project,
including its script, tests, and documentation. They are neither the
persistence mechanism nor a backup. The private runtime exists only under
`HACP_RUNTIME_ROOT`, while the real local `MEMORY.md` resides in the persistent
workspace under `/config`.

## One-time installation acceptance

Default path:

```sh
HACP_CHECK_AUTH=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
```

Reference path:

```sh
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_CHECK_AUTH=YES \
sh /config/Codex/.runtime/bootstrap/ha-codex-persistence.sh audit
```

The audit must report only `OK` checks and end with `OK result active`. Also
verify in the add-on options that every previous `init_commands` entry remains,
exactly one persistent `boot` command appears first, `packages` contains
neither `gh` nor `github-cli`, and every unrelated package remains unchanged.

The audit must additionally report the exact persistent GitHub and Gist
credential helpers as `OK`. The add-on-owned `/data/git/.gitconfig` remains in
place; only the two explicitly managed keys are changed.

This acceptance check verifies the one-time migration. It is not a chat backup
or a preparation step for later restarts. After a successful `install`, new
state is written directly to persistent storage. Normal restarts require no
prior backup, export, or manual script invocation.

## Targeted Git credential helpers

The standard add-on path `/root/.gitconfig` points to the persistent
`/data/git/.gitconfig`. Neither `install` nor `boot` copies this file into the
project runtime or replaces its complete contents. Both commands atomically
publish only:

```text
credential.https://github.com.helper
credential.https://gist.github.com.helper
```

Each key must then contain exactly two values in this order:

```text
1. <empty>  (resets lower-priority or system helpers)
2. !GH_CONFIG_DIR=/root/.config/gh /usr/local/bin/gh auth git-credential
```

Missing values, empty values, and recognized older
`!…/gh auth git-credential` entries are migrated. Every other Git setting is
preserved. An unknown custom value in either managed key is never replaced
automatically and causes `BLOCK` before activation. The persistent boot command
checks the same contract automatically at every container start; no preparation
step is required before later restarts. Atomic publication preserves every
other value as well as the file mode and owner.

## Offline steady state

After successful installation, normal startup of the persistent `gh` requires
neither APT nor network access. `boot` does not install or update programs. If
unrelated entries remain in `packages`, the add-on continues to process them
before `init_commands`; their package sources therefore remain a documented
risk to a fully offline add-on start. Persisted program upgrades must later use
the verified workflow described by BL-005 and never run during `boot`.

## One-time restart evidence

For the one-time real TC-012 acceptance, record comparison values without
private content before the test restart:

- number of native Codex session files;
- one deliberately resumable session;
- both sign-in statuses;
- project paths, Git HEADs, and working-tree status;
- checksum of the private memory file;
- installed Studio Code extensions.

Then restart the add-on in a controlled manner. `boot` runs automatically
before `code-server`; no manual chat import or repeated sign-in is expected.
Repeat the audit and baseline comparison after startup.

These comparison values serve only as project acceptance evidence. Normal
operation does not require a baseline, backup, or preparation before a restart.

Complete TC-012 acceptance later with a controlled container recreation or
add-on update using the same evidence.

## Include memory

`install` creates only missing `Memories/AGENTS.md` and `Memories/MEMORY.md`
files from `examples/memory`. Existing files remain byte-for-byte unchanged.
Codex uses a non-empty `$CODEX_HOME/AGENTS.override.md` as the global startup
file when it exists; otherwise it uses `$CODEX_HOME/AGENTS.md`. A managed block
references the memory rules first and the private `MEMORY.md` second using
absolute paths. Existing unrelated content is not replaced. The global
location and absolute paths also work when Codex starts inside nested Git
repositories.

The persistent workspace must not be the installation repository itself or be
located below its checkout. The populated working copy is never copied back
into this repository. Native chats remain under `codex-home/sessions`.

## Failed deployment

- When a check reports `BLOCK`, do not delete, move, or combine source and
  target paths.
- Do not manually place a missing or incorrect link over a populated path.
- Preserve add-on logs and audit output only after removing secret values.
- If the Supervisor option update fails during the final installation step,
  audit the state, resolve Supervisor access, and repeat the same `install`
  invocation. Until the atomic option update succeeds, `gh` may remain
  configured as a bootstrap package and may therefore still depend on APT or
  network access.
- Do not execute a program whose checksum is invalid.
- If a sign-in is invalid, rotate or sign in to the affected account again,
  then repeat the authentication audit.
- For `BLOCK git-helper`, do not delete or overwrite the reported existing
  helper. Determine its origin and intended function first. Only then either
  migrate it deliberately to the documented target value or leave the project
  installation safely aborted without changes.

There is no automatic data merge and no automatic program upgrade during
`boot`.

## Removal and recovery

Preserve the persistent runtime unchanged before removing the integration.
Deletion is not a rollback. Before taking the solution out of service, inspect
the add-on startup entry, expected links, required working data, and an
encrypted recovery point individually.

After restoring from a trusted backup, use the read-only audit to verify owners,
modes, markers, program checksums, and links before starting Codex or GitHub
CLI.
