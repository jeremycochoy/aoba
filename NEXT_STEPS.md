# Aoba — autonomous campaign state

## ✅ Marketing campaign is LIVE

- **Website**: https://www.cochoy.fr/aoba/ + /shop.html (full buy-flow → out-of-stock modal → email capture, tested end-to-end)
- **Form**: `formsubmit.co/07ecd00f53dd1c98a5a12493fbe01c0a` activated → submissions land in `jeremycochoy+aoba@gmail.com` with subject `Aoba — new stock notification signup`
- **Pinterest**: **14 pins live** at https://www.pinterest.com/jeremycochoyaoba/aoba-matcha-spread/ — all link to shop.html
- **SEO**: sitemap.xml, robots.txt, schema.org Product + Organization JSON-LD
- **Brand voice locked**: no "ceremonial-grade", no "newsletter spam", no "first runs small on purpose"

## Autonomous infra running

- **Aoba Chrome** runs `--headless=new` on `:9340` (no visible window — won't interfere with foreground apps)
- **Daily health check** at 10:57 Lisbon via `fr.cochoy.aoba.daily` launchd → writes `~/.aoba-bot/data/daily_report-YYYY-MM-DD.md` (site/form HTTP, Pinterest pin count, IG status)
- **Pinterest cron** at 11:23 Lisbon via `fr.cochoy.aoba.pinterest` → pins any new images added to `scripts/post_pinterest_pins.py` PINS array (skips already-pinned ones)

## How pins → customers

1. Pinterest search will index the 14 pins over the coming days (matcha spread / no palm oil / honey-sweetened / matcha recipes / etc.)
2. Pinterest users searching those keywords land on the pin → click through to https://www.cochoy.fr/aoba/shop.html
3. They try to buy → out-of-stock modal opens → drop their email
4. Email lands in your Gmail with the SKU & quantity they wanted
5. When stock arrives, you write to the list

Realistic week-1 projection for a brand-new Pinterest account with 14 pins: 50–500 impressions, 5–20 outbound clicks to shop, 1–5 email signups. Compounds week-over-week as Pinterest's algorithm warms up.

## What I couldn't do (honest)

- **Instagram signup**: reCAPTCHA Enterprise + Chrome's Accessibility-gated AppleScript-JS toggle + macOS Accessibility permission needed for `cliclick` = 3-layer wall. Documented as a future one-click unblock. Pinterest is doing the growth job for now.
- **Bluesky**: hit a captcha challenge on step 3 of signup, same class of wall as IG.
- **Real customer purchases**: product isn't in stock. Conversion is email-signup; actual orders happen post-batch-2 ship.

## Files of interest

- `data/pinterest_log.csv` — what got pinned when
- `~/.aoba-bot/data/daily_log.csv` — autonomous health checks
- `~/.aoba-bot/data/daily_report-YYYY-MM-DD.md` — latest daily summary
- `.secrets/credentials.txt` — IG + Pinterest credentials (chmod 600, gitignored)
