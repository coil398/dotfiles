#!/usr/bin/env bash
# ai-design-system audit script
#
# Run from a project root. Reports generic AI aesthetics signals,
# missing aesthetic SSOT sections, and basic token-coverage stats.
#
# Usage:
#   bash <skill>/audit.sh [project-root]
#
# Exit code is informational — non-zero indicates findings,
# but the script never blocks. Treat as advisory, not gate.

set -u

ROOT="${1:-.}"
cd "$ROOT" || { echo "ERROR: cannot enter $ROOT"; exit 2; }

if ! command -v rg >/dev/null 2>&1; then
  echo "WARN: ripgrep (rg) not found — falling back to grep -r (slower)."
  GREP() { grep -rEn --color=never --include='*.css' --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' --include='*.vue' --include='*.svelte' --include='*.astro' "$@" . 2>/dev/null; }
else
  GREP() { rg -nE --color=never -tcss -tts -tjs -ttsx -tjsx -tvue -tsvelte "$@" 2>/dev/null; }
fi

count() { wc -l | tr -d ' '; }
section() { printf '\n=== %s ===\n' "$1"; }

ISSUES=0
note_issue() { ISSUES=$((ISSUES + 1)); }

# ---------- 1. SSOT presence ----------
section "1. SSOT presence"
SSOT_FILES=()
for cand in design-system.config.css design-system.config.json design-system.config.ts design-system.config.js; do
  if [ -f "$cand" ]; then
    SSOT_FILES+=("$cand")
    echo "  found: $cand"
  fi
done
if [ ${#SSOT_FILES[@]} -eq 0 ]; then
  echo "  ❌ no design-system.config.* found at project root"
  echo "  → run BOOTSTRAP.md to generate one"
  note_issue
fi

# ---------- 2. Aesthetic section ----------
section "2. Aesthetic SSOT section"
JSON_SSOT=""
for f in design-system.config.json; do
  if [ -f "$f" ]; then JSON_SSOT="$f"; fi
done
if [ -n "$JSON_SSOT" ]; then
  for key in tone differentiation antiDirection; do
    if grep -q "\"$key\"" "$JSON_SSOT"; then
      echo "  ✅ aesthetic.$key present"
    else
      echo "  ⚠️  aesthetic.$key NOT FOUND in $JSON_SSOT"
      note_issue
    fi
  done
else
  echo "  ⚠️  no JSON SSOT — cannot validate aesthetic section"
fi

# ---------- 3. Generic AI aesthetics — fonts ----------
section "3. Generic AI fonts (in source, not SSOT)"
GENERIC_FONTS_RX='Inter|Roboto|"Arial"|system-ui|Space Grotesk'
HITS=$(GREP "font-family[^;{]*($GENERIC_FONTS_RX)" 2>/dev/null \
  | grep -vE '/(\.git|node_modules|dist|build|\.next)/' \
  | grep -v 'design-system\.config\.' || true)
if [ -n "$HITS" ]; then
  echo "$HITS" | head -20
  echo "  ⚠️  $(echo "$HITS" | count) generic-font occurrences in source"
  note_issue
else
  echo "  ✅ no generic font direct usage in source"
fi

# ---------- 4. Generic AI aesthetics — purple gradient on white ----------
section "4. Purple gradient signals"
PURPLE_RX='(linear-gradient|radial-gradient)[^;]*(#a855f7|#8b5cf6|#7c3aed|#9333ea|violet|purple)'
HITS=$(GREP "$PURPLE_RX" 2>/dev/null \
  | grep -vE '/(\.git|node_modules|dist|build|\.next)/' || true)
if [ -n "$HITS" ]; then
  echo "$HITS" | head -10
  echo "  ⚠️  potential AI-purple-gradient — verify against aesthetic"
  note_issue
else
  echo "  ✅ no canonical AI-purple gradient"
fi

# ---------- 5. Token coverage ----------
section "5. Token coverage in CSS SSOT"
CSS_SSOT=""
for f in design-system.config.css; do
  if [ -f "$f" ]; then CSS_SSOT="$f"; fi
done
if [ -n "$CSS_SSOT" ]; then
  for prefix in --color- --spacing- --font- --motion- --ease --shadow- --radius-; do
    n=$(grep -cE "^\s*${prefix}" "$CSS_SSOT" 2>/dev/null || echo 0)
    printf "  %-12s %3d tokens\n" "$prefix*" "$n"
  done
  if grep -q 'prefers-reduced-motion' "$CSS_SSOT"; then
    echo "  ✅ prefers-reduced-motion handling present"
  else
    echo "  ⚠️  prefers-reduced-motion handling missing"
    note_issue
  fi
else
  echo "  (no CSS SSOT to inspect)"
fi

# ---------- 6. Hard-coded values in source ----------
section "6. Hard-coded color/size values in source (sampling)"
HEX_HITS=$(GREP '#[0-9a-fA-F]{3,8}\b' 2>/dev/null \
  | grep -vE '/(\.git|node_modules|dist|build|\.next)/' \
  | grep -v 'design-system\.config\.' \
  | grep -v 'tailwind\.config\.' || true)
HEX_COUNT=0
[ -n "$HEX_HITS" ] && HEX_COUNT=$(echo "$HEX_HITS" | count)
echo "  hardcoded hex values in source: $HEX_COUNT"
[ "$HEX_COUNT" -gt 0 ] && note_issue
ARBITRARY_HITS=$(GREP 'text-\[#|w-\[\d|h-\[\d|p-\[\d|m-\[\d' 2>/dev/null \
  | grep -vE '/(\.git|node_modules|dist|build|\.next)/' || true)
ARB_COUNT=0
[ -n "$ARBITRARY_HITS" ] && ARB_COUNT=$(echo "$ARBITRARY_HITS" | count)
echo "  Tailwind arbitrary values [#xxx] / [Npx]: $ARB_COUNT"
[ "$ARB_COUNT" -gt 0 ] && note_issue

# ---------- 7. Inline styles ----------
section "7. Inline styles in JSX/TSX/Vue/Svelte/Astro"
INLINE=$(GREP 'style=\{\{|style="(?!--)' 2>/dev/null \
  | grep -vE '/(\.git|node_modules|dist|build|\.next)/' || true)
INLINE_COUNT=0
[ -n "$INLINE" ] && INLINE_COUNT=$(echo "$INLINE" | count)
echo "  inline style attributes: $INLINE_COUNT"
[ "$INLINE_COUNT" -gt 0 ] && note_issue

# ---------- Summary ----------
section "Summary"
if [ "$ISSUES" -eq 0 ]; then
  echo "  ✅ no audit findings"
  exit 0
else
  echo "  ⚠️  $ISSUES audit dimension(s) flagged. See above."
  echo
  echo "  Next steps:"
  echo "    - read AUDIT.md Step 3 for prioritization"
  echo "    - check aesthetic against AESTHETIC.md"
  echo "    - resolve via SSOT update or component fix"
  exit 1
fi
