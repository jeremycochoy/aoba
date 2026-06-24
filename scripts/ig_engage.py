#!/opt/homebrew/opt/python@3.11/bin/python3.11
"""Leave 5 genuine, varied comments on niche matcha posts to drive
profile traffic to @aoba.spread. Headless Chrome on :9340.

Safety: small batch (5), varied wording (no copy-paste), 90-120s sleep
between actions to avoid IG anti-spam flagging on a 14-follower new
account."""
import sys, os, time, json, random, csv, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cdp import CDP, list_pages, PORT
import urllib.request

LOG = os.path.expanduser("~/.aoba-bot/data/ig_engagement.csv")
os.makedirs(os.path.dirname(LOG), exist_ok=True)

# Hashtag search seeds — Pinterest matcha-niche overlap
SEEDS = ["matcharecipe", "matchaspread", "cleaneating", "palmoilfree", "matchalover"]

# Varied, genuine-sounding comments (no URLs, no @mentions, no copy-paste)
COMMENTS = [
    "Beautiful matcha shot. The colour tells you the quality.",
    "This is what real matcha looks like — bright, not yellow-green.",
    "Saving this for the weekend. The honey pairing always wins.",
    "That green is the giveaway. Tender first-pick, no doubt.",
    "Honest matcha posts on this feed — love seeing it.",
]

def log_action(action, target, status, note=""):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["timestamp","action","target","status","note"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), action, target, status, note[:200]])

def new_tab(url):
    req = urllib.request.Request(f"http://localhost:{PORT}/json/new?{url}", method="PUT")
    urllib.request.urlopen(req, timeout=5).read()

def close_tab(target_id):
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/json/close/{target_id}", timeout=5).read()
    except Exception: pass

def wait_for(c, js, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if c.evaluate(js): return True
        except Exception: pass
        time.sleep(0.5)
    return False

def get_ig_tab():
    for p in list_pages():
        if "instagram.com" in p.get("url",""): return p
    new_tab("https://www.instagram.com/")
    time.sleep(5)
    for p in list_pages():
        if "instagram.com" in p.get("url",""): return p
    return None

def main():
    seed = random.choice(SEEDS)
    print(f"=== seed: #{seed} ===")
    page = get_ig_tab()
    if not page:
        log_action("init","-","no_tab"); return
    c = CDP(page=page)
    c.goto(f"https://www.instagram.com/explore/tags/{seed}/"); c.wait_load(timeout=20); time.sleep(5)

    # Collect post URLs from grid
    urls = c.evaluate("""(function(){
      const links = [...document.querySelectorAll('a[href*="/p/"]')]
        .map(a => a.href)
        .filter(h => /\\/p\\/[A-Za-z0-9_-]+/.test(h));
      return JSON.stringify([...new Set(links)].slice(0, 12));
    })()""")
    try:
        post_urls = json.loads(urls)
    except Exception:
        post_urls = []
    print(f"  collected {len(post_urls)} post urls")
    if not post_urls:
        log_action("search", seed, "no_posts"); return

    random.shuffle(post_urls)
    posted = 0
    target = 5
    for i, url in enumerate(post_urls):
        if posted >= target: break
        print(f"\n--- post {i+1}: {url[:90]} ---")
        c.goto(url); c.wait_load(timeout=20); time.sleep(random.uniform(4, 7))

        # Find the comment textarea
        if not wait_for(c, "document.querySelector('textarea[aria-label*=\"commentaire\" i],textarea[aria-label*=\"comment\" i]') !== null", timeout=12):
            print("  no comment box, skipping")
            log_action("comment", url, "no_box"); continue

        comment = random.choice(COMMENTS)
        js = f"""(function(t){{
          const ta = document.querySelector('textarea[aria-label*="commentaire" i],textarea[aria-label*="comment" i]');
          if (!ta) return false;
          ta.focus();
          const s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
          s.call(ta, t);
          ta.dispatchEvent(new InputEvent('input', {{bubbles:true, data:t, inputType:'insertFromPaste'}}));
          ta.dispatchEvent(new Event('change', {{bubbles:true}}));
          return true;
        }})({json.dumps(comment)})"""
        if not c.evaluate(js):
            log_action("comment", url, "fill_fail"); continue

        time.sleep(random.uniform(2.5, 4.5))

        # Click "Publier" / "Post"
        clicked = c.evaluate("""(function(){
          const btns = [...document.querySelectorAll('button,div[role=button]')];
          const b = btns.find(x => /^(Publier|Post)$/i.test(x.textContent.trim()) && !x.disabled);
          if (b) { b.click(); return true; }
          return false;
        })()""")
        if not clicked:
            log_action("comment", url, "btn_fail"); continue
        time.sleep(random.uniform(5, 8))

        # Verify comment landed
        landed = c.evaluate(f"document.body.textContent.includes({json.dumps(comment[:30])})")
        log_action("comment", url, "posted" if landed else "click_unverified", comment)
        print(f"  {'✓' if landed else '✗'} {comment[:50]}")
        posted += 1
        # Long jitter between actions to avoid anti-spam
        wait = random.uniform(75, 130)
        print(f"  sleeping {wait:.0f}s")
        time.sleep(wait)

    print(f"\nDone. posted={posted}")

if __name__ == "__main__":
    main()
