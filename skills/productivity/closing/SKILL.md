---
name: closing
description: Wrap up the session before closing. Persist memory, keep CLAUDE.md lean and true, verify what shipped is really live, and list loose ends and what is blocked on the user
argument-hint: [notes optionnelles]
disable-model-invocation: true
---

The user is about to close this session. Do a full wrap-up so nothing is lost and the next
session starts clean. Work through ALL sections, then give the short final report. Check, do
not assume: every claim in the report comes from a command you ran in this wrap-up.

## 1. Inventory what this session touched

Build the list first, the other sections depend on it. Go through the conversation and collect:
- **Repos**: every git repo written to, not just the working directory (standalone CLI repos,
  dataset repos, `~/.hermes`, `~/.claude` skills, dotfiles). Run `git status -sb` in each.
- **Scheduled jobs**: launchd plists added, edited, reloaded or disabled (`~/Library/LaunchAgents`),
  remote crontabs, Hermes or other agent cron jobs. These never show up in `git status`.
- **Deploys and publishes**: servers deployed, packages published, artifacts or remote configs changed.
- **Environment state**: `gh auth` active account, npm or other registry auth, Chrome MCP tabs,
  background tasks and monitors, temp servers or ports opened.

## 2. Verify what shipped is really live

For each deploy or publish from step 1, verify rather than trust the log:
- Server HEAD equals `origin/main`, the build is newer than the last code commit, the process
  restart actually happened (restart count or uptime), and a URL that is new this session answers 200.
- Published packages: `npm view <pkg> version` (or the registry equivalent) matches what was bumped.
- A deploy that is pending (committed, not deployed) is a loose end, say so.

## 3. Memory (auto-memory directory)

- Review the session: decisions, gotchas, fixes, state changes, user feedback and corrections.
- For each durable, non-obvious fact: update the memory file that covers it, else create one
  (correct frontmatter, `[[links]]`). One fact per file.
- Delete or rewrite memories this session proved WRONG or outdated (e.g. "X is broken" after X
  was fixed, a job that was disabled, a count that changed).
- Sync `MEMORY.md`: one line per memory, accurate hooks, no orphan or stale entries.

## 4. CLAUDE.md: true, and not longer than it has to be

- Diff what changed this session (architecture, commands, workflows, deploys, jobs, env) against
  the CLAUDE.md claims. Fix every claim the session made false.
- Split rule: a durable RULE or RUNBOOK step goes in CLAUDE.md; STATE and HISTORY (what shipped
  when, counts, incidents) go in memory. Never write the same fact in both.
- Prefer replacing or deleting a stale paragraph over appending a new one. If CLAUDE.md is already
  long, move history out to memory or a doc while you are there.
- Commit per project rules (branch + PR if required, else a direct docs commit). Stage explicit
  paths only.

## 5. Put the environment back

- `gh auth` back on the default account if it was switched; registry auth untouched or restored.
- Close Chrome MCP tabs this session opened; stop background tasks and monitors that are not
  meant to outlive the session (or hand them off explicitly).
- Remove scratch files only from the session scratchpad, never from the repo.

## 6. Loose ends: report, don't fix

- `git status` in every repo from step 1: uncommitted or untracked files, marked **this session**
  vs **foreign** (other tools or sessions). Never absorb foreign changes.
- Unpushed commits, unmerged branches, open PRs created this session and their CI state.
- Anything half-done or promised but not delivered, with what remains.
- Pending chores discovered this session (put them in memory if they are durable).

## 7. Blocked on the user

A separate list from the loose ends: actions only the user can take (credentials, tokens, paid
or account decisions, CAPTCHAs, dashboard toggles, anything public-facing waiting for a yes).
For each: what it unblocks, and the exact command or click path. Record them in memory too, so
the next session does not rediscover the block.

## 8. Final report

Short, no fluff, in the user's language:
- Persisted: memory files touched, CLAUDE.md updated or not (and what).
- Live check: pass or fail per deploy or publish.
- Jobs changed: what is scheduled now that was not, or the reverse.
- Loose ends.
- Blocked on you: with the command to run.

If the user passed notes, treat them as priorities for the wrap-up: $ARGUMENTS
