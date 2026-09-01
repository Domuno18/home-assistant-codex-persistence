# Project profile: Home Assistant Codex Persistence

## Identity

| Field | Value |
|---|---|
| Project | Home Assistant Codex Persistence |
| Repository | `home-assistant-codex-persistence` |
| Users | Home Assistant operators using Studio Code Server, Codex, and GitHub CLI |
| Ownership and priorities | Repository maintainers |
| Operational acceptance | Operator of the Home Assistant reference system |
| First beta target | 2026-07-30 |
| Status | Installation, add-on restart, update `6.0.1` to `7.0.0`, container replacement, subsequent restart, and Home Assistant host cold start accepted |
| Visibility | Published community-beta source repository |

## Scope references

- Project purpose, scope, roles, risks, and acceptance:
  [Project charter](docs/PROJECT-CHARTER.md)
- Requirements and acceptance criteria:
  [Requirements](docs/REQUIREMENTS.md)
- System and domain boundaries:
  [System context](docs/SYSTEM-CONTEXT.md) and
  [Domain model](docs/DOMAIN-MODEL.md)
- Architecture and interfaces:
  [Architecture](docs/ARCHITECTURE.md) and
  [Interfaces](docs/INTERFACES.md)
- Work packages, tests, and traceability:
  [Project plan](docs/PROJECT-PLAN.md),
  [Test plan](docs/TEST-PLAN.md), and
  [Evidence matrix](docs/EVIDENCE-MATRIX.md)

ISA-95 and mathematical/control modeling are not applicable to this project;
empty placeholder documents are intentionally not retained.

## Acceptance status

- [x] Scope, requirements, architecture, interfaces, and security documented
- [x] Automated integration, failure, Supervisor, and security tests pass
- [x] Real installation and add-on restart accepted under TC-012
- [x] Real add-on update from `6.0.1` to `7.0.0`, container replacement,
      and subsequent container restart accepted under TC-012
- [x] Public-beta publication and release controls approved
- [x] Home Assistant host cold start accepted under TC-012
