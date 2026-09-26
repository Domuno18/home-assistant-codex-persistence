# Domain model

## Domain boundary

The project owns migration, verification, activation, startup restoration, and
read-only auditing of the persistent Codex and GitHub CLI runtime. Home
Assistant, Studio Code Server, account providers, project contents, and real
memory contents remain outside this boundary.

## Shared language

| Term | Meaning |
|---|---|
| container state | Disposable paths normally located below `/root` |
| persistent runtime | Claimed storage below `HACP_RUNTIME_ROOT` |
| generation | Immutable candidate containing Codex home, GitHub CLI state, and verified tools |
| active generation | Fully verified generation selected by `current` |
| managed path | Standard container path linked to the active generation |
| persistent workspace | Operator-owned storage for projects and manual memory |
| container-access profile | Explicit Codex configuration for a container that provides the outer isolation boundary when nested `bwrap` is unavailable |
| fail closed | Stop with `BLOCK` while preserving unexpected state |

## Domain objects

| ID | Object | Responsibility |
|---|---|---|
| DOM-O-001 | Runtime claim | Binds a narrow directory to this project |
| DOM-O-002 | Runtime generation | Holds one verified immutable state |
| DOM-O-003 | Active marker | Selects the only active generation |
| DOM-O-004 | State manifest | Records expected files, modes, and hashes |
| DOM-O-005 | Tool bundle | Holds verified Codex and GitHub CLI programs |
| DOM-O-006 | Managed path set | Maps standard container paths to `current` |
| DOM-O-007 | Persistent workspace | Holds projects and real manual memory outside the runtime |
| DOM-O-008 | Container-access profile | Binds technical access to `danger-full-access` while retaining on-request, user-reviewed approvals |

## Domain rules

| ID | Invariant | Evidence |
|---|---|---|
| DOM-R-001 | Installation activates only a stable and complete copy. | TC-001, TC-006 |
| DOM-R-002 | Only a verified generation may become active. | TC-001, TC-013 |
| DOM-R-003 | Repeated startup restores the same active generation idempotently. | TC-002, TC-003 |
| DOM-R-004 | Unexpected non-disposable container state is preserved and blocks startup. | TC-004 |
| DOM-R-005 | Executable or manifest integrity failure blocks activation and links. | TC-005 |
| DOM-R-006 | Real memory content is never copied into the repository; existing memory is preserved. | TC-011 |
| DOM-R-007 | Project worktrees and add-on-owned persistence are not absorbed or replaced. | TC-012, TC-017 |
| DOM-R-008 | Audit observes state without mutation or secret disclosure. | TC-009, TC-015 |
| DOM-R-009 | Supervisor changes are compare-before-write, selective, and verified by read-back. | TC-016 |
| DOM-R-010 | Only the two GitHub credential-helper keys may be migrated; unknown values block. | TC-017 |
| DOM-R-011 | Container access is never implicit: only an explicit operator acknowledgement may set the three exact top-level Codex access keys. | TC-018 |
| DOM-R-012 | The access-profile update preserves every unrelated config byte semantically, rejects ambiguous or unsafe config paths, and is reported by read-only audit. | TC-018 |
| DOM-R-013 | HACP does not disable Home Assistant add-on protection; the add-on container remains the outer isolation boundary. | TC-018, TC-012 |

## State transitions

```text
unclaimed --install--> ready --verify/activate--> active
active --boot--> active
active --audit--> active
any invariant violation --> BLOCK without destructive cleanup
```

## Domain events

- `RuntimeReady`: runtime trees and tools have passed verification.
- `RuntimeActivated`: `current` selects the verified generation.
- `BootstrapConfigured`: the managed startup command is installed.
- `ContainerAccessConfigured`: persistent access defaults were explicitly set; this does not attest an active chat's effective permissions.
- `AuditPassed`: all selected read-only checks succeeded.

## Beta.4 invariants

| ID | Invariant | Evidence |
|---|---|---|
| DOM-R-014 | Remote is opt-in; persistence restores first; unrelated options and running native services are preserved. | TC-019–TC-024 |
| DOM-R-015 | The official CLI owns remote transport, package updates and models; HACP creates no custom CLI or model override. | TC-024 |
| DOM-R-016 | Core Knowledge never overlaps native memory by path or case, merges stores or redirects legacy guidance silently. | TC-028 |
| DOM-R-017 | Status and audit have no HACP filesystem mutations; native service logging is outside that assertion. | TC-015 |
| DOM-R-018 | Release archives match their commit/version manifest and contain only regular safe source members. | TC-027 |

## Beta.5 native compatibility rules

| ID | Invariant | Evidence |
|---|---|---|
| DOM-R-019 | A native rendezvous alias is trusted only when its owner and private control directory are verified and its target exactly matches `/tmp/codex-daemon-<uid>/<sha256>` for the canonical alias path. Target ownership, `0700` directory mode, root-owned sticky `/tmp`, and safe ancestors remain mandatory. | TC-029 |
| DOM-R-020 | Removing a child-process `CODEX_HOME` override requires an existing native default symlink to the same persistent home. Other cases retain the explicit persistent home; child working directory and client-selected folder are separate concepts. | TC-030 |
| DOM-R-021 | Remote transport connection, native home-directory access, explicit-folder chat startup, and automatic-home voice startup are distinct observations; one does not prove the others. | TC-031 |
| DOM-R-022 | Both repository lines contain the same product files and behavior; only the enumerated provenance fields in REPOSITORY-PARITY.md may differ. | TC-032 |

A **native rendezvous alias** is the persistent control-path symlink created by
the original CLI. Its **physical socket** lives in a private host-local temporary
directory and may disappear on container replacement. A validated missing
physical target is `stale`, not evidence that private persistent state was lost.
A refused connection is stale only when the kernel has no corresponding socket
entry. Unsupported or unsafe aliases and inconclusive checks remain
`unreachable`; HACP never reclaims the endpoint itself.

The exact compatibility decision and failure boundaries are recorded in
[ADR-001](entscheidungen/ADR-001-NATIVE-REMOTE-COMPATIBILITY.md).
