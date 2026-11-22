// Browser smoke test: the site must load with no script errors, show the same scores as the data file,
// open a locality, and fit a phone screen. Serve the repo first: python3 -m http.server 8765, then: node scripts/smoke.js
const { chromium } = require("playwright");
const BASE = process.env.BASE || "http://localhost:8765/";
const fail = [];

(async () => {
  const b = await chromium.launch();
  for (const width of [1280, 390]) {
    const p = await b.newPage({ viewport: { width, height: 900 } });
    p.on("pageerror", e => fail.push(`${width}px: script error: ${e.message}`));
    await p.goto(BASE, { waitUntil: "load" });
    await p.waitForFunction(() => window.locs && Object.keys(locs).length > 0, null, { timeout: 30000 });
    const r = await p.evaluate(async () => {
      const raw = await (await fetch("data/localities.json")).json();
      return { n: raw.length, cards: document.querySelectorAll(".loc").length, wide: document.documentElement.scrollWidth > innerWidth + 1,
               off: raw.filter(d => locs[d.name].score !== d.score || locs[d.name].rank !== d.rank).map(d => d.name) };
    });
    if (r.off.length) fail.push(`${width}px: page scores differ from the data file for ${r.off.join(", ")}`);
    if (!r.cards) fail.push(`${width}px: no locality cards shown`);
    if (r.wide) fail.push(`${width}px: the page scrolls sideways`);
    await p.evaluate(() => openLocality(Object.keys(locs)[0]));
    if (!(await p.locator("#drawer .bar b").isVisible())) fail.push(`${width}px: the locality panel did not open`);
    console.log(`${width}px: ${r.n} localities, ${r.cards} cards shown`);
  }
  const lp = await b.newPage();
  lp.on("pageerror", e => fail.push(`locality page: script error: ${e.message}`));
  const res = await lp.goto(BASE + "locality/kondapur/");
  if (!res.ok() || (await lp.locator("h1").innerText()) !== "Kondapur") fail.push("locality/kondapur/ did not load");
  await b.close();
  if (fail.length) { console.error(fail.join("\n")); process.exit(1); }
  console.log("Smoke test passed.");
})().catch(e => { console.error(e); process.exit(1); });
