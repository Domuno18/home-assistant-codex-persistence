# User stories

## US-001 — Survive container replacement without loss

As a Home Assistant operator, I want the complete Codex workspace and GitHub
access to remain usable after a Studio Code Server restart, update, or
container replacement, so that work can continue without restoration or a new
sign-in.

### Acceptance criteria

- AC-001: Native Codex sessions remain present and resumable.
- AC-002: Codex file-backed authentication remains valid.
- AC-003: GitHub CLI file-backed authentication remains valid.
- AC-004: Projects in the persistent workspace remain unchanged.
- AC-005: Codex and GitHub CLI programs remain available through verified
  persistent copies.
- AC-009: Installation activates only a complete, verified runtime generation.
- AC-010: Automatic startup restores all managed paths and credential helpers.
- AC-012: Existing unrelated Git configuration and add-on options remain
  unchanged.

## US-002 — Audit safely and fail closed

As an operator, I want a read-only health check and safe failure behavior so
that damaged or conflicting state is never hidden or deleted.

### Acceptance criteria

- AC-006: Repeated `boot` runs are idempotent.
- AC-007: Unknown, conflicting, or damaged state causes `BLOCK` without
  destructive cleanup.
- AC-008: Credentials, sessions, and populated memory never enter Git,
  diagnostics, or examples.

## US-003 — Preserve concise long-term memory

As a Codex user, I want neutral manual-memory files in the persistent workspace
so that durable working conventions survive container lifecycle events without
copying private content into the project repository.

### Acceptance criterion

- AC-011: Missing neutral memory files and one managed global startup block are
  created atomically; existing memory content is preserved byte-for-byte and
  ambiguous managed blocks are rejected.
