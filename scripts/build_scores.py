"""Build data/localities.json from open data, for each locality's 2 km circle.

Sources (fetched once into .cache/, re-run with --refresh to fetch again):
- Overture Maps places (schools, healthcare, daily needs), release REL, CDLA Permissive 2.0
- Overture Maps base/infrastructure, i.e. OpenStreetMap stations (metro, MMTS), ODbL
- ESA WorldCover 2021 v200, 10 m land cover (green cover), CC BY 4.0
Locality centres and zones come from data/centres.json (scripts/geocode.py, OpenStreetMap Nominatim).
Needs: pip install pyarrow rasterio numpy
shortcut: equal 2 km circles, not official boundaries; switch when GHMC publishes the 300-ward map.
"""
import json, math, os, sys
import numpy as np
import pyarrow.compute as pc, pyarrow.dataset as ds, pyarrow.fs as fs, pyarrow.parquet as pq
import rasterio
from rasterio.windows import from_bounds

REL = "2026-11-18.0"
W, S, E, N = 78.20, 17.15, 78.75, 17.65  # Hyderabad box, wider than every 2 km circle
R_KM = 2.0
MIN_CONFIDENCE = 0.5  # Overture places below this are often stale or duplicate listings
CACHE = ".cache"
CA = "/root/.ccr/ca-bundle.crt"
WORLDCOVER = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N15E078_Map.tif"

SCHOOLS = {"school", "private_school", "public_school", "elementary_school", "middle_school", "high_school", "preschool", "day_care_preschool"}
HEALTH = {"hospital", "childrens_hospital", "doctors_office", "pediatric_clinic", "primary_care_or_general_clinic", "walk_in_clinic", "dental_clinic"}
DAILY = {"supermarket", "pharmacy", "bank", "bank_or_credit_union", "atm"}  # plus every *grocery_store
GREEN = (10, 20, 30, 90)  # WorldCover tree cover, shrubland, grassland, wetland


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def overture(theme, typ, columns, refresh):
    path = f"{CACHE}/{theme}-{typ}-{W}-{S}-{E}-{N}.parquet"  # a new box never reuses an old cache
    if refresh or not os.path.exists(path):
        os.environ.setdefault("AWS_CA_BUNDLE", CA if os.path.exists(CA) else "")
        s3 = fs.S3FileSystem(anonymous=True, region="us-west-2", proxy_options=os.environ.get("HTTPS_PROXY") or None, scheme="https")
        d = ds.dataset(f"overturemaps-us-west-2/release/{REL}/theme={theme}/type={typ}/", filesystem=s3, format="parquet")
        f = (pc.field("bbox", "xmin") <= E) & (pc.field("bbox", "xmax") >= W) & (pc.field("bbox", "ymin") <= N) & (pc.field("bbox", "ymax") >= S)
        pq.write_table(d.to_table(columns=columns, filter=f), path)
    return pq.read_table(path).to_pylist()


def worldcover(refresh):
    path = f"{CACHE}/worldcover-{W}-{S}-{E}-{N}.tif"
    if refresh or not os.path.exists(path):
        os.environ.setdefault("CURL_CA_BUNDLE", CA if os.path.exists(CA) else "")
        if os.environ.get("HTTPS_PROXY"):
            os.environ.setdefault("GDAL_HTTP_PROXY", os.environ["HTTPS_PROXY"].removeprefix("http://"))
        with rasterio.open("/vsicurl/" + WORLDCOVER) as src:
            win = from_bounds(W, S, E, N, src.transform)
            a = src.read(1, window=win)
            prof = {**src.profile, "width": a.shape[1], "height": a.shape[0], "transform": src.window_transform(win), "compress": "deflate", "tiled": False}
        with rasterio.open(path, "w", **prof) as d:
            d.write(a, 1)
    with rasterio.open(path) as src:
        return src.read(1), src.transform


def main(refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    centres = [{k: d[k] for k in ("name", "zone", "lat", "lon")} for d in json.load(open("data/centres.json"))]

    places = [p for p in overture("places", "place", ["names", "taxonomy", "confidence", "operating_status", "bbox"], refresh)
              if p["confidence"] >= MIN_CONFIDENCE and p["operating_status"] not in ("permanently_closed", "temporarily_closed")]
    infra = overture("base", "infrastructure", ["names", "class", "bbox"], refresh)
    cover, tr = worldcover(refresh)

    def where(b): return (b["ymin"] + b["ymax"]) / 2, (b["xmin"] + b["xmax"]) / 2
    def label(n): return n.title() if n.islower() else n
    def cat(p): return (p["taxonomy"] or {}).get("primary") or ""
    # Durgam Cheruvu is a metro station that OpenStreetMap tags as a railway station
    # "(u/c)" marks Old City extension stations still under construction; they don't serve anyone yet
    metro = [(label(r["names"]["primary"]), *where(r["bbox"])) for r in infra
             if (r["class"] == "subway_station" or (r["class"] == "railway_station" and (r["names"] or {}).get("primary") == "Durgam Cheruvu"))
             and "(u/c)" not in (r["names"] or {}).get("primary", "")]
    rail = [(r["names"]["primary"], *where(r["bbox"])) for r in infra if r["class"] == "railway_station" and r["names"]["primary"] not in {m[0] for m in metro}
            and "(u/c)" not in r["names"]["primary"] and r["names"]["primary"] != "Durgam Cheruvu"]
    assert len(metro) >= 20 and len(rail) >= 5, (len(metro), len(rail))

    px_deg, inv = tr.a, ~tr
    out = []
    for c in centres:
        near = [p for p in places if km(c["lat"], c["lon"], *where(p["bbox"])) <= R_KM]
        def count(test): return sum(1 for p in near if test(cat(p)))
        def nearest(pts):
            n, la, lo = min(pts, key=lambda s: km(c["lat"], c["lon"], s[1], s[2]))
            return {"name": n, "km": round(km(c["lat"], c["lon"], la, lo), 2)}
        # equirectangular distance is exact enough at 2 km for a pixel mask
        col, row = (int(v) for v in inv * (c["lon"], c["lat"]))
        h = int(R_KM / 111.2 / px_deg) + 2  # half-width of a window that holds the circle
        assert h <= row and h <= col and row + h <= cover.shape[0] and col + h <= cover.shape[1], f"{c['name']} is too close to the data box edge; widen W, S, E, N"
        win = cover[row - h:row + h, col - h:col + h]
        rr, cc = np.indices(win.shape)
        lons, lats = tr * (cc + col - h + 0.5, rr + row - h + 0.5)
        px = win[((lats - c["lat"]) * 111.2) ** 2 + ((lons - c["lon"]) * 111.2 * math.cos(math.radians(c["lat"]))) ** 2 <= R_KM ** 2]
        out.append({**c,
                    "counts": {"schools": count(SCHOOLS.__contains__), "healthcare": count(HEALTH.__contains__),
                               "daily": count(lambda t: t in DAILY or t.endswith("grocery_store"))},
                    "metro": nearest(metro), "rail": nearest(rail),
                    "green_pct": round(100 * np.isin(px, GREEN).mean(), 1), "built_pct": round(100 * (px == 50).mean(), 1)})
        print(f"{c['name']:20} {out[-1]['counts']} metro {out[-1]['metro']} green {out[-1]['green_pct']}%")

    assert len(out) == len(centres) and all(o["counts"]["healthcare"] > 0 for o in out)
    json.dump(out, open("data/localities.json", "w"), indent=1)


if __name__ == "__main__":
    main(refresh="--refresh" in sys.argv)
