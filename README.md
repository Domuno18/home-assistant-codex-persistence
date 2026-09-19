# Home Assistant Codex Persistence

> A persistent, restart-safe AI engineering workspace for Home Assistant.

**Community beta candidate · Self-hosted · GitHub-ready · Core Knowledge included**

Home Assistant Codex Persistence keeps a complete local Codex engineering workspace alive when the Studio Code Server container restarts or is recreated. Sessions, sign-ins, configuration, tools, GitHub access, projects, and the Core Knowledge remain available from persistent storage. Codex-managed local Memories also remain persistent when the operator enables that separate Codex feature.

> [!WARNING]
> This is an independent community beta. Back up your Home Assistant system,
> read the installation steps, and test on non-critical infrastructure first.

## Why

**Your coding agent should come back after a restart exactly where it left off.**

A useful engineering agent is more than a login or a command. It has ongoing sessions, tools, repositories, configuration, working conventions, and accumulated context. Losing that workspace at every container lifecycle event turns a long-lived engineering partner back into a freshly installed tool.

**Persistent workspace. Persistent context. Persistent engineering.**

The goal is not to modify Codex or Home Assistant. The goal is to create a durable local coding agent that does not start from zero after a container restart. This project adds a reproducible persistence layer between Home Assistant storage and the complete Codex workspace used inside Studio Code Server. The included Core Knowledge is one part of that workspace, not the product by itself.

## How

One guarded installation moves the relevant container-local state into a
private persistent runtime and connects the standard paths back to it. An
automatic startup command restores those connections before `code-server`
starts.

The project provides:

- persistent Codex sessions, sign-in, configuration, and local state;
- persistent GitHub CLI sign-in and HTTPS Git credentials;
- persistent, verified Codex and GitHub CLI executables;
- a separate workspace for projects and Core Knowledge, configured
  by default unless installation explicitly uses `HACP_MEMORY_SETUP=NO`;
- persistence of Codex-managed local Memories when the operator enables them separately;
- automatic bootstrap on every add-on start;
- read-only runtime and authentication validation;
- an explicitly activated container-access profile for protected add-on
  environments where a second Linux `bwrap` sandbox is unavailable;
- on-request approvals routed to the user while the add-on container remains
  the outer isolation boundary;
- targeted removal and read-only detection of the retired HACP `rm -rf`
  startup command while preserving unrelated add-on commands;
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
Server add-on update from `6.0.1` to `7.0.0`, including container replacement
and a subsequent container restart, preserved Codex sessions, manual memory,
both sign-ins, both CLI programs, Git credential helpers, and the managed
startup entry. Authenticated runtime and network cold-start audits passed
afterward.

A second real update from Studio Code Server `7.0.0` to `7.1.0`, containing
`code-server 4.137.0`, also recreated the add-on container successfully. The
existing Codex conversation resumed and projects, GitHub access, Codex
sessions, and manual memory remained available. The post-update authenticated
persistence audit passed without a blocker. See the
[7.1.0 lifecycle evidence](docs/REFERENCE-UPDATE-7.1.0.md).

`v0.9.0-beta.4` adds opt-in native remote startup and Core Knowledge / Codex Memories compatibility. It remains a beta; see [acceptance and limits](docs/BETA-4-ACCEPTANCE.md).
On the reference system, the existing remote chat's command and file tools
worked after the operator selected Full access and sent the next message.
No new conversation or container restart was needed. A successful stored-config
audit alone did not prove that access. Client approval settings are separate;
see [the required access level and verification](docs/INSTALLATION.md#required-codex-access-level-local-and-remote).

Independent installation feedback remains valuable beta evidence. The
reference environment has now also passed a complete Home Assistant host cold
start.

## Tested environment

| Component | Tested value |
|---|---|
| Hardware | Fujitsu Futro S740 |
| CPU | Intel Celeron J4105 |
| Memory | 16 GB RAM |
| Storage | 128 GB SSD |
| Platform | Home Assistant OS |
| Editor | Studio Code Server community add-on `7.1.0` |
| Editor runtime | `code-server 4.137.0` |
| Agent | OpenAI Codex IDE extension and CLI |
| Git integration | GitHub CLI |

✅ Successfully tested for installation, add-on updates from `6.0.1` to
`7.0.0` and from `7.0.0` to `7.1.0`, container replacement, a subsequent
container restart, and a complete Home Assistant host cold start on this
environment.

Other architectures and hardware combinations are welcome as community test
reports.

## Installation and operation

Use the canonical [installation and operation guide](docs/INSTALLATION.md).
It contains prerequisites, device sign-in, the one-time installation command,
audit, normal operation, memory configuration, lifecycle evidence,
troubleshooting, and recovery guidance.

Do not install from abbreviated commands copied into issues or discussions.
The guarded procedure and its safety conditions belong to that guide.

## Community beta

Feedback, issues, tested-environment reports, and pull requests are welcome.
Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md)
before sharing logs or diagnostic information.

This software is provided without warranty under the [MIT License](LICENSE).
Use it on non-critical systems first and keep an appropriate Home Assistant
backup.

## Documentation

All public user and engineering documentation is maintained in English.

- [Installation and operations](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project charter](docs/PROJECT-CHARTER.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Domain model](docs/DOMAIN-MODEL.md)
- [Interfaces](docs/INTERFACES.md)
- [Test plan](docs/TEST-PLAN.md)
- [Evidence matrix](docs/EVIDENCE-MATRIX.md)
- [Detailed security model](docs/SECURITY.md)
- [Release policy](docs/RELEASES.md)
- [Backlog](docs/BACKLOG.md)
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

## Next beta development plan

See the [two-sprint development plan](docs/DEVELOPMENT-PLAN.md) for remote recovery, recent platform-update evidence, regression and smoke coverage, and the next documented beta release.

## Native remote startup and memory compatibility

[Remote startup](docs/REMOTE-STARTUP.md) uses the original OpenAI CLI and preserves
its native update and model behavior, including Astra where available. No custom
CLI is introduced. [Core Knowledge and Codex Memories](docs/MEMORY-COMPATIBILITY.md)
use separate stores; existing safe memory content remains in place. The current
[update investigation](docs/REFERENCE-UPDATE-7.1.1.md) distinguishes persistence
from remote connectivity.
