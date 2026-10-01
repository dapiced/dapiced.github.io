const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const BlogSearchCore = require("../../../assets/js/blog-search-core.js");
const searchScript = fs.readFileSync(
  path.resolve(__dirname, "../../../assets/js/blog-search.js"),
  "utf8",
);

function startSearchPage(fetchIndex) {
  const root = {
    dataset: {
      searchResults: "{n} results",
      searchOneResult: "1 result",
      searchNone: "No results",
      searchError: "Search index could not be loaded.",
      searchTagLabel: "Tag {tag}",
      searchFrenchMarker: "FR",
      searchFrenchLabel: "French",
      searchLocale: "en",
    },
  };
  const form = { addEventListener() {} };
  const input = { value: "", addEventListener() {} };
  const status = { textContent: "" };
  const fallback = { hidden: false };
  const results = { replaceChildren() {} };
  const elements = {
    "blog-search": root,
    "blog-search-form": form,
    "blog-search-query": input,
    "search-status": status,
    "search-fallback": fallback,
  };
  const document = {
    getElementById(id) {
      return elements[id] || null;
    },
    querySelector(selector) {
      return selector === "#search-results ol" ? results : null;
    },
  };
  const window = {
    BlogSearchCore,
    history: { replaceState() {} },
    location: { href: "https://example.test/blog/search/", search: "" },
  };
  vm.runInNewContext(searchScript, {
    URL,
    URLSearchParams,
    clearTimeout() {},
    document,
    fetch: fetchIndex,
    setTimeout() { return 1; },
    window,
  });

  return { fallback, status };
}

test("loads_search_index_when_search_page_opens", async () => {
  const requestedUrls = [];
  const page = startSearchPage(async (url) => {
    requestedUrls.push(url);
    return { ok: true, json: async () => [] };
  });
  await new Promise(setImmediate);

  assert.deepEqual(requestedUrls, ["/blog/search.json"]);
  assert.equal(page.fallback.hidden, true);
});

test("reports_initial_index_load_failure_and_keeps_fallback_visible", async () => {
  const page = startSearchPage(async () => ({ ok: false }));
  await new Promise(setImmediate);

  assert.equal(page.status.textContent, "Search index could not be loaded.");
  assert.equal(page.fallback.hidden, false);
});
