#!/usr/bin/env bash
# preview-tokens.sh
#
# design-system.config.css を読み、color / typography / motion / shadow
# のサンプル swatch を含む静的 HTML を生成する軽量プレビュー。
#
# Usage:
#   bash <skill>/preview-tokens.sh [project-root] [output.html]
#
# 出力先 default: ./design-system-preview.html

set -u

ROOT="${1:-.}"
OUT="${2:-${ROOT}/design-system-preview.html}"
CSS="${ROOT}/design-system.config.css"
JSON="${ROOT}/design-system.config.json"

if [ ! -f "$CSS" ]; then
  echo "ERROR: $CSS not found. Run BOOTSTRAP first."
  exit 1
fi

# -- aesthetic block を JSON から抽出（jq があれば使う、なければ最小フォールバック） --
TONE=""; DIFF=""; ANTI=""
if [ -f "$JSON" ] && command -v jq >/dev/null 2>&1; then
  TONE=$(jq -r '.aesthetic.tone // ""' "$JSON" 2>/dev/null || echo "")
  DIFF=$(jq -r '.aesthetic.differentiation // ""' "$JSON" 2>/dev/null || echo "")
  ANTI=$(jq -r '(.aesthetic.antiDirection // []) | join(" / ")' "$JSON" 2>/dev/null || echo "")
fi

# -- token 抽出: --color-* / --font-* / --motion-* / --ease-* / --shadow-* / --spacing-* / --radius-* --
extract() {
  local prefix="$1"
  grep -oE "^\s*${prefix}[a-zA-Z0-9_-]+\s*:\s*[^;]+" "$CSS" \
    | sed -E "s/^\s*//; s/\s*$//; s/:\s*/|/" \
    || true
}

COLORS=$(extract '--color-')
FONTS=$(extract '--font-')
MOTION=$(extract '--motion-\|--duration-')
EASES=$(extract '--ease-\|--easing-')
SHADOWS=$(extract '--shadow-')
SPACINGS=$(extract '--spacing-\|--space-')
RADIUS=$(extract '--radius-\|--rounded-')

# Helper: produce HTML for a token group
swatch_color() {
  local NAME="$1" VAL="$2"
  cat <<EOF
<div class="swatch">
  <div class="sw-color" style="background:${VAL};"></div>
  <div class="sw-meta"><code>${NAME}</code><span>${VAL}</span></div>
</div>
EOF
}
swatch_text() {
  local NAME="$1" VAL="$2"
  cat <<EOF
<div class="row"><code>${NAME}</code><span class="val">${VAL}</span></div>
EOF
}
swatch_shadow() {
  local NAME="$1" VAL="$2"
  cat <<EOF
<div class="swatch">
  <div class="sw-box" style="box-shadow:${VAL};"></div>
  <div class="sw-meta"><code>${NAME}</code><span>${VAL}</span></div>
</div>
EOF
}

# Build HTML
{
cat <<HTMLHEAD
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Design System Preview</title>
<link rel="stylesheet" href="design-system.config.css">
<style>
  body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 24px; max-width: 1100px; margin: 0 auto; background: #fafafa; color: #111; }
  h1 { font-size: 22px; margin: 0 0 6px; }
  h2 { font-size: 15px; text-transform: uppercase; letter-spacing: 0.06em; margin: 32px 0 12px; padding-top: 12px; border-top: 1px solid #e2e2e2; }
  .header { padding: 16px; background: #fff; border: 1px solid #e2e2e2; border-radius: 8px; margin-bottom: 24px; }
  .meta { color: #666; font-size: 13px; }
  .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
  .swatch { background: #fff; border: 1px solid #e2e2e2; border-radius: 8px; overflow: hidden; }
  .sw-color { height: 80px; }
  .sw-box { height: 60px; margin: 12px; background: #fff; border-radius: 4px; }
  .sw-meta { padding: 8px 12px; font-size: 12px; }
  .sw-meta code { display: block; font-family: ui-monospace, "JetBrains Mono", monospace; font-size: 11px; color: #333; }
  .sw-meta span { display: block; color: #888; font-size: 10px; margin-top: 2px; word-break: break-all; }
  .row { display: flex; justify-content: space-between; padding: 6px 12px; border-bottom: 1px solid #eee; font-size: 13px; }
  .row code { font-family: ui-monospace, monospace; font-size: 12px; }
  .row .val { color: #666; font-size: 12px; }
  .typography-sample { padding: 16px; background: #fff; border: 1px solid #e2e2e2; border-radius: 8px; margin-bottom: 8px; }
  .typography-sample .label { font-family: ui-monospace, monospace; font-size: 11px; color: #888; margin-bottom: 4px; }
  .anti { background: #fffaf0; border-left: 3px solid #d97706; padding: 8px 12px; margin: 8px 0; font-size: 13px; }
  .empty { color: #999; font-style: italic; padding: 8px 0; font-size: 13px; }
</style>
</head>
<body>
HTMLHEAD

cat <<HEAD2
<div class="header">
  <h1>Design System Preview</h1>
  <div class="meta">Generated from <code>design-system.config.css</code></div>
HEAD2

if [ -n "$TONE" ]; then
  echo "<p><strong>Tone</strong>: $TONE</p>"
fi
if [ -n "$DIFF" ]; then
  echo "<p><strong>Differentiation</strong>: $DIFF</p>"
fi
if [ -n "$ANTI" ]; then
  echo "<div class=\"anti\"><strong>Anti-direction</strong>: $ANTI</div>"
fi

echo "</div>"

# COLORS
echo "<h2>Color tokens</h2>"
if [ -n "$COLORS" ]; then
  echo "<div class=\"grid\">"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    NAME="${line%%|*}"; VAL="${line#*|}"
    swatch_color "$NAME" "$VAL"
  done <<< "$COLORS"
  echo "</div>"
else
  echo "<div class=\"empty\">no --color-* tokens detected</div>"
fi

# TYPOGRAPHY
echo "<h2>Typography tokens</h2>"
if [ -n "$FONTS" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    NAME="${line%%|*}"; VAL="${line#*|}"
    cat <<TYP
<div class="typography-sample">
  <div class="label">${NAME} → ${VAL}</div>
  <div style="font-family: ${VAL}; font-size: 28px;">The quick brown fox jumps over the lazy dog</div>
  <div style="font-family: ${VAL}; font-size: 14px; color: #555; margin-top: 6px;">Body sample · 0123456789 · MMxx — 一意の文字</div>
</div>
TYP
  done <<< "$FONTS"
else
  echo "<div class=\"empty\">no --font-* tokens detected</div>"
fi

# MOTION
echo "<h2>Motion (duration)</h2>"
if [ -n "$MOTION" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    NAME="${line%%|*}"; VAL="${line#*|}"
    swatch_text "$NAME" "$VAL"
  done <<< "$MOTION"
else
  echo "<div class=\"empty\">no --motion-* / --duration-* tokens detected</div>"
fi

# EASING
echo "<h2>Easing</h2>"
if [ -n "$EASES" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    NAME="${line%%|*}"; VAL="${line#*|}"
    swatch_text "$NAME" "$VAL"
  done <<< "$EASES"
else
  echo "<div class=\"empty\">no --ease-* tokens detected</div>"
fi

# SHADOWS
echo "<h2>Shadow tokens</h2>"
if [ -n "$SHADOWS" ]; then
  echo "<div class=\"grid\">"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    NAME="${line%%|*}"; VAL="${line#*|}"
    swatch_shadow "$NAME" "$VAL"
  done <<< "$SHADOWS"
  echo "</div>"
else
  echo "<div class=\"empty\">no --shadow-* tokens detected</div>"
fi

# SPACING
echo "<h2>Spacing scale</h2>"
if [ -n "$SPACINGS" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    NAME="${line%%|*}"; VAL="${line#*|}"
    swatch_text "$NAME" "$VAL"
  done <<< "$SPACINGS"
else
  echo "<div class=\"empty\">no --spacing-* tokens detected</div>"
fi

# RADIUS
echo "<h2>Radius scale</h2>"
if [ -n "$RADIUS" ]; then
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    NAME="${line%%|*}"; VAL="${line#*|}"
    swatch_text "$NAME" "$VAL"
  done <<< "$RADIUS"
else
  echo "<div class=\"empty\">no --radius-* tokens detected</div>"
fi

cat <<TAIL
<h2>About this preview</h2>
<p class="meta">This static page was generated by ai-design-system <code>preview-tokens.sh</code>.
It is a quick visual check of token coverage and aesthetic — not a Storybook. Re-run after token edits.</p>
</body>
</html>
TAIL
} > "$OUT"

echo "Generated: $OUT"
echo "Open with: open '$OUT'"
