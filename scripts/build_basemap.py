"""Write data/basemap.geojson: a light base map of Hyderabad (main roads, metro and rail lines, lakes and rivers)
drawn by the site itself, so the map needs no outside tile service. Data: OpenStreetMap via Overture Maps (ODbL).
Needs: pip install pyarrow shapely numpy rasterio (shares the cached Overture download with build_scores.py)
"""
import json, os, sys
from shapely import wkb
from shapely.geometry import mapping
from shapely.ops import linemerge, unary_union

sys.path.insert(0, os.path.dirname(__file__))
from build_scores import overture, W, S, E, N  # same box and cache

ROADS = {"motorway", "trunk", "primary", "secondary"}
WATER = {"lake", "reservoir", "river", "water", "pond"}
MIN_WATER_DEG2 = 4e-6  # about 0.05 km²; skips tanks and pools that only add clutter
TOL = {"motorway": 0.0001, "trunk": 0.0001, "primary": 0.00015, "secondary": 0.00025, "metro": 0.0001, "rail": 0.0001, "water": 0.00015}  # degrees; 0.0001 is about 11 m


def rounded(geom):
    def r(c): return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], float) else [r(x) for x in c]
    m = mapping(geom)
    return {"type": m["type"], "coordinates": r(m["coordinates"])}


def main(refresh=False):
    parts = {k: [] for k in TOL}
    for s in overture("transportation", "segment", ["subtype", "class", "geometry"], refresh):
        k = s["class"] if s["subtype"] == "road" and s["class"] in ROADS else "metro" if s["class"] == "subway" else "rail" if s["subtype"] == "rail" else None
        if k:
            parts[k].append(wkb.loads(s["geometry"]))
    for w in overture("base", "water", ["subtype", "class", "geometry"], refresh):
        g = wkb.loads(w["geometry"])
        if w["subtype"] in WATER and w["class"] != "swimming_pool" and g.geom_type.endswith("Polygon") and g.area >= MIN_WATER_DEG2:
            parts["water"].append(g)
    counts = {k: len(v) for k, v in parts.items()}
    assert counts["metro"] > 20 and counts["water"] > 20 and counts["primary"] > 100, counts
    # one merged feature per kind keeps the file small: thousands of road pieces become a few long lines
    feats = [{"type": "Feature", "properties": {"k": k}, "geometry": rounded((unary_union(v) if k == "water" else linemerge(unary_union(v))).simplify(TOL[k]))}
             for k, v in parts.items()]
    json.dump({"type": "FeatureCollection", "features": feats}, open("data/basemap.geojson", "w"), separators=(",", ":"))
    print(counts, os.path.getsize("data/basemap.geojson") // 1024, "KB")


if __name__ == "__main__":
    main(refresh="--refresh" in sys.argv)
