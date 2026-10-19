Skills are organized into bucket folders under `skills/`:

- `engineering/`: coding workflow, agent orchestration, local LLMs
- `productivity/`: non-code workflow tools
- `video/`: video post-production (audio mastering, captions)

Each bucket is shipped as its own Claude Code plugin, declared in `.claude-plugin/marketplace.json` (marketplace `wecko-ai`, plugins `wecko-<bucket>`). A skill belongs to exactly one plugin. When you add, move, rename or remove a skill, update in the same change:

1. the plugin's `skills` array in `.claude-plugin/marketplace.json`
2. the bucket `README.md` (one line, skill name linked to its `SKILL.md`)
3. the top-level `README.md` (same line, path from the repo root)

Plugins that are not skills (hooks, tools) live in `plugins/<name>/` with their own `.claude-plugin/plugin.json`, a `README.md`, and a marketplace entry whose `source` is that folder. List each one in the Plugins section of the top-level `README.md`.

Run `scripts/check.sh` before every commit. It verifies frontmatter, the three lists above, private-data patterns and em-dashes. Run `claude plugin validate .` after touching the manifest.

## Skill rules

- Folder name = `name:` in the frontmatter, file named exactly `SKILL.md`.
- Files a skill ships (scripts, templates, references) live inside its folder and are referenced as `${CLAUDE_SKILL_DIR}/<path>`.
- `agents/openai.yaml` gives Codex a display name and short description. A skill with `disable-model-invocation: true` also sets `policy.allow_implicit_invocation: false` there.
- Skills keep the language they were written in (several are in French).

## Public repo: no private data

Only skills useful to someone other than Wecko belong here. Skills tied to Wecko's own channels, accounts, brands or private repos stay in his local skill folders.

This repo is public. Never commit API keys, tokens, IP addresses, private hostnames, ssh users, account, workspace or device ids, personal mailboxes, client names, revenue figures, face photos or absolute home paths. Configuration goes through documented environment variables (for example `HIGGSFIELD_WORKSPACE`) or user-provided files listed in a per-skill `.gitignore`.

## Style

No em-dashes anywhere in this repo's prose. Rewrite the sentence with a comma, colon, period or parentheses instead.

## Local install for maintainers

`scripts/link-skills.sh` symlinks every skill into `~/.claude/skills` and `~/.agents/skills`. It skips names that already exist as real folders unless `--force` is passed, which moves them aside to `<name>.bak-<timestamp>`.
