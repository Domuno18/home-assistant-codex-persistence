# Core Knowledge and Codex Memories

HACP supports separate storage for **Core Knowledge** and **Codex Memories**,
with either mechanism used alone or both present. HACP applies only to Home
Assistant. Independent workspace tooling can use the same Core Knowledge store
without requiring HACP on other platforms.

| Mechanism | Responsibility | Location and activation |
|---|---|---|
| Core Knowledge | Important, confirmed, durable information under the existing maintenance rules | New setups: `<workspace>/core-knowledge`; enabled by normal HACP memory setup unless explicitly disabled |
| Codex Memories | Native OpenAI generation, retrieval and controls | `<CODEX_HOME>/memories` and other native state; enable or disable through supported Codex settings separately |

Safe existing `<workspace>/Memories` directories remain in use without migration.
If both workspace directories exist, HACP stops for explicit reconciliation;
it never chooses a store by inspecting its contents. Case-insensitive overlap
with native memory, including ancestors and descendants, is rejected. A native
`.codex/Memories` path is not a safe alternate name for Core Knowledge.

The historical `HACP MEMORY` block markers remain for compatibility. HACP
preserves supported legacy startup blocks and extended Core Knowledge startup
rules from independent workspace tooling when they reference the same two files.
It does not replace those extended rules. Incorrect, incomplete or duplicated
blocks fail validation. Neither memory system grants permissions or overrides
current user instructions and authoritative project sources.

## Native settings

OpenAI documents native memory controls in
[Codex Memories](https://learn.chatgpt.com/docs/customization/memories).
The reference CLI exposes the `memories` feature. The user chooses its setting;
HACP does not silently enable it. Native generation can depend on idle time,
usage limits and the installed version. Do not edit generated native files to
imitate native generation or apply Core Knowledge selection rules to them.

HACP persists the complete supported native home without merging, interpreting
or synchronizing native memory with Core Knowledge. For a fresh native config
that already contains TOML tables, set the required top-level
`cli_auth_credentials_store = "file"` explicitly before those tables as described
in the installation guide. HACP rejects ambiguous storage configuration rather
than rewriting unrelated settings.

The supported combinations are deliberately independent:

| Core Knowledge | Codex Memories | Supported result |
|---|---|---|
| disabled | disabled | persistent Codex workspace without either memory layer |
| enabled | disabled | deliberately maintained Core Knowledge only |
| disabled | enabled | native OpenAI-managed local Memories only |
| enabled | enabled | both stores persist separately without synchronization |

On 2026-09-19 the reference operator explicitly enabled native Codex Memories
in the persistent Codex configuration. The original CLI reported the stable
`memories` feature as enabled, while the existing Core Knowledge path remained
unchanged. This is live activation evidence only. It does not claim that a
memory was generated, recalled, deduplicated or reconciled across the stores.

## Compatibility verdict

Automated synthetic tests cover all four enable/disable combinations, fresh and
legacy stores, repeated setup, both workspace-tool installation orders, container
replacement, full read-only audit manifests, native configuration preservation,
and conflicting synthetic facts remaining in their own stores. These establish
storage and setup compatibility; they do not establish deterministic native
recall or generation.

Live native generation/retrieval, actual case-insensitive platform execution and
interactive on-request client approval remain separately reported evidence
boundaries. The live feature was enabled only after explicit operator approval,
not merely to make storage tests pass. The beta must not claim a full behavioral
pass from activation or file-preservation tests.
