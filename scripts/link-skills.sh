#!/usr/bin/env bash
set -euo pipefail

# Dev-only helper for maintainers of this repo, not a supported installer.
#
# Symlinks every skill of this repo into the local harness skill directories:
#   - ~/.claude/skills: Claude Code
#   - ~/.agents/skills: Codex and other Agent Skills-compatible harnesses
# A `git pull` then keeps the installed skills current. Re-run after adding,
# removing or renaming a skill.
#
# An existing real folder with the same name is never deleted: it is skipped,
# or moved aside to <name>.bak-<timestamp> when --force is passed.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills")
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

names=()
srcs=()
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  names+=("$(basename "$src")")
  srcs+=("$src")
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -print0)

for DEST in "${DESTS[@]}"; do
  if [ -L "$DEST" ]; then
    resolved="$(readlink -f "$DEST")"
    case "$resolved" in
      "$REPO"|"$REPO"/*)
        echo "error: $DEST is a symlink into this repo ($resolved). Remove it and re-run." >&2
        exit 1
        ;;
    esac
  fi
  mkdir -p "$DEST"

  for i in "${!names[@]}"; do
    name="${names[$i]}"
    src="${srcs[$i]}"
    target="$DEST/$name"

    if [ -e "$target" ] && [ ! -L "$target" ]; then
      if [ "$FORCE" = 1 ]; then
        bak="$target.bak-$(date +%Y%m%d%H%M%S)"
        mv "$target" "$bak"
        echo "moved existing $target -> $bak"
      else
        echo "skip $name: $target is a real folder (re-run with --force to move it aside)"
        continue
      fi
    fi

    ln -sfn "$src" "$target"
    echo "linked $name -> $src ($DEST)"
  done
done
