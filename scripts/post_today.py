#!/opt/homebrew/opt/python@3.11/bin/python3.11
"""Post today's Matchaé Instagram post(s) according to the calendar in STRATEGY.md.

Loads the day's slot from content/captions.md, opens Instagram in the Matchaé
Chrome (CDP port :9340), and walks the web composer up to the final "Share"
click — which is left to you, because IG occasionally drops a captcha on
publish for new accounts.

Usage:
  ./scripts/post_today.py            # post the next un-posted slot for today
  ./scripts/post_today.py --slot N   # post the Nth slot from today's calendar
  ./scripts/post_today.py --dry      # show what it would post, no Chrome

Each successful post is appended to data/posts.csv with its theory tag so we
can later attribute engagement to theory.
"""
import os, sys, csv, re, time, argparse, datetime, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cdp import CDP

REPO = os.path.dirname(HERE)
CAPTIONS = os.path.join(REPO, "content", "captions.md")
POSTS_CSV = os.path.join(REPO, "data", "posts.csv")
LAUNCH_DATE = datetime.date(2026, 6, 22)  # day 1

def parse_captions():
    """Yields dicts with keys: day, slot, theory, image, caption, hashtags."""
    text = open(CAPTIONS).read()
    # split on '## Day N — Slot S (T-X) — `img/...`'
    rx = re.compile(r"^## Day (\d+) — Slot (\d+) \((T-[A-Z])\) — `([^`]+)`(.*?)(?=\n## Day |\Z)",
                    re.MULTILINE | re.DOTALL)
    for m in rx.finditer(text):
        day, slot, theory, img, body = m.groups()
        # caption block: skip '**Caption:**' and trailing tag line
        body = body.strip()
        body = re.sub(r"^\*\*Caption.*?\*\*\s*", "", body, flags=re.DOTALL)
        # hashtags line is the last paragraph starting with #
        parts = [p.strip() for p in body.split("\n\n")]
        hashtags = parts[-1] if parts and parts[-1].startswith("#") else ""
        caption_body = "\n\n".join(parts[:-1]) if hashtags else body
        yield dict(day=int(day), slot=int(slot), theory=theory, image=img,
                   caption=caption_body.strip(), hashtags=hashtags.strip())

def already_posted(day, slot):
    if not os.path.exists(POSTS_CSV):
        return False
    with open(POSTS_CSV) as f:
        for row in csv.DictReader(f):
            if int(row["day"]) == day and int(row["slot"]) == slot:
                return True
    return False

def record(post):
    os.makedirs(os.path.dirname(POSTS_CSV), exist_ok=True)
    new = not os.path.exists(POSTS_CSV)
    with open(POSTS_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp","day","slot","theory","image","caption_hook","impressions","reach","profile_visits","link_clicks","follows","email_signups"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                    post["day"], post["slot"], post["theory"], post["image"],
                    post["caption"].splitlines()[0][:60], "", "", "", "", "", ""])

def today_day():
    return (datetime.date.today() - LAUNCH_DATE).days + 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", type=int)
    ap.add_argument("--day", type=int)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    day = args.day or today_day()
    posts = [p for p in parse_captions() if p["day"] == day]
    if not posts:
        print(f"No captions found for day {day}. Check content/captions.md."); sys.exit(1)
    if args.slot:
        posts = [p for p in posts if p["slot"] == args.slot]
    posts = [p for p in posts if not already_posted(p["day"], p["slot"])]
    if not posts:
        print(f"Day {day}: all slots already posted (per data/posts.csv)."); return

    post = posts[0]
    img_path = os.path.abspath(os.path.join(REPO, post["image"]))
    print(f"Day {post['day']} Slot {post['slot']} — theory {post['theory']}")
    print(f"  image: {img_path}")
    print(f"  caption first line: {post['caption'].splitlines()[0][:80]}")
    if args.dry:
        return

    full_caption = post["caption"] + ("\n\n" + post["hashtags"] if post["hashtags"] else "")

    c = CDP()
    c.goto("https://www.instagram.com/")
    c.wait_load()
    time.sleep(2)
    # Click "Create" / "Créer"
    c.evaluate("(function(){const links=[...document.querySelectorAll('a,div[role=button]')];const t=links.find(a=>/Créer|Create/i.test(a.textContent.trim()) && a.textContent.trim().length<15);if(t){t.click();return true}return false})()")
    time.sleep(2)
    c.evaluate("(function(){const links=[...document.querySelectorAll('a,div[role=button]')];const t=links.find(a=>/^Publication|^Post$/i.test(a.textContent.trim()));if(t){t.click();return true}return false})()")
    time.sleep(2)
    print("\nFile picker is now open in the Matchaé Chrome.")
    print("Please drag-drop this image into the picker — Chromium blocks programmatic native file pickers:")
    print(f"  open {img_path}")
    print("\nAfter the image is loaded, return here and press Enter to paste the caption.")
    input()
    # paste caption
    c.evaluate("(function(c){const tas=[...document.querySelectorAll('textarea,div[contenteditable=true]')];const t=tas[tas.length-1];if(!t)return false;t.focus();if(t.tagName==='TEXTAREA'){const s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;s.call(t,c);}else{t.textContent=c;}t.dispatchEvent(new InputEvent('input',{bubbles:true,data:c}));return true})(" + json.dumps(full_caption) + ")")
    print("Caption pasted. Review the post, then click 'Partager' / 'Share' yourself —")
    print("IG sometimes drops a captcha on publish for new accounts.")
    record(post)
    print(f"Logged to {POSTS_CSV}")

if __name__ == "__main__":
    main()
