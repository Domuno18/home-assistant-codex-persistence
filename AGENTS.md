# Project working rules

## Order of work

1. Read `README.md` and `PROJEKT-STECKBRIEF.md`.
2. Review requirements and terminology before changing code.
3. Clarify domain rules in the domain model first.
4. Implement each change with tests and documentation.
5. Run `./scripts/validate.sh` before every commit, push, or release.

## Architecture

- Keep domain and mathematical logic independent from frameworks, protocols,
  databases, UI, and secret sources.
- Connect external systems through adapters; normalize vendor-specific names,
  units, and signs at the boundary.
- Record new dependencies and non-obvious decisions as ADRs below
  `docs/entscheidungen/`.
- Avoid unnecessary layers; small projects may remain small.

## Traceability

- Requirements use `REQ-*`; domain rules use `DOM-*`; acceptance criteria use
  `AC-*`; work packages use `AP-*`; tests use `TC-*`.
- Every important requirement and domain rule needs an objective test.
- Tests or the evidence matrix identify the requirement covered by an
  implementation change.
- Do not invent unknown facts. Record them with `OPEN-*`, `ANN-*`, or `RISK-*`.

## Secrets and confidential data

- Never write real tokens, passwords, keys, private addresses, personal data,
  production data, chat text, native sessions, or populated memories into
  code, tests, documentation, examples, logs, or chat responses.
- Domain logic does not read environment variables or secret files directly;
  a configuration boundary provides validated runtime values.
- Examples use artificial placeholders such as `OPEN (API token)`.
- Never bypass a secret finding with `--no-verify`. Revoke a committed
  credential first, then clean and rescan reachable Git history.

## Git and publication

- Remote repositories stay private by default.
- Public visibility requires the documented checklist in `docs/SECURITY.md`
  and explicit owner approval.
- Create releases only through `./release.sh`; deployment remains separate as
  described in `DEPLOY.md`.
- Preserve unrelated existing changes.

## Language and quality

- Public project documentation is written in English.
- Keep code identifiers and user-facing messages consistently English.
- State units, time bases, time zones, signs, and tolerances explicitly.
- Tests cover normal behavior, boundaries, and relevant failure behavior.
