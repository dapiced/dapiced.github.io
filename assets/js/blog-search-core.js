(function (root, factory) {
  const api = factory();

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  root.BlogSearchCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function normalize(value) {
    return String(value ?? "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{M}+/gu, "")
      .replace(/[^\p{L}\p{N}]+/gu, " ")
      .trim()
      .replace(/\s+/g, " ");
  }

  function formatDate(value, locale) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value ?? "");
    return new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeZone: "UTC",
    }).format(date);
  }

  function searchPosts(posts, query) {
    const tokens = normalize(query).split(" ").filter(Boolean);
    if (tokens.length === 0) return [];

    return posts
      .map((post, index) => {
        const title = normalize(post.title);
        const excerpt = normalize(post.excerpt);
        const tags = normalize(Array.isArray(post.tags) ? post.tags.join(" ") : post.tags);
        const fields = [title, excerpt, tags];
        let score = 0;

        for (const token of tokens) {
          if (!fields.some((field) => field.includes(token))) return null;
          score += tags.includes(token) ? 3 : title.includes(token) ? 2 : 1;
        }

        return { post, index, score };
      })
      .filter(Boolean)
      .sort((left, right) => {
        if (left.score !== right.score) return right.score - left.score;
        const dateOrder = String(right.post.date || "").localeCompare(String(left.post.date || ""));
        return dateOrder || left.index - right.index;
      })
      .map(({ post }) => post);
  }

  return { formatDate, normalize, searchPosts };
});
