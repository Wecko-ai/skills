#!/bin/bash
# Office block for a Claude Code statusline: source this from your own
# statusline script, then append "$OFFICE" to whatever you already print.
#
#   source ~/.claude/statusline-office.sh
#   printf "...your existing statusline...%s" "$OFFICE"
#
# Renders one full line per running agent of THIS session:
#   tnk 3m15s refactor the auth module › Edit src/auth.ts
# Ownership: state files carry the spawning claude's pid (.boss); we walk our own
# process tree to find our claude and only show matching agents. Legacy files
# without .boss are resolved by walking up from the agent's pid instead.
# Deps: jq, ps.

ESC=$'\033'
OFFICE=""
ACTIVE_DIR="$HOME/.claude/office-logs/active"
if [ -d "$ACTIVE_DIR" ]; then
  MY_CLAUDE=0
  p=$$
  for _ in 1 2 3 4 5 6 7 8; do
    p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    [ -z "$p" ] || [ "$p" -le 1 ] && break
    case "$(ps -o comm= -p "$p" 2>/dev/null)" in
      *claude*) MY_CLAUDE=$p; break ;;
    esac
  done
  shopt -s nullglob
  for f in "$ACTIVE_DIR"/*.json; do
    parsed=$(jq -r '[.agent,.start,.pid,(.task // ""),(.action // ""),(.boss // 0)]|@tsv' "$f" 2>/dev/null) || continue
    agent=$(echo "$parsed"  | cut -f1)
    start=$(echo "$parsed"  | cut -f2)
    pid=$(echo "$parsed"    | cut -f3)
    task=$(echo "$parsed"   | cut -f4)
    action=$(echo "$parsed" | cut -f5)
    boss=$(echo "$parsed"   | cut -f6)
    # 3-letter display codes: match these to YOUR roster in office-agent
    case "$agent" in
      lead) code="tnk" ;;
      ds)   code="suz" ;;
      glm)  code="ken" ;;
      k2)   code="yuk" ;;
      flash) code="hay" ;;
      *)    code="$agent" ;;
    esac
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$f"
      continue
    fi
    # legacy state file without .boss: resolve owner from the agent's pid
    if [ "$boss" = "0" ] || [ -z "$boss" ] || [ "$boss" = "null" ]; then
      bp=$pid
      for _ in 1 2 3 4 5 6 7 8; do
        bp=$(ps -o ppid= -p "$bp" 2>/dev/null | tr -d ' ')
        [ -z "$bp" ] || [ "$bp" -le 1 ] && break
        case "$(ps -o comm= -p "$bp" 2>/dev/null)" in
          *claude*) boss=$bp; break ;;
        esac
      done
    fi
    if [ "$boss" != "0" ] && [ -n "$boss" ] && [ "$boss" != "null" ] && [ "$MY_CLAUDE" != "0" ] && [ "$boss" != "$MY_CLAUDE" ]; then
      continue
    fi
    now=$(date +%s)
    elapsed=$(( now - start ))
    if   [ "$elapsed" -lt 60 ];   then e="${elapsed}s"
    elif [ "$elapsed" -lt 3600 ]; then e="$((elapsed/60))m$((elapsed%60))s"
    else h=$((elapsed/3600)); m=$(((elapsed%3600)/60)); e="${h}h${m}m"; fi
    [ -n "$action" ] && action=" ${ESC}[90m› ${action}${ESC}[0m"
    OFFICE+=$'\n'" ${ESC}[35m${code}${ESC}[0m ${ESC}[36m${e}${ESC}[0m ${task}${action}"
  done
  shopt -u nullglob
fi
