# Setup: get the office running on your machine

The office is three small pieces:

1. **`office-agent`**: spawns a headless Claude Code process under a non-Anthropic model
2. **A local LiteLLM proxy**: translates Claude Code's Anthropic API calls to any OpenAI-compatible provider
3. **The `/office` skill**: tells your session model how to boss the roster

You do NOT need the exact models in the default roster. Any OpenAI-compatible endpoint
(Alibaba MaaS, DeepSeek, OpenRouter, Together, a local Ollama...) or any
Anthropic-compatible endpoint (Kimi coding API) works. The roster is just a table at
the top of `office-agent`: edit it.

## Prerequisites

- `claude` CLI installed and working (`claude -p "hi"` answers)
- `jq`, `zsh`, `python3` (all present by default on macOS)
- An API key for at least one OpenAI-compatible model provider
- `pip install litellm` (or `pipx install litellm`)

## 1. Install the skill + scripts

```bash
git clone https://github.com/Wecko-ai/skills.git /tmp/wecko-skills
cp -r /tmp/wecko-skills/skills/engineering/office ~/.claude/skills/office
mkdir -p ~/bin && ln -sf ~/.claude/skills/office/scripts/office-{agent,watch,hq} ~/bin/   # or anywhere on PATH
```

The scripts live in `~/.claude/skills/office/scripts/` (the skill calls them from there, the
symlinks are only so you can type `office-agent` / `office-hq` / `office-watch` yourself).
`office-hq` finds its pixel-art scene in `../assets/hq/` next to the script (or in
`~/.claude/office-hq-assets/` if that folder exists), so there is nothing else to copy.

## 2. Configure the proxy

Copy the example config and put your provider + models in it:

```bash
mkdir -p ~/.config/litellm
cp ~/.claude/skills/office/examples/litellm-office.yaml ~/.config/litellm/office.yaml
# edit: api_base + model names for YOUR provider, key via env var
```

Run it (foreground, for a first test):

```bash
export OFFICE_PROVIDER_KEY="your-provider-key"
export LITELLM_MASTER_KEY="sk-local-office"
export LITELLM_USE_CHAT_COMPLETIONS_URL_FOR_ANTHROPIC_MESSAGES=true
litellm --config ~/.config/litellm/office.yaml --port 10101
```

The `LITELLM_USE_CHAT_COMPLETIONS_URL_FOR_ANTHROPIC_MESSAGES=true` env var matters:
without it LiteLLM routes some providers to `/v1/responses`, which many upstreams
don't serve. The equivalent YAML setting is NOT honored: it must be the env var.

`office-agent` authenticates to the proxy with `$LITELLM_MASTER_KEY` when it is set in the
environment of the Claude Code session, and with `sk-local-office` (the value above) otherwise.

To keep the proxy running permanently on macOS, use the launchd example:

```bash
cp ~/.claude/skills/office/examples/com.office.litellm.plist ~/Library/LaunchAgents/
# edit the paths/keys inside, then:
launchctl load ~/Library/LaunchAgents/com.office.litellm.plist
```

(Linux: any process manager works, e.g. a systemd user unit running the same command.)

## 3. Point the roster at your models

Open `~/.claude/skills/office/scripts/office-agent`, top of the file:

```zsh
ROSTER=(lead qwen3.8-max-preview ds deepseek-v4-flash-0731 glm glm-5.2 k2 kimi-for-coding flash qwen3.6-flash)
```

Replace the model ids with the `model_name` entries from your LiteLLM config. Keep at
least `lead` (main executor) and one cheap agent for mechanical work. Delete roster
entries you don't serve: the skill tells the boss to skip agents whose backend is missing.

Two hardcoded routes to know about:

- Models starting with `k3`/`kimi-` skip the proxy and go straight to
  `api.kimi.com/coding` with the key read from `~/.config/kimi/api_key`. No Kimi plan?
  Remove `k2` from the roster.
- Models matching `glm-*`/`deepseek-*` are spawned with `MAX_THINKING_TOKENS=0`
  (see the gotcha in the script header). Harmless to keep.

## 4. Test a spawn

```bash
office-agent lead --task "smoke test" "reply with just: pong"
```

First spawn is slow (~10-20s: headless Claude Code loads your MCP config). You should
get `pong` back and a line appended to `~/.claude/office-logs/runs.jsonl`.

## 5. Statusline (optional but the fun part)

If you use a custom statusline, source the snippet in `examples/statusline-office.sh`
from your own script: it renders one line per running agent (code, elapsed, task,
live action) and only shows agents belonging to YOUR session. Works with any
statusline; it just appends lines.

No custom statusline yet? See
[claude-statusline](https://github.com/Wecko-ai/claude-statusline) for a base to
bolt it onto.

## 6. Live office view (optional)

```bash
office-hq --daemon  # web dashboard at http://localhost:4545 (the skill auto-starts it)
office-watch        # same as a terminal TUI, your session's agents only
office-watch --all  # every session on the machine
```

`office-hq --stop` stops the dashboard. `q` quits the TUI.

## 7. Activate

In any Claude Code session: `/office`. Give it a build task and watch the desks fill up.

## Troubleshooting

- **"proxy down, starting..." then "proxy failed to start"**: the launchd plist isn't
  installed or its paths are wrong. Start the proxy manually (step 2) and check its
  output; office-agent only auto-starts the proxy if the plist from `PLIST=` exists.
- **Agent returns empty output**: read stderr (it passes through). A 429 means your
  provider pool is throttled; a 401 means the key env var isn't reaching LiteLLM (or `LITELLM_MASTER_KEY` differs from the token `office-agent` sends).
- **`400 Unsupported model` from upstream**: your provider doesn't serve that model on
  `/v1/responses`; make sure the env var from step 2 is set in the proxy's environment,
  and that thinking-capable models you can't serve are in the `MAX_THINKING_TOKENS=0`
  case of office-agent.
- **Statusline shows agents from another session**: your state files predate v1.2.2;
  they resolve once the old runs finish.
