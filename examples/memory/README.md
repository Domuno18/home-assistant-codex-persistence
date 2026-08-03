# Manual long-term memory template

The standard installation uses this template to add a small, transparent
memory layer beside Codex's native sessions and Codex-managed memories.

## Three separate concepts

1. **Native sessions** are resumable chats stored inside the persistent Codex
   home.
2. **Codex-managed memories** are local state created by Codex when that
   product feature is enabled.
3. **Manual memory** is the operator-maintained `Memories/MEMORY.md` described
   here.

Persisting the complete Codex home protects native sessions and also preserves Codex-managed local Memories if the operator enables that separate Codex feature. This template adds the manual mechanism without copying private content into Git. The two memory mechanisms are not synchronized or merged.

## Automatic setup

By default, installation creates missing files below:

```text
${HACP_WORKSPACE_ROOT:-/config/Codex}/Memories/
├── AGENTS.md
└── MEMORY.md
```

Existing files are preserved byte-for-byte. The installer adds one managed block to the effective global Codex instruction file. Codex discovers that global guidance at session start, and the block instructs Codex to read the manual rules and memory, including when work begins in a nested Git repository. The bootstrap does not read these files itself, and this is an instruction rather than a technical include mechanism.

The workspace must not be this installation repository or a directory inside
its checkout. There is no automatic copy-back from the real memory file to the
template.

Use a different persistent workspace with:

```sh
HACP_WORKSPACE_ROOT=/another/persistent/workspace \
HACP_INSTALL_OK=YES \
sh ./scripts/ha-codex-persistence.sh install
```

Operators can explicitly disable only this manual memory setup during the
one-time installation with `HACP_MEMORY_SETUP=NO`. Native sessions and
Codex-managed memories remain part of the persistent Codex home.

## How to maintain memory

1. Add only confirmed information that remains useful across sessions.
2. Include an ISO date and leading source.
3. Replace stale statements instead of accumulating contradictions.
4. Keep details in project documentation and link to them from memory.
5. Never add credentials, chat transcripts, session IDs, logs, databases,
   runtime files, or sensitive personal information.

This repository contains only the empty neutral template. A real populated
`MEMORY.md` belongs exclusively in the operator's private persistent workspace.
