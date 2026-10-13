// End-to-end check of offline support (sw.js): the worker installs and takes
// control, a page read online opens again offline, an unread page falls back
// to the "Signal lost" page in the reader's language, and that page lists
// what is available.
// Usage: node pwa-check.mjs [site-dir]   (default: ../../../_site)
import { chromium } from "playwright";
import { serveSite } from "./serve.mjs";

const SITE = process.argv[2] ?? new URL("../../../_site", import.meta.url).pathname;
const server = await serveSite(SITE);
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch();
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };

try {
  const context = await browser.newContext();
  const page = await context.newPage();

  // Online: first visit installs the worker; the second load is controlled.
  await page.goto(origin + "/about/");
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload();
  check(await page.evaluate(() => Boolean(navigator.serviceWorker.controller)),
    "the service worker does not control the page");
  await page.goto(origin + "/blog/2026/07/a-star-for-my-father/");
  await page.waitForTimeout(300); // let the page copy land in the cache

  // Playwright's setOffline does not reach requests made by the service
  // worker itself, so take the origin down for real: stop the server.
  server.closeAllConnections();
  await new Promise((resolve) => server.close(resolve));

  // A page read online opens offline, styled.
  await page.goto(origin + "/about/");
  check(/I keep production running/.test(await page.textContent("h1")), "/about/ is not served offline");
  const styled = await page.evaluate(() => getComputedStyle(document.body).fontFamily);
  check(/Plex/.test(styled), `offline page lost its stylesheet (font: ${styled})`);

  // An unread page falls back to "Signal lost", in English or French.
  await page.goto(origin + "/now/");
  check(/You are offline/.test(await page.textContent("h1")), "unread English page has no offline fallback");
  await page.waitForSelector("#offline-list li");
  const listed = await page.$$eval("#offline-list a", (links) => links.map((a) => a.getAttribute("href")));
  check(listed.includes("/about/") && listed.includes("/blog/2026/07/a-star-for-my-father/"),
    `offline list misses read pages: ${listed.join(", ")}`);

  await page.goto(origin + "/fr/cv/");
  check(/Vous êtes hors ligne/.test(await page.textContent("h1")), "unread French page has no French fallback");

  await context.close();
} finally {
  await browser.close();
  if (server.listening) server.close();
}

if (failures.length) {
  console.error(failures.map((f) => `✗ ${f}`).join("\n"));
  process.exit(1);
}
console.log("Offline support: all checks passed.");
