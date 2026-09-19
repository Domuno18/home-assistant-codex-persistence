# Beta.4 acceptance — 2026-09-19

Status: both delivery sprints completed. Automated checks, real restart,
release publication and downloaded assets were verified; beta coverage limits
remain explicit below.

| Area | Current evidence |
|---|---|
| Automated regressions | 83 tests pass through full validation in each repository; original lifecycle coverage is retained |
| SM-01 versions and sign-ins | Current component versions recorded in REFERENCE-UPDATE-7.1.1.md; authenticated persistence audit passed before and after candidate deployment |
| SM-02 native remote | Original managed Codex daemon reports connected; operator confirmed remote usability |
| SM-03 command/file smoke | Same-conversation temporary file create/read/edit/delete passed under the actual unrestricted client profile |
| SM-04 repeated start/status | Synthetic idempotence and read-only native socket tests pass; two installed live starts returned connected / already-running |
| SM-05 post-repair add-on restart | Passed after an actual Studio Code Server restart: HACP restored first, native remote reconnected, authenticated audit passed, existing session files and curated/configuration hashes were preserved |
| SM-06 handover | Operator confirmed remote continuation after the initial repair; no chat lock deletion is part of this product |
| SM-07 effective approvals | Current client uses unrestricted access with approval policy never; HACP configuration is unchanged. Interactive on-request approval remains a documented beta limitation under BL-020 |
| SM-08 publication/artifacts | Candidate source and artifacts are validated by the release procedure; publication read-back is recorded after upload |
| SM-09 memory | All four synthetic modes pass. Actual independent workspace/persistence installers pass in both orders and on repeat. Live native generation/retrieval remains unverified; the live feature was not enabled for testing |

A native CLI process restart with a synthetic unauthenticated home confirmed that
official CLI 0.154.0 can reclaim its own stale socket. This was an isolated crash
probe, not a real add-on restart or a connected-session lifecycle pass.

No custom CLI, pinned executable or model override is created. Astra availability
remains governed by the original OpenAI client/account. HACP does not replace
native memories, package updates, authentication or chat ownership logic.

## Explicit TC-018 scope resolution

The configured on-request defaults and effective client policy are separate. This
repair does not change client permissions or claim an interactive approval pass.
BL-020 remains open as an existing beta coverage limit; it is not silently marked
complete. The beta.4 delivery gate covers preservation and correct reporting of
that boundary, which TC-018/025 and the live smoke establish. Native generation
and retrieval likewise remain outside the proven storage compatibility verdict.
No independent review or broad platform acceptance is claimed.

## Publication verified

The beta prerelease and both assets were published and downloaded again; asset
bytes matched the verified local build. Release commit: `874429cfbaadef79ee9d66b5fa008e173e08596f`.
Archive SHA-256: `407c8d98d7fee70b1cdf727fa679d4a9a95a3aebee4d2ac0229846b7a9b36420`.
Release: [v0.9.0-beta.4](https://github.com/Domuno18/home-assistant-codex-persistence/releases/tag/v0.9.0-beta.4).
