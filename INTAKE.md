# Confirmed project intake

## Summary

| Question | Confirmed answer |
|---|---|
| What will be built? | A reusable persistence solution for Codex CLI and GitHub CLI in the Home Assistant Studio Code Server add-on. |
| What problem does it solve? | The replaceable container must no longer be the only copy of native Codex chats, sign-ins, configuration, and required CLI programs. |
| Who uses the result? | Home Assistant operators who use Studio Code Server with Codex and GitHub CLI. |
| How is success determined? | After a restart or container recreation, native chats remain resumable, both sign-ins remain valid, HTTPS Git access uses the persistent GitHub sign-in, projects and memory remain available, and the audit reports no `BLOCK`. |
| Which systems are involved? | Home Assistant Supervisor, Studio Code Server, the Codex extension and Codex CLI, GitHub CLI, persistent add-on storage, and a persistent workspace. |
| What is confidential? | Sign-in files, native sessions, databases, private configuration, and real memory content. |

## Confirmed installation sequence

1. Install Studio Code Server as a Home Assistant add-on.
2. Install the Codex extension in Studio Code.
3. Install GitHub CLI once as the `gh` bootstrap package through the add-on
   configuration.
4. Sign in to Codex and GitHub CLI and successfully run both status checks.
5. Clone `home-assistant-codex-persistence` into persistent storage under
   `/config`, close all Codex processes, and run `install` exactly once from a
   normal terminal.

After a successful `install`, `boot` runs automatically before `code-server` at
every add-on start. `audit` remains a strictly read-only check. After verifying
the persistent `gh` copy and synchronizing the ready generation, the same
Supervisor update removes only `gh` and `github-cli` from `packages`, preserves
unrelated packages and commands, and places the managed boot command first.
Normal startup of `gh` then requires neither APT nor network access. Any
unrelated packages that remain configured limit this offline guarantee for the
complete add-on startup.

## Storage decision

- Generic default: `/data/codex-persistence`
- Configurable alternative: a safe absolute path under `/data`, `/config`, or
  `/share`
- Reference example: `/config/Codex/.runtime`
- Studio Code and extensions: already persisted by the add-on under
  `/data/vscode`
- Global Git configuration: already persisted by the add-on under
  `/data/git/.gitconfig`; this project publishes only the two ordered GitHub
  and Gist reset-plus-helper value pairs
- Projects and real memory file: a separate persistent workspace under
  `/config`
- GitHub repository: storage and distribution of the version-controlled
  installation project only; never runtime persistence or backup

## Protection and boundary decisions

- The complete Codex home is treated as one state boundary, including native
  sessions, sign-in, configuration, and databases.
- The complete GitHub CLI configuration is persisted together.
- The add-on-owned global Git configuration is not copied into the project
  runtime and its complete semantic contents are not replaced. Only the GitHub
  and Gist helpers are atomically set to an empty reset value followed by the
  persistent `gh auth git-credential` command; unknown helpers remain unchanged
  and cause a block.
- Codex and GitHub CLI programs are verified during `install` and stored
  persistently so that a new container does not depend on their previous
  locations.
- `gh` is only a bootstrap package. Its package aliases are removed selectively
  only after persistence has been verified; unrelated packages and commands
  remain unchanged. `boot` does not install or update programs.
- The volatile native IPC socket is not copied; other special files block
  installation.
- Two populated or contradictory states are never merged automatically.
- The repository contains only a neutral memory template. A populated real
  memory file remains in the persistent workspace.
- The private runtime exists only under `HACP_RUNTIME_ROOT`; Git and GitHub do
  not receive a copy.
- Native chats are not restored from Markdown; their authoritative source
  remains `codex-home/sessions`.
- Real credentials, sessions, and memory content never enter Git or ordinary
  unprotected mirrors.

## Modeling scope

| Area | Decision | Rationale |
|---|---|---|
| Domain model | required | Installation, active generation, links, and blocking conditions have fixed invariants. |
| Interfaces | required | Filesystem, Supervisor API, `init_commands`, and both CLIs must remain clearly separated. |
| State and security logic | required | Unsafe states must fail closed. |
| Mathematics and control | not applicable | There is no domain calculation or control function. |
| ISA-95 | not applicable | The project has no production or industrial-equipment context. |

## Assumptions and risks

- `ANN-001`: The selected target path remains persistent across restart, update,
  and container recreation.
- `ANN-002`: `init_commands` run with the required permissions before
  `code-server`.
- `ANN-003`: Studio Code and extensions remain independently persistent under
  `/data/vscode`.
- `ANN-004`: The add-on processes a non-empty `packages` list through APT before
  `init_commands`; an empty list skips that step.
- `RISK-001`: A restart before a successful `install` can lose the only native
  state under `/root`.
- `RISK-002`: A changing source cannot produce a consistent copy and must cause
  a block.
- `RISK-003`: Runtime data or real memory content can accidentally enter Git,
  logs, or mirrors.
- `RISK-004`: Providers can revoke or expire sign-ins server-side; persistence
  alone does not guarantee permanent account validity.
- `RISK-005`: Persistence protects against container replacement but does not
  replace an encrypted backup of persistent storage.
- `RISK-006`: Unrelated add-on packages that remain configured may require APT
  or network access before `init_commands` and prevent offline startup.
- `RISK-007`: Persisted CLI programs may become outdated or incompatible with a
  later container; the upgrade workflow remains BL-005.

## Remaining evidence

The isolated baseline tests, selective package transition, and automated
Supervisor evidence TC-016 are complete. A real Studio Code Server add-on
restart has also been accepted successfully. Home Assistant host-reboot
evidence and a future real add-on update or container recreation remain beta
follow-up evidence under TC-012; they are not claimed as already proven
compatibility.

## Traceability

```text
Intake -> US/REQ/AC -> DOM/ARC -> AP -> TC -> Acceptance
```

The complete mapping is maintained in `docs/NACHWEISMATRIX.md`.
