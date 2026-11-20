# Hyderabad Locality Score

A property search for West Hyderabad: flats, houses, villas, plots, offices and shops to rent or buy, with an open-data score for every locality.

This is a preview. The 26 listings are clearly marked examples with illustrative prices. Owner listings are not open yet; the "List your property" form saves a draft in the visitor's own browser only.

## What's in the repo

| Path | What it is |
| --- | --- |
| `src/page.html` | The site source (HTML, CSS and JS in one file), written for the claude.ai artifact viewer |
| `index.html` | Standalone build of `src/page.html` for any static host. Regenerate with `python3 scripts/build_site.py` |
| `data/localities.json` | Measures for 12 localities: place counts, nearest metro and MMTS station, green cover |
| `data/listings.json` | Example listings (every record has `example: true`) |
| `data/photos.json` | Each photo's author, licence, Wikimedia address, and whether a local copy exists |
| `media/` | Web-sized photos and the two looping videos |
| `vendor/maplibre-gl.css` | Map library stylesheet |
| `scripts/build_scores.py` | Builds `data/localities.json` from Overture Maps, OpenStreetMap stations and ESA WorldCover |
| `scripts/scrape_osm.py` | Earlier Nominatim scraper; still the source of the locality centre points |
| `scripts/make_examples.py` | Builds the example listings |
| `scripts/process_media.py` | Resizes photos and renders the videos with ffmpeg |
| `scripts/build_site.py` | Builds `index.html` from `src/page.html` |

## Run locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000. After editing `src/page.html`, run `python3 scripts/build_site.py` to rebuild `index.html`.

Photos without a local copy in `media/` load directly from Wikimedia Commons; if they can't load, a line drawing of the property type shows instead.

## Data notes

- Everything is measured within 2 km of each locality centre (centres geocoded with OpenStreetMap Nominatim). Equal circles keep the comparison fair until GHMC publishes the new 300-ward map; the old 150-ward polygons in OpenStreetMap are not official and some look mislabelled, so they are not used.
- Schools, healthcare and daily needs: places from [Overture Maps](https://overturemaps.org), release 2026-11-18.0 (CDLA Permissive 2.0), confidence 0.5 or higher.
- Metro and MMTS stations: © OpenStreetMap contributors (ODbL), read from Overture's base layer.
- Green cover: [ESA WorldCover 2021 v200](https://esa-worldcover.org), 10 m land cover (CC BY 4.0); trees, shrubland, grassland and wetland.
- Scoring: counts on a log scale against the best locality; metro full marks within 500 m and none beyond 5 km; green cover against the greenest locality. The total is the average of the five.
- Scores cover 5 of the brief's 21 components. The other 16 show "not enough data".
- Re-run with `pip install pyarrow rasterio numpy` then `python3 scripts/build_scores.py` (add `--refresh` to fetch fresh data).
- Photos: Wikimedia Commons, each with its own licence (CC0, CC BY, CC BY-SA or public domain). Credits are listed in the site footer and in `data/photos.json`. The videos are slow pans and zooms made from those photos and carry the same licences.
- Map tiles: CARTO basemaps (© OpenStreetMap contributors, © CARTO). Map library: MapLibre GL JS.
- No figures come from property portals or listing sites.
