#!/usr/bin/env bash
# Generate product/marketing imagery for Matchaé via Pollinations.ai (free, no auth).
# All outputs go to img/ — overwrites are fine; reruns are idempotent per filename.
set -uo pipefail

OUT="${1:-img}"
mkdir -p "$OUT"

# helper: urlencode via python (always present on macOS)
enc(){ python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"; }

# helper: fetch one image. args: filename, w, h, seed, model, prompt
fetch(){
  local name="$1" w="$2" h="$3" seed="$4" model="$5" prompt="$6"
  local enc_p; enc_p=$(enc "$prompt")
  local url="https://image.pollinations.ai/prompt/${enc_p}?width=${w}&height=${h}&model=${model}&seed=${seed}&nologo=true&enhance=true"
  echo "→ $name"
  curl -sS -o "$OUT/$name" "$url" || { echo "  FAIL"; return 1; }
  # verify size > 5KB (Pollinations sometimes returns an error png)
  local sz; sz=$(stat -f%z "$OUT/$name" 2>/dev/null || echo 0)
  if [ "$sz" -lt 5000 ]; then echo "  too small ($sz B), retrying once"; sleep 2; curl -sS -o "$OUT/$name" "$url" || true; fi
  echo "  saved ($(stat -f%z "$OUT/$name" 2>/dev/null) B)"
}

# ---- HERO (landing page) ----
fetch hero-jar.jpg 1200 1500 11 flux \
"editorial product photograph of an open glass jar of bright matcha-green spread, soft silky texture catching warm side light, jar resting on a cream linen cloth, a wooden spoon dripping the green spread, ceremonial matcha powder dusted around, raw honeycomb fragment, blocks of cocoa butter, dark wood surface, soft natural morning window light, shallow depth of field, premium minimal brand aesthetic, no text, no labels, magazine quality, hyperreal, 50mm"

# ---- T-A clean-label ingredients flatlay ----
fetch t-a-ingredients.jpg 1200 1500 22 flux \
"overhead flatlay on white marble, an open glass jar of green matcha spread without any label, next to small piles of ceremonial matcha powder, raw honeycomb chunk, blocks of cocoa butter, tiny pile of sea salt flakes, soft daylight, clean minimal composition, four ingredients laid out plainly, scandinavian editorial food photography, no text"

# ---- T-A side-by-side (we'll add text overlay in CSS for posts) ----
fetch t-a-jar-pour.jpg 1200 1500 33 flux \
"macro photograph of bright matcha-green spread being slowly poured from a wooden spoon back into a clean glass jar, silky thick texture, soft morning light, cream linen background, premium minimal aesthetic, no text"

# ---- T-B matcha aesthete ----
fetch t-b-chasen.jpg 1200 1500 44 flux \
"moody close-up of a bamboo chasen whisk beside a small ceramic bowl of bright green matcha powder and a wooden spoon coated in green spread, single shaft of warm side light, dark wood, japanese wabi-sabi composition, shadows, editorial, no text"

fetch t-b-uji.jpg 1200 1500 55 flux \
"vertical editorial photo, hands of a tea farmer cradling young first-harvest matcha leaves, soft mist, tea field in background, golden hour, cinematic, premium documentary food photography, no text"

# ---- T-C parents/kids ----
fetch t-c-toast.jpg 1200 1500 66 flux \
"a child's hand holding a slice of sourdough toast spread thickly with bright green matcha spread, drips, bright kitchen window light, white plate, joyful warm tones, lifestyle food photography, friendly and homey, no text"

fetch t-c-lunchbox.jpg 1200 1500 77 flux \
"flatlay of a children's bento lunchbox with slices of brioche spread with bright matcha-green spread, slices of strawberry, blueberries, cream background, top-down, bright cheerful tones, no text"

# ---- T-D wellness/fitness ----
fetch t-d-yogurt.jpg 1200 1500 88 flux \
"overhead shot of a ceramic bowl of thick greek yogurt topped with a generous swirl of bright matcha-green spread, sliced banana, granola, on a kitchen counter, bright morning light, clean wellness aesthetic, no text"

fetch t-d-macros.jpg 1200 1500 99 flux \
"editorial product photograph of an open glass jar of bright green matcha spread on a slate surface beside a sliced sourdough loaf and a bowl of Greek yogurt, clean minimal wellness composition, bright daylight, no text"

# ---- T-E foodie/recipe ----
fetch t-e-croissant.jpg 1200 1500 110 flux \
"macro shot of a golden flaky croissant sliced in half and filled with bright matcha-green spread, oozing slightly, flakes scattered, dark moody background, restaurant food photography, no text"

fetch t-e-cookie.jpg 1200 1500 121 flux \
"a stack of soft chewy cookies with a thick layer of bright matcha-green spread sandwiched between them, melted dripping, warm wooden board, restaurant food photography, no text"

fetch t-e-swirl.jpg 1200 1500 132 flux \
"macro shot of a wooden spoon swirling bright matcha-green spread into thick batter, beautiful green ribbon pattern, baking scene, warm kitchen light, food photography, no text"

# ---- IG square 1:1 hero crops for grid ----
fetch grid-1.jpg 1200 1200 11 flux \
"square crop, editorial product photograph of an open glass jar of bright matcha-green spread, on a cream linen cloth, warm morning light, premium minimal aesthetic, no text"
fetch grid-2.jpg 1200 1200 22 flux \
"square crop, overhead flatlay of bright matcha-green spread on a sourdough toast slice, cream background, daylight, minimal, no text"
fetch grid-3.jpg 1200 1200 33 flux \
"square crop, macro shot of a wooden spoon dripping bright matcha-green spread, cream linen background, soft light, minimal premium aesthetic, no text"

# ---- IG profile photo (square logo-style) ----
fetch profile.jpg 800 800 1 flux \
"premium minimal brand logo aesthetic, the wordmark 'Matchaé' in a thin elegant serif on a cream background, the é accent in matcha green, professional, clean, no other text"

echo "Done. $(ls -1 "$OUT" | wc -l | tr -d ' ') images in $OUT/"
