# Home Assistant Codex Persistence

> A persistent, restart-safe AI engineering workspace for Home Assistant.

**Community beta candidate · Self-hosted · GitHub-ready · Manual-memory included**

Home Assistant Codex Persistence keeps a complete local Codex engineering workspace alive when the Studio Code Server container restarts or is recreated. Sessions, sign-ins, configuration, tools, GitHub access, projects, and the standard manual file-based memory remain available from persistent storage. Codex-managed local Memories also remain persistent when the operator enables that separate Codex feature.

> [!WARNING]
> This is an independent community beta. Back up your Home Assistant system,
> read the installation steps, and test on non-critical infrastructure first.

## Why

**Your coding agent should come back after a restart exactly where it left off.**

A useful engineering agent is more than a login or a command. It has ongoing sessions, tools, repositories, configuration, working conventions, and accumulated context. Losing that workspace at every container lifecycle event turns a long-lived engineering partner back into a freshly installed tool.

**Persistent workspace. Persistent context. Persistent engineering.**

The goal is not to modify Codex or Home Assistant. The goal is to create a durable local coding agent that does not start from zero after a container restart. This project adds a reproducible persistence layer between Home Assistant storage and the complete Codex workspace used inside Studio Code Server. The included manual file-based memory is one part of that workspace, not the product by itself.

## How

One guarded installation moves the relevant container-local state into a
private persistent runtime and connects the standard paths back to it. An
automatic startup command restores those connections before `code-server`
starts.

The project provides:

- persistent Codex sessions, sign-in, configuration, and local state;
- persistent GitHub CLI sign-in and HTTPS Git credentials;
- persistent, verified Codex and GitHub CLI executables;
- a separate workspace for projects and manual file-based memory, configured
  by default unless installation explicitly uses `HACP_MEMORY_SETUP=NO`;
- persistence of Codex-managed local Memories when the operator enables them separately;
- automatic bootstrap on every add-on start;
- read-only runtime and authentication validation;
- fail-closed protection against conflicting paths or damaged state;
- no prepare, export, or restore step before a normal restart.

New sessions and state changes are written directly to persistent storage after
installation. This is persistence, not a Git-based backup of private data.

## What

`home-assistant-codex-persistence` is an installer, startup integration,
read-only audit, test suite, and documentation for an existing Home Assistant
Studio Code Server installation.

It is **not**:

- Home Assistant or a Home Assistant add-on;
- Studio Code Server;
- OpenAI Codex or its IDE extension;
- GitHub CLI;
- a distributor of any of those projects;
- a repository for chats, credentials, projects, or populated memory files.

It distributes only this project code and neutral templates. It does not redistribute Home Assistant, Studio Code Server, OpenAI Codex, Visual Studio Code, or GitHub CLI. This is an independent community project and is not affiliated with or endorsed by OpenAI, Home Assistant, Microsoft, or GitHub. See [THIRD_PARTY.md](THIRD_PARTY.md) for the compatibility and license review.

## Current beta status

The reference system has been migrated successfully. A real Studio Code
Server add-on restart preserved Codex sessions, both sign-ins, and both CLI
programs. The generated `init_commands` entry now matches that verified
startup path.

This public repository contains the reviewed `v0.9.0-beta.1` prerelease. The private development history is not published.

Independent installation feedback, host-reboot evidence, and a later add-on update remain valuable beta evidence. They are not presented as compatibility that has already been proven.

## Tested environment

| Component | Tested value |
|---|---|
| Hardware | Fujitsu Futro S740 |
| CPU | Intel Celeron J4105 |
| Memory | 16 GB RAM |
| Storage | 128 GB SSD |
| Platform | Home Assistant OS |
| Editor | Studio Code Server community add-on |
| Agent | OpenAI Codex IDE extension and CLI |
| Git integration | GitHub CLI |

✅ Successfully tested for installation and add-on restart on this environment.

Other architectures and hardware combinations are welcome as community test
reports.

## Prerequisites

Before running the installer:

1. Install and start the Home Assistant **Studio Code Server** community
   add-on.
2. Install the OpenAI Codex extension in Studio Code.
3. Add package `gh` to the add-on configuration and restart the add-on once.
4. Sign in to Codex and GitHub CLI using device authentication.
5. Clone this repository into persistent storage below `/config`.

The installer later removes only the temporary `gh`/`github-cli` bootstrap
package after it has verified the persistent copy. It preserves all unrelated
packages and startup commands.

## Device sign-in

Codex must use file-backed credential storage because a container-local
keyring is not persistent:

```sh
CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login --device-auth

CODEX_HOME=/root/.codex \
codex -c 'cli_auth_credentials_store="file"' login status
```

GitHub CLI must likewise store its credential below its configured directory:

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

GitHub displays a device code. If no browser opens, visit
<https://github.com/login/device>, enter the code, and authorize GitHub CLI.
Never print the stored credential with `--show-token`.

## Install once

Close **all Codex chats and Codex processes** before installation. Then run the
following commands in a normal Studio Code terminal:

```sh
GH_CONFIG_DIR=/root/.config/gh \
gh repo clone Domuno18/home-assistant-codex-persistence \
  /config/home-assistant-codex-persistence

cd /config/home-assistant-codex-persistence
HACP_INSTALL_OK=YES sh ./scripts/ha-codex-persistence.sh install
```

The default private runtime is `/data/codex-persistence`. Advanced users may
select another narrow persistent path below `/data`, `/config`, or `/share`:

```sh
HACP_RUNTIME_ROOT=/config/Codex/.runtime \
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

The target must be outside every Git checkout. The installer claims it with a
strict ownership marker and refuses unknown non-empty directories, symlinked
paths, active Codex processes, unstable source data, and unverifiable sign-in
state.

After a successful installation, simply restart the add-on whenever needed.
There is no `prepare` step and no manual chat backup or restore workflow.

## Verify the installation

Run the read-only audit once after installation and optionally after a restart
or container lifecycle event:

```sh
HACP_CHECK_AUTH=YES \
sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
```

The expected result contains only `OK` checks and ends with:

```text
OK result active
```

For a custom runtime root, invoke the bootstrap script below that root.

## What stays persistent

| Data | Default location | Owner |
|---|---|---|
| Studio Code and extensions | `/data/vscode` | Studio Code Server add-on |
| global Git configuration | `/data/git/.gitconfig` | add-on; this project manages only two GitHub credential-helper keys |
| Codex home and sessions | `/data/codex-persistence/current/codex-home` | Codex and this project |
| GitHub CLI configuration | `/data/codex-persistence/current/gh` | GitHub CLI and this project |
| persisted CLI executables | `/data/codex-persistence/current/tools` | this project |
| projects and manual memory | persistent workspace below `/config` | operator |

The private runtime contains credentials and chat state. Never commit, mirror,
or attach it to an issue.

## Sessions and memories

The repository implements one memory mechanism and preserves a second optional mechanism. They are independent.

### Included: manual file-based memory

As part of a standard installation, the installer creates missing
`Memories/AGENTS.md` and `Memories/MEMORY.md` files in the persistent workspace.
It also adds one managed block to the effective global `AGENTS.override.md` or
`AGENTS.md` in the persistent Codex home. This setup is skipped only when the
operator explicitly installs with `HACP_MEMORY_SETUP=NO`.

Codex automatically discovers that global guidance when a session starts. The managed block instructs Codex to read the manual rules first and the manual memory second. The bootstrap does not read either file, and this project implements no memory engine or technical include mechanism. Existing files are preserved and real memory content is never copied back into this repository.

### Optional: Codex-managed local Memories

The installer does **not** add the following setting:

```toml
[features]
memories = true
```

An operator may enable it separately in the persistent `config.toml`. Because this project persists the complete Codex home, the configuration and any Codex-managed `memories/` state remain available after container restarts.

There is no synchronization, deduplication, conflict resolution, automatic import, or merge between Codex-managed Memories and the manual `MEMORY.md`. See [the manual memory guide](examples/memory/README.md) and the [official Codex Memories documentation](https://learn.chatgpt.com/docs/customization/memories#configure-local-memories).

## Community beta

Feedback, issues, tested-environment reports, and pull requests are welcome.
Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md)
before sharing logs or diagnostic information.

This software is provided without warranty under the [MIT License](LICENSE).
Use it on non-critical systems first and keep an appropriate Home Assistant
backup.

## Documentation

The English README, installation guide, architecture, security model, release
policy, and memory guide are the authoritative public user documentation.
Some additional engineering records retain their original German language;
they are not required to install or operate the project.

- [Installation and operations](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Detailed security model](docs/SECURITY.md)
- [Release policy](docs/RELEASES.md)
- [Public beta roadmap](docs/PUBLIC_BETA_ROADMAP.md)
- [Release notes](RELEASE_NOTES.md)
- [Third-party and trademark statement](THIRD_PARTY.md)
- [Changelog](CHANGELOG.md)

## Development and validation

```sh
./scripts/validate.sh
```

The validation checks shell and Python syntax, project structure,
traceability, secrets, and the automated integration test suite. Real add-on and
host lifecycle evidence remains a separate acceptance step.

## Official references

- [Studio Code Server add-on configuration](https://github.com/hassio-addons/addon-vscode/blob/main/vscode/DOCS.md)
- [Codex authentication](https://learn.chatgpt.com/docs/auth)
- [Codex config and state locations](https://learn.chatgpt.com/docs/config-file/config-advanced#config-and-state-locations)
- [Codex `AGENTS.md` guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex local Memories](https://learn.chatgpt.com/docs/customization/memories#configure-local-memories)
- [GitHub CLI authentication](https://cli.github.com/manual/gh_auth_login)
- [GitHub CLI authentication status](https://cli.github.com/manual/gh_auth_status)
