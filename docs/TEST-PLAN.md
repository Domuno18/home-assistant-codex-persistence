# Test concept and test cases

## Strategy

Automated tests use artificial isolated roots and test doubles. Real lifecycle
acceptance is recorded separately because simulation cannot prove behavior on
the Home Assistant reference system.

## Automated integration and failure tests

| ID | Covers | Action and expected result | Status |
|---|---|---|---|
| TC-001 | REQ-F-001, REQ-F-002, REQ-F-005, REQ-I-002, REQ-I-004 | install artificial native state, replace the container tree, boot and audit; sessions, auth, tools, links, and helpers persist | automated |
| TC-002 | REQ-I-002, REQ-Q-003, DOM-R-003 | run `boot` without installation; return `BLOCK` and create nothing | automated |
| TC-003 | REQ-Q-001, AC-006 | repeat `boot` and container replacement; active state remains unchanged | automated |
| TC-004 | REQ-Q-003, DOM-R-004 | create a non-empty conflicting path; preserve it and block all managed links | automated |
| TC-005 | REQ-F-005, DOM-R-005 | alter a persisted executable; checksum failure blocks activation | automated |
| TC-006 | REQ-Q-002, AC-009 | add an unsupported special file or mutate source during install; preserve source and block | automated |
| TC-007 | REQ-O-001, AC-002 | remove Codex authentication before install; block without activation | automated |
| TC-008 | REQ-F-002, AC-003 | test missing and keyring-only GitHub credentials; both block | automated |
| TC-009 | REQ-O-002, DOM-R-008 | remove authentication after boot; auth audit reports failure without mutation | automated |
| TC-010 | REQ-O-001, REQ-O-002 | invoke an unsupported lifecycle command; return usage error | automated |
| TC-011 | REQ-F-004, DOM-R-006, AC-011 | create missing neutral memory files, preserve existing files and approved legacy block, reject ambiguous blocks | automated and reviewed |
| TC-013 | REQ-I-002, DOM-R-002 | activate a fully verified ready generation after container replacement | automated |
| TC-014 | REQ-O-001, REQ-Q-003 | configure unsupported external credential stores; block before `current` | automated |
| TC-015 | REQ-O-002, DOM-R-008 | compare complete runtime-tree manifests before and after audit | automated in beta.4 |
| TC-016 | REQ-I-001, DOM-R-009 | verify Supervisor comparison, selective update, concurrency abort, read-back, and persisted `gh` after replacement | automated |
| TC-017 | REQ-I-003, REQ-I-004, DOM-R-010 | migrate only supported helper values and preserve unrelated Git configuration | automated |
| TC-018 | REQ-F-006, REQ-I-005, REQ-S-003, REQ-O-005, DOM-R-011–DOM-R-013 | require explicit activation, preserve unrelated Codex config, publish the exact profile idempotently, remove only the exact retired HACP startup command, and detect both drifts read-only | automated; real new-session acceptance pending |
| TC-DOM-001 | DOM-R-001–DOM-R-013 | evaluate all positive and negative invariant cases together | automated; real TC-012 evidence recorded separately |
| TC-SEC-001 | REQ-S-001, REQ-S-002 | scan working tree and history and test ownership, path, link, mode, and output boundaries | automated |

## TC-012 — Real restart and container acceptance

- **Prerequisites:** automated tests and security scan pass; Codex and GitHub
  CLI are installed with file-backed sign-ins; installation and authenticated
  audit pass; Supervisor packages, startup command, and Git helpers match the
  documented contract.
- **Action:** record a non-sensitive baseline, restart the add-on, perform a
  controlled add-on update/container replacement, restart the replacement
  container, and separately perform a Home Assistant host reboot.
- **Expected:** sessions resume; both sign-ins remain valid; projects, memory,
  Studio Code state, extensions, tools, helpers, and unrelated configuration
  remain unchanged; audits return no `BLOCK`.
- **Tolerance:** no missing session, changed project state, repeated sign-in,
  helper setup, or manual link repair.
- **Status:** installation and add-on restart passed; update `6.0.1` to
  `7.0.0`, container replacement, subsequent container restart, and complete
  Home Assistant host cold start passed. A second update from `7.0.0` to
  `7.1.0`, containing `code-server 4.137.0`, recreated the container and
  preserved the existing Codex conversation, projects, GitHub access,
  sessions, and manual memory. The authenticated post-update persistence
  audit completed without a blocker.
- **Current follow-up:** Studio Code Server `7.1.1` is running and its
  post-repair add-on restart passed. Native Codex Memories were then enabled
  by explicit operator choice and are reported active by a fresh CLI process.
  This verifies configuration activation, not memory generation or retrieval.

## Execution

```sh
./scripts/validate.sh
```

## Beta.4 coverage plan

[DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md) assigned TC-019 through TC-028,
included TC-015, and defined SM-01 through SM-09. The resulting beta.4 regression
coverage is described below; its executed outcomes are recorded in the dated
acceptance document. Later changes extend `scripts/validate.sh` without dropping
existing checks and keep real lifecycle acceptance separate.

## Beta.4 regression execution

`validate.sh` parses every Python script/test and retains the existing lifecycle,
structure and security gates. `test_hacp_remote.py` covers TC-019–TC-024 with
synthetic Supervisor, process and native socket boundaries, including opt-in,
concurrency, failed read-back, timeout, stale socket, original CLI selection and
no model overrides. `test_memory_compatibility.py` covers TC-015/028 with all
four memory modes, container replacement, native configuration preservation,
legacy roots, path collisions and both workspace startup orders.
`test_release_contract.py` covers candidate consistency and positive/negative
archive checks under TC-026/027. TC-025 retains TC-018 without widening access.

Connection failure states use test doubles; actual transport reconnect, native
memory recall and interactive client approvals require separate live evidence.
The exact smoke results are in [BETA-4-ACCEPTANCE.md](BETA-4-ACCEPTANCE.md).

## Beta.5 native compatibility and smartphone checks

| ID | Covers | Action and expected result | Status |
|---|---|---|---|
| TC-029 | REQ-I-006, AC-017, DOM-R-019 | Test direct sockets and exact native aliases; reject wrong targets, ownership, modes, ancestors, and symlink chains. Simulate loss of the temporary directory/socket; verify safe stale classification. Compare refused connections with and without kernel entries, and retain `unreachable` for permission or inspection failures. | passed in 108-test candidate validation |
| TC-030 | REQ-I-007, AC-018, DOM-R-020 | Test matching, missing, dangling, unrelated, and non-symlink default home paths; verify explicit fallback, preservation of unrelated environment, and native command cwd without model/approval overrides. | passed in 108-test candidate validation |
| TC-031 | REQ-O-007, AC-019, DOM-R-021 | Review the smartphone steps; record the operator-confirmed new-chat-in-explicit-folder-to-voice sequence, existing-chat voice, automatic-home startup, and client platform separately. Backend status/home checks must not close a failed client scenario. | reference iPhone observations recorded; automatic-home startup remains open |
| TC-032 | REQ-Q-005, AC-020, DOM-R-022 | Compare both product inventories, executable status and normalized content. Reject code/version/shared-doc drift, extra files, wrong line identity, dirty release candidates and symlinks; allow only precise provenance fields. | automated; clean release-pair comparison recorded in BETA-5-ACCEPTANCE.md |

The operator confirmed the complete sequence of creating a new chat in the
correct explicitly chosen remote folder and then starting voice, as well as
voice in an existing chat. This is an operator-reported client acceptance, not
an automated or server-side reproduction. The supplied screenshot shows app
version `1.2026.258`. Automatic home selection still fails on the reference
phone; no Android, desktop, or general iOS compatibility result is inferred.

The candidate's complete automated results, fresh runtime checks, and artifact
verification belong to [BETA-5-ACCEPTANCE.md](BETA-5-ACCEPTANCE.md). A synthetic
stale-alias test does not replace a real beta.5 container-replacement test.
