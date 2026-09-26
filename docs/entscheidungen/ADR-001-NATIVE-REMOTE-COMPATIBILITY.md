# ADR-001: Native remote socket and home compatibility

- Date: 2026-09-26
- Status: accepted; beta.5 code and independent review passed, publication evidence recorded separately
- Scope: REQ-I-006/007, REQ-O-007; DOM-R-019–021; TC-029–031

## Context

The original Codex CLI `0.157.1` advertises its local control socket through a
persistent symlink. The physical socket uses a private directory below `/tmp`.
Rejecting every socket symlink therefore rejects a legitimate native service;
accepting arbitrary links would weaken HACP's control-path boundary. Container
replacement can remove the temporary target while retaining the persistent
alias.

HACP also previously supplied an explicit persistent `CODEX_HOME` even when the
native default symlink already selected that home. Child working directory,
Codex state home, operating-system home, and a mobile client's selected remote
folder are different values and must not be treated as interchangeable.

## Decision

1. Retain support for direct private sockets. For a Linux native alias, verify
   its owner, private control directory, and trusted ancestors. Derive the
   expected target as `/tmp/codex-daemon-<uid>/<sha256>`, where the hash covers
   the canonical alias parent joined with the alias filename. Require exact
   target equality, root-owned sticky `/tmp`, a user-owned `0700` target
   directory, and a user-owned socket with no additional symlink chain.
2. Only after that validation, classify a missing temporary directory or
   socket as stale. A refused connection additionally requires absence from
   the kernel socket table. Inconclusive and unsafe states stay unreachable.
   HACP performs no deletion or process termination; native Codex owns recovery.
3. Omit the child `CODEX_HOME` override only when the existing default
   `~/.codex` symlink resolves to the verified persistent home. Otherwise keep
   the explicit persistent value. Preserve `HOME` and other environment values,
   and launch from the runtime root's parent rather than an inherited cwd.
4. Document the smartphone explicit-folder procedure separately from these
   backend compatibility changes. Automatic home detection remains open.

## Consequences and verification

This is a narrow Linux compatibility adapter, not a replacement transport,
custom CLI, client patch, or guarantee for all Codex versions. The alias shape
and temporary-directory contract come from the original tagged CLI sources:
[native socket mapping](https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/app-server-transport/src/transport/unix_socket.rs)
and [private temporary directory](https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/uds/src/daemon_directory.rs).

TC-029 must cover accepted paths, rejection boundaries, and stale temporary
state. TC-030 must cover default-home eligibility, fallback, and cwd. TC-031
must retain separate mobile observations. Candidate execution results belong to
[BETA-5-ACCEPTANCE.md](../BETA-5-ACCEPTANCE.md); existing operational spot checks
are not a full candidate or container-replacement acceptance.
