#!/usr/bin/env bash
set -uo pipefail

# Repo checks, run before every commit:
#   1. every SKILL.md has frontmatter with `name:` equal to its folder and a `description:`
#   2. every skill is listed in exactly one plugin of .claude-plugin/marketplace.json, and
#      every listed path exists
#   3. every skill is linked from the top-level README.md and its bucket README.md
#   4. nothing private leaks: absolute home paths, IPv4 addresses, key-shaped tokens,
#      personal mailboxes, Higgsfield workspace ids
#   5. no em-dash in prose

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
fail=0
err() { echo "FAIL: $*"; fail=1; }

while IFS= read -r md; do
  dir="$(dirname "$md")"
  name="$(basename "$dir")"
  bucket="$(basename "$(dirname "$dir")")"
  head -1 "$md" | grep -qx -- '---' || err "$md: no frontmatter"
  fm="$(awk 'NR==1{next} /^---$/{exit} {print}' "$md")"
  echo "$fm" | grep -qx "name: $name" || err "$md: name must be '$name'"
  echo "$fm" | grep -q '^description:' || err "$md: missing description"
  grep -q "\./$dir\"" .claude-plugin/marketplace.json || err "$dir: not in marketplace.json"
  grep -q "(\./$dir/SKILL.md)" README.md || err "$dir: not linked from README.md"
  grep -q "(\./$name/SKILL.md)" "skills/$bucket/README.md" 2>/dev/null || err "$dir: not linked from skills/$bucket/README.md"
done < <(find skills -name SKILL.md -not -path '*/node_modules/*' | sort)

for dir in plugins/*/; do
  [ -d "$dir" ] || continue
  dir="${dir%/}"
  [ -f "$dir/.claude-plugin/plugin.json" ] || err "$dir: missing .claude-plugin/plugin.json"
  [ -f "$dir/README.md" ] || err "$dir: missing README.md"
  grep -q "\"source\": \"\./$dir\"" .claude-plugin/marketplace.json || err "$dir: no marketplace entry with this source"
  grep -q "(\./$dir/README.md)" README.md || err "$dir: not linked from README.md"
done

python3 - <<'EOF' || fail=1
import json, os, sys, collections
m = json.load(open(".claude-plugin/marketplace.json"))
seen = collections.Counter()
ok = True
for p in m["plugins"]:
    for s in p.get("skills", []):
        seen[s] += 1
        if not os.path.isfile(os.path.join(s, "SKILL.md")):
            print(f"FAIL: {p['name']} lists {s}, which has no SKILL.md"); ok = False
for s, n in seen.items():
    if n > 1:
        print(f"FAIL: {s} is listed in {n} plugins"); ok = False
sys.exit(0 if ok else 1)
EOF

leaks="$(grep -rnIE \
  -e '/Users/[a-z]' -e '/home/[a-z]+/' \
  -e '(^|[^0-9.])([0-9]{1,3}\.){3}[0-9]{1,3}([^0-9.]|$)' \
  -e 'sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{12,}|xox[bp]-' \
  -e '[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|icloud)\.com' \
  -e 'workspace set [0-9a-f]{8}-' \
  --exclude-dir=.git --exclude=check.sh . || true)"
# Loopback addresses are fine (local proxies and dev servers).
allowed='127\.0\.0\.1'
leaks="$(echo "$leaks" | grep -vE "$allowed" || true)"
[ -n "$leaks" ] && { echo "$leaks"; err "possible private data above"; }

dashes="$(grep -rnI "$(printf '\342\200\224')" --exclude-dir=.git . || true)"
[ -n "$dashes" ] && { echo "$dashes"; err "em-dash found (rewrite the sentence)"; }

[ "$fail" = 0 ] && echo "OK: all checks passed"
exit "$fail"
