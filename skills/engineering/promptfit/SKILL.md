---
name: promptfit
description: Turn a vague request into a structured ticket via a local LLM, then build it. Usage /promptfit [-y] <your prompt>
argument-hint: "[-y|--auto] <your vague prompt>"
disable-model-invocation: true
---

The user invoked `/promptfit` to refine a vague request into a structured, actionable ticket BEFORE you implement it. The point: a cheap local model does the scoping work (clear acceptance criteria, explicit out-of-scope) so you execute against a tight spec instead of guessing.

The raw request is: $ARGUMENTS

## Step 0: Parse the bypass flag

If the request begins with `-y`, `--yes`, or `--auto` (a leading flag token), set AUTO mode and strip that token, the rest is the actual prompt. Otherwise AUTO is off.
- AUTO **off** (default): show the ticket and wait for the developer's approval before implementing (Step 5).
- AUTO **on**: skip the approval gate: show the ticket, then implement immediately without asking.

Only treat it as the flag when it's a leading token (e.g. `/promptfit -y add dark mode`). A `-y` buried mid-sentence is part of the prompt, not the flag.

## Step 1: Pick the installed local model

promptfit defaults to `qwen3:8b`, which may not be the model the user actually pulled. First find an installed Ollama model and use it explicitly:

```bash
ollama list   # first column = model tags already on disk
```

Take the first non-`NAME` tag (e.g. `qwen3:14b-q4_K_M`) and pass it via `--model` in Step 2. If `ollama list` errors (Ollama not installed) or shows no models, skip to Step 3 (fallback) and tell the user to run `modelfit --yes` to install the best model for their machine.

## Step 2: Gather repo context (this is what makes the ticket accurate)

The local model has NO repo knowledge. Without context it invents plausible-but-wrong file paths; with the right files it produces a repo-accurate ticket (correct files, functions, and test commands). So invest a few seconds here.

1. Pull concrete nouns from the request: feature names, symbols, filenames, UI elements (e.g. "search bar", "login button", "ranking").
2. Find the 1-2 implementation files most likely to change. Use the fast tools you have: Grep for those terms, Glob for likely filenames. Prefer the actual implementation file over tests or types.
3. ALSO attach the project's manifest so the ticket's acceptance criteria use REAL commands, not invented ones. The local model cannot guess your test script: if it isn't in context it WILL hallucinate one (e.g. `npm run test:recommend` when the real script is `npm run audit:hardware`). Include whichever exist: `package.json` (or `pyproject.toml`/`Cargo.toml`/`go.mod`/`Makefile`) and `CLAUDE.md`.
4. If the request is plainly repo-agnostic (e.g. "write a bash script to rename files"), skip context entirely.

Total budget: at most ~3-4 files (1-2 implementation + manifest + CLAUDE.md). More context = slower + noisier, not better. Don't read whole large files just to choose; filenames and a grep hit are enough.

## Step 3: Refine via the local model

Run promptfit with the detected model AND the context files you found. Use the flag-stripped prompt from Step 0 (NOT the raw `-y ...` token) as the quoted argument. Try these in order, first that works (replace `<PROMPT>` with the stripped request, `<MODEL>` with the tag; add one `--context` per file):

```bash
# A) global install (fastest): impl file(s) + manifest so commands are real
pf '<PROMPT>' --model <MODEL> --context lib/foo.ts package.json CLAUDE.md

# B) no global install, run via npx
npx -y @wecko-ai/promptfit '<PROMPT>' --model <MODEL> --context lib/foo.ts package.json
```

If Step 2 found no relevant files, run it without `--context`.

Capture the structured ticket from stdout. Note: reasoning models (Qwen3) think first, so a refinement can take 30-90s (that's normal); run it in the background and read the candidate files meanwhile so you're ready to implement. Common failures:
- `command not found` / npx cannot resolve the package → promptfit isn't available locally.
- `Cannot connect to LLM` / `ECONNREFUSED` → Ollama isn't running (`ollama serve`).
- `model ... not found` → the tag is wrong; re-check `ollama list`.

## Step 4: If the local model is unavailable

Do NOT abort. Fall back: structure the ticket YOURSELF in the same format below (this still gives the user scoping discipline), then tell them once, briefly, how to enable the faster local path:
> Tip: install the local refiner for cheaper pre-processing: `npm i -g @wecko-ai/promptfit` and `modelfit --yes` (installs the best model for your machine).

Ticket format:
```
## Task: <clear, specific title>

### Context
- What to read first; existing patterns / CLAUDE.md to follow.

### Requirements
- What must change, specifically. Expected behavior after.

### Steps
1. <action> → verify <checkpoint>

### Acceptance Criteria
- [ ] Testable criterion (prefer a runnable command: npm test, tsc --noEmit, a curl)
- [ ] No regressions: name the check

### Do NOT
- Out of scope / over-engineering to resist
```

## Step 5: Show the ticket and WAIT for approval (default gate)

**If AUTO mode is on (Step 0):** skip the gate. Show the ticket, then implement it straight away (the implementation rules in point 3 below still apply). Do not ask for approval.

Otherwise (default), the ticket is the contract, do NOT start implementing until the developer approves it.

1. Show the refined ticket, enough to judge it: Task, Requirements, Acceptance Criteria, and Do NOT. (Trim only genuinely redundant lines; the developer needs to actually evaluate the spec, not a teaser.)
2. Then STOP and explicitly ask for a decision, e.g.:
   > Approve this ticket? **proceed** to implement · **edit** (tell me what to change) · **cancel**
   If anything in the ticket looks ambiguous or wrong to you, surface it here in one line rather than waiting for the developer to spot it.
3. Wait for their answer. Do not write or edit any code until they reply:
   - **proceed / yes / go** → implement against the ticket. Follow the acceptance criteria exactly, respect the "Do NOT" section, run the named checks, and don't expand scope beyond the ticket.
   - **edit / change X** → apply their adjustment. If it's a substantive scope change, re-run promptfit (Step 3) with the amended request; for a small tweak, just edit the ticket inline. Then show it and ask again.
   - **cancel / no** → stop. Don't implement. Leave the ticket shown so they can copy it elsewhere.

This approval gate is the default and applies even when the ticket looks obviously correct: the developer asked for a spec to review, not an autopilot. (The one exception is the bypass flag, see top of this skill.)

Once approved, keep it tight: implement the ticket, don't turn it into a conversation.
