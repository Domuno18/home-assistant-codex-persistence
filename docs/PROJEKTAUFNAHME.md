# Project intake record

## Confirmed need

The disposable Studio Code Server container must not be the only location for
Codex sessions, authentication, configuration, GitHub CLI state, or required
CLI executables. The solution must preserve the complete engineering workspace
without placing confidential runtime data in Git.

## Confirmed environment

- Home Assistant OS with the Studio Code Server community add-on;
- persistent storage available below `/data`, `/config`, or `/share`;
- Codex IDE extension and CLI;
- GitHub CLI and HTTPS Git integration;
- an operator-controlled workspace for projects and manual memory.

## Confirmed decisions

- Use an explicit one-time installer and automatic guarded bootstrap.
- Persist native state directly; Markdown chat export is not restoration.
- Use file-backed credentials and verified persistent executable copies.
- Keep the runtime outside every project checkout.
- Preserve add-on-owned storage and unrelated Supervisor/Git configuration.
- Fail closed on unknown or damaged state.
- Keep manual memory neutral in the repository and real content local.

## Acceptance route

Automated integration and security tests precede TC-012. Real installation,
add-on restart, update from `6.0.1` to `7.0.0`, container replacement, and
subsequent container restart have passed. A Home Assistant host reboot remains
the only open lifecycle item.

## Intake status

- [x] purpose, users, scope, and non-goals confirmed;
- [x] persistence and trust boundaries confirmed;
- [x] functional, security, operational, and traceability requirements defined;
- [x] public-beta publication explicitly approved;
- [ ] Home Assistant host-reboot evidence pending.
