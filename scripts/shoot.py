#!/opt/homebrew/opt/python@3.11/bin/python3.11
"""Screenshot a specific tab by URL substring. Usage: shoot.py <urlsubstr> <out.png> [w h]"""
import sys, os, urllib.request, json, base64
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cdp import CDP, list_pages, PORT

substr = sys.argv[1]
out = sys.argv[2]
w = int(sys.argv[3]) if len(sys.argv) > 3 else None
h = int(sys.argv[4]) if len(sys.argv) > 4 else None
pages = [p for p in list_pages() if substr in p.get("url","")]
if not pages:
    print("no tab matching", substr); sys.exit(1)
page = pages[0]
c = CDP(page=page)
if w and h:
    c.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=2, mobile=False)
c.screenshot(out)
print("saved", out)
