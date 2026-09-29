# Reference update acceptance — Studio Code Server 7.2.0

Date: 2026-09-29. HACP: `0.9.0-beta.5`. Scope: the existing Home Assistant
reference installation, updated from Studio Code Server `7.1.1` to `7.2.0`.

**Studio Code Server 7.2.0 is supported by HACP beta.5 on this tested reference
installation.** No HACP code change, reinstall or access-profile repair was
needed during the post-update check.

## Observed results

The operator reported completing the add-on update. Read-only Supervisor
queries before and after it reported `7.1.1` and `7.2.0`, respectively; the
updated add-on was `started`. The installed editor reports `code-server
4.139.1` with Code `1.139.1`.

| Check | Post-update result |
|---|---|
| Persistence | Codex/GitHub state and executable links, runtime permissions and Git credential helpers passed the HACP audit |
| Sessions and Core Knowledge | Native session-file count matched the pre-update count; the Core Knowledge startup/maintenance contract passed; the existing conversation continued |
| Sign-ins | Codex file-based login cache recognized; GitHub authentication valid |
| Startup | Exactly one managed HACP boot command; remote launcher follows it; required `procps` and `python3` packages remain configured |
| Container access | Stored `danger-full-access` / `on-request` / `user` profile passed; actual commands in the continued remote chat succeeded without a sandbox or `bwrap` error |
| Remote transport | Native daemon `running`, connection `connected` |
| Overall audit | Authentication, add-on configuration and access-profile checks all passed; exit status `0`, ending in `OK result active` |

## Repeating the check

Use the installation's actual runtime root. For the default installation:

```sh
HACP_RUNTIME_ROOT=/data/codex-persistence HACP_CHECK_AUTH=YES \
  HACP_CHECK_ADDON_CONFIG=YES HACP_CHECK_CODEX_ACCESS=YES \
  sh /data/codex-persistence/bootstrap/ha-codex-persistence.sh audit
python3 /data/codex-persistence/bootstrap/hacp_remote.py status \
  --runtime-root /data/codex-persistence
code-server --version
```

## Acceptance boundary

This is fresh beta.5 evidence for the real `7.1.1` to `7.2.0` add-on update
under TC-012, with access-profile evidence relevant to TC-018. Successful
commands establish usable access in this continued chat; they do not establish
interactive approval behavior or every possible client override. Session-count
continuity does not establish byte-for-byte integrity of every session file.

No separate Home Assistant host reboot, fresh installation on another host,
new smartphone voice test or native-memory generation/recall test was performed.
The existing automatic remote-home selection issue remains open. Compatibility
on other hosts remains subject to their own checks.

This post-release documentation addendum applies to the existing beta.5 code.
The release tag and published source archives retain their original contents.

## Upstream release

[Studio Code Server v7.2.0](https://github.com/hassio-addons/app-vscode/releases/tag/v7.2.0)
updates code-server to `4.139.1` and the Debian base image from `9.4.0` to
`9.5.0`. The upstream tag comparison changes only `vscode/Dockerfile` and
`vscode/build.yaml`; add-on configuration and startup scripts are unchanged.
