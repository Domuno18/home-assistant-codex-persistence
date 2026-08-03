# Project profile: Home Assistant Codex Persistence

## Identity

| Field | Value |
|---|---|
| Project | Home Assistant Codex Persistence |
| Repository | `home-assistant-codex-persistence` |
| Users | Home Assistant operators using Studio Code Server, Codex, and GitHub CLI |
| Ownership and priorities | Repository maintainers |
| Operational acceptance | Operator of the Home Assistant reference system |
| Target date of the first version | 2026-07-30 |
| Status | Runtime migrated and real add-on restart confirmed; host reboot and a future add-on update or container recreation remain additional beta evidence |
| Visibility | Clean public source repository; full development history retained separately in the private archive |

## Goal and value

The Codex home, native chats, Codex sign-in and configuration, and GitHub CLI
sign-in are stored outside the replaceable Studio Code Server container. After
one installation, an automatic startup command restores every required link and
the two GitHub credential helpers. Projects and the condensed long-term memory
remain independently stored in a persistent workspace.

The following therefore survive a restart, add-on update, or container
recreation:

- resumable Codex sessions;
- Codex and GitHub sign-ins;
- Codex configuration;
- required CLI programs;
- HTTPS Git access through the persistent GitHub sign-in;
- Studio Code and extensions through the add-on's existing persistence;
- projects and the private memory file in the persistent workspace.

## Installation sequence

1. Install Studio Code Server.
2. Install the Codex extension.
3. Install GitHub CLI once as the `gh` add-on bootstrap package.
4. Sign in to Codex and GitHub CLI.
5. Clone the repository under `/config` and run `install` once.

Afterwards, `boot` runs automatically before `code-server`, while the read-only
`audit` remains available at any time. After persistence has been verified, the
same Supervisor update removes only `gh` or `github-cli` from `packages`,
preserves unrelated packages and commands, and places the managed boot command
first. The persisted `gh` can then start without APT or network access.
Unrelated packages that remain configured are a documented residual risk to
fully offline add-on startup.

Git and GitHub contain only the installation project. They are neither the
persistence mechanism nor a backup. The private runtime resides under
`HACP_RUNTIME_ROOT`, while the real local `MEMORY.md` resides in the persistent
workspace.

## Storage locations

| Area | Generic default | Reference example |
|---|---|---|
| private runtime | `/data/codex-persistence` | `/config/Codex/.runtime` |
| Studio Code and extensions | `/data/vscode` | `/data/vscode` |
| global Git configuration | add-on-owned `/data/git/.gitconfig` | `/data/git/.gitconfig`; the project manages only two helper keys |
| projects and real memory file | persistent workspace under `/config` | `/config/Codex` |

## Scope

**Included in the project:**

- portable shell implementation for `install`, `boot`, and `audit`;
- persistent Codex and GitHub CLI state and verified programs;
- automatic integration through `init_commands`;
- atomic, selective removal of the one-time `gh` bootstrap packages while
  preserving unrelated add-on options unchanged;
- targeted management of only the GitHub and Gist credential helpers in the
  add-on-owned persistent Git configuration;
- neutral memory template;
- tests and security, operations, and acceptance documentation.

**Not included in the project:**

- installation or internal persistence of Studio Code and extensions;
- real credentials, sessions, or populated memory files in the repository;
- automatic program upgrades during `boot`;
- unencrypted backup of the private runtime;
- restoration of native chats from Markdown exports.

## Modeling requirements

| Area | Status | Document |
|---|---|---|
| Domain model | required | `docs/DOMAENENMODELL.md` |
| Interfaces and startup sequence | required | `docs/SCHNITTSTELLEN.md` |
| State and security logic | required | `docs/DOMAENENMODELL.md`, `docs/SECURITY.md` |
| ISA-95 | not applicable | `docs/ISA95-MODELL.md` |
| Mathematics or control | not applicable | `docs/MATHEMATISCHES-MODELL.md` |

## Acceptance status

- [x] Project purpose and protection requirements documented
- [x] Requirements, architecture, and domain rules traceable
- [x] Neutral memory template contains no private content
- [x] Isolated container, failure, and security tests successful
- [x] Package transition implemented in the script
- [x] Git helper migration and conflict handling automated through TC-017
- [x] Automated Supervisor test TC-016 completed
- [x] Real installation and add-on restart confirmed under TC-012
- [x] Clean public repository created without the private development history
- [ ] Home Assistant host reboot accepted under TC-012
- [ ] Future add-on update or container recreation accepted as a regression test
- [x] Public beta tag and GitHub Prerelease explicitly approved and published
