# Third-party projects

Home Assistant Codex Persistence is an independent community project. It is
not part of, sponsored by, or endorsed by Home Assistant, the Home Assistant
Community Add-ons project, OpenAI, Microsoft, or GitHub.

The repository contains only this project's own source code, tests,
documentation, and neutral examples. It does not vendor, modify, bundle, or
redistribute Home Assistant, Studio Code Server, OpenAI Codex, Visual Studio
Code, or GitHub CLI. It interacts with software already installed by the
operator through documented commands, configuration paths, and Home Assistant
add-on options.

The following upstream licenses were reviewed before selecting MIT for this
project:

| Upstream project | License | How this project relates to it |
|---|---|---|
| [Home Assistant Core](https://github.com/home-assistant/core) | [Apache-2.0](https://github.com/home-assistant/core/blob/dev/LICENSE.md) | external platform; no code redistributed |
| [Studio Code Server add-on](https://github.com/hassio-addons/addon-vscode) | [MIT](https://github.com/hassio-addons/addon-vscode/blob/main/LICENSE.md) | existing add-on configured through `packages` and `init_commands`; no code redistributed |
| [OpenAI Codex](https://github.com/openai/codex) | [Apache-2.0](https://github.com/openai/codex/blob/main/LICENSE) | existing CLI and IDE extension; no code redistributed |
| [GitHub CLI](https://github.com/cli/cli) | [MIT](https://github.com/cli/cli/blob/trunk/LICENSE) | existing CLI copied into private local runtime by the operator; no binary distributed by this repository |

Names and trademarks are used only to describe compatibility. All trademarks
belong to their respective owners. This review documents the repository's
current technical composition; it is not legal advice.

