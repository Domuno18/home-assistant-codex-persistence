# Project structure plan

## Work packages

| ID | Deliverable | Covers | Evidence | Status |
|---|---|---|---|---|
| AP-100 | Charter, user stories, requirements, and domain model | US-001–US-003, all REQ and AC IDs | document and traceability review | complete |
| AP-200 | Architecture, interfaces, security model, and decisions | integration, quality, and security requirements | architecture and security review | complete |
| AP-300 | Portable `install`, `boot`, `configure-access`, `audit`, tools, helpers, and Supervisor integration | functional and operational requirements | TC-001–TC-010, TC-016–TC-018 | complete |
| AP-400 | Automated, security, and real lifecycle evidence | all mandatory requirements | TC-SEC-001 and TC-012–TC-018 | automated complete; TC-018 real new-session check pending |
| AP-500 | User, operations, deployment, release, and handover documentation | REQ-F-003, REQ-F-004, REQ-F-006, REQ-I-003, REQ-I-005, operational requirements | documentation review | complete |

## Deliverables

- AP-100: approved scope, atomic requirements, domain objects, and invariants.
- AP-200: storage and trust boundaries, lifecycle interfaces, fail-closed
  behavior, Supervisor transport, and credential-helper contract.
- AP-300: implementation scripts, immutable generations, verified tools,
  selective package transition, and managed memory setup.
- AP-400: integration tests, failure tests, security scans, and separately
  recorded real lifecycle acceptance.
- AP-500: README, installation, architecture, security, operations, deployment,
  release, and contribution documentation.

## Completion review

- [x] Every mandatory requirement maps to a work package and objective evidence.
- [x] Roles, dependencies, architecture, and security boundaries are documented.
- [x] Automated tests and security scans pass.
- [x] Installation, add-on restart, real update, container replacement, and
      subsequent container restart are accepted.
- [x] Home Assistant host cold start is accepted under BL-001 and TC-012.

## Next beta development

The next two sprints, regression coverage, live smoke checks, update-evidence requirements and dual-repository beta release gates are defined in [DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md). Both beta.4 delivery sprints are complete with documented beta coverage limits. See [BETA-4-ACCEPTANCE.md](BETA-4-ACCEPTANCE.md).

## Beta.5 compatibility follow-up

AP-100/AP-200 cover REQ-I-006/007, REQ-O-007, DOM-R-019–021, and ADR-001.
AP-300/AP-400 cover TC-029/030 and the existing remote regressions; AP-400/AP-500
separate TC-031 smartphone observations from native status and home checks.
Fresh candidate validation passed; subsequent release and deployment evidence is recorded
in [BETA-5-ACCEPTANCE.md](BETA-5-ACCEPTANCE.md).
