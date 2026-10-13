// Accessibility gate: runs axe-core (WCAG 2.0/2.1/2.2 A + AA) on every page of
// the built sitemap plus the 404 page, at desktop and mobile widths, in both
// themes (Night, and Dawn via prefers-color-scheme: light).
// Fails on "serious" and "critical" violations; "moderate" and "minor" ones
// are printed as warnings so they stay visible without blocking a PR.
//
//   node axe-check.mjs [path/to/_site]
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { chromium } from "playwright";
import { serveSite } from "./serve.mjs";

const require = createRequire(import.meta.url);
const SITE = process.argv[2] || "../../../_site";
const BLOCKING = new Set(["serious", "critical"]);
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const VIEWPORTS = [{ width: 1280, height: 900 }, { width: 375, height: 800 }];
const THEMES = ["dark", "light"];

const axeSource = await readFile(require.resolve("axe-core/axe.min.js"), "utf8");
const sitemap = await readFile(`${SITE}/sitemap.xml`, "utf8");
const paths = [...sitemap.matchAll(/<loc>https?:\/\/[^/]+(\/[^<]*)<\/loc>/g)].map((m) => m[1]);
paths.push("/this-page-does-not-exist/");

const server = await serveSite(SITE);
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const findings = new Map();

for (const colorScheme of THEMES) for (const viewport of VIEWPORTS) {
  // Reduced motion: the starfield and reveal animations do not affect the audit.
  const context = await browser.newContext({ viewport, colorScheme, reducedMotion: "reduce" });
  // Third-party widgets (comments, analytics) are not this site's markup.
  await context.route(/goatcounter|giscus\.app/, (route) => route.abort());
  // Four pages at a time: same results, a fraction of the wall-clock time.
  let next = 0;
  const worker = async () => {
    while (next < paths.length) {
      const path = paths[next++];
      const page = await context.newPage();
      await page.goto(origin + path, { waitUntil: "load" });
      await page.addScriptTag({ content: axeSource });
      const { violations } = await page.evaluate(
        (tags) => window.axe.run(document, { runOnly: { type: "tag", values: tags } }),
        TAGS,
      );
      for (const v of violations) {
        const key = `${v.impact}\t${v.id}`;
        const entry = findings.get(key) || { help: v.help, url: v.helpUrl, hits: [] };
        for (const node of v.nodes) entry.hits.push(`${path} @${viewport.width}px ${colorScheme}  ${node.target.join(" ")}`);
        findings.set(key, entry);
      }
      await page.close();
    }
  };
  await Promise.all([worker(), worker(), worker(), worker()]);
  await context.close();
}
await browser.close();
server.close();

let blocking = 0;
for (const [key, { help, url, hits }] of [...findings].sort()) {
  const [impact, id] = key.split("\t");
  const isBlocking = BLOCKING.has(impact);
  if (isBlocking) blocking += hits.length;
  console.log(`${isBlocking ? "ERROR" : "warn "} [${impact}] ${id}: ${help} (${hits.length})\n        ${url}`);
  for (const hit of hits.slice(0, 5)) console.log(`        - ${hit}`);
  if (hits.length > 5) console.log(`        … ${hits.length - 5} more`);
}
console.log(`axe: ${paths.length} pages x ${VIEWPORTS.length} widths x ${THEMES.length} themes, ${blocking} blocking issue(s)`);
process.exit(blocking ? 1 : 0);
