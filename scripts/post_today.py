#!/opt/homebrew/opt/python@3.11/bin/python3.11
"""Post today's Aoba Instagram slot autonomously. See top-of-file docstring."""
import os, sys, csv, re, time, json, argparse, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

CAPTIONS = [os.path.join(REPO, "content", "captions.md"), os.path.join(REPO, "content", "captions-week2.md")]
POSTS_CSV = os.path.join(REPO, "data", "posts.csv")
LAUNCH_DATE = datetime.date(2026, 6, 22)
IG_FLAG = os.path.join(REPO, "data", ".ig_active")

def parse_captions():
    out = []
    rx = re.compile(r"^## Day (\d+) — Slot (\d+) \((T-[A-Z])\)[^`]*`([^`]+)`(.*?)(?=\n## Day |\Z)",
                    re.MULTILINE | re.DOTALL)
    for f in CAPTIONS:
        if not os.path.exists(f): continue
        for m in rx.finditer(open(f).read()):
            day, slot, theory, img, body = m.groups()
            body = body.strip()
            body = re.sub(r"^\([^)]*\)\s*", "", body)
            body = re.sub(r"^\*\*Caption[^*]*\*\*\s*", "", body, flags=re.DOTALL)
            parts = [p.strip() for p in body.split("\n\n")]
            hashtags = parts[-1] if parts and parts[-1].startswith("#") else ""
            cap = "\n\n".join(parts[:-1]) if hashtags else body
            out.append(dict(day=int(day), slot=int(slot), theory=theory, image=img,
                            caption=cap.strip(), hashtags=hashtags.strip()))
    return out

def already_posted(day, slot):
    if not os.path.exists(POSTS_CSV): return False
    return any(int(r["day"])==day and int(r["slot"])==slot and r.get("status","")=="shared"
               for r in csv.DictReader(open(POSTS_CSV)))

def record(post, status):
    os.makedirs(os.path.dirname(POSTS_CSV), exist_ok=True)
    new = not os.path.exists(POSTS_CSV)
    with open(POSTS_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["timestamp","day","slot","theory","image","caption_hook","status"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), post["day"], post["slot"],
                    post["theory"], post["image"], post["caption"].splitlines()[0][:60], status])

def today_day():
    return (datetime.date.today() - LAUNCH_DATE).days + 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", type=int); ap.add_argument("--day", type=int); ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    if not args.dry and not os.path.exists(IG_FLAG):
        print(f"IG account not flagged active. (touch {IG_FLAG} once logged in.)"); return

    day = args.day or today_day()
    if day < 1 or day > 14:
        print(f"Day {day} outside 1..14 campaign window."); return

    posts = [p for p in parse_captions() if p["day"] == day]
    if args.slot:
        posts = [p for p in posts if p["slot"] == args.slot]
    posts = [p for p in posts if not already_posted(p["day"], p["slot"])]
    if not posts:
        print(f"Day {day}: all slots already posted."); return

    post = posts[0]
    img_path = os.path.abspath(os.path.join(REPO, post["image"]))
    print(f"Day {post['day']} Slot {post['slot']} — theory {post['theory']}")
    print(f"  image: {img_path}")
    print(f"  first line: {post['caption'].splitlines()[0][:80]}")
    if args.dry: return

    from cdp import CDP, list_pages
    pages = list_pages()
    if not pages:
        record(post, "no_chrome"); sys.exit(2)
    ig = [p for p in pages if "instagram.com" in p.get("url","")]
    c = CDP(page=ig[0] if ig else pages[0])
    c.goto("https://www.instagram.com/"); c.wait_load(); time.sleep(3)

    # Open the composer (Create → Publication)
    c.evaluate("(function(){const e=[...document.querySelectorAll('a,div[role=button],span')].find(x=>{const t=x.textContent.trim();return (t==='Créer'||t==='Create')&&t.length<10});if(e)e.click();return !!e})()")
    time.sleep(2)
    c.evaluate("(function(){const e=[...document.querySelectorAll('a,div[role=button],span')].find(x=>/^Publication|^Post$/i.test(x.textContent.trim()));if(e)e.click();return !!e})()")
    time.sleep(3)

    # Set the file via CDP DOM.setFileInputFiles (bypasses native picker)
    try:
        r = c.send("DOM.getDocument", depth=-1)
        root_id = r["root"]["nodeId"]
        q = c.send("DOM.querySelector", nodeId=root_id, selector="input[type=file]")
        ni = q.get("nodeId")
        if not ni:
            record(post, "no_file_input"); sys.exit(3)
        c.send("DOM.setFileInputFiles", files=[img_path], nodeId=ni)
        print("uploaded image via CDP")
    except Exception as e:
        record(post, f"file_err:{e}"); sys.exit(4)
    time.sleep(4)

    # Two "Suivant" clicks: crop step → caption step
    for _ in range(2):
        c.evaluate("(function(){const e=[...document.querySelectorAll('div[role=button],button')].find(x=>/^Suivant|^Next$/i.test(x.textContent.trim()));if(e)e.click();return !!e})()")
        time.sleep(2.5)

    # Type caption (last contenteditable is the caption box)
    full = post["caption"] + ("\n\n" + post["hashtags"] if post["hashtags"] else "")
    c.evaluate("(function(t){const xs=[...document.querySelectorAll('div[contenteditable=true]')];const e=xs[xs.length-1];if(!e)return false;e.focus();document.execCommand('insertText',false,t);return true})(" + json.dumps(full) + ")")
    time.sleep(2)

    # Final share — MUST click the Partager in the "Créer une publication" dialog header,
    # NOT the share-icon button that opens a share-with-friends overlay. Find by scoping
    # to the create-publication dialog only.
    shared = c.evaluate("""(function(){
      const dialogs = [...document.querySelectorAll('[role=dialog]')];
      const createDlg = dialogs.find(d => /Créer une publication|Create new post/i.test(d.textContent));
      if (!createDlg) return false;
      const btns = [...createDlg.querySelectorAll('button,div[role=button]')];
      // Prefer the topmost Partager (header), not buttons deeper in the body
      const partager = btns.filter(b => /^Partager$|^Share$/i.test(b.textContent.trim()))
                            .sort((a,b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0];
      if (!partager) return false;
      partager.click();
      return true;
    })()""")
    if not shared:
        record(post, "share_btn_missing"); sys.exit(5)
    time.sleep(8)
    ok = c.evaluate("/publication a été partagée|votre publication|your post has been shared|partagée\\./i.test(document.body.textContent)")
    record(post, "shared" if ok else "share_clicked_unverified")
    print("posted" if ok else "shared but unverified")

if __name__ == "__main__":
    main()
