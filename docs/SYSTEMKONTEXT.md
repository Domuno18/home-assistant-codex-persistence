# System context

## System boundary

Home Assistant Codex Persistence runs inside the Studio Code Server add-on and
stores selected Codex and GitHub CLI state on persistent Home Assistant
storage. It does not own Home Assistant, Studio Code Server, account services,
project contents, or real memory contents.

## Actors and neighboring systems

| Actor or system | Provides | Expects |
|---|---|---|
| Home Assistant operator | installation approval, persistent path, lifecycle operations | safe, documented recovery behavior |
| Studio Code Server add-on | disposable container plus add-on-owned `/data` state | startup command that fails safely |
| Supervisor API | add-on options read/write | narrow, verified option changes |
| Codex CLI | native state format and status command | complete home at `/root/.codex` |
| GitHub CLI | file-backed configuration and status command | configuration at `/root/.config/gh` |
| GitHub | authenticated HTTPS Git service | valid user authorization |
| persistent workspace | projects and manual memory | no absorption into private runtime |
| project repository | portable scripts, tests, docs, neutral examples | no private runtime data |

## Main data flows

### One-time installation

```text
container state + verified CLI programs
             |
             v
 stable copy -> manifest verification -> ready generation
             -> Supervisor option update
             -> active generation -> managed links
```

### Automatic startup

```text
Supervisor init_commands -> persistent bootstrap -> verify active generation
                         -> validate conflicts -> restore managed links
                         -> code-server
```

### Read-only audit

```text
runtime markers + manifests + links + tools + Git helpers
                         -> optional authentication checks
                         -> OK / WARN / BLOCK
```

## Trust assumptions

- The operator controls the selected persistent path and Home Assistant backup.
- The container runs with the privileges required by the add-on.
- Account providers may expire credentials independently.
- `/data/git/.gitconfig` remains add-on-owned; the project controls only two
  credential-helper keys.
- Project worktrees and real manual memory stay outside `HACP_RUNTIME_ROOT`.
