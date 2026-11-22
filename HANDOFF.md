# Hyderabad Locality Score: handoff

As of 21 Nov 2026. Read this first in a new session.

## Update, 22 Nov 2026 (read this first)

Merged to `main` and live:
- Open items 1–5 below are done. Rajendranagar now uses the old Ward 60 centroid, but that still sits on the university campuses; a better hand-picked point is still needed.
- Honesty fixes: "early score, 5 of 21 measures" everywhere, the 2 km circle is stated as not an official boundary, retrieved-on dates, a Method section, a metro-distance note on low scores.
- 88 localities (38 added on 22 Nov: West 33, Central 16, North 14, East 13, South 12). New centre points come from Overture divisions (OSM), Nominatim, or the middle of Overture places named for the area; each has a `match` note in `data/centres.json`. Rajendranagar and Kollur now use the middle of places named for them. The data box now reaches 17.70 N for Medchal. Kollur and Shamirpet map almost no places in open data.
- Photos for 46 of the original 50 localities; the 38 new ones show letter tiles, stored in `media/loc-*.jpg` and credited in `data/photos.json` (with captions). No suitable photo yet: Kompally, Bowenpally, Nagole, Rajendranagar.
- New look after a Gemini "HydScore" mock-up (layout only, none of its invented data): split hero with a live top-locality card, search and data-based filter chips, richer cards (12 at a time), weight sliders with a live top-10 chart, radar chart in each panel, compare up to 3, shareable `#loc=` and `#compare=` links, map bands and legend, mobile menu, About and feedback link in the footer.
- `const COMMUNITY = false;` hides resident notes and the early-access list. Run `supabase/community.sql` in the Supabase SQL editor (not yet done), then set it to `true`.
- "Data last updated" in the footer is typed by hand; change it when the data is rebuilt.
- The `hyderabad-locality-score` environment now also allows share.gemini.google, gemini.google.com, www.gstatic.com, gemini.gstatic.com and one *.scf.usercontent.goog host (added once to read the mock-up); they can be removed.

Circles (22 Nov): schools and daily needs within 1 km, healthcare and green cover within 2 km (`R_NEAR`, `R_WIDE` in `build_scores.py`), chosen after a 1 km vs 2 km comparison.

Locality pages (22 Nov): `build_scores.py` now writes each locality's measure scores (`parts`), default `score` and `rank`; the page only re-weights them. `build_site.py` also runs `build_pages.py`, which writes `locality/<slug>/index.html`, `locality/index.html` and `sitemap.xml` (submit it in Google Search Console). "Customise what matters most" now sits right under the hero.

Checks and refresh (22 Nov): `.github/workflows/check.yml` runs on every push: rebuilds and fails if built files are stale, then `scripts/check.py` (data, photo credits, pages, links) and `scripts/smoke.js` (browser). Push to a branch, wait for green, then merge to `main`. `.github/workflows/refresh.yml` runs on the 1st of each month (or by hand from the Actions tab): `scripts/refresh.py` switches to the newest Overture release, rebuilds everything, updates the dates the site shows, and opens a pull request with the score changes for the owner to merge. If Actions may not open pull requests (Settings > Actions > General), it leaves a `data-refresh-YYYY-MM` branch instead.

Green space (22 Nov): the green measure is now half green cover, half the nearest park (OSM parks via Overture land use; 100 within 250 m, 0 from 2 km). Buses were tested and left out: OSM maps only about 650 stops city-wide (20 of 88 areas show none within 1 km, Kukatpally 3), so they stay unscored until TSRTC's GTFS licence is confirmed. Still 5 of 21 measures.

Next, in order: analytics and a custom domain (need the owner's accounts), move scoring into `build_scores.py`, one static page per locality, then new measures (bus stops, parks).

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

- **88 localities in 5 zones:** West 33, Central 16, North 14, East 13, South 12 (`data/centres.json`).
- **Score out of 100 from 5 measures around each centre (1 km for schools and daily needs, 2 km for healthcare and green):** schools, healthcare, daily needs (groceries, pharmacies, banks/ATMs), distance to the nearest *operating* metro station, and green cover.
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
python3 scripts/build_site.py     # wraps src/page.html into index.html and writes the locality pages and sitemap; ALWAYS run after editing the page or data
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
