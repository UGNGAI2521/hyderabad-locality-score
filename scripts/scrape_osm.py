"""Collect amenity counts around West Hyderabad localities from OpenStreetMap (Nominatim).
Respects Nominatim's policy: 1 request/second, identifying User-Agent, small volume."""
import json, time, urllib.parse, urllib.request, sys

LOCALITIES = ["Gachibowli", "Madhapur", "Kondapur", "HITEC City", "Financial District", "Nanakramguda",
    "Manikonda", "Narsingi", "Kokapet", "Raidurg", "Miyapur", "Nallagandla"]  # handoff doc: Phase 1 + later list
# factor -> search phrases (OSM category words Nominatim understands)
FACTORS = {"schools": ["school"], "hospitals": ["hospital", "clinic"], "metro_transit": ["metro station", "bus stop"],
    "parks": ["park"], "shopping": ["supermarket", "mall"], "food": ["restaurant", "cafe"],
    "banks": ["bank", "atm"], "safety": ["police"]}
UA = {"User-Agent": "hyderabad-locality-score/0.1 (personal research project)"}
R = 0.018  # ~2 km half-width box around the locality centre
last = 0.0

def get(params):
    global last
    time.sleep(max(0, 2.0 - (time.time() - last)))
    last = time.time()
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({**params, "format": "jsonv2"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            print("retry", params.get("q"), e, file=sys.stderr); time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"failed after retries: {params.get('q')}")  # never count a failed search as zero

import os
only = sys.argv[2:]
out = [x for x in json.load(open(sys.argv[1]))if x["name"] not in only] if only and os.path.exists(sys.argv[1]) else []
seen = {(x["lat"], x["lon"]) for x in out}
for name in (only or LOCALITIES):
    g = []
    for q in (f"{name}, Hyderabad, Telangana", f"{name}, Ranga Reddy, Telangana", f"{name}, Telangana"):
        g = [x for x in get({"q": q, "limit": 5}) if (float(x["lat"]), float(x["lon"])) not in seen][:1]
        if g: break
    if not g:
        print("not found:", name, file=sys.stderr); continue
    lat, lon = float(g[0]["lat"]), float(g[0]["lon"])
    box = f"{lon-R},{lat+R},{lon+R},{lat-R}"
    counts = {}
    for f, phrases in FACTORS.items():
        ids = set()
        for p in phrases:
            for x in get({"q": p, "viewbox": box, "bounded": 1, "limit": 50}):
                ids.add(x["osm_id"])
        counts[f] = len(ids)  # shortcut: Nominatim caps 50/phrase, upgrade to an OSM extract for exact counts
    seen.add((lat, lon))
    out.append({"name": name, "lat": lat, "lon": lon, "counts": counts})
    print(name, counts, flush=True)

order = {n: i for i, n in enumerate(LOCALITIES)}
out = [x for x in out if x["name"] in order]
json.dump(sorted(out, key=lambda x: order.get(x["name"], 99)), open(sys.argv[1], "w"), indent=1)
