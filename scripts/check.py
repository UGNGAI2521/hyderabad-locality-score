"""Checks that must pass before anything goes live. GitHub Actions runs them on every push; by hand: python3 scripts/check.py
Only the standard library, so it runs anywhere. Exits 1 and lists every problem it finds."""
import glob, json, math, os, re, sys
from urllib.parse import unquote, urljoin, urlparse

errors = []
def check(ok, msg):
    if not ok: errors.append(msg)

centres = json.load(open("data/centres.json"))
locs = json.load(open("data/localities.json"))
photos = json.load(open("data/photos.json"))
MEASURES = {"schools", "healthcare", "daily", "transport", "green"}

# data: one row per centre, sane values, scores that add up
check([o["name"] for o in locs] == [c["name"] for c in centres], "data/localities.json does not match data/centres.json: re-run scripts/build_scores.py")
check(sorted(o.get("rank", 0) for o in locs) == list(range(1, len(locs) + 1)), "ranks are not 1 to N")
for o in locs:
    p, n = o.get("parts", {}), o["name"]
    check(set(p) == MEASURES and all(isinstance(v, int) and 0 <= v <= 100 for v in p.values()), f"{n}: measure scores missing or outside 0-100")
    check(o.get("score") == math.floor(sum(p.values()) / len(MEASURES) + 0.5), f"{n}: score is not the average of its five measures")
    check(all(o["counts"][k] >= 0 for k in ("schools", "healthcare", "daily")) and 0 <= o["green_pct"] <= 100 and o["metro"]["km"] >= 0, f"{n}: impossible raw value")
    check(o.get("park", {}).get("km", -1) >= 0 and set(o.get("green_parts", {})) == {"cover", "park"}, f"{n}: nearest park or green-space parts missing")
    check(17.0 < o["lat"] < 17.9 and 78.0 < o["lon"] < 79.0, f"{n}: centre is outside Hyderabad")
check(sum(o["counts"]["healthcare"] > 0 for o in locs) >= 0.9 * len(locs), "most localities map no clinic: the places download is probably broken")

# photos: every credited photo has its files and a full credit
for k, v in photos.items():
    if not k.startswith("loc-"): continue
    check(all(v.get(f) for f in ("author", "license", "page", "caption")), f"{k}: photo credit is incomplete")
    if v.get("local"):
        for f in (f"media/{k}.jpg", f"media/{k}-sm.jpg"): check(os.path.exists(f), f"{k}: {f} is missing")

# generated pages: one per locality, in the sitemap, and every internal link or image resolves
pages = glob.glob("locality/*/index.html")
check(len(pages) == len(locs), f"{len(pages)} locality pages for {len(locs)} localities: run scripts/build_site.py")
check(open("sitemap.xml").read().count("<loc>") == len(locs) + 2, "sitemap.xml is out of date: run scripts/build_site.py")
for f in ["index.html", "locality/index.html"] + pages:
    for u in re.findall(r'(?:href|src)="([^"]+)"', open(f, encoding="utf-8").read()):
        if u.startswith(("http:", "https:", "mailto:", "#", "data:")) or "${" in u: continue
        path = unquote(urlparse(urljoin("/" + f, u)).path).lstrip("/")
        path = path + "index.html" if path.endswith("/") or not path else path
        check(os.path.exists(path), f"{f}: broken link {u}")

if errors:
    print(f"{len(errors)} problem(s):", *errors[:50], sep="\n  ")
    sys.exit(1)
print(f"All checks passed: {len(locs)} localities, {sum(1 for k, v in photos.items() if k.startswith('loc-') and v.get('local'))} local photos, {len(pages)} pages.")
