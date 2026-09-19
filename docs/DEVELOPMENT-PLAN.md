# Development plan: remote recovery and the next beta

Date: 2026-09-19. Status: both delivery sprints complete, with the documented beta coverage limits.
Repository language: English. This document is suitable for public distribution.

## Objective and scope

Deliver update-resilient, explicitly enabled Codex remote startup, extend the
existing validation suite, document recent Home Assistant and Studio Code
Server lifecycle evidence, and finish with documented beta prereleases in
both the private and public repositories. The provisional next version is
`0.9.0-beta.4`; confirm that it is unused before preparing the release.
The two sprints below are sequential. Planning does not mark their work done.

Preserve the existing persistence, authentication, access-profile, memory,
Supervisor-option, and Git-helper contracts. Remote connectivity and persistent
state are separate acceptance criteria. A working foreground remote process
is not proof of a managed background service or restart recovery.

## Verified baseline and update evidence

Read-only Supervisor API inspection on 2026-09-19 returned:

| Component | Installed | Available at inspection | Evidence boundary |
|---|---|---|---|
| Home Assistant Core | 2026.9.3 | 2026.9.3 | Current version only; previous version and upgrade time unverified |
| Home Assistant Supervisor | 2026.09.2 | 2026.09.2 | Current version only; previous version and upgrade time unverified |
| Home Assistant OS | 18.2 | 18.3 | 18.3 was available, not installed or accepted |
| Studio Code Server add-on | 7.1.1 | 7.1.1 | Current version; an update was reported by the operator |
| code-server editor runtime | 4.137.0 | Not inspected | Read from the installed package metadata |

The accepted 7.0.0 to 7.1.0 add-on update remains historical evidence in
[REFERENCE-UPDATE-7.1.0.md](REFERENCE-UPDATE-7.1.0.md). It does not establish the
exact later upgrade path or prove remote recovery on 7.1.1.

The local 7.1.1 investigation found persistence and sign-ins intact, but no
managed remote daemon. Starting it failed because `ps` was missing. Installing
`procps` and starting the native managed daemon restored connectivity; repeated
start returned `alreadyRunning`. The operator confirmed successful remote
handover. A real add-on restart after this repair is still unverified.
This is bounded reference evidence, not proof that the update removed `ps`.

Sprint 1 must add a dated, sanitized update record with component versions,
known source and target versions, source of evidence, observed impact, recovery,
checks performed, and outstanding limitations. Unknown upgrade dates or prior
versions stay explicitly unknown. Do not install a pending HA update merely to
complete this record. Refresh versions before lifecycle testing and publication.

## Sprint 1 — implementation and lifecycle acceptance

Status: complete with documented beta evidence limits. Primary development takes place in the private repository.

1. Define the remote lifecycle requirements and domain rules before coding;
   link acceptance criteria to the test IDs below and the evidence matrix.
2. Generalize the local fix: explicit opt-in, validated runtime and CLI paths,
   persistent `procps` dependency, HACP-first startup ordering, idempotent
   daemon start, bounded connection wait, and documented disable/rollback.
3. Preserve unrelated Supervisor options; compare before writing and verify
   read-back. Never enable remote access for existing users without opt-in.
4. Keep HACP `boot` network- and upgrade-free. Resolve/install dependencies
   during an explicit setup or the supported add-on package phase. Define the
   native daemon's separate download/auto-update behavior and compatibility
   policy. The owner explicitly requires the original CLI and Astra compatibility:
   no custom CLI, executable pin, downgrade or model override. Native remote
   startup retains OpenAI updates; HACP persistence boot remains offline.
5. Distinguish a read-only status check from a start/reconnect operation.
   A remote outage must not prevent the local editor from starting. Reject
   unsafe ownership/path/configuration states without changing private data.
6. Extend `scripts/validate.sh` and its invoked tests, retaining all existing
   checks. Add the regression matrix below, including the previously planned
   complete audit non-mutation proof TC-015. Do not weaken gates to pass.
7. Run the live smoke matrix and a controlled add-on restart; record actual
   outcomes separately from simulations. Complete or explicitly resolve the
   existing TC-018 new-session/approval-evidence gap before release.
8. Update installation, architecture, requirements, test plan, evidence matrix,
   backlog, and changelog. Add the current HA/add-on update record described above.

Exit: all applicable automated checks pass, mandatory smoke tests pass, the
real post-repair add-on restart and remote return are evidenced, and rollback
is tested in an isolated environment. No required failed check is waived silently.

## Parallel memory compatibility — Sprint 1 investigation

The delivery goal is compatibility with BOTH deliberately maintained memory
and native Codex Memories, separately and together. HACP and independently
installed workspace tooling must each preserve both mechanisms, including when
used together on the same host. HACP remains specific to Home Assistant; the
maintained-memory function must not depend on HACP on other platforms.
Existing synthetic persistence coverage is not proof of native generation,
retrieval, or successful live coexistence. The final name and storage layout for
the maintained memory are resolved: **Core Knowledge**, with new stores in
`<workspace>/core-knowledge` and safe legacy stores preserved. No automatic
migration is performed. See [MEMORY-COMPATIBILITY.md](MEMORY-COMPATIBILITY.md).

Acceptance includes each mechanism alone and both enabled, fresh setup and
existing installations, repeated setup in either product order, case-insensitive
path collisions, local/remote use and supported lifecycle events. Preserve
existing content and native OpenAI behavior; do not silently merge stores,
change feature settings or rewrite another tool's startup guidance.

- Core Knowledge remains selective: important, confirmed, durable facts and
  working decisions under the existing maintenance rules. Exclude transcripts,
  transient status, credentials, and duplicated project documentation.
- Native Codex Memories retain OpenAI's own supported generation, retrieval,
  retention and control behavior. HACP must not implement a replacement memory
  engine, rewrite native memory files, or apply its manual selection rules to
  the native store. Verify available controls against the installed version
  and current official documentation; do not assume feature availability.
- Document distinct storage locations, ownership, activation and disable paths.
  Persist supported native state without merging the two stores or adding
  automatic synchronization between them. Do not enable the feature merely by
  documenting or testing its compatibility; use isolated opt-in test profiles.
- Test native memory enabled and disabled, manual memory enabled and disabled,
  repeated startup, container replacement, and local/remote session use. Confirm
  that one mechanism does not suppress or overwrite the other. Distinguish
  native generation/retrieval evidence from mere file preservation.
- Use synthetic facts to investigate duplicates, stale facts and contradictory
  recall. Current user corrections and authoritative project sources retain
  priority; neither memory mechanism supplies new permissions. Report limitations
  rather than claiming deterministic native recall or modifying OpenAI's logic.
- Record a compatibility verdict and supported-version boundary in both repos.
  If native functionality is unavailable, mark behavioral evidence unverified;
  do not label preservation tests as a full parallel-operation pass.

Sprint 2 must include the verdict, setup boundaries, tests and known limitations
in the English beta documentation. Never publish populated memory stores or
private examples. This work fits within the existing two sprints.

## Regression matrix — planned automated coverage

The following IDs define acceptance. Implemented coverage and remaining live
boundaries are recorded in [BETA-4-ACCEPTANCE.md](BETA-4-ACCEPTANCE.md).
Tests use synthetic state, isolated roots, mocked network and process adapters.

| ID | Cases and expected result |
|---|---|
| TC-019 | Missing `ps`, missing/unsupported CLI, missing login, invalid runtime ownership and unsafe paths: precise diagnosis, bounded failure, no partial activation or disclosure |
| TC-020 | First start, repeated start, competing starts, stale PID/socket and PID reuse: one correct daemon, no unrelated process termination, no deletion of an active writer lock |
| TC-021 | Remote disabled by default; explicit enable/disable; package and startup ordering; unrelated options preserved; concurrent Supervisor edit and failed read-back rejected |
| TC-022 | Offline network, timeout, rejected authentication, disconnect and reconnect: truthful connection state, bounded startup, editor remains available, secrets absent from output |
| TC-023 | Synthetic container replacement and repeated boot: sessions, sign-ins, tools, memory and Git helpers persist; opted-in remote starts after HACP; no HACP persistence-boot downloads/upgrades; native remote update behavior retained |
| TC-024 | CLI/extension path changes, incompatible versions, explicit dependency setup failure, disable and rollback: preserve previous usable state and avoid hard-coded extension versions |
| TC-015 | Full before/after synthetic runtime manifests prove audit and remote status do not alter files, config or locks, spawn a daemon, or refresh auth |
| TC-025 | Existing TC-018 access profiles and effective client overrides remain distinct; no silent permission widening or automatic lock bypass |
| TC-026 | English docs and relative links; sanitized version/evidence records; public working tree, history, tags and release notes reject confidential markers and private metadata |
| TC-027 | Release version consistency, archive allowlist, SHA-256 manifest verification, archive extraction validation, and parity of intended private/public product code |
| TC-028 | Core Knowledge/native memory mode combinations, isolated persistence and ownership, no cross-store writes or synchronization, explicit opt-in, and synthetic conflict cases; native behavior remains version-dependent |

Retain TC-001 through TC-018, TC-DOM-001 and TC-SEC-001. Expand existing test
cases where appropriate instead of duplicating assertions. Include meaningful
negative cases demonstrating that new validators actually reject violations.
Default validation must remain isolated: no real HA restart, real session
termination, dependency installation, publication, or live account mutation.

## Smoke matrix — planned real reference checks

| ID | Check | Required evidence |
|---|---|---|
| SM-01 | Preflight: component and CLI versions, HACP audit and sign-ins | Sanitized versions and pass/fail; no credential or session content |
| SM-02 | Managed daemon and mobile connection | Background daemon remains alive after launcher exits; connected without timeout; existing conversation usable |
| SM-03 | Same-conversation tools | Harmless command and temporary-file create/read/edit/delete succeed under the selected client permissions |
| SM-04 | Repeat start and reconnect | No duplicate daemon; reconnect succeeds; read-only status does not initiate a connection |
| SM-05 | Controlled Studio Code Server restart | HACP restores first; daemon returns without terminal intervention; sessions and sign-ins persist |
| SM-06 | Local-to-remote handover | Local writer releases normally; same chat resumes remotely; no lock-file deletion or unrelated process stop |
| SM-07 | Fresh-session access-profile check (TC-018) | Actual effective permissions and approval interaction recorded; stored defaults alone do not constitute a pass |
| SM-08 | Repository and artifact smoke | Validate both exact release candidates and extracted artifacts; verify checksums, tags and published prerelease metadata |
| SM-09 | Parallel memory compatibility in an isolated opt-in profile | Manual memory remains selective; native generation/retrieval is checked separately from persistence; local/remote and restart results carry an explicit compatibility verdict |

SM-01 through SM-06, the explicit TC-018 scope resolution under SM-07, and
the bounded SM-09 compatibility investigation gate Sprint 1; SM-08 gates Sprint 2.
SM-07 interactive approvals remain the existing BL-020 beta limitation, as
explained in BETA-4-ACCEPTANCE.md; this is not a claimed approval-interaction pass. A blocked or unperformed
check stays open with its reason. Do not turn old beta.3 evidence into a new pass.
A real HA host reboot or future update/container replacement is a separately
coordinated lifecycle check; simulations and an add-on restart cannot be labelled
as that evidence. Do not disrupt the live host merely to populate a test table.

## Sprint 2 — public transfer and documented beta releases

Status: complete. Prerelease and assets published, downloaded and verified; see BETA-4-ACCEPTANCE.md.

1. Transfer only reviewed product changes to the public repository. Keep this
   development plan and its test/release gates available in both repositories.
2. Review every public surface in English: README, engineering documents,
   fixtures, examples, comments, commit/tag messages, CI output, release text,
   archives, and manifests. Private operational notes are not source material
   to copy wholesale. Use neutral examples and bounded, sanitized evidence.
3. Exclude credentials, private addresses, device/environment/chat identifiers,
   real session or memory data, private project names, and internal provenance.
   Maintain the existing confidential-name prohibition. Use synthetic fixtures
   for leak-detection tests; never place the real prohibited text in public tests.
4. Set the agreed beta version consistently in both candidates. Update
   CHANGELOG, README, release policy and update evidence with features, fixes,
   tested versions, actual validation results, known limits, upgrade and rollback.
5. Run the appropriate full validation and all-history security scan on both
   candidates. Verify a fresh public clone and the extracted release archive;
   check intended code parity without copying private history into public.
6. Build through the documented release entrypoint, preserving the separate
   private and public modes. Verify artifact contents and SHA-256 manifests.
7. Finish with documented GitHub beta prereleases in both repositories, using
   the reviewed commits/tags and their respective artifacts. Preserve repository
   visibility. Read back version, tag, prerelease flag, notes and asset checksums.

Exit: both beta releases are published and verified, their English documentation
matches the shipped behavior, and no public surface contains private details.
A local commit, tag, archive or draft alone is not a completed release.

## Validation and evidence contract

Use `./scripts/validate.sh` during development; exercise the existing `--ci`,
`--release`, and `--private-release` modes in their applicable contexts.
New regression tests must run through that entrypoint, including in CI.
Machine-readable smoke results may be validated automatically, but their
existence must never be substituted for actually performing the live check.
Record exact candidate versions and revisions, test totals, failures/skips,
real lifecycle boundaries, and artifact checksums without exporting private logs.

The schedule does not assume any remaining model quota or promise completion
within it. Complete each sprint with reproducible evidence and a reviewable state.
