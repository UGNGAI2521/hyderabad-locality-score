"""Write one static page per locality (locality/<slug>/index.html), an index of all of them (locality/index.html)
and sitemap.xml, so search engines can find each area. Run by build_site.py; reads data/*.json and src/page.html.

The source list, the "not scored yet" reasons and the data date are read from src/page.html, so they are written once."""
import html, json, math, os, re, shutil
from datetime import datetime
from urllib.parse import quote

SITE = "https://ugngai2521.github.io/hyderabad-locality-score/"
page = open("src/page.html", encoding="utf-8").read()
SOURCES = re.search(r"const SOURCES = '(.*?)';", page).group(1)
NO_DATA = re.findall(r'\["([^"]+)", "([^"]+)"\]', page[page.index("const NO_DATA = ["):page.index("];", page.index("const NO_DATA = ["))])
DATA_DATE = re.search(r"Data last updated (\d{1,2} \w+ \d{4})", page).group(1)
assert len(NO_DATA) == 16 and "Overture" in SOURCES
LABELS = {"schools": "Schools", "healthcare": "Healthcare", "daily": "Daily needs", "transport": "Metro access", "green": "Green space"}
esc = html.escape
slug = lambda n: re.sub(r"[^a-z0-9]+", "-", n.lower())
pct = lambda x: math.floor(x + 0.5)  # round halves up, as the main page does

CSS = """
:root{--paper:#f8fafc;--surface:#fff;--ink:#0f172a;--muted:#475569;--line:#e2e8f0;--lake:#047857;--lake-soft:#ecfdf5;--marigold:#f59e0b;--marigold-soft:#fef3c7;--amber-ink:#b45309;--brand:#d97706;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--paper:#0b1120;--surface:#111a2e;--ink:#e2e8f0;--muted:#94a3b8;--line:#1e293b;--lake:#34d399;--lake-soft:#0d2b24;--marigold:#fbbf24;--marigold-soft:#3a2a0c;--amber-ink:#fbbf24;--brand:#f59e0b;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--lake)}h1,h2,h3{line-height:1.15;letter-spacing:-.02em;margin:0}h1{font-size:clamp(32px,5vw,48px);font-weight:800}h2{font-size:22px;font-weight:700;margin-bottom:12px}
.wrap{max-width:1040px;margin:0 auto;padding:0 16px}.top{border-bottom:1px solid var(--line);background:var(--surface)}.top .wrap{display:flex;align-items:center;justify-content:space-between;height:60px;gap:12px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;color:var(--ink);text-decoration:none}.brand i{width:28px;height:28px;border-radius:8px;background:var(--brand);display:inline-block}
.crumbs{font-size:13px;color:var(--muted);margin:18px 0 8px}.crumbs a{color:var(--muted)}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--amber-ink);margin:0 0 6px}
.hero{display:grid;grid-template-columns:1.1fr .9fr;gap:28px;align-items:center;padding:8px 0 28px}.lede{color:var(--muted);font-size:17px;max-width:56ch}
.score{display:inline-flex;align-items:baseline;gap:4px;background:var(--lake-soft);color:var(--lake);border-radius:14px;padding:8px 16px;margin:14px 0}.score b{font-size:40px;line-height:1}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px}.btn{display:inline-block;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:10px 18px;text-decoration:none;font-weight:600;font-size:14px}
.btn.primary{background:var(--marigold);border-color:var(--marigold);color:#1c1003}
figure{margin:0}figure img{width:100%;height:auto;aspect-ratio:16/10;object-fit:cover;border-radius:18px;display:block}figcaption{font-size:12px;color:var(--muted);margin-top:6px}
section{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:20px;margin-bottom:16px}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:600;font-size:12px}
.bar{display:block;height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-top:6px;min-width:90px}.bar i{display:block;height:100%;background:var(--marigold)}
.near{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;list-style:none;margin:0;padding:0}.near a{display:block;border:1px solid var(--line);border-radius:12px;padding:10px 12px;text-decoration:none;color:var(--ink)}
.near small{display:block;color:var(--muted)}.near b{color:var(--lake)}
ul.plain{margin:0;padding-left:18px;display:grid;gap:6px}.fine{font-size:13px;color:var(--muted)}
footer{padding:24px 0 40px;font-size:13px;color:var(--muted)}
.zone{margin-bottom:16px}.zone ol{columns:3;column-gap:24px;margin:0;padding-left:22px}.zone li{break-inside:avoid;padding:3px 0}
@media (max-width:760px){.hero{grid-template-columns:1fr}.zone ol{columns:1}td:nth-child(4),th:nth-child(4){display:none}}
"""


def shell(title, desc, canonical, body, depth, image=None, jsonld=None):
    up = "../" * depth
    meta = [f'<meta name="description" content="{esc(desc)}">', f'<link rel="canonical" href="{canonical}">',
            f'<meta property="og:title" content="{esc(title)}">', f'<meta property="og:description" content="{esc(desc)}">',
            f'<meta property="og:type" content="website">', f'<meta property="og:url" content="{canonical}">']
    if image: meta.append(f'<meta property="og:image" content="{image}">')
    if jsonld: meta.append(f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{chr(10).join(meta)}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body><header class="top"><div class="wrap"><a class="brand" href="{up}"><i aria-hidden="true"></i>Locality Score</a><a class="btn" href="{up}#localities">Compare all localities</a></div></header>
<main class="wrap">{body}</main>
<footer class="wrap">Data last updated {DATA_DATE}. Scores come only from open, official and satellite data; where there is no reliable source we say "not enough data". <a href="{up}#method">How the score works</a> · <a href="{up}locality/">All localities</a> · <a href="https://github.com/UGNGAI2521/hyderabad-locality-score/issues/new" rel="noopener">Report a problem</a></footer>
</body></html>
"""


def km(a, b):
    p = math.pi / 180
    x = math.sin((b["lat"] - a["lat"]) * p / 2) ** 2 + math.cos(a["lat"] * p) * math.cos(b["lat"] * p) * math.sin((b["lon"] - a["lon"]) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))


def locality_page(L, all_locs, photos):
    n, s = L["name"], slug(L["name"])
    c = L["counts"]
    near = sorted((o for o in all_locs if o is not L), key=lambda o: km(L, o))[:6]
    parts = L["parts"]
    best, worst = max(parts, key=parts.get), min(parts, key=parts.get)
    rows = [("schools", f'{c["schools"]} schools and preschools', "within 1 km"),
            ("healthcare", f'{c["healthcare"]} hospitals and clinics', "within 2 km"),
            ("daily", f'{c["daily"]} groceries, pharmacies, banks and ATMs', "within 1 km"),
            ("transport", f'Nearest operating metro: {esc(L["metro"]["name"])}, {L["metro"]["km"]:.1f} km. Nearest MMTS station: {esc(L["rail"]["name"])}, {L["rail"]["km"]:.1f} km', "straight-line distance"),
            ("green", f'{pct(L["green_pct"])}% of land under trees, shrubs, grass or wetland ({L["green_parts"]["cover"]}/100); nearest mapped park: {esc(L["park"]["name"] or "an unnamed park")}, {L["park"]["km"]:.1f} km ({L["green_parts"]["park"]}/100)', "green cover within 2 km; park by distance")]
    ph = photos.get("loc-" + s)
    figure = (f'<figure><img src="../../media/loc-{s}.jpg" alt="{esc(ph.get("caption") or n)}" width="1280" height="800">'
              f'<figcaption>{esc(ph.get("caption") or "")}. Photo: {esc(ph.get("author") or "Unknown")}, <a href="{esc(ph["page"])}" rel="noopener">{esc(ph["license"])}</a>, via Wikimedia Commons.</figcaption></figure>') if ph and ph.get("local") else ""
    total = len(all_locs)
    desc = (f'{n} ({L["zone"]} zone, Hyderabad): early score {L["score"]}/100, rank {L["rank"]} of {total}. {c["schools"]} schools within 1 km, '
            f'{c["healthcare"]} clinics within 2 km, nearest metro {L["metro"]["km"]:.1f} km, {pct(L["green_pct"])}% green cover, nearest park {L["park"]["km"]:.1f} km. Open data, every source cited.')
    body = f"""
<nav class="crumbs"><a href="../../">Home</a> › <a href="../">All localities</a> › {esc(n)}</nav>
<div class="hero"><div>
  <p class="eyebrow">{esc(L["zone"])} zone · Hyderabad</p>
  <h1>{esc(n)}</h1>
  <div class="score"><b>{L["score"]}</b>/ 100 · early score</div>
  <p class="lede">{esc(n)} ranks {L["rank"]} of {total} Hyderabad localities on 5 of the 21 measures we plan. Its strongest measure is {LABELS[best].lower()} ({parts[best]}/100) and its weakest is {LABELS[worst].lower()} ({parts[worst]}/100).</p>
  <div class="cta"><a class="btn primary" href="../../#loc={quote(n)}">Open on the map</a><a class="btn" href="../../#compare={quote(n)},{quote(near[0]["name"])},{quote(near[1]["name"])}">Compare with {esc(near[0]["name"])} and {esc(near[1]["name"])}</a></div>
</div>{figure}</div>
<section><h2>The five measures</h2>
<table><thead><tr><th>Measure</th><th>What we found</th><th>Score</th><th>Counted</th></tr></thead><tbody>
{"".join(f'<tr><td>{LABELS[k]}</td><td>{what}</td><td><b>{parts[k]}</b>/100<span class="bar"><i style="width:{parts[k]}%"></i></span></td><td class="fine">{where}</td></tr>' for k, what, where in rows)}
</tbody></table>
<p class="fine">Counts show how many places are mapped in open data, not how good they are, and outer areas are mapped less fully. Scores are relative: each measure is compared with the other {total - 1} localities, and the early score is the average of the five with equal weights (provisional).</p></section>
<section><h2>Nearby localities</h2><ul class="near">
{"".join(f'<li><a href="../{slug(o["name"])}/"><b>{o["score"]}</b> {esc(o["name"])}<small>{km(L, o):.1f} km away · {esc(o["zone"])} zone</small></a></li>' for o in near)}
</ul></section>
<section><h2>Not scored yet</h2><p class="fine">16 of the 21 measures show "not enough data" because no open, official source covers them at locality level yet.</p>
<ul class="plain">{"".join(f"<li><b>{esc(a)}</b>: {esc(b)}</li>" for a, b in NO_DATA)}</ul></section>
<section><h2>Sources</h2><p class="fine">{SOURCES} Places listed with low confidence are left out.</p>
<p class="fine">Centre point: {L["lat"]:.4f}° N, {L["lon"]:.4f}° E. The circles around it are not an official ward boundary; official boundaries for the new 300 wards are not published yet.</p></section>
"""
    canonical = f"{SITE}locality/{s}/"
    jsonld = {"@context": "https://schema.org", "@type": "Place", "name": f"{n}, Hyderabad", "url": canonical,
              "geo": {"@type": "GeoCoordinates", "latitude": L["lat"], "longitude": L["lon"]},
              "containedInPlace": {"@type": "City", "name": "Hyderabad"}}
    img = f"{SITE}media/loc-{s}.jpg" if ph and ph.get("local") else None
    return shell(f"{n}, Hyderabad: locality score {L['score']}/100 | Locality Score", desc, canonical, body, 2, img, jsonld)


def index_page(all_locs):
    zones = {}
    for o in sorted(all_locs, key=lambda o: o["rank"]):
        zones.setdefault(o["zone"], []).append(o)
    body = f"""<nav class="crumbs"><a href="../">Home</a> › All localities</nav>
<h1>All {len(all_locs)} Hyderabad localities</h1>
<p class="lede">Every locality we score, ranked within its zone by early score (5 of 21 measures, equal weights). Open one for its numbers and sources, or <a href="../#localities">compare them on the map</a>.</p>
{"".join(f'<section class="zone"><h2>{z} zone</h2><ol>' + "".join(f'<li><a href="{slug(o["name"])}/">{esc(o["name"])}</a> <b>{o["score"]}</b></li>' for o in ls) + "</ol></section>" for z, ls in zones.items())}"""
    return shell(f"All {len(all_locs)} Hyderabad localities | Locality Score", f"Early scores for {len(all_locs)} Hyderabad localities from open data: schools, healthcare, daily needs, metro access and green cover, every source cited.",
                 f"{SITE}locality/", body, 1)


def main():
    locs = json.load(open("data/localities.json"))
    photos = json.load(open("data/photos.json"))
    assert all("parts" in o and "rank" in o for o in locs), "run scripts/build_scores.py first"
    shutil.rmtree("locality", ignore_errors=True)
    for L in locs:
        os.makedirs(f"locality/{slug(L['name'])}", exist_ok=True)
        open(f"locality/{slug(L['name'])}/index.html", "w", encoding="utf-8").write(locality_page(L, locs, photos))
    open("locality/index.html", "w", encoding="utf-8").write(index_page(locs))
    day = datetime.strptime(DATA_DATE, "%d %b %Y").date().isoformat()
    urls = [SITE, f"{SITE}locality/"] + [f"{SITE}locality/{slug(o['name'])}/" for o in locs]
    open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                   + "".join(f"  <url><loc>{u}</loc><lastmod>{day}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    assert len({slug(o["name"]) for o in locs}) == len(locs) == len(os.listdir("locality")) - 1
    print(len(locs), "locality pages, locality/index.html, sitemap.xml with", len(urls), "URLs")


if __name__ == "__main__":
    main()
