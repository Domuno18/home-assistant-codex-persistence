# Requirements

## Functional requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-F-001 | Persist the complete Codex home, including native sessions, configuration, and file-backed sign-in, outside the disposable container. | AC-001, AC-002, AC-005, AC-009 |
| REQ-F-002 | Persist GitHub CLI configuration and provide authenticated HTTPS Git access through the persistent sign-in. | AC-003, AC-005, AC-009, AC-012 |
| REQ-F-003 | Leave projects and Studio Code add-on-owned persistence outside the project runtime and unchanged. | AC-004, AC-010 |
| REQ-F-004 | Create and preserve the Core Knowledge setup unless explicitly disabled. | AC-011 |
| REQ-F-005 | Persist verified Codex and GitHub CLI executable files with checksums and architecture compatibility. | AC-005, AC-010 |
| REQ-F-006 | Provide an explicitly activated Codex container-access profile for Studio Code Server environments that cannot create the nested Linux sandbox. | AC-013 |

## Integration requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-I-001 | Update Supervisor options atomically, remove only the one-time `gh` package and exact retired HACP `rm -rf` command, preserve unrelated options and commands, and install the managed boot command first. | AC-009, AC-010, AC-013 |
| REQ-I-002 | Restore standard container paths from the active persistent generation before `code-server` starts. | AC-005, AC-010 |
| REQ-I-003 | Keep the persistent workspace and add-on-owned storage outside `HACP_RUNTIME_ROOT`. | AC-010, AC-012 |
| REQ-I-004 | Manage only the GitHub and Gist credential-helper keys and preserve all unrelated Git configuration. | AC-007, AC-009, AC-010, AC-012 |
| REQ-I-005 | Bind the container-access profile to the exact top-level Codex settings `danger-full-access`, `on-request`, and user-reviewed approvals while preserving unrelated settings. | AC-013 |

## Quality and security requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-Q-001 | `boot` is idempotent. | AC-006 |
| REQ-Q-002 | Installation copies stable regular files only and detects source changes. | AC-009 |
| REQ-Q-003 | Unknown ownership, paths, helpers, special files, or integrity failures block without destructive mutation. | AC-007 |
| REQ-S-001 | Repository content, history, examples, logs, and artifacts contain no credentials, native sessions, private runtime, or populated memory. | AC-008 |
| REQ-S-002 | Publication requires explicit approval and completed security and license review. | AC-008, AC-011 |
| REQ-S-003 | HACP must not silently disable Home Assistant add-on protection, bypass approvals, or activate container access without an explicit operator acknowledgement. | AC-013 |

## Operational requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-O-001 | `install` validates prerequisites, supported credential storage, programs, paths, and process state before activation. | AC-002, AC-003, AC-009 |
| REQ-O-002 | `audit` is read-only and reports runtime, integrity, helper, and optional authentication state without exposing secrets. | AC-002, AC-003, AC-007, AC-008, AC-011, AC-012 |
| REQ-O-003 | Default and custom runtime roots are documented and constrained to persistent storage. | AC-005, AC-009 |
| REQ-O-004 | Real lifecycle acceptance records installation, restart, update, container replacement, and host-reboot evidence separately. | AC-001 through AC-006, AC-010, AC-012 |
| REQ-O-005 | `audit` optionally verifies the persisted Codex container-access defaults and managed Supervisor startup command without mutation or disclosure; actual chat access requires separate command and file-tool evidence. | AC-013 |

## Constraints

- Normal startup performs no package download or executable upgrade.
- The runtime root must be a narrow persistent path below `/data`, `/config`,
  or `/share`, outside every Git checkout.
- All Codex processes must be closed during initial installation or runtime
  migration. A verified already-active installation may refresh only its HACP
  bootstrap/configured launcher without migrating state or restarting Codex;
  see the bounded maintenance procedure in INSTALLATION.md.
- Container-access configuration supplies defaults, not an override of the
  active chat. Client-selected permissions and approval behavior must be
  verified in the actual local or remote response. Updating permissions for
  the same chat does not require discarding its conversation.
- Installation, add-on restart, add-on update, container replacement,
  subsequent container restart, and Home Assistant host cold-start evidence
  are complete for the reference environment.

## Beta.4 additions

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-F-007 | Explicit remote opt-in delegates to the original managed Codex CLI, preserving native updates and model selection. | AC-014, TC-019–TC-024 |
| REQ-F-008 | Core Knowledge and native Codex Memories coexist without merging, enabling or overwriting one another. | AC-015, TC-028 |
| REQ-O-006 | Remote status is read-only, bounded and free of machine identity; remote boot failure leaves the editor available. | AC-014, TC-015, TC-022 |
| REQ-Q-004 | Candidate version, source archives and checksum manifests are verified in both repository lines. | AC-016, TC-026, TC-027 |

AC-014 requires isolated normal/failure tests and separately identified live
remote evidence. AC-015 requires fresh/legacy and all memory-mode combinations,
including both independent workspace setup orders and case-insensitive overlap
rejection. AC-016 requires complete validation, public-content review and
verified release artifacts. Current evidence is in
[BETA-4-ACCEPTANCE.md](BETA-4-ACCEPTANCE.md); earlier lifecycle passes do not
establish a post-repair restart or native memory recall.

## Beta.5 compatibility requirements

| ID | Requirement | Acceptance |
|---|---|---|
| REQ-I-006 | Read the original native CLI control socket through either the supported direct socket or its exact deterministic Linux alias; classify a safely validated missing temporary target as stale and delegate recovery to native Codex. | AC-017, TC-029 |
| REQ-I-007 | Use the native default Codex home only when its existing symlink resolves to the verified persistent home; otherwise pass that persistent home explicitly. Preserve other environment values and launch from the runtime root's parent. | AC-018, TC-030 |
| REQ-O-007 | Document an explicit-folder smartphone startup procedure and distinguish observed client behavior from backend checks and unproven causes. | AC-019, TC-031 |
| REQ-Q-005 | Keep both repository lines at the same product version, code, tests and shared documentation, permitting only enumerated historical provenance and publication metadata differences. | AC-020, TC-032 |

- AC-017: Accept the expected native alias and legacy direct socket; reject
  wrong hashes, owners, modes, symlink chains, and untrusted ancestors. Missing
  native temporary directory/socket after container loss yields `stale` only
  for the validated alias. A refused connection requires absent kernel-listener
  evidence before stale recovery; permission and inspection failures stay
  `unreachable`. Status itself performs no recovery or deletion.
- AC-018: With a verified matching default symlink, omit only `CODEX_HOME` from
  the child environment. Missing, unrelated, regular-directory, or dangling
  default paths retain the explicit persistent value. Keep `HOME`, unrelated
  environment values, and native model/approval selection unchanged; verify
  the child's working directory independently of client folder selection.
- AC-019: The guide identifies the intended remote host, an existing remote
  folder, chat creation, and voice startup in sequence. Evidence records
  existing-chat voice, the complete new-chat-in-explicit-folder-to-voice
  workaround, and automatic-home startup separately, distinguishing operator
  reports from automated checks and stating the client platform and uncertainty.
- AC-020: The parity checker reports zero unexplained inventory, executable,
  version or product-content differences; both release candidates are clean.
  Drift blocks build/tag creation. No whole product file is exempted.

Fresh candidate validation passed; subsequent release and deployment outcomes are recorded in
[BETA-5-ACCEPTANCE.md](BETA-5-ACCEPTANCE.md). These requirements do not promise
that a backend compatibility change repairs the client's automatic folder
selection. OPEN-REMOTE-001 tracks that unresolved behavior.
