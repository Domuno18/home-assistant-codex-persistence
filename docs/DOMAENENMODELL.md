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
- `AuditPassed`: all selected read-only checks succeeded.
