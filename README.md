# Wecko's Skills

The agent skills I use every day to ship apps and videos, collected in one place.

Each skill is a folder with a `SKILL.md` and whatever it needs (scripts, templates, references). They work in Claude Code, and in any agent that reads Agent Skills. Small, hackable, made to be adapted: fork them and make them yours.

Some skills are written in French, the language I work in. They work the same with any model.

## Installation

### Claude Code (plugins, auto-update)

Skills ship as one plugin per bucket, so you only install what you need:

```bash
claude plugin marketplace add Wecko-ai/skills
claude plugin install wecko-engineering@wecko-ai
```

Skill plugins: `wecko-engineering`, `wecko-productivity`, `wecko-video`. Hook plugin: `wecko-agent-notify` (see [Plugins](#plugins)). Inside a session, the same works with `/plugin marketplace add Wecko-ai/skills`.

### Any other agent, or editable copies

```bash
npx skills@latest add Wecko-ai/skills
```

Pick the skills you want when asked. Re-run to update.

### Requirements

Skills declare what they need in their own `SKILL.md`. The common ones: Python 3, Node.js, `ffmpeg`, [`whisper.cpp`](https://github.com/ggml-org/whisper.cpp) (`whisper-cli`) for the video skills, and [Ollama](https://ollama.com) for `promptfit`.

## Engineering

Coding workflow, agent orchestration, local LLMs. [Bucket README](./skills/engineering/README.md)

- **[office](./skills/engineering/office/SKILL.md)**: Office mode. The session model becomes the boss and delegates execution to a multi-model roster of headless agents, with a live pixel-office dashboard.
- **[promptfit](./skills/engineering/promptfit/SKILL.md)**: Turn a vague request into a structured ticket with a local LLM, then build it. User-invoked: `/promptfit <prompt>`.
- **[vision](./skills/engineering/vision/SKILL.md)**: Let a text-only model see. Sends an image plus your exact question to a vision model behind any OpenAI-compatible endpoint.
- **[find-local-llm](./skills/engineering/find-local-llm/SKILL.md)**: Find the best local LLM for an Apple device and RAM size via modelfit.io (MCP tool or website wizard).
- **[apple-silicon-ram-guide](./skills/engineering/apple-silicon-ram-guide/SKILL.md)**: How much unified memory a local model needs on Apple silicon, KV cache and long context included.

## Productivity

[Bucket README](./skills/productivity/README.md)

- **[closing](./skills/productivity/closing/SKILL.md)**: Wrap up a session before closing it: persist memory, keep `CLAUDE.md` lean and true, verify what shipped is live, list loose ends. User-invoked: `/closing`.
- **[continue](./skills/productivity/continue/SKILL.md)**: Hand off a session whose context is filling up: stop at a clean point, check the real git state, and get a self-contained prompt (copied and saved) to resume in a fresh conversation. User-invoked: `/continue [focus]`.

## Video

Video post-production. [Bucket README](./skills/video/README.md)

- **[youtube-audio-master](./skills/video/youtube-audio-master/SKILL.md)**: Audit and repair a finished video's audio for YouTube (-14 LUFS, -1 dBTP, clipping, level jumps between blocks) without re-encoding the picture.
- **[karaoke-captions](./skills/video/karaoke-captions/SKILL.md)**: Word-by-word karaoke caption overlay for vertical videos, the current word popped on a white chip, timed from whisper word timings.

## Plugins

Hooks and tools that are not skills, installed the same way.

- **[wecko-agent-notify](./plugins/agent-notify/README.md)**: Phone ping (ntfy, Telegram, any command) when Claude Code or Codex is really done: it waits for background agents, teammates and shells, and stays quiet while you are at the Mac. `claude plugin install wecko-agent-notify@wecko-ai`

## Moved here

`promptfit` (from [Wecko-ai/claude-skills](https://github.com/Wecko-ai/claude-skills)), `office` (from [Wecko-ai/claude-office](https://github.com/Wecko-ai/claude-office)) and `closing` (from [Wecko-ai/closing-skill](https://github.com/Wecko-ai/closing-skill)) now live in this repo, and [Wecko-ai/kage-agent-notify](https://github.com/Wecko-ai/kage-agent-notify) became the `wecko-agent-notify` plugin. The old repos stay installable but get no new versions.

## Contributing

Issues and PRs welcome. Read [AGENTS.md](./AGENTS.md) first and run `scripts/check.sh` before opening a PR.

## License

[MIT](./LICENSE). Made by [Wecko](https://wecko.ai).
