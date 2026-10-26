# Agent Variants

Reference links should be reviewed before major releases because agent tooling changes frequently.

## Current assessment

The current kit is strong on discipline, verification, and project DNA.

The gaps are mostly structural:

- the README promises support for several agents, but the repo only ships one full generic kit
- some tools now prefer native filenames and scoped rule files
- the always-on instruction surface is larger than it needs to be

## Recommended architecture

Use a hub-and-spoke model:

1. Keep the root kit as the canonical policy pack.
2. Add thin native adapters for each agent.
3. Keep always-on files short.
4. Push deep context into the project docs instead of duplicating it everywhere.
5. Let all adapters defer to `SESSION.md` for resumable session checkpoints.

## Variant matrix

| Tool | Preferred native format | Notes |
| --- | --- | --- |
| OpenAI Codex | `AGENTS.md` and optional `AGENTS.override.md` | Supports layered discovery from global scope to current directory. |
| Claude Code | `CLAUDE.md` plus `.claude/settings.json` | Keep behavior in the markdown file and config/permissions in settings. |
| Cursor | `.cursor/rules/*.mdc` | `.cursorrules` is legacy. |
| GitHub Copilot | `.github/copilot-instructions.md` plus `.github/instructions/*.instructions.md` | Repo-wide and path-specific instructions are both first-class. |
| Gemini CLI | `GEMINI.md` | Hierarchical context files are supported, and filenames can be customized. |
| Windsurf | `.windsurf/rules/*.md` | Rule files can be scoped and triggered. |
| Cline | `.clinerules/*.md` | Simple markdown rules, compatible with cross-tool content. |
| Aider | `CONVENTIONS.md` loaded via `.aider.conf.yml` or `--read` | Aider works best with an explicit conventions file. |

## Reference base

- OpenAI Codex AGENTS docs: https://developers.openai.com/codex/guides/agents-md
- OpenAI Codex usage patterns: https://openai.com/business/guides-and-resources/how-openai-uses-codex/
- OpenAI harness engineering: https://openai.com/index/harness-engineering/
- Anthropic Claude Code settings: https://docs.anthropic.com/en/docs/claude-code/settings
- Cursor rules docs: https://docs.cursor.com/context/rules-for-ai
- GitHub Copilot custom instructions: https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- Gemini CLI project context: https://geminicli.com/docs/cli/gemini-md/
- Windsurf memories and rules: https://docs.windsurf.com/pt-BR/windsurf/cascade/memories
- Cline rules: https://docs.cline.bot/customization/cline-rules
- Aider conventions: https://aider.chat/docs/usage/conventions.html
