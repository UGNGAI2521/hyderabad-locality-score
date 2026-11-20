# Hyderabad Locality Score

A property search for West Hyderabad: flats, houses, villas, plots, offices and shops to rent or buy, with an open-data score for every locality.

This is a preview. The 26 listings are clearly marked examples with illustrative prices. Owner listings are not open yet; the "List your property" form saves a draft in the visitor's own browser only.

## What's in the repo

| Path | What it is |
| --- | --- |
| `index.html` | The whole site (HTML, CSS and JS in one file) |
| `data/localities.json` | OpenStreetMap place counts for 12 localities |
| `data/listings.json` | Example listings (every record has `example: true`) |
| `data/credits.json` | Author and licence for each photo |
| `media/` | Web-sized photos and the two looping videos |
| `vendor/maplibre-gl.css` | Map library stylesheet |
| `scripts/scrape_osm.py` | Collects the locality counts from OpenStreetMap (Nominatim) |
| `scripts/make_examples.py` | Builds the example listings |
| `scripts/process_media.py` | Resizes photos and renders the videos with ffmpeg |

## Run locally

`index.html` is written for the claude.ai artifact viewer, which adds the `<!doctype html>`, `<head>` and `<body>` wrapper when it publishes. To view it locally or host it elsewhere, wrap it first:

```bash
python3 -c "import sys;b=open('index.html').read();open('site.html','w').write('<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1,viewport-fit=cover\"></head><body style=margin:0>'+b+'</body></html>')"
```

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000/site.html.

## Data notes

- Locality counts © OpenStreetMap contributors (ODbL), collected 20 Nov 2026 within about 2 km of each locality centre. Volunteer-mapped, so some places are missing (Gachibowli shows 1 school, which is clearly too low).
- Scores cover 5 of the brief's 21 components. The other 16 show "not enough data".
- Photos: Wikimedia Commons, each with its own licence (CC0, CC BY, CC BY-SA or public domain). Credits are listed in the site footer and in `data/credits.json`. The videos are slow pans and zooms made from those photos and carry the same licences.
- Map tiles: CARTO basemaps (© OpenStreetMap contributors, © CARTO). Map library: MapLibre GL JS.
- No figures come from property portals or listing sites.
