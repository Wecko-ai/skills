# Engineering

Skills for coding workflow, agent orchestration and local LLMs.

## User-invoked

Reachable only when you type them (Claude Code: `disable-model-invocation: true`; Codex: `policy.allow_implicit_invocation: false` in `agents/openai.yaml`).

- **[promptfit](./promptfit/SKILL.md)**: Turn a vague request into a structured ticket with a local LLM, then build it.

## Model-invoked

Model- or user-reachable: the description tells the model when to reach for them.

- **[office](./office/SKILL.md)**: Office mode. The session model becomes the boss and delegates execution to a multi-model roster of headless agents, with a live pixel-office dashboard.
- **[vision](./vision/SKILL.md)**: Let a text-only model see. Sends an image plus your exact question to a vision model behind any OpenAI-compatible endpoint.
- **[find-local-llm](./find-local-llm/SKILL.md)**: Find the best local LLM for an Apple device and RAM size via modelfit.io (MCP tool or website wizard).
- **[apple-silicon-ram-guide](./apple-silicon-ram-guide/SKILL.md)**: How much unified memory a local model needs on Apple silicon, KV cache and long context included.
