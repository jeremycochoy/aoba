#!/opt/homebrew/opt/python@3.11/bin/python3.11
"""Bulk-post Aoba pins to Pinterest via the logged-in :9340 Chrome.

Each pin: image, title, description (with hashtags), link to shop.html.
Forces a clean page load between iterations so Pinterest's SPA doesn't
re-use stale DOM (which kills the file input).
"""
import sys, os, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from cdp import CDP, list_pages

LINK = "https://www.cochoy.fr/aoba/shop.html"
LOG = os.path.join(REPO, "data", "pinterest_log.csv")
os.makedirs(os.path.dirname(LOG), exist_ok=True)

PINS = [
    ("img/hero-jar.jpg",
     "Matcha spread without palm oil — Aoba 青葉",
     "Aoba is an organic matcha spread of cocoa butter, raw wildflower honey, tender first-pick Uji matcha, and a pinch of sea salt. No palm oil. No refined sugar. No bitterness — only the soft green of the first leaves. Tastes like white chocolate and matcha, but made of the real thing.\n\n#matcha #matchaspread #cleaneating #palmoilfree #realfood #organicfood #ujimatcha #honeysweetened #smallbatch #greenrecipes"),
    ("img/t-a-ingredients.jpg",
     "Four-ingredient matcha spread — no palm oil",
     "Aoba is built on four ingredients: tender first-pick Uji matcha, organic cocoa butter, raw wildflower honey, sea salt. No palm oil. No refined sugar. No additives. The whole label fits on a postcard.\n\n#matcha #cleaneating #cleanlabel #palmoilfree #realfood #noaddedsugar #organicfood #pantrystaples"),
    ("img/t-a-jar-pour.jpg",
     "Matcha spread, honey-sweetened, no palm oil",
     "Cocoa butter, raw honey, Uji matcha. That's the whole jar. No palm oil. No emulsifiers. No stabilisers.\n\n#matcha #palmoilfree #cleanlabel #realfood #organicfood #honeysweetened #spreadable #matcharecipe"),
    ("img/t-b-chasen.jpg",
     "Uji matcha, made into a spread",
     "A spread that tastes like the matcha you drink. Single-origin Uji matcha, stone-ground, picked when the leaves are young and light.\n\n#ujimatcha #matcha #matchaspread #greentea #japanesematcha #craftsmanship"),
    ("img/t-b-uji.jpg",
     "Single-origin Uji matcha — Aoba spread",
     "Matcha from a single Uji farm. Picked tender. Stone-ground. Sealed under nitrogen. Then folded into cocoa butter and honey.\n\n#ujimatcha #matchasourcing #japanesetea #matcha #matchaspread #craftsmanship #firstharvest"),
    ("img/t-c-toast.jpg",
     "Healthy matcha spread on toast (kids ask for seconds)",
     "A green spread your kids will actually beg for. Honey, not refined sugar. Cocoa butter, not palm oil. Real matcha green, not food dye.\n\n#momlife #kidsfood #healthysnacks #healthyforkids #toast #breakfastideas #nopalmoil #realfood #matchatoast"),
    ("img/t-c-lunchbox.jpg",
     "Matcha lunchbox idea — clean ingredients",
     "Brioche slices, a layer of Aoba, strawberries, blueberries. Three ingredients on the plate, no hidden seed oils, no food dye, no negotiating.\n\n#lunchbox #kidsfood #healthysnacks #momlife #breakfastideas #realfood #nopalmoil #afterschoolsnack"),
    ("img/t-d-yogurt.jpg",
     "Greek yogurt + matcha spread (no seed oils)",
     "Greek yogurt + a spoonful of Aoba: tender Uji matcha, cocoa butter, raw honey. Real fat, real protein, real sugar — no proprietary blend, no maltitol, no flavourings.\n\n#realfood #seedoilfree #wellness #honeysweetened #greekyogurt #breakfast #cleaneating #matcha #fuelyourbody"),
    ("img/t-d-macros.jpg",
     "Matcha spread macros — real food, no seed oils",
     "Per tablespoon: ~95 cal, 8g cocoa-butter fat, 6g carbs from raw honey, 0g added sugar. Three rules: real fat, real sugar, real flavour.\n\n#realfood #seedoilfree #honeysweetened #wellness #macros #cleaneating #nutrition #fuelyourbody"),
    ("img/t-e-croissant.jpg",
     "Matcha croissant filling recipe",
     "Warm croissant, sliced. Half a spoonful of Aoba in the fold. Butter on one side, cocoa butter on the other, honey and matcha meeting in the middle.\n\n#croissant #matcha #brunch #foodphotography #matcharecipe #f52grams #weekendbreakfast #bakingfromscratch"),
    ("img/t-e-cookie.jpg",
     "Matcha sandwich cookies — recipe idea",
     "Brown-butter sablé cookies, sandwiched with a generous layer of Aoba matcha spread.\n\n#cookies #matcha #matcharecipe #dessertstagram #bakingfromscratch #sandwichcookies #foodphotography"),
    ("img/t-e-swirl.jpg",
     "Matcha spread on sourdough toast",
     "A slice of warm sourdough, generously covered in Aoba. Honey-sweet, never sugar-sweet. Real cocoa butter, no palm oil.\n\n#toast #sourdough #breakfast #matcha #cleanlabel #honeysweetened #realfood #morningroutine"),
    ("img/grid-2.jpg",
     "Matcha spread on sourdough — clean morning",
     "Sourdough toast, full pour of Aoba. Cocoa butter melts in. Honey settles. Matcha stays green. A complete breakfast in four ingredients.\n\n#toast #sourdough #breakfastideas #matcha #cleanlabel #honeysweetened #realfood #morningroutine"),
    ("img/grid-3.jpg",
     "Matcha brioche with strawberries — Aoba spread",
     "Two slices of toasted brioche, a layer of Aoba matcha spread, fresh strawberries. A breakfast that looks like it took skill and didn't.\n\n#brioche #breakfast #matcha #strawberries #brunch #foodphotography #weekendbreakfast"),
]

def already_pinned(image):
    if not os.path.exists(LOG): return False
    import csv
    with open(LOG) as f:
        for row in csv.DictReader(f):
            if row["image"] == image and row["status"] == "published":
                return True
    return False

def log_result(image, status, error=""):
    import csv, datetime
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["timestamp","image","status","error"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), image, status, error[:200]])

def wait_for(c, js_check, timeout=20, label="condition"):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if c.evaluate(js_check):
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print(f"  ! timeout waiting for: {label}")
    return False

def main():
    pages = [p for p in list_pages() if "pinterest" in p.get("url","")]
    if not pages:
        print("No Pinterest tab open. Start with Chrome on :9340 logged into Pinterest.")
        sys.exit(2)
    c = CDP(page=pages[0])
    c.send("Page.bringToFront")
    time.sleep(1)

    published = 0
    skipped = 0
    failed = 0

    for img, title, desc in PINS:
        if already_pinned(img):
            print(f"--- skip {img} (already pinned) ---")
            skipped += 1
            continue

        img_path = os.path.abspath(os.path.join(REPO, img))
        if not os.path.exists(img_path):
            print(f"--- skip {img} (missing) ---")
            log_result(img, "missing_file")
            continue

        print(f"\n=== {img} ===")
        # Force a clean nav each time — Pinterest's SPA doesn't reset DOM otherwise
        c.goto(f"https://www.pinterest.com/pin-creation-tool/?n={int(time.time()*1000)}")
        c.wait_load(timeout=20)
        time.sleep(3)
        if not wait_for(c, "document.querySelectorAll('input[type=file]').length > 0", timeout=15, label="file input"):
            log_result(img, "no_file_input"); failed += 1; continue

        try:
            r = c.send("DOM.getDocument", depth=-1)
            root_id = r["root"]["nodeId"]
            q = c.send("DOM.querySelector", nodeId=root_id, selector="input[type=file]")
            ni = q.get("nodeId")
            if not ni: log_result(img, "no_file_input_node"); failed += 1; continue
            c.send("DOM.setFileInputFiles", files=[img_path], nodeId=ni)
            print(f"  uploaded")
        except Exception as e:
            log_result(img, "upload_err", str(e)); failed += 1; continue

        # Wait for title input to appear (means upload was processed)
        if not wait_for(c, "[...document.querySelectorAll('input')].some(i=>i.placeholder&&/Parlez-nous|Tell us|Title/i.test(i.placeholder))", timeout=20, label="title input"):
            log_result(img, "no_title_input"); failed += 1; continue

        fill = """(function(t, d, l){
          function setI(el, v){const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;el.focus();s.call(el,v);el.dispatchEvent(new InputEvent('input',{bubbles:true,data:v,inputType:'insertFromPaste'}));el.dispatchEvent(new Event('change',{bubbles:true}));}
          function setE(el, v){el.focus();document.execCommand('insertText',false,v);}
          const inputs=[...document.querySelectorAll('input')];
          const tEl=inputs.find(i=>i.placeholder&&/Parlez-nous|Tell us|Title/i.test(i.placeholder));
          const lEl=inputs.find(i=>i.placeholder&&/Ajouter un lien|Add a link|destination link/i.test(i.placeholder));
          const dEl=[...document.querySelectorAll('[contenteditable=true]')].find(x=>(x.getAttribute('aria-label')||'').match(/Décrivez|Tell|Description/i))||[...document.querySelectorAll('[contenteditable=true]')][0];
          if(tEl) setI(tEl,t);
          if(lEl) setI(lEl,l);
          if(dEl) setE(dEl,d);
          return JSON.stringify({t:!!tEl,d:!!dEl,l:!!lEl});
        })(""" + json.dumps(title) + "," + json.dumps(desc) + "," + json.dumps(LINK) + ")"
        print("  filled:", c.evaluate(fill))
        time.sleep(1.5)

        clicked = c.evaluate("(function(){const b=[...document.querySelectorAll('button')].find(x=>/^Publier|^Publish/i.test(x.textContent.trim()));if(b){b.click();return true}return false})()")
        if not clicked: log_result(img, "no_publish_btn"); failed += 1; continue
        time.sleep(7)
        ok = c.evaluate("/Épingle publiée|Pin saved|published|saved/i.test(document.body.textContent)")
        if ok:
            log_result(img, "published")
            published += 1
            print("  ✓ published")
        else:
            log_result(img, "publish_unverified")
            failed += 1
            print("  ✗ unverified (may have published anyway)")
        time.sleep(2)

    print(f"\n\nDone. published={published} skipped={skipped} failed={failed}")

if __name__ == "__main__":
    main()
