#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fetch(){
  local out="$1" seed="$2" prompt="$3"
  local enc; enc=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$prompt")
  local url="https://image.pollinations.ai/prompt/${enc}?width=1200&height=1500&model=flux&nologo=true&enhance=true&seed=${seed}"
  echo "→ $out (seed=$seed)"
  curl -sS -A "Mozilla/5.0" -o "$out" "$url" || { echo "  FAIL"; return 1; }
  local sz; sz=$(stat -f%z "$out")
  if [ "$sz" -lt 8000 ]; then
    echo "  too small ($sz), retry with new seed"; sleep 2
    seed=$((seed+1000))
    url="https://image.pollinations.ai/prompt/${enc}?width=1200&height=1500&model=flux&nologo=true&enhance=true&seed=${seed}"
    curl -sS -A "Mozilla/5.0" -o "$out" "$url" || true
  fi
  echo "  $(stat -f%z "$out") B"
}

fetch img/t-a-jar-pour.jpg 4242 \
"close-up still life of an open glass jar of bright matcha-green organic spread on a cream linen cloth, beside the jar a slice of toasted sourdough with green spread on it, a clean small wooden butter knife on the table, soft natural morning window light, premium minimal food photography, hyperreal, magazine quality, no text, no labels, no people"

fetch img/t-b-chasen.jpg 5252 \
"editorial photograph of a small ceramic bowl filled with vibrant green matcha powder beside a clean open glass jar of bright matcha-green spread, on a dark wooden tea table, soft warm side light, japanese wabi-sabi composition, premium minimal food photography, no whisk, no bamboo, no spoon, hyperreal, no text"

fetch img/t-e-swirl.jpg 6363 \
"overhead top-down photograph of a slice of warm sourdough toast generously covered with bright matcha-green spread, next to an open jar of matcha spread, scattered fresh strawberries, on a cream linen background, soft morning light, premium food photography, hyperreal, no text, no people, no spoon, no knife"

fetch img/grid-3.jpg 7474 \
"square overhead photograph of two slices of toasted brioche covered with bright matcha-green spread, fresh sliced strawberries on top, an open jar of matcha-spread nearby, cream linen background, premium minimal food photography, hyperreal, no spoon, no knife, no text, no people"

echo "Done."
