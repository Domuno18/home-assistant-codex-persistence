# Persistent manual Codex memory rules

## Purpose

This directory contains a short, human-maintained summary of confirmed facts
that remain useful across sessions. It is separate from native Codex sessions
and Codex-managed memories.

## Start of every session

1. Read this file completely.
2. Read `MEMORY.md` completely.
3. Treat newer explicit user instructions as authoritative.
4. Verify current external facts instead of treating memory as live data.

## What belongs in MEMORY.md

Add only information that is:

- explicitly confirmed;
- useful beyond the current chat;
- concise enough to review manually;
- dated and linked to a leading local or public source;
- safe to keep in the operator's persistent workspace.

Prefer keeping detailed project knowledge in the project's own documentation.
Memory should point to that source rather than duplicate it.

## Maintenance

- Update memory after a durable decision is confirmed, not after every turn.
- Replace outdated statements instead of adding contradictory copies.
- Distinguish facts, decisions, preferences, and open questions.
- Remove details that are no longer useful.
- Keep the file readable without native session history.

## Never store

- tokens, passwords, keys, cookies, or authentication files;
- chat transcripts, prompts, session IDs, or native session data;
- database contents, logs, runtime archives, or internal tool traces;
- sensitive personal information;
- guesses presented as confirmed facts.

Credentials and other private runtime state belong only in the protected
persistent runtime. Real `MEMORY.md` content must never be copied back into the
installation repository or a public issue.
