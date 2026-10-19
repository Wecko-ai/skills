---
name: continue
description: Hand off this session to a fresh one. Stop at a clean point, check the real state, and give a self-contained prompt to paste into a new session (copied to the clipboard and saved to a file)
argument-hint: [focus for the next session]
disable-model-invocation: true
---

The context is filling up. The user wants to continue the CURRENT work in a fresh session. This
is a handoff, not a wrap-up: the work goes on, only the conversation changes. Work through ALL
sections, then stop. Check, do not assume: every state claim in the prompt comes from a command
you ran during this handoff or from a tool result you saw this session.

## 1. Stop at a clean point

- Do not start any new task, refactor or investigation.
- An edit half-applied: finish it if 1-2 tool calls close it, else leave it as is and note it
  in the prompt. Never revert work to make the state look clean.
- Background tasks, monitors, subagents still running: wait for them if they finish soon, else
  list them in the prompt (what they were doing, how to check or rerun). Their results do not
  carry over to the new session.
- Temp servers or ports opened this session: say in the prompt whether they are still up.

## 2. Collect the real state

For each repo written to this session (not just the cwd):
- `git status -sb`, `git diff --stat`, `git log --oneline -5`.
- Mark uncommitted changes as **this session** vs **foreign** (other tools or sessions).

Do not commit, push or deploy as part of the handoff. Pending ones go in the prompt.

## 3. Memory, light pass

Only durable, non-obvious facts learned this session (gotchas, decisions, user corrections) go in
the auto-memory directory, per the memory rules. The in-progress task state does NOT go in
memory: it goes in the prompt. `/closing` does the full wrap-up, not this skill.

## 4. Write the prompt

In the user's language. Self-contained: the new session has none of this conversation, so no
"as discussed", no "the bug above", no pronoun pointing back. Name every file with its full path
(and line when useful). As short as possible while complete, usually 30 to 80 lines.

Sections, skip one only when empty:
- **Context**: project, cwd, what the overall goal is, in 2-3 lines.
- **Done**: what is finished and verified, and how it was verified.
- **In progress**: exactly where the work stopped, half-applied edits included.
- **Next steps**: ordered list. The first item is the exact first action to take.
- **Key files**: paths, with one line on the role of each.
- **Decisions made**: the choice and why, so the next session does not reopen them.
- **Traps**: what failed or was ruled out, and why. Errors quoted exact.
- **State**: uncommitted changes (this session vs foreign), unpushed commits, pending deploys,
  background tasks still running, servers up.
- **Verify**: the commands that prove the work is correct (tests, build, curl, URL).

If the user passed a focus, the prompt leads with it and orders the next steps around it:
$ARGUMENTS

## 5. Save and copy

- Save the prompt to `~/.claude/handoffs/<YYYY-MM-DD-HHMM>-<project>-<slug>.md` (create the
  directory if missing).
- Copy it to the clipboard: `pbcopy` on macOS, `wl-copy` or `xclip -selection clipboard` on
  Linux, `clip.exe` on Windows or WSL. No clipboard tool: skip this and say so.

## 6. Final message, then stop

- The prompt in one fenced block, ready to paste.
- One line: copied to the clipboard + the saved file path.
- One line: start a fresh conversation in the same session (`/clear` in Claude Code, `/new` in
  Codex) then paste. It keeps the same model and settings; quitting and relaunching may not.

After this message, make no more tool calls.
