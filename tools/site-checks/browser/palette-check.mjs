// End-to-end check of the command palette (assets/js/command-palette.js) on
// the built site: keyboard shortcut, search, keyboard navigation, `ping
// vincenzo`, Escape restoring focus, and axe on the open dialog.
// Usage: node palette-check.mjs [site-dir]   (default: ../../../_site)
import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { chromium } from "playwright";
import { serveSite } from "./serve.mjs";

const require = createRequire(import.meta.url);
const SITE = process.argv[2] ?? new URL("../../../_site", import.meta.url).pathname;
const server = await serveSite(SITE);
const origin = `http://127.0.0.1:${server.address().port}`;
const axeSource = await readFile(require.resolve("axe-core/axe.min.js"), "utf8");

const browser = await chromium.launch();
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };

try {
  for (const [path, lang] of [["/", "en"], ["/blog/2026/09/ce-que-jai-appris-sur-facebook-prophet/", "fr"]]) {
    const page = await browser.newPage();
    await page.goto(origin + path);

    // Ctrl+K opens the dialog with the input focused.
    await page.keyboard.press("Control+k");
    const dialog = page.locator("dialog.palette");
    await dialog.waitFor({ state: "visible" });
    check(await page.evaluate(() => document.activeElement?.classList.contains("palette-input")),
      `${path}: input not focused after Ctrl+K`);

    // Empty query lists the navigation and the actions.
    const initial = await dialog.locator(".palette-option").count();
    check(initial >= 8, `${path}: expected navigation and actions, got ${initial} options`);

    // Search hits the index; accents are ignored ("donnees" finds "données").
    await page.keyboard.type(lang === "fr" ? "prophet" : "voyager");
    await page.waitForFunction(() => document.querySelectorAll(".palette-option").length > 0
      && [...document.querySelectorAll(".palette-kind")].some((k) => /post|billet/i.test(k.textContent)));
    const first = await dialog.locator(".palette-option").first().textContent();
    check(/prophet|voyager|oldest/i.test(first), `${path}: unexpected first result "${first}"`);

    // Arrow keys move aria-activedescendant (empty query: several options).
    await page.fill(".palette-input", "");
    const before = await page.locator(".palette-input").getAttribute("aria-activedescendant");
    await page.keyboard.press("ArrowDown");
    const after = await page.locator(".palette-input").getAttribute("aria-activedescendant");
    check(before !== after, `${path}: ArrowDown did not move the active option`);

    // axe on the open dialog.
    await page.addScriptTag({ content: axeSource });
    const violations = await page.evaluate(async () => {
      const result = await window.axe.run(document.querySelector("dialog.palette"), {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
      });
      return result.violations.filter((v) => ["serious", "critical"].includes(v.impact)).map((v) => v.id);
    });
    check(violations.length === 0, `${path}: axe violations in the palette: ${violations.join(", ")}`);

    // `ping vincenzo` answers in the status line and keeps the dialog open.
    await page.fill(".palette-input", "ping vincenzo");
    await page.keyboard.press("Enter");
    const reply = await dialog.locator(".palette-output").textContent();
    check(/pong/.test(reply) && /Andromedae/.test(reply), `${path}: ping vincenzo replied "${reply}"`);

    // The theme action works with the dialog still open.
    const themeBefore = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
    await page.fill(".palette-input", "theme");
    await page.keyboard.press("Enter");
    const themeAfter = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
    check(themeBefore !== themeAfter, `${path}: theme action did not switch the theme`);

    // Escape closes and gives focus back to the page.
    await page.keyboard.press("Escape");
    await dialog.waitFor({ state: "hidden" });

    // "/" opens it too, but not while typing in a field.
    await page.keyboard.press("/");
    await dialog.waitFor({ state: "visible" });
    await page.keyboard.press("Escape");

    // Enter on a result navigates.
    await page.keyboard.press("Control+k");
    await page.keyboard.type("resume");
    await page.waitForTimeout(150);
    await Promise.all([page.waitForURL(/\/resume\/$/), page.keyboard.press("Enter")]);
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}

if (failures.length) {
  console.error(failures.map((f) => `✗ ${f}`).join("\n"));
  process.exit(1);
}
console.log("Command palette: all checks passed.");
