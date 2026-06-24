#!/opt/homebrew/opt/python@3.11/bin/python3.11
"""Round 2: 5 fresh-angle pins targeting gift, paleo, anti-inflammatory,
Mother's Day, Christmas pre-order. Same plumbing as post_pinterest_pins.py
but reads its own log so already-pinned() doesn't false-skip."""
import sys, os, time, json, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from cdp import CDP, list_pages, PORT

LINK = "https://www.cochoy.fr/aoba/shop.html"
LOG = os.path.join(REPO, "data", "pinterest_log.csv")
os.makedirs(os.path.dirname(LOG), exist_ok=True)

PINS = [
    ("img/gift-box.jpg",
     "Matcha gift jar — clean ingredients, no palm oil",
     "Aoba matcha spread: tender first-pick Uji matcha, organic cocoa butter, raw wildflower honey, sea salt. Tied in linen, ready to gift. No palm oil. No refined sugar.\n\n#giftideas #foodiegift #matcha #matchagift #hostessgift #cleanlabel #organicgift #thinkingofyou #gourmetgift #smallbatch"),
    ("img/paleo-plate.jpg",
     "Paleo matcha spread — honey, cocoa butter, no seed oils",
     "A paleo-friendly matcha spread sweetened with raw honey. Cocoa butter, no seed oils, no refined sugar, no grains. Perfect on fruit, in yogurt, or off a spoon.\n\n#paleo #paleorecipes #paleobreakfast #paleofriendly #seedoilfree #honeysweetened #matcha #cleaneating #realfood #nograins"),
    ("img/antiinflam-still.jpg",
     "Anti-inflammatory pantry staple — matcha spread",
     "Matcha is rich in EGCG; raw honey carries its own anti-inflammatory profile. Aoba folds them into cocoa butter — no seed oils, no refined sugar, no additives.\n\n#antiinflammatory #wellnessroutine #cleaneating #pantrystaples #matcha #egcg #honeyhealing #functionalfood #wholefood #wellness"),
    ("img/mothersday-tray.jpg",
     "Mother's Day breakfast-in-bed: matcha spread & croissant",
     "Warm croissant, a fresh ceramic cup of tea, a small jar of Aoba matcha spread on the tray. A clean-label breakfast that actually shows up.\n\n#mothersday #mothersdaygift #breakfastinbed #brunchideas #mothersdaybreakfast #matcha #brunch #foodiegift #cleanlabel #momlife"),
    ("img/xmas-anticipate.jpg",
     "Christmas pre-order — matcha spread in linen & twine",
     "Small-batch matcha spread, finished by hand, tied in twine. Pre-order the holiday batch — sign up and we'll write you the moment the next run is ready.\n\n#christmasgift #holidaygift #preorder #stockingstuffer #foodiegift #matcha #christmasbaking #handmadegift #smallbatch #giftguide"),
]

def already_pinned(image):
    if not os.path.exists(LOG): return False
    import csv
    with open(LOG) as f:
        for row in csv.DictReader(f):
            if row["image"] == image and row["status"] in ("published","publish_unverified"):
                return True
    return False

def log_result(image, status, error=""):
    import csv, datetime
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["timestamp","image","status","error"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), image, status, error[:200]])

def new_tab(url):
    req = urllib.request.Request(f"http://localhost:{PORT}/json/new?{url}", method="PUT")
    urllib.request.urlopen(req, timeout=5).read()

def close_tab(target_id):
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/json/close/{target_id}", timeout=5).read()
    except Exception:
        pass

def wait_for(c, js, timeout=20, label=""):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if c.evaluate(js): return True
        except Exception:
            pass
        time.sleep(0.5)
    print(f"  ! wait timeout: {label}")
    return False

def main():
    published = skipped = failed = 0
    for img, title, desc in PINS:
        if already_pinned(img):
            print(f"--- skip {img} (already pinned)"); skipped += 1; continue
        img_path = os.path.abspath(os.path.join(REPO, img))
        if not os.path.exists(img_path):
            print(f"  ! missing file {img_path}"); log_result(img, "missing_file"); failed += 1; continue

        print(f"\n=== {img} ===")

        c = None
        page = None
        for attempt in range(3):
            pages_all = list_pages()
            pin_pages = [p for p in pages_all if "pinterest" in p.get("url","")]
            for p in pin_pages:
                if "/pin/" in p.get("url","") and "creation-tool" not in p.get("url",""):
                    close_tab(p["id"])
            pages_all = list_pages()
            pin_pages = [p for p in pages_all if "pinterest" in p.get("url","")]
            if not pin_pages:
                new_tab("https://www.pinterest.com/pin-creation-tool/")
                time.sleep(3); continue
            page = next((p for p in pin_pages if "pin-creation-tool" in p.get("url","")), pin_pages[0])
            try:
                c = CDP(page=page); break
            except Exception:
                time.sleep(1); continue
        if c is None:
            print("  ! attach fail"); log_result(img, "cdp_attach_err"); failed += 1; continue

        c.goto("about:blank"); c.wait_load(timeout=10); time.sleep(1)
        c.goto("https://www.pinterest.com/pin-creation-tool/")
        c.wait_load(timeout=20); time.sleep(4)

        if not wait_for(c, "document.querySelectorAll('input[type=file]').length > 0", timeout=15, label="file input"):
            log_result(img, "no_file_input"); failed += 1; close_tab(page["id"]); continue

        try:
            r = c.send("DOM.getDocument", depth=-1)
            root_id = r["root"]["nodeId"]
            q = c.send("DOM.querySelector", nodeId=root_id, selector="input[type=file]")
            ni = q.get("nodeId")
            if not ni: log_result(img, "no_file_node"); failed += 1; close_tab(page["id"]); continue
            c.send("DOM.setFileInputFiles", files=[img_path], nodeId=ni)
            print(f"  uploaded {img_path}")
        except Exception as e:
            log_result(img, "upload_err", str(e)); failed += 1; close_tab(page["id"]); continue

        if not wait_for(c, "[...document.querySelectorAll('input')].some(i=>i.placeholder&&/Parlez-nous|Tell us|Title/i.test(i.placeholder))", timeout=25, label="title input"):
            log_result(img, "no_title_input"); failed += 1; close_tab(page["id"]); continue

        fill = """(function(t, d, l){
          function setI(el, v){const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;el.focus();s.call(el,v);el.dispatchEvent(new InputEvent('input',{bubbles:true,data:v,inputType:'insertFromPaste'}));el.dispatchEvent(new Event('change',{bubbles:true}));}
          function setE(el, v){el.focus();document.execCommand('insertText',false,v);}
          const inputs=[...document.querySelectorAll('input')];
          const tEl=inputs.find(i=>i.placeholder&&/Parlez-nous|Tell us|Title/i.test(i.placeholder));
          const lEl=inputs.find(i=>i.placeholder&&/Ajouter un lien|Add a link/i.test(i.placeholder));
          const dEl=[...document.querySelectorAll('[contenteditable=true]')].find(x=>(x.getAttribute('aria-label')||'').match(/Décrivez|Tell|Description/i))||[...document.querySelectorAll('[contenteditable=true]')][0];
          if(tEl) setI(tEl,t);
          if(lEl) setI(lEl,l);
          if(dEl) setE(dEl,d);
          return JSON.stringify({t:!!tEl,d:!!dEl,l:!!lEl});
        })(""" + json.dumps(title) + "," + json.dumps(desc) + "," + json.dumps(LINK) + ")"
        print("  filled:", c.evaluate(fill))
        time.sleep(1.5)

        clicked = c.evaluate("(function(){const b=[...document.querySelectorAll('button')].find(x=>/^Publier|^Publish/i.test(x.textContent.trim()));if(b){b.click();return true}return false})()")
        if not clicked:
            log_result(img, "no_publish_btn"); failed += 1; close_tab(page["id"]); continue
        time.sleep(7)
        ok = c.evaluate("/Épingle publiée|Pin saved|published/i.test(document.body.textContent)")
        if ok:
            log_result(img, "published"); published += 1
            print("  ✓ published")
        else:
            log_result(img, "publish_unverified"); failed += 1
            print("  ✗ unverified")
        time.sleep(1)
        close_tab(page["id"])

    print(f"\nDone. published={published} skipped={skipped} failed={failed}")

if __name__ == "__main__":
    main()
