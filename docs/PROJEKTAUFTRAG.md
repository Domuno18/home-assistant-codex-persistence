# Project charter

> Status: runtime migration, add-on restart, Studio Code Server update from
> `6.0.1` to `7.0.0`, container replacement, and subsequent container
> restart are accepted. Home Assistant host-reboot evidence remains open.

## Assignment

Provide a guarded persistence layer that keeps Codex sessions, configuration,
file-backed sign-in, GitHub CLI sign-in, verified CLI programs, Git credential
helpers, projects, and manual memory usable across Studio Code Server container
lifecycle events.

## Goal and value

After one explicit installation, normal starts require no prepare, export,
restore, package download, link repair, or repeated sign-in. Unexpected state
must block without deletion.

## Roles

| Responsibility | Role |
|---|---|
| scope, priorities, releases | repository maintainers |
| implementation and review | project development |
| add-on options, lifecycle, audit, backup | Home Assistant operator |
| real acceptance under TC-012 | reference-system operator |

## In scope

- REQ-F-001 through REQ-O-004 and AC-001 through AC-012;
- `install`, `boot`, and read-only `audit`;
- immutable runtime generations, manifests, verified tools, and managed links;
- selective Supervisor package transition and Git helper migration;
- neutral manual-memory templates;
- automated tests, security scan, operations, deployment, and acceptance docs.

## Out of scope

- modifying or distributing Home Assistant, Studio Code Server, Codex, or
  GitHub CLI;
- automatic CLI upgrades during startup;
- storing projects, chats, credentials, or populated memory in Git;
- unencrypted runtime backup;
- restoring native sessions from Markdown exports.

## Success criteria

- TC-001 through TC-017 and TC-SEC-001 pass as applicable.
- A real container lifecycle preserves state with no new sign-in or manual
  repair.
- Unknown or damaged state produces `BLOCK` without destructive cleanup.
- Publication contains no confidential state and has explicit approval.

## Risks

| ID | Risk | Control |
|---|---|---|
| RISK-001 | Restart before successful installation loses container-only state. | Require successful authenticated audit first. |
| RISK-002 | Concurrent state changes produce an inconsistent copy. | Close Codex processes and verify source stability. |
| RISK-003 | A conflicting path is overwritten. | Fail closed and preserve it. |
| RISK-004 | Server-side authentication expires. | Audit and controlled reauthentication. |
| RISK-005 | Persistent storage is damaged. | External encrypted backup and verified restore. |
| RISK-006 | Secrets enter Git or diagnostics. | Exclusions, scans, neutral fixtures, and review. |
| RISK-007 | Persisted CLI tools become incompatible. | Explicit verified upgrade/rollback workflow under BL-005. |

## Acceptance

- [x] Scope, requirements, security boundary, and architecture approved.
- [x] Implementation, isolated tests, TC-016, and TC-017 completed.
- [x] Real installation and add-on restart accepted.
- [x] Real add-on update, container replacement, and subsequent restart accepted.
- [x] Publication review, tag, and prerelease approved.
- [ ] Home Assistant host reboot accepted under TC-012.
