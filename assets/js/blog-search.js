(function () {
  const root = document.getElementById("blog-search");
  if (!root || !window.BlogSearchCore) return;

  const form = document.getElementById("blog-search-form");
  const input = document.getElementById("blog-search-query");
  const status = document.getElementById("search-status");
  const fallback = document.getElementById("search-fallback");
  const results = document.querySelector("#search-results ol");
  const labels = {
    results: root.dataset.searchResults,
    oneResult: root.dataset.searchOneResult,
    none: root.dataset.searchNone,
    error: root.dataset.searchError,
    tag: root.dataset.searchTagLabel,
    frenchMarker: root.dataset.searchFrenchMarker,
    frenchLabel: root.dataset.searchFrenchLabel,
  };
  let postsPromise;
  let debounce;

  function format(template, values) {
    return template.replace(/\{(n|q|tag)\}/g, (_, key) => values[key] ?? "");
  }

  function updateAddressBar(query) {
    const url = new URL(window.location.href);
    if (query) url.searchParams.set("q", query);
    else url.searchParams.delete("q");
    window.history.replaceState(null, "", url);
  }

  function loadPosts() {
    if (!postsPromise) {
      postsPromise = fetch("/blog/search.json").then((response) => {
        if (!response.ok) throw new Error("Search index request failed");
        return response.json();
      }).then((posts) => {
        if (!Array.isArray(posts)) throw new Error("Search index must be an array");
        fallback.hidden = true;
        return posts;
      });
    }
    return postsPromise;
  }

  function renderPost(post) {
    const item = document.createElement("li");
    item.className = "post-item";

    const title = document.createElement("a");
    title.className = "post-link";
    title.href = post.url;
    title.textContent = post.title;
    item.append(title);

    const metadata = document.createElement("p");
    metadata.className = "post-meta";
    const date = document.createElement("time");
    date.dateTime = post.date;
    const parsedDate = new Date(post.date);
    date.textContent = Number.isNaN(parsedDate.getTime())
      ? post.date
      : new Intl.DateTimeFormat(root.dataset.searchLocale, { dateStyle: "medium" }).format(parsedDate);
    metadata.append(date);

    if (post.lang === "fr") {
      const marker = document.createElement("span");
      marker.className = "translation-label";
      marker.textContent = labels.frenchMarker;
      marker.setAttribute("aria-label", labels.frenchLabel);
      metadata.append(" · ", marker);
    }
    item.append(metadata);

    const excerpt = document.createElement("p");
    excerpt.className = "excerpt";
    excerpt.textContent = post.excerpt;
    item.append(excerpt);

    if (post.tags.length) {
      const tagList = document.createElement("p");
      tagList.className = "post-meta";
      for (const [index, tag] of post.tags.entries()) {
        if (index) tagList.append(" ");
        const link = document.createElement("a");
        link.className = "tag";
        link.href = `/blog/tag/${encodeURIComponent(tag)}/`;
        link.textContent = `#${tag}`;
        link.setAttribute("aria-label", format(labels.tag, { tag }));
        tagList.append(link);
      }
      item.append(tagList);
    }
    return item;
  }

  async function runSearch(query) {
    updateAddressBar(query);
    if (!window.BlogSearchCore.normalize(query)) {
      results.replaceChildren();
      status.textContent = "";
      return;
    }

    let posts;
    try {
      posts = await loadPosts();
    } catch {
      results.replaceChildren();
      status.textContent = labels.error;
      return;
    }

    const matches = window.BlogSearchCore.searchPosts(posts, query);
    results.replaceChildren(...matches.map(renderPost));
    status.textContent = matches.length === 0
      ? format(labels.none, { q: query })
      : matches.length === 1
        ? format(labels.oneResult, { q: query })
        : format(labels.results, { n: matches.length, q: query });
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearTimeout(debounce);
    void runSearch(input.value.trim());
  });

  input.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => void runSearch(input.value.trim()), 150);
  });

  const initialQuery = new URLSearchParams(window.location.search).get("q") || "";
  input.value = initialQuery;
  if (initialQuery) void runSearch(initialQuery);
})();
