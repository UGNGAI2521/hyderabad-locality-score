# Hyderabad Locality Score: handoff

As of 21 Nov 2026. Read this first in a new session.

## The idea

We help people choose the right **area** in Hyderabad to live, work, buy property or open a business, whether it's a flat, an independent house or a commercial space. The right area matters more than the right flat. **For now the site is locality comparison only**, scored from honest open data. No posting, no listings.

## Links

| What | Where |
| --- | --- |
| Live site | https://ugngai2521.github.io/hyderabad-locality-score/ (GitHub Pages, from `main`, root) |
| Repo (public) | https://github.com/UGNGAI2521/hyderabad-locality-score |
| Preview (claude.ai artifact, private) | https://claude.ai/artifact/8ZbGrBYBqS4FdeRBJeq7pZ (publish `src/page.html` to it) |
| Original handoff doc (rules, 21 components, source ideas) | https://claude.ai/artifact/JJxrjMX1n1NnNSoPDrddMH |
| Source register Sheet (private, owner's) | https://claude.ai/artifact/UxKc3KaPtnoFSXrshG5bNi |

## What the site does now

- **50 localities in 5 zones:** West 19, Central 8, North 8, East 8, South 7 (`data/centres.json`).
- **Score out of 100 from 5 measures within 2 km of each centre:** schools, healthcare, daily needs (groceries, pharmacies, banks/ATMs), distance to the nearest *operating* metro station, and green cover.
- **"What matters to you" chips** re-rank the list (a picked measure counts 3×). There's a zone filter.
- **The map draws itself** (MapLibre plus `data/basemap.geojson`: main roads, lakes, metro and rail). No tile service, so it also shows in the claude.ai preview.
- Each locality opens a panel with its numbers, its sources and the **16 "not enough data" components**.
- Light and dark themes; works on phones.
- Current top 5: Jubilee Hills 85, KPHB Colony 85, Ameerpet 84, Kukatpally 83, Panjagutta 83.

## Built but switched off

`const LISTINGS = false;` in `src/page.html` hides all property features. Setting it to `true` brings back:
- property search (rent/buy, 6 types, filters for budget, rate per sq ft, bedrooms, locality, locality score);
- owner posting with photos and buyer enquiries via **Supabase**;
- an admin approval step.

The Supabase project is `neqonqsxpejbzcumuylp`, region Seoul, free plan. The schema in `supabase/schema.sql` was tested end to end, including 19 row-level-security checks. Before going public it would need custom SMTP for sign-in emails. The 26 example listings in `data/listings.json` show only when listings are on and no real listing is live.

## Data and how to rebuild

| Measure | Source | Licence |
| --- | --- | --- |
| Schools, healthcare, daily needs | Overture Maps places, release `2026-11-18.0`, confidence ≥ 0.5 | CDLA Permissive 2.0 |
| Metro and MMTS stations | OpenStreetMap via Overture base layer; "(u/c)" stations excluded | ODbL |
| Green cover | ESA WorldCover 2021 v200, 10 m (trees, shrub, grass, wetland) | CC BY 4.0 |
| Centres | OpenStreetMap Nominatim, hand-checked | ODbL |
| Base map | OpenStreetMap via Overture (transportation and water) | ODbL |
| Photos | Wikimedia Commons, credited in the footer and in `data/photos.json` | various CC |

Scoring: counts use a log scale against the best locality; metro gets 100 within 500 m and 0 beyond 5 km; green cover is scaled against the greenest locality; the total is the average of the five. Scores are relative, so adding localities changes everyone's numbers.

Rebuild (needs `pip install pyarrow rasterio numpy shapely`):
```bash
python3 scripts/geocode.py        # only looks up names missing from data/centres.json
python3 scripts/build_scores.py   # writes data/localities.json (add --refresh for new data)
python3 scripts/build_basemap.py  # writes data/basemap.geojson
python3 scripts/build_site.py     # wraps src/page.html into index.html, ALWAYS run after editing the page
```
Edit `src/page.html`, never `index.html`. Overture and ESA are read from public AWS S3 through the session proxy.

## Rules (from the owner and the original handoff)

- Never invent data. A number with no source shows "not enough data". Every number carries its source and date.
- **No scraping of property portals or listing sites** (MagicBricks, 99acres, etc.).
- Score inputs only from government bodies, satellite or open-map datasets, or our own hand-checked reading of official filings.
- Free or near-free until January 2027.
- Plain, straight English. Discuss before big changes.

## Cloud environment

Environment **`hyderabad-locality-score`** (personal, tied to this repo):
- **Allowed hosts:** Nominatim, Wikipedia, Wikimedia, the Supabase project, GHMC, Overpass mirrors.
- **Saved secrets:**
  - Supabase access token (`api.supabase.com`).
  - OpenAQ key (`api.openaq.org`). Not working: it isn't sent in the `X-API-Key` header. Air quality work is **paused** by the owner.
- **Blocked or unusable:**
  - GHMC (its firewall rejects this server).
  - Overpass and Geofabrik (connections reset).
  - Wikipedia and Wikimedia APIs (heavy rate limiting).
  - github.io (can't check the live site from here).
  - CDNs for the browser in tests (serve local copies via Playwright routes).
- **Node fetch through the proxy:** run with `NODE_USE_ENV_PROXY=1`.

## Open items, in priority order

1. **Rajendranagar's centre sits inside university campuses**, so it shows 10 schools and 7 clinics. Move it to the old Ward 60 Rajendra Nagar centroid, then re-run `build_scores.py`.
2. **Edge crash risk:** a locality within about 2 km of the data box edge gives NaN green cover and invalid JSON. Shrink `CITY` in `geocode.py` by about 0.05°, or assert the window fits in `build_scores.py`.
3. **Delete `scripts/scrape_osm.py`** and its README row. It is obsolete, and running it overwrites `localities.json` in the old format.
4. **README:** mark the owner-posting paragraph as "when `LISTINGS` is on".
5. **Remove** the one-time migration lines in `scripts/geocode.py` (L41-43).
6. **Missing components (16 of 21):** water, power, traffic, safety, flooding, cost of living, price and yield, noise, construction dust, legal/title, apartment quality, internet and mobile, jobs, air quality, sewage and lakes, future infrastructure.
   - Reachable option: internet speed from Ookla open data. Its licence is non-commercial only (CC BY-NC-SA).
   - Most of the government sources in the handoff doc block this server.
7. **Official ward boundaries:** none are published yet (new 300-ward map). Equal 2 km circles are used instead. Old OpenStreetMap wards look mislabelled.
8. **Photos:** 6 are stored locally; the rest load from Wikimedia on the live site and fall back to drawings in the preview.

## Testing used so far

- Local server: `python3 -m http.server 8765` in the repo.
- Playwright from Node, with `maplibre-gl` and `@supabase/supabase-js` served from local `node_modules` through `page.route`.
- Fonts and outside images aborted.
- Checks: no page errors, no sideways scroll at 390 px, filters and zone chips work, map draws base layers.
