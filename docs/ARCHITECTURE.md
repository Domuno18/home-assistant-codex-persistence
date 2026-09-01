# Detailed architecture

## Architecture goals

1. Preserve native Codex and GitHub CLI state across disposable-container
   lifecycle events.
2. Activate only complete and verified runtime generations.
3. Restore standard paths before `code-server` starts.
4. Preserve unexpected state and fail closed.
5. Keep projects, add-on-owned persistence, and real memory outside the runtime.
6. Perform no network download or executable upgrade during normal startup.

## Storage layout

```text
HACP_RUNTIME_ROOT/
├── .hacp-runtime
├── bootstrap/ha-codex-persistence.sh
├── generations/<id>/
│   ├── codex-home/
│   ├── gh/
│   ├── tools/bin/{codex,gh}
│   └── manifests/
└── current -> generations/<id>

/root/.codex       -> HACP_RUNTIME_ROOT/current/codex-home
/root/.config/gh   -> HACP_RUNTIME_ROOT/current/gh
managed tool links -> HACP_RUNTIME_ROOT/current/tools/bin/*
```

The runtime root and active generation use mode `0700`. Projects and manual
memory remain in an independent persistent workspace. Studio Code and
extensions remain under the add-on's native `/data/vscode` persistence.

## Components

| ID | Component | Responsibility |
|---|---|---|
| ARC-001 | installation controller | validate, copy stable state, create manifests, and prepare a generation |
| ARC-002 | generation store | retain complete immutable runtime generations |
| ARC-003 | bootstrap controller | verify active state and restore links before `code-server` |
| ARC-004 | audit adapter | report runtime, integrity, helper, and optional auth state without mutation |
| ARC-005 | workspace/memory boundary | keep projects and real memory separate from private runtime and examples |
| ARC-006 | Supervisor/Git adapter | perform narrow package, startup-command, and helper changes |

## Install sequence

1. Require explicit `HACP_INSTALL_OK=YES` and no active Codex process.
2. Resolve and validate the persistent runtime root.
3. Validate file-backed Codex and GitHub authentication.
4. Resolve Codex and `gh`, check regular-file boundaries, version, and
   architecture, then create checksums.
5. Copy native state and tools into a new generation while verifying source
   stability.
6. Create and verify manifests and neutral memory setup.
7. Compare current Supervisor options, remove only `gh`/`github-cli`, place
   the managed boot command first, write, and verify by read-back.
8. Migrate only supported GitHub and Gist credential-helper values.
9. Mark the generation ready, activate it atomically, and restore managed links.

Repeated installation upgrades only the reviewed bootstrap and managed control
plane when the existing active generation passes every invariant.

## Package lifecycle and offline boundary

The add-on package `gh` is a one-time bootstrap source. After a verified
persistent executable exists, installation removes only `gh` or
`github-cli` from `packages`. Unrelated packages remain untouched and may
still impose their own network requirements. Persisted program upgrades are a
separate, explicit operation under BL-005 and never occur in `boot`.

## Boot sequence

1. Verify runtime claim, active marker, generation path, manifests, modes,
   executable checksums, and versions.
2. Verify the managed Supervisor command and exact Git helper contract.
3. Reject unexpected non-disposable container paths without deleting them.
4. Remove only narrowly defined disposable fresh-container IPC/temp paths.
5. Restore Codex, GitHub CLI, and tool links atomically.
6. Return `OK result active`; otherwise return `BLOCK`.

## Audit sequence

`audit` performs the same ownership, integrity, link, tool, startup, and Git
helper checks without mutation. With `HACP_CHECK_AUTH=YES`, it also invokes
the supported Codex and GitHub status commands without printing credentials.

## Supervisor and Git configuration

Supervisor changes use GET, comparison, POST, and GET read-back. Concurrent
changes abort before the write. The add-on-owned `/data/git/.gitconfig`
remains outside the runtime. Only these keys are managed:

- `credential.https://github.com.helper`
- `credential.https://gist.github.com.helper`

Each managed key is the ordered pair of an empty reset value and the persistent
`gh auth git-credential` helper. Unknown custom values block.

## Lifecycle evidence

The reference installation passed initial installation, add-on restart, a real
Studio Code Server update from `6.0.1` to `7.0.0` with container
replacement, a subsequent container restart, and a complete Home Assistant
host cold start.
