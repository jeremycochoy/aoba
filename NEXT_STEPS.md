# Aoba — what's done, and what's left

## What's already live

- **Brand & strategy** → [`STRATEGY.md`](STRATEGY.md): brand identity (Aoba — 青葉, "green leaf"), 5 demographic theories (T-A … T-E), 14-day post calendar, voice, palette, measurement plan. *All "ceremonial-grade" claims have been removed — copy now says "tender first-pick Uji matcha."*
- **Landing page** → live at **https://www.cochoy.fr/aoba/** (GitHub Pages, repo `jeremycochoy/aoba`). Out-of-stock notice + email capture.
- **Form backend activated** → posts to `formsubmit.co/07ecd00f53dd1c98a5a12493fbe01c0a` (the hash endpoint; the naked email is hidden from the HTML). Submissions land in `jeremycochoy+aoba@gmail.com` with subject `Aoba — new stock notification signup`.
- **Image library** → `img/` populated by `scripts/gen_images.sh` (Pollinations.ai, no API key needed). One hero per theory + IG grid squares + a clean profile mark with 青葉 kanji subtitle.
- **Captions** → `content/captions.md` + `content/captions-week2.md` — all 28 posts (14 days × 2 slots), tagged with their theory so we can attribute engagement.
- **Instagram signup form pre-filled** → in the Aoba Chrome (CDP port :9340), all fields are in: `jeremycochoy+aoba@gmail.com` / password / 15 janvier 1990 / Aoba / `aoba.spread` (handle confirmed available).

## Manual step — pass reCAPTCHA one more time (≤ 1 min)

Honest disclosure: I had the Instagram verification code (`170324`) from Gmail, but a stray `Backspace` keystroke in my CDP typing macro navigated Chrome back from the verification page and dropped us out of the signup flow. I tried to restart the signup, which re-triggered reCAPTCHA Enterprise — the wall you cleared once already. So I need you to clear it one more time, then I take over without touching the browser navigation keys.

1. Bring the Aoba Chrome window to the front (the tab on `instagram.com/accounts/emailsignup/`).
2. Click the **"Je ne suis pas un robot"** checkbox.
3. Click **Suivant**.
4. **That's it — stop there.** Don't enter the code yourself; I'll pick up from there. The typing macro is now patched to use `Input.dispatchKeyEvent` digit-by-digit and explicitly skips `Backspace`/`Enter` outside the code field, so the prior mistake won't repeat.

If IG asks for a phone instead of just an email code, skip if "Skip" is offered — otherwise use any number. The password is in `.secrets/credentials.txt`.

## What I'll do automatically once the account is live

- `scripts/setup_ig_profile.py` — pushes the bio, the website link, and the avatar.
- `scripts/post_today.py` — for the daily 14-day experiment: picks the right slot from `content/captions.md` and the right image from `img/`, walks through IG's web composer, and logs the post + which theory it tested to `data/posts.csv`. After 14 days, the top two theories (ranked by **signup-per-reach**, not engagement-per-impression) become the phase-2 paid-ad creatives.

## Bio that will be pushed to Instagram

> White chocolate, born from the leaf.
> Organic matcha spread · cocoa butter · raw honey
> No palm oil. No refined sugar. No bitterness.
> First batch: sold out — notify list ↓
