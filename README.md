# Hyderabad Locality Score

Helps people choose the right area to live, work or buy property anywhere in Hyderabad, using honest open data. For now the site is locality comparison only: property search, owner posting and enquiries are built and tested but switched off with `LISTINGS = false` in `src/page.html`.

When `LISTINGS` is on, owners sign in by email and post listings with photos; buyers send enquiries that only the owner can read. Every new or edited listing waits for the admin's approval before it goes live. Until the first listing is approved, the site shows 26 clearly marked example listings.

## Running the marketplace

- **Approve listings:** open the [Supabase table editor](https://supabase.com/dashboard/project/neqonqsxpejbzcumuylp/editor), pick `listings`, and change `status` from `pending` to `live`. Set it to `closed` to take a listing down.
- **Sign-in emails:** Supabase's built-in email only reaches the project's team members and sends 2 emails an hour. Before opening to the public, add an SMTP provider under Authentication → Emails → SMTP Settings (for example Brevo's free plan, 300 emails a day), then raise the email rate limit under Authentication → Rate Limits.
- **Database rules** live in `supabase/schema.sql` (safe to re-run). `supabase/config.js` holds the project URL and publishable key, which are meant to be public; row-level security protects the data.

## What's in the repo

| Path | What it is |
| --- | --- |
| `src/page.html` | The site source (HTML, CSS and JS in one file), written for the claude.ai artifact viewer |
| `index.html` | Standalone build of `src/page.html` for any static host. Regenerate with `python3 scripts/build_site.py` |
| `data/centres.json` | 88 localities in 5 zones and their centre points (`scripts/geocode.py`, hand-checked) |
| `data/localities.json` | Measures for each locality: place counts, nearest metro and MMTS station, green cover, nearest park, measure scores and rank |
| `data/basemap.geojson` | Main roads, metro and rail lines, lakes: the map draws this itself (`scripts/build_basemap.py`) |
| `data/listings.json` | Example listings, shown only while no owner listing is live |
| `supabase/schema.sql` | Tables, row-level security and photo storage for owner listings and enquiries |
| `locality/`, `sitemap.xml` | One static page per locality, an index of all of them and the sitemap, written by `scripts/build_pages.py` (run from `build_site.py`) |
| `scripts/check.py`, `scripts/smoke.js` | Checks run by GitHub Actions on every push: data, photo credits, pages, links, and a browser smoke test |
| `scripts/refresh.py` | Monthly refresh (GitHub Actions, 1st of the month): newest Overture release, rebuild, pull request for review |
| `supabase/community.sql` | Tables and row-level security for resident notes (read only once marked live) and the early-access list. Not applied yet: run it once in the Supabase SQL editor to switch both on |
| `supabase/config.js` | Supabase project URL and publishable key |
| `data/photos.json` | Each photo's author, licence, Wikimedia address, and whether a local copy exists |
| `media/` | Web-sized photos and the two looping videos |
| `vendor/maplibre-gl.css` | Map library stylesheet |
| `scripts/build_scores.py` | Builds `data/localities.json` from Overture Maps, OpenStreetMap stations and parks, and ESA WorldCover |
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

- Schools and daily needs are counted within 1 km of each locality centre (a short walk); clinics and green cover within 2 km. Equal circles keep the comparison fair until GHMC publishes the new 300-ward map; the old 150-ward polygons in OpenStreetMap are not official and some look mislabelled, so they are not used.
- Schools, healthcare and daily needs: places from [Overture Maps](https://overturemaps.org), release 2026-11-18.0 (CDLA Permissive 2.0), confidence 0.5 or higher.
- Metro and MMTS stations: © OpenStreetMap contributors (ODbL), read from Overture's base layer.
- Green cover: [ESA WorldCover 2021 v200](https://esa-worldcover.org), 10 m land cover (CC BY 4.0); trees, shrubland, grassland and wetland.
- Scoring: counts on a log scale against the best locality; metro full marks within 500 m and none beyond 5 km; green cover against the greenest locality. The total is the average of the five.
- Scores cover 5 of the brief's 21 components. The other 16 show "not enough data".
- Re-run with `pip install pyarrow rasterio numpy` then `python3 scripts/build_scores.py` (add `--refresh` to fetch fresh data).
- Photos: Wikimedia Commons, each with its own licence (CC0, CC BY, CC BY-SA or public domain). Credits are listed in the site footer and in `data/photos.json`. The videos are slow pans and zooms made from those photos and carry the same licences.
- Base map: main roads, metro and rail lines and lakes from © OpenStreetMap contributors (ODbL) via Overture Maps, drawn by the site with MapLibre GL JS. No tile service.
- Metro distance counts operating stations only; stations marked under construction (u/c) are left out.
- No figures come from property portals or listing sites.
