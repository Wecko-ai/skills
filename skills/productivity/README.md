# Productivity

Non-code workflow tools.

## User-invoked

Reachable only when you type them (Claude Code: `disable-model-invocation: true`; Codex: `policy.allow_implicit_invocation: false` in `agents/openai.yaml`).

- **[closing](./closing/SKILL.md)**: Wrap up a session before closing it: persist memory, keep `CLAUDE.md` lean and true, verify what shipped is live, list loose ends.
- **[continue](./continue/SKILL.md)**: Hand off a session whose context is filling up: stop at a clean point, check the real git state, and get a self-contained prompt (copied and saved) to resume in a fresh conversation.
