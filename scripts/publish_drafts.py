#!/opt/homebrew/opt/python@3.11/bin/python3.11
"""Pinterest: walk through all saved drafts, set them to the 'Aoba — matcha spread' board, click Publier.

Requires the 'Aoba — matcha spread' board to already exist (created via inline 'Créer un tableau' in the picker).
"""
import sys, os, time, urllib.request, json
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from cdp import CDP, list_pages

BOARD_NAME = "Aoba — matcha spread"

def main():
    # Navigate fresh to drafts
    req = urllib.request.Request("http://localhost:9340/json/new?https://www.pinterest.com/pin-creation-tool/?tab=drafts", method="PUT")
    urllib.request.urlopen(req, timeout=5).read()
    time.sleep(6)
    pages = [p for p in list_pages() if "tab=drafts" in p.get("url","")]
    if not pages: print("no drafts tab"); sys.exit(1)
    c = CDP(page=pages[0])
    c.wait_load(timeout=15); time.sleep(4)

    published_count = 0
    attempt_cap = 20

    for i in range(attempt_cap):
        # Re-list drafts (the published ones are still in the sidebar but marked complete)
        # Find a draft that is NOT yet published (no 'Publication terminée' next to it)
        draft_idx = c.evaluate("""(function(){
          const drafts = [...document.querySelectorAll('[data-test-id=pin-draft-content-container]')];
          for (let i=0; i<drafts.length; i++) {
            const txt = drafts[i].textContent || '';
            if (!/Publication terminée|publication réussie|Échec/i.test(txt)) {
              return i;
            }
          }
          return -1;
        })()""")
        if draft_idx == -1:
            print("No more un-published drafts.")
            break
        print(f"\n=== Draft #{draft_idx + 1} ===")

        # Click the draft to open it
        opened = c.evaluate(f"""(function(){{
          const d = document.querySelectorAll('[data-test-id=pin-draft-content-container]')[{draft_idx}];
          if(!d) return 'no';
          d.scrollIntoView({{block:'center'}});
          d.click();
          return 'ok';
        }})()""")
        if opened != 'ok':
            print(f"  ! couldn't open: {opened}"); continue
        time.sleep(3)

        # Capture title for logging
        title = c.evaluate("(document.querySelector('input[placeholder*=Parlez-nous]')||{}).value || ''")
        print(f"  title: {title[:60]}")

        # Click the board picker button
        c.evaluate("""(function(){
          const btn = document.querySelector('[data-test-id=board-dropdown-select-button]');
          if(!btn) return;
          btn.scrollIntoView({block:'center'});
          const r = btn.getBoundingClientRect();
          const cx = r.left + r.width/2, cy = r.top + r.height/2;
          ['mouseover','mousedown','mouseup','click'].forEach(t=>{
            btn.dispatchEvent(new MouseEvent(t,{view:window,bubbles:true,cancelable:true,clientX:cx,clientY:cy,buttons:1}));
          });
        })()""")
        time.sleep(2)

        # Type board name in the picker's search input
        # Find the picker input (the one without ariaLabel)
        ok = c.evaluate("""(function(name){
          const inputs = [...document.querySelectorAll('input[role=combobox]')];
          const i = inputs.find(x => !x.ariaLabel && (x.placeholder||'').match(/Rechercher|tableau/i)) || inputs.find(x => !x.ariaLabel);
          if (!i) return 'no-input';
          const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
          i.focus(); s.call(i, name);
          i.dispatchEvent(new InputEvent('input',{bubbles:true,data:name,inputType:'insertFromPaste'}));
          return 'typed';
        })(""" + json.dumps(BOARD_NAME) + ")")
        time.sleep(2)
        # Click the matching board option
        sel = c.evaluate(f"""(function(name){{
          const opts = [...document.querySelectorAll('[role=option], [role=button], div[tabindex]')].filter(e=>{{
            const t = e.textContent.trim();
            const r = e.getBoundingClientRect();
            return t === name && r.width > 100 && r.height > 20;
          }});
          if(opts.length) {{ opts[0].click(); return 'picked'; }}
          // try by inclusion
          const opts2 = [...document.querySelectorAll('[role=option]')].filter(e=>e.textContent.includes(name));
          if(opts2.length) {{ opts2[0].click(); return 'picked-inc'; }}
          return 'no-board-option';
        }})({json.dumps(BOARD_NAME)})""")
        print(f"  board pick: {sel}")
        time.sleep(2)

        # Click Publier
        clicked = c.evaluate("""(function(){
          const btn = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Publier' && b.getBoundingClientRect().top < 200);
          if(!btn) return 'no';
          btn.click(); return 'clicked';
        })()""")
        print(f"  publier: {clicked}")
        if clicked != 'clicked':
            print("  ! couldn't click Publier"); continue
        time.sleep(8)
        # Verify by checking for 'Publication terminée' on the sidebar item OR success toast
        ok = c.evaluate("/Publication terminée|publication.{0,10}réussie|votre épingle est publiée/i.test(document.body.textContent)")
        print(f"  result: {'✓ published' if ok else '✗ unverified'}")
        if ok: published_count += 1
        time.sleep(2)

    print(f"\n*** Published {published_count} new pins ***")

if __name__ == "__main__":
    main()
