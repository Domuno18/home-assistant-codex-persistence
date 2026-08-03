# Source code

Recommended minimal structure; create these directories only when needed:

```text
<project>/
├── domain/          domain objects, rules, and events
├── application/     use cases and ports
├── adapters/        protocols, databases, UI, and external systems
└── bootstrap/       configuration and wiring
```

Small projects may combine this structure into fewer modules. The dependency
direction toward the domain remains mandatory.
