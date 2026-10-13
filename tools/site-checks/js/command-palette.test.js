const test = require("node:test");
const assert = require("node:assert/strict");

const { normalize, searchPosts } = require("../../../assets/js/blog-search-core.js");
const { matchCommands, searchIndex, isTypingTarget } = require("../../../assets/js/command-palette.js");

const commands = [
  { label: "Blogue", keywords: "/blog/" },
  { label: "Passer au thème Aube", keywords: "theme dark light nuit aube" },
  { label: "ping vincenzo", keywords: "papa star etoile andromeda" },
];

test("empty_query_lists_every_command", () => {
  assert.equal(matchCommands(commands, "  ", normalize).length, 3);
});

test("commands_match_label_or_keywords_without_accents", () => {
  assert.deepEqual(matchCommands(commands, "theme", normalize).map((c) => c.label), ["Passer au thème Aube"]);
  assert.deepEqual(matchCommands(commands, "étoile", normalize).map((c) => c.label), ["ping vincenzo"]);
  assert.deepEqual(matchCommands(commands, "ping vinc", normalize).map((c) => c.label), ["ping vincenzo"]);
});

test("search_prefers_the_readers_language_on_equal_rank", () => {
  const items = [
    { title: "What I learned about Prophet", excerpt: "", tags: ["prophet"], lang: "en", date: "2026-09-26" },
    { title: "Ce que j'ai appris sur Prophet", excerpt: "", tags: ["prophet"], lang: "fr", date: "2026-09-26" },
  ];
  assert.equal(searchIndex(items, "prophet", "fr", searchPosts)[0].lang, "fr");
  assert.equal(searchIndex(items, "prophet", "en", searchPosts)[0].lang, "en");
});

test("search_returns_at_most_eight_results", () => {
  const items = Array.from({ length: 20 }, (_, i) => ({ title: `Azure ${i}`, excerpt: "", tags: [], lang: "en" }));
  assert.equal(searchIndex(items, "azure", "en", searchPosts).length, 8);
});

test("slash_is_ignored_while_typing_in_a_field", () => {
  assert.equal(isTypingTarget({ tagName: "INPUT" }), true);
  assert.equal(isTypingTarget({ tagName: "DIV", isContentEditable: true }), true);
  assert.equal(isTypingTarget({ tagName: "BODY" }), false);
  assert.equal(isTypingTarget(null), false);
});
