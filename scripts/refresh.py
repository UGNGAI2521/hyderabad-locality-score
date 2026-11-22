"""Monthly data refresh. If Overture has published a newer release, switch to it, rebuild the scores, base map and pages,
and update the dates the site shows. Prints a markdown summary of what changed (used as the pull request text).
Needs: pip install pyarrow rasterio numpy shapely. Run from the repo root: python3 scripts/refresh.py [--force]"""
import datetime, json, os, re, subprocess, sys
import pyarrow.fs as fs

SCORES = "scripts/build_scores.py"
src = open(SCORES).read()
cur = re.search(r'REL = "([^"]+)"', src).group(1)
if os.path.exists("/root/.ccr/ca-bundle.crt"):  # the cloud session's proxy; GitHub's runners need nothing
    os.environ.setdefault("AWS_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
s3 = fs.S3FileSystem(anonymous=True, region="us-west-2", proxy_options=os.environ.get("HTTPS_PROXY") or None, scheme="https")
latest = max(i.base_name for i in s3.get_file_info(fs.FileSelector("overturemaps-us-west-2/release/")) if i.type == fs.FileType.Directory)
if latest <= cur and "--force" not in sys.argv:
    print(f"No refresh: already on the newest Overture release ({cur}).")
    sys.exit(0)

human = lambda d: f"{d.day} {d:%b %Y}"
today, new_day, old_day = datetime.date.today(), datetime.date.fromisoformat(latest[:10]), datetime.date.fromisoformat(cur[:10])
before = {o["name"]: o for o in json.load(open("data/localities.json"))}

open(SCORES, "w").write(src.replace(f'REL = "{cur}"', f'REL = "{latest}"'))
for step in (["scripts/build_scores.py"], ["scripts/build_basemap.py"]):
    subprocess.run([sys.executable, *step], check=True, stdout=sys.stderr)

page = open("src/page.html", encoding="utf-8").read()
page = page.replace(f"release of {human(old_day)}", f"release of {human(new_day)}")
page = re.sub(r"retrieved \d{1,2} \w{3} \d{4}", f"retrieved {human(today)}", page)
page = re.sub(r"Data last updated \d{1,2} \w{3} \d{4}", f"Data last updated {human(today)}", page)
open("src/page.html", "w", encoding="utf-8").write(page)
subprocess.run([sys.executable, "scripts/build_site.py"], check=True, stdout=sys.stderr)

after = json.load(open("data/localities.json"))
moved = sorted((o for o in after if o["name"] in before), key=lambda o: -abs(o["score"] - before[o["name"]]["score"]))
print(f"## Monthly data refresh: Overture {cur} → {latest}\n")
print(f"Scores, base map, locality pages and sitemap rebuilt for {len(after)} localities; the site's dates now read {human(today)}.")
print("Check the changes below, then merge this pull request to publish them.\n")
print("**Top 10:** " + ", ".join(f"{o['name']} {o['score']}" for o in sorted(after, key=lambda o: o["rank"])[:10]) + "\n")
print("| Locality | Score before | Score after | Rank before | Rank after |\n|---|---|---|---|---|")
for o in [o for o in moved if o["score"] != before[o["name"]]["score"]][:15]:
    b = before[o["name"]]
    print(f"| {o['name']} | {b['score']} | {o['score']} | {b['rank']} | {o['rank']} |")
if all(o["score"] == before[o["name"]]["score"] for o in moved):
    print("| (no score changed) | | | | |")
