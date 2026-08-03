# Release notes

## v0.9.0-beta.1 — prepared, not yet tagged

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
- A future add-on update or container recreation is treated as a regression
  test when an update is available.
- CLI upgrades and rollback are not automated. Startup intentionally performs
  no package download or tool upgrade.
- Backup and restore of the private runtime are outside this release.
- Installation requires root access inside the Studio Code Server add-on and
  must be performed with all Codex processes closed.

### Release gate

This public snapshot is not a GitHub Release yet. Tag and release publication require a clean artifact review, successful validation, and explicit owner approval. Independent installation feedback remains preferred beta evidence, but its absence may be accepted transparently as a beta risk.
