"""Write data/centres.json: the centre point of every locality we score, found with OpenStreetMap Nominatim.

Points already in data/centres.json are kept, so re-running only looks up new names.
Nominatim's policy: at most 1 request a second and an identifying User-Agent.
"""
import json, os, sys, time, urllib.parse, urllib.request

ZONES = {
    "West": ["Gachibowli", "Madhapur", "Kondapur", "HITEC City", "Financial District", "Nanakramguda", "Manikonda", "Narsingi",
             "Kokapet", "Raidurg", "Miyapur", "Nallagandla", "Chandanagar", "Kukatpally", "KPHB Colony", "Nizampet",
             "Jubilee Hills", "Banjara Hills", "Tolichowki"],
    "Central": ["Ameerpet", "Begumpet", "Somajiguda", "Khairatabad", "Himayatnagar", "Abids", "Mehdipatnam", "Panjagutta"],
    "North": ["Secunderabad", "Kompally", "Alwal", "Bowenpally", "Sainikpuri", "Malkajgiri", "Tarnaka", "Bachupally"],
    "East": ["Uppal", "LB Nagar", "Dilsukhnagar", "Habsiguda", "Nagole", "Vanasthalipuram", "Boduppal", "Saroornagar"],
    "South": ["Attapur", "Rajendranagar", "Shamshabad", "Charminar", "Santosh Nagar", "Chandrayangutta", "Malakpet"],
}
CITY = (78.20, 17.15, 78.75, 17.65)  # W, S, E, N: anything outside is a wrong match
UA = {"User-Agent": "hyderabad-locality-score/0.2 (open-data locality comparison)"}
OUT = "data/centres.json"


def search(q, settlement):
    params = {"q": q, "format": "jsonv2", "limit": 5, "countrycodes": "in", **({"featureType": "settlement"} if settlement else {})}
    for wait in (2, 10, 30):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params), headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception as e:
            print("  retry:", e, file=sys.stderr)
    raise RuntimeError(f"Nominatim kept failing for {q!r}")


def inside(x):
    W, S, E, N = CITY
    return W <= float(x["lon"]) <= E and S <= float(x["lat"]) <= N


def main():
    known = {c["name"]: c for c in json.load(open(OUT))} if os.path.exists(OUT) else {}
    # the first 12 centres were checked by hand in the earlier West Hyderabad release
    if not known and os.path.exists("data/localities.json"):
        known = {d["name"]: {"name": d["name"], "lat": d["lat"], "lon": d["lon"], "match": "carried over"} for d in json.load(open("data/localities.json"))}
    out = []
    for zone, names in ZONES.items():
        for name in names:
            c = known.get(name)
            if not c:
                hit = None
                for q, settlement in ((f"{name}, Hyderabad, Telangana", True), (f"{name}, Telangana", True), (f"{name}, Hyderabad, Telangana", False)):
                    hit = next((x for x in search(q, settlement) if inside(x)), None)
                    if hit:
                        break
                if not hit:
                    raise SystemExit(f"No match inside Hyderabad for {name}; add its point by hand")
                c = {"name": name, "lat": round(float(hit["lat"]), 6), "lon": round(float(hit["lon"]), 6), "match": f'{hit.get("type")}: {hit["display_name"][:90]}'}
                print(f"{zone:8} {name:20} {c['lat']:.4f}, {c['lon']:.4f}  {c['match']}")
            out.append({**c, "zone": zone})
    assert len({c["name"] for c in out}) == len(out) == sum(map(len, ZONES.values()))
    json.dump(out, open(OUT, "w"), indent=1)
    print(len(out), "centres written")


if __name__ == "__main__":
    main()
