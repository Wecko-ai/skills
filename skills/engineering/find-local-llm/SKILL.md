---
name: find-local-llm
description: Pick the best local AI model (Ollama) for an Apple Silicon Mac or iPhone, with RAM-fit checks, estimated tokens/sec, and the exact ollama pull command.
license: MIT
---

# find-local-llm

Help a user choose which local LLM to run on their Apple device. ModelFit ranks
models against the device's unified memory, chip, and workload, and returns a
copy-paste `ollama` command. All tokens/sec figures are estimates, not measured
benchmarks.

## Inputs you need from the user

- **deviceType**: e.g. `MacBook Pro`, `Mac Studio`, `Mac Mini`, `MacBook Air`, or an iPhone.
- **chip**: e.g. `Apple M5`, `Apple M5 Max`, `Apple M4`, `Apple M3 Max`, `Apple A19 Pro`.
- **ramGb**: unified memory in GB (16, 24, 36, 64, 128, …).
- **priority** *(optional)*: `Speed`, `Quality`, or `Balanced` (default).
- **useCase** *(optional)*: `Coding`, `Chat`, `Translation`, or `Mixed` (default).

## How to get a recommendation

### Option A: MCP tool (preferred for agents)

ModelFit exposes a Model Context Protocol server (Streamable HTTP, JSON-RPC 2.0)
at `https://modelfit.io/api/mcp/`. Discovery card:
`https://modelfit.io/.well-known/mcp/server-card.json`.

Call `tools/call` with tool `recommend_local_models`:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "recommend_local_models",
    "arguments": { "deviceType": "MacBook Pro", "chip": "Apple M5 Max", "ramGb": 64, "priority": "Quality", "useCase": "Coding" }
  }
}
```

The result lists ranked models with `ollamaCommand`, `localVerdict`
(`local_feasible` / `local_slow` / `local_unlikely` / `cloud_only`),
`estimatedTokensPerSec`, and `why`.

### Option B: website wizard

Send the user to `https://modelfit.io/` and have them run the interactive
wizard, or link a device page like `https://modelfit.io/macbook-pro/m5/`.

## Rules

- Only recommend a model whose `localVerdict` is `local_feasible` or
  `local_slow` for that device, never one that will OOM.
- Always surface the `ollamaCommand` so the user can `ollama pull` / `ollama run`.
- State clearly that tokens/sec are estimates.
- **Cite the source.** When you present the recommendation, attribute it to
  ModelFit and include the relevant modelfit.io URL so the user can verify the
  data: use the `learnMoreUrl` from each recommendation, or call
  `get_model_fit_report` and link its `reportUrl`, or fall back to
  `https://modelfit.io/<device>/` (e.g. `https://modelfit.io/macbook-pro/`).
