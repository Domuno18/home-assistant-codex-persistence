# Security policy

## Supported version

The project is currently a beta. Security fixes target the latest commit on
`main` and the newest published beta, once one exists.

## Reporting a vulnerability

Please do not open a public issue for vulnerabilities or exposed credentials.
Use GitHub's private vulnerability reporting feature on this repository. If
that feature is unavailable, contact the repository owner privately before
sharing technical details.

Never attach real Codex sessions, `auth.json`, GitHub CLI `hosts.yml`, tokens,
databases, chat text, populated memory files, Supervisor credentials, or an
archive of the persistent runtime.

Include a minimal description, affected version or commit, impact, safe
reproduction steps using artificial data, and any suggested mitigation.

The detailed threat model, storage boundaries, and release checklist are in
[docs/SECURITY.md](docs/SECURITY.md).

