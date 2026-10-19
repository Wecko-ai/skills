# wecko-agent-notify

Get a phone ping when **Claude Code** or **Codex CLI** is really done, but **only when you're away from your Mac**.

```
✅ Claude Code finished (14:32)
📁 ~/projects/my-app
```

- **Waits for the real end.** Claude Code fires `Stop` at the end of every turn, even while background agents, teammates, shells or workflows keep running. The hook reads the in-flight work from the hook payload (`background_tasks`, `session_crons`) and stays quiet until the final `Stop`. Idle teammates (waiting on their mailbox) and `tail -f` log watchers don't count as work.
- **Presence-aware.** Checks keyboard/mouse idle time (`IOHIDSystem`) and screen lock. Away = notify, at the keyboard = silence.
- **Debounced.** At most one ping per session every 90 s.
- **Any delivery.** You choose the command: [`ntfy`](https://ntfy.sh), a Telegram bot script, [Hermes Agent](https://github.com/NousResearch/hermes-agent), Pushover, a webhook.

## Requirements

- macOS (presence detection is Mac-specific)
- Python 3
- A delivery command that takes the message as its last argument

## Install (Claude Code)

```bash
claude plugin marketplace add Wecko-ai/skills
claude plugin install wecko-agent-notify@wecko-ai
```

The plugin registers the `Stop` and `SessionEnd` hooks itself (async, they never block Claude Code). Then tell it how to deliver, in `~/.claude/settings.json`:

```json
{
  "env": {
    "KAGE_NOTIFY_SEND_CMD": "ntfy publish my-secret-topic"
  }
}
```

Without `KAGE_NOTIFY_SEND_CMD` nothing is sent.

If you previously added `kage-agent-notify` hooks to `settings.json` by hand, remove them, or every ping arrives twice.

## Codex CLI

Codex has no plugin hooks: point its `notify` at the wrapper. Copy `bin/kage-agent-notify` and `bin/codex-notify-wrapper` somewhere stable (for example `~/bin`), make them executable, then in `~/.codex/config.toml` (absolute path, TOML does not expand `~`):

```toml
notify = ["/ABSOLUTE/PATH/TO/codex-notify-wrapper", "turn-ended"]
```

Export `KAGE_NOTIFY_SEND_CMD` in the shell Codex starts from. The wrapper also forwards the event to another notifier if you set `KAGE_CODEX_FORWARD` to its path.

## Configuration

| Env var | Default | What it does |
|---|---|---|
| `KAGE_NOTIFY_SEND_CMD` | unset (nothing sent) | Delivery command. The message is appended as the last argument. |
| `KAGE_NOTIFY_IDLE_SKIP_SEC` | `180` | If you touched the Mac within this many seconds (and the screen is unlocked), skip the ping. |
| `KAGE_NOTIFY_FORCE` | unset | `1` bypasses the presence check (testing). |
| `KAGE_NOTIFY_DEBUG` | unset | `1` keeps the last `Stop` payload of each session in `~/.cache/kage-agent-notify/last-stop-<id>.json`. |
| `KAGE_CODEX_FORWARD` | unset | Optional binary that also receives Codex events (wrapper only). |

## Test it

```bash
echo '{"cwd":"/tmp","session_id":"abc123"}' | KAGE_NOTIFY_FORCE=1 KAGE_NOTIFY_SEND_CMD="ntfy publish my-topic" ./bin/kage-agent-notify claude-stop
```

## How presence detection works

- **Screen locked**: you're away, always notify.
- **Screen unlocked**: check HID idle time. Below `KAGE_NOTIFY_IDLE_SKIP_SEC`, you're working, skip.
- Screen-lock detection uses the `Quartz` Python module when available, falling back to an `osascript` frontmost-app check (`loginwindow` = locked). The fallback needs Accessibility permission for the terminal app running the hook.

Debounce state lives in `~/.cache/kage-agent-notify/` (mtime-based files). Delete the folder to reset.

Formerly [Wecko-ai/kage-agent-notify](https://github.com/Wecko-ai/kage-agent-notify).
