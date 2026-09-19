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

## Compatibility verdict

Automated synthetic tests cover all four enable/disable combinations, fresh and
legacy stores, repeated setup, both workspace-tool installation orders, container
replacement, full read-only audit manifests, native configuration preservation,
and conflicting synthetic facts remaining in their own stores. These establish
storage and setup compatibility; they do not establish deterministic native
recall or generation.

Live native generation/retrieval, actual case-insensitive platform execution and
interactive on-request client approval remain separately reported evidence
boundaries. The live feature was not enabled merely to run the storage tests.
The beta must not claim a full behavioral pass from file-preservation tests.
