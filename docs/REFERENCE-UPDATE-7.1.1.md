# Reference update investigation — 2026-09-19

This record contains sanitized observations, not host identities or private logs.

| Component | Installed | Available when inspected |
|---|---|---|
| Home Assistant Core | 2026.9.3 | 2026.9.3 |
| Home Assistant Supervisor | 2026.09.2 | 2026.09.2 |
| Home Assistant OS | 18.2 | 18.3 |
| Studio Code Server | 7.1.1 | 7.1.1 |
| code-server | 4.137.0 | Not separately assessed |

The values came from read-only Supervisor queries and the installed editor
package. HAOS 18.3 was available, not installed as part of this repair. Previous
HA component versions and exact update timestamps were not established. The
previous verified Studio Code Server update was 7.0.0 to 7.1.0 on 2026-09-13;
see [that record](REFERENCE-UPDATE-7.1.0.md). Do not infer the precise subsequent
upgrade path from current version numbers.

A later read-only Supervisor query on 2026-09-19 again reported Studio Code
Server `7.1.1` in the `started` state. The post-repair restart evidence therefore
applies to the current installed version, without turning the unknown update
path into an invented migration record.

The operator reported remote access offline after an add-on update. Persistence,
Codex sessions and both sign-ins remained intact. No native remote daemon was
running; its start failed because `ps` was unavailable. Installing `procps` and
starting official Codex remote control restored the connection. This association
does not establish that the update itself removed `ps`. The operator confirmed
remote handover. The native status endpoint later reported `connected`.

The product fix makes remote startup explicit and repeatable after HACP restores
persistent paths. It preserves the official CLI and its native update/model
behavior. Core Knowledge and Codex Memories remain separate. Current lifecycle
and beta acceptance results are tracked in [DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md)
and [BETA-4-ACCEPTANCE.md](BETA-4-ACCEPTANCE.md); historical beta evidence is not
relabelled as a new post-repair restart pass.

After explicit operator approval, the persistent Codex configuration was set to
`[features] memories = true`. The original CLI reported `memories` as a stable,
enabled feature and the existing Core Knowledge path remained unchanged. No
memory contents were inspected or published. Native generation and retrieval
remain a separate, unverified behavioral boundary.

## Container-access profile maintenance

A later read-only check found no `bwrap` executable in the add-on container.
This is the already documented protected-container case: HACP does not install
a second sandbox and Home Assistant add-on protection remains the outer
isolation boundary. Command execution in the active explicitly unrestricted
chat remained available.

The same audit found that the persistent sandbox setting was still
`danger-full-access`, but the persistent approval policy had drifted from the
HACP default `on-request` to `never`. The cause of that persisted change was not
inferred. The operator authorized the existing guarded recovery interface:

```sh
HACP_CODEX_CONTAINER_ACCESS=YES <bootstrap> configure-access
```

It restored exactly `sandbox_mode = "danger-full-access"`, `approval_policy =
"on-request"`, and `approvals_reviewer = "user"`. An authenticated follow-up
audit reported every checked runtime, access, permission, session, memory and
sign-in item as `OK`. No add-on restart, HACP reinstall, repository-code change
or release rebuild was required. The correction applies to new Codex sessions;
an existing chat can retain its client-selected effective policy.
