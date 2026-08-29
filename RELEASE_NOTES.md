# Release notes

## v0.9.0-beta.2 — public beta maintenance prerelease

This maintenance candidate restores the guarded persistent bootstrap as the
automatic Studio Code Server startup entry. The generated `init_commands`
entry now invokes the installed `boot` command instead of deleting and
recreating runtime links directly.

### Fixed

- Startup verifies the runtime ownership marker, active generation, manifests,
  persisted executables, Git credential helpers, process state, and every
  conflicting container path before restoring links.
- Unexpected non-disposable Codex or GitHub CLI state blocks startup without
  being removed; only the narrowly defined fresh-container IPC, temporary, and
  empty GitHub CLI directories remain disposable.
- Re-running the explicitly confirmed `install` command on an already active
  installation upgrades the persistent bootstrap copy and managed Supervisor
  startup entry without remigrating sessions, credentials, or CLI programs.
- The read-only audit and repeated install accept both exact official manual
  memory startup blocks from `v0.1.0` and `v0.9.0-beta.1`. Modified, partial,
  duplicated, or mixed managed blocks still fail closed.

### Upgrade

Close active Codex chats and run the documented `install` command again from
this release checkout. A successful repeat installation preserves the sealed
runtime generation, updates the bootstrap and `init_commands`, and must be
followed by the authenticated audit. This is a control-plane update only; it
does not upgrade the persisted Codex or GitHub CLI executables.

### Verified

- The published source passed the complete validation, regression-test,
  traceability, and security-scan gates.
- The reference installation was upgraded through the documented repeated
  `install` path and passed authenticated runtime and network cold-start audits
  before and after a real Studio Code Server restart.
- With bootstrap `0.9.0-beta.2` installed, a real Studio Code Server update
  from `6.0.1` to `7.0.0` replaced the container. Sessions, manual memory,
  Codex and GitHub sign-ins, persisted CLI programs, Git credential helpers,
  and the managed startup entry remained available. Authenticated runtime and
  network cold-start audits also passed after a subsequent container restart.
- The installed bootstrap is byte-identical to the reviewed release source.

## v0.9.0-beta.1 — public beta prerelease

The first public-beta candidate makes it practical to run a durable local Codex agent on a Home Assistant server. The goal is not to modify Codex or Home Assistant, but to keep the complete engineering workspace available when the disposable Studio Code Server container restarts or is recreated.

### Highlights

- Restart-safe Codex sessions, sign-in, configuration, and local state.
- Persistent GitHub CLI sign-in and HTTPS Git credential integration.
- Persistent Codex and GitHub CLI executables for container recreation.
- Standard manual file-based long-term memory through `AGENTS.md`, `MEMORY.md`, and a managed global startup instruction; explicit opt-out is available with `HACP_MEMORY_SETUP=NO`.
- Persistence of Codex-managed local Memories when the operator enables that separate Codex feature; the project does not activate or synchronize it.
- No real memory content is copied into Git.
- Automatic startup integration after one successful installation.
- Read-only runtime and authentication audit.
- Fail-closed handling of conflicting paths, unstable sources, unknown Git
  credential helpers, and damaged persisted executables.

### Tested environment

- Fujitsu Futro S740
- Intel Celeron J4105
- 16 GB RAM
- 128 GB SSD
- Home Assistant OS
- Studio Code Server community add-on
- OpenAI Codex IDE extension and CLI
- GitHub CLI

The add-on restart path has been successfully tested on this environment.
Hardware and software combinations beyond it need community feedback.

### Known limitations

- This is a community beta, not an official Home Assistant, OpenAI, or GitHub
  product.
- A Home Assistant host reboot still needs explicit reference evidence.
- Additional add-on updates and container recreations remain regression tests.
- CLI upgrades and rollback are not automated. Startup intentionally performs
  no package download or tool upgrade.
- Backup and restore of the private runtime are outside this release.
- Installation requires root access inside the Studio Code Server add-on and
  must be performed with all Codex processes closed.

### Release gate

This version is published as a GitHub prerelease after a clean artifact review, successful validation, and explicit owner approval. Independent installation feedback remains preferred beta evidence, and its absence is disclosed as a beta risk rather than broad compatibility evidence.
