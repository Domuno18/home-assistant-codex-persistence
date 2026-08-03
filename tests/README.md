# Tests

- `domain/`: domain rules, value objects, and invariants
- `model/`: units, equations, reference cases, and boundary cases
- `unit/`: small technical units
- `integration/`: adapters, contracts, and failure behavior
- `architecture/`: permitted dependency directions
- `acceptance/`: confirmed stakeholder scenarios

A test qualifies as evidence only when it has a concrete test oracle and
references `REQ-*`, `DOM-*`, `AC-*`, or `RISK-*`.
