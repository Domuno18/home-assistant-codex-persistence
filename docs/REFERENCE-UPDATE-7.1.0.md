# Reference update evidence: Studio Code Server 7.1.0

| Field | Value |
|---|---|
| Owner | Home Assistant reference-system operator |
| Audience | HACP users, maintainers, and beta testers |
| Scope | Real Studio Code Server add-on update and HACP persistence |
| Evidence date | 2026-09-13, Europe/Vienna |
| Document status | Accepted reference-system lifecycle evidence |
| Source state | Studio Code Server `7.0.0` |
| Target state | Studio Code Server `7.1.0` |
| Included editor runtime | `code-server 4.137.0` |

## Update and result

The Home Assistant reference-system operator performed the available Studio
Code Server update from `7.0.0` to `7.1.0`. The update recreated the add-on
container and temporarily interrupted the remote connection. After Studio Code
Server restarted, the existing Codex conversation resumed successfully.

The following HACP-managed or HACP-supported state remained available:

- existing Codex sessions;
- the project workspace below `/config/Codex`;
- GitHub CLI authentication and repository access;
- manual file-based memory;
- persistent Codex and GitHub CLI executables;
- the single managed HACP startup command.

No export, restore, repeated sign-in, new conversation, or manual link repair
was required.

## Verification

The installed add-on state reported Studio Code Server `7.1.0` with no update
pending. The installed `code-server` package reported version `4.137.0`,
matching the add-on `7.1.0` dependency changelog.

The authenticated HACP audit checked the persistent links, Git helper,
Supervisor startup command, runtime permissions, session store, manual memory,
Codex authentication, and GitHub authentication. Every requested persistence
check returned `OK`; the audit ended with `OK result active`.

The continuing conversation and accessible repositories provided the
operational checks for session and project continuity. No private session,
credential, memory, repository, or Home Assistant data is reproduced in this
document.

## Boundary and recovery

This is acceptance evidence for the documented reference system, not a claim
that every future Studio Code Server version or third-party installation is
compatible. If a later update fails, restore the Home Assistant backup retained
for that update and follow the recovery procedure in
[INSTALLATION.md](INSTALLATION.md).
