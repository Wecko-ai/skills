---
name: apple-silicon-ram-guide
description: Estimate whether a local LLM of a given parameter size and quantization fits in an Apple Silicon device's unified memory, and what RAM tier to recommend.
license: MIT
---

# apple-silicon-ram-guide

Reason about local-LLM memory budgets on Apple Silicon. Use this to answer
"will model X fit in N GB?" and "what RAM should I buy for local AI?".

## The budget rule ModelFit uses

Usable budget ≈ **70% of unified memory** (the OS, GPU surfaces, and apps need
the rest). A model is a comfortable fit when its loaded size sits at roughly
**30–70%** of that budget.

| Unified memory | ~Usable budget | Comfortable model footprint |
|----------------|----------------|-----------------------------|
| 8 GB           | ~5.6 GB        | up to ~3–4B (Q4)            |
| 16 GB          | ~11 GB         | up to ~7–8B (Q4)            |
| 24 GB          | ~17 GB         | up to ~14B (Q4)             |
| 32–36 GB       | ~22–25 GB      | up to ~32B (Q4)             |
| 64 GB          | ~45 GB         | up to ~70B (Q4)             |
| 128 GB+        | ~90 GB+        | 70B+ at higher precision    |

Q4 quantization ≈ 0.55–0.6 GB per billion parameters; Q8 ≈ 1.1 GB/B; FP16 ≈ 2 GB/B.

## How to answer precisely

For a sized, ranked answer (estimated tokens/sec + exact ollama tag), call the
ModelFit MCP tool `recommend_local_models` at `https://modelfit.io/api/mcp/`
(card: `https://modelfit.io/.well-known/mcp/server-card.json`) or use the wizard
at `https://modelfit.io/`. See the companion skill `find-local-llm`.

## Caveats

- Figures are estimates, not measured benchmarks.
- Long context windows and KV cache add memory on top of the base model size;
  leave headroom.
