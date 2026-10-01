const test = require("node:test");
const assert = require("node:assert/strict");

const { formatDate, normalize, searchPosts } = require("../../../assets/js/blog-search-core.js");

test("normalize_removes_accents_and_normalizes_hyphens", () => {
  assert.equal(normalize("Données machine-learning"), "donnees machine learning");
});

test("search_requires_every_token_across_fields", () => {
  const posts = [
    { title: "Machine learning", excerpt: "", tags: [] },
    { title: "Machine", excerpt: "Learning from the results", tags: [] },
    { title: "Machine", excerpt: "A different topic", tags: [] },
  ];

  assert.deepEqual(searchPosts(posts, "machine learning"), posts.slice(0, 2));
});

test("search_scores_tag_then_title_then_excerpt", () => {
  const posts = [
    { title: "Machine", excerpt: "", tags: [] },
    { title: "Unrelated", excerpt: "", tags: ["machine-learning"] },
    { title: "Unrelated", excerpt: "Machine matters", tags: [] },
  ];

  assert.deepEqual(searchPosts(posts, "machine"), [posts[1], posts[0], posts[2]]);
});

test("search_breaks_score_ties_by_newest_date", () => {
  const older = { title: "Machine", excerpt: "", tags: [], date: "2024-01-01" };
  const newer = { title: "Machine", excerpt: "", tags: [], date: "2025-01-01" };

  assert.deepEqual(searchPosts([older, newer], "machine"), [newer, older]);
});

test("search_empty_query_returns_no_results", () => {
  assert.deepEqual(searchPosts([{ title: "Any post" }], ""), []);
});

test("search_punctuation_only_query_returns_no_results", () => {
  assert.deepEqual(searchPosts([{ title: "Any post" }], "!!! — ..."), []);
});

test("format_date_preserves_iso_calendar_day_in_toronto", () => {
  const previousTimezone = process.env.TZ;
  process.env.TZ = "America/Toronto";
  try {
    assert.equal(formatDate("2026-09-26", "en-US"), "Sep 26, 2026");
  } finally {
    if (previousTimezone === undefined) delete process.env.TZ;
    else process.env.TZ = previousTimezone;
  }
});
