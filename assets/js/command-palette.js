/* Command palette: Ctrl+K, ⌘K or "/" from any page.
   Navigation, actions (theme, language, `ping vincenzo`) and a search over
   /search-index.json, fetched the first time the palette opens.
   ARIA combobox pattern: the input owns a listbox, arrows move the active
   option, Enter opens it, Escape closes the dialog and focus goes back. */
(function (root, factory) {
  var api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.CommandPalette = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var MAX_RESULTS = 8;

  /* Commands match on their label and keywords, accents and case ignored. */
  function matchCommands(commands, query, normalize) {
    var q = normalize(query);
    if (!q) return commands.slice();
    var tokens = q.split(" ");
    return commands.filter(function (command) {
      var haystack = normalize(command.label + " " + (command.keywords || ""));
      return tokens.every(function (token) { return haystack.indexOf(token) !== -1; });
    });
  }

  /* Content results: same ranking as the blog search, pages in the reader's
     language first when two results score the same. */
  function searchIndex(items, query, lang, search) {
    var ranked = search(items, query);
    var position = new Map(ranked.map(function (item, i) { return [item, i]; }));
    return ranked
      .slice()
      .sort(function (a, b) {
        var la = a.lang === lang ? 0 : 1;
        var lb = b.lang === lang ? 0 : 1;
        return la - lb || position.get(a) - position.get(b);
      })
      .slice(0, MAX_RESULTS);
  }

  function isTypingTarget(element) {
    if (!element) return false;
    var tag = element.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || element.isContentEditable === true;
  }

  function init() {
    var opener = document.querySelector(".palette-open");
    var core = window.BlogSearchCore;
    if (!opener || !core || typeof HTMLDialogElement === "undefined") return;

    var t = opener.dataset;
    /* Show the shortcut of the reader's platform on the button. */
    var platform = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
    if (/mac|iphone|ipad/i.test(platform)) opener.dataset.shortcut = "⌘K";
    var lang = document.documentElement.lang === "fr" ? "fr" : "en";
    var kinds = { page: t.kindPage, post: t.kindPost, portfolio: t.kindPortfolio, sky: t.kindSky };
    var indexPromise = null;
    var activeIndex = -1;
    var options = [];
    var lastFocus = null;

    /* ---- dialog ---- */
    var dialog = document.createElement("dialog");
    dialog.className = "palette";
    dialog.setAttribute("aria-label", t.title);
    dialog.innerHTML =
      '<div class="palette-box">' +
      '<div class="palette-field"><span class="palette-prompt" aria-hidden="true">&gt;</span>' +
      '<input class="palette-input" type="text" role="combobox" autocomplete="off" spellcheck="false"' +
      ' aria-autocomplete="list" aria-expanded="true" aria-controls="palette-list"></div>' +
      '<ul class="palette-list" id="palette-list" role="listbox"></ul>' +
      '<p class="palette-output" role="status" aria-live="polite"></p>' +
      '<p class="palette-hint"></p>' +
      "</div>";
    document.body.appendChild(dialog);

    var input = dialog.querySelector(".palette-input");
    var list = dialog.querySelector(".palette-list");
    var output = dialog.querySelector(".palette-output");
    input.placeholder = t.placeholder;
    input.setAttribute("aria-label", t.placeholder);
    list.setAttribute("aria-label", t.results);
    dialog.querySelector(".palette-hint").textContent = t.hint;

    /* ---- commands ---- */
    function commands() {
      var result = [];
      document.querySelectorAll("#nav-links a").forEach(function (link) {
        result.push({
          label: link.textContent.trim(),
          kind: t.kindGo,
          keywords: link.getAttribute("href"),
          run: function () { link.click(); },
        });
      });
      var theme = document.querySelector(".theme-toggle");
      if (theme) {
        result.push({
          label: theme.getAttribute("aria-label"),
          kind: t.kindAction,
          keywords: "theme dark light nuit aube",
          keep: true,
          run: function () { theme.click(); },
        });
      }
      var switcher = document.querySelector(".lang-switch");
      if (switcher) {
        result.push({
          label: switcher.getAttribute("aria-label"),
          kind: t.kindAction,
          keywords: "language langue english francais",
          run: function () { switcher.click(); },
        });
      }
      result.push({
        label: "ping vincenzo",
        kind: t.kindAction,
        keywords: "papa star etoile andromeda",
        keep: true,
        vincenzo: true,
        run: function () {
          var status = typeof window.vincenzoStarStatus === "function" ? window.vincenzoStarStatus() : "";
          output.textContent = t.pingReply + (status ? " " + status : "");
          output.classList.add("palette-vincenzo");
        },
      });
      return result;
    }

    /* ---- rendering ---- */
    function setActive(index) {
      if (!options.length) { activeIndex = -1; input.removeAttribute("aria-activedescendant"); return; }
      activeIndex = (index + options.length) % options.length;
      options.forEach(function (option, i) {
        option.element.setAttribute("aria-selected", i === activeIndex ? "true" : "false");
      });
      var active = options[activeIndex].element;
      input.setAttribute("aria-activedescendant", active.id);
      active.scrollIntoView({ block: "nearest" });
    }

    function addOption(label, meta, run, extraClass) {
      var item = document.createElement("li");
      item.id = "palette-option-" + options.length;
      item.className = "palette-option" + (extraClass ? " " + extraClass : "");
      item.setAttribute("role", "option");
      var title = document.createElement("span");
      title.className = "palette-label";
      title.textContent = label;
      var tag = document.createElement("span");
      tag.className = "palette-kind";
      tag.textContent = meta;
      item.append(title, tag);
      item.addEventListener("click", function () { activate(options.indexOf(entry)); });
      var entry = { element: item, run: run };
      options.push(entry);
      list.appendChild(item);
    }

    function render(query, items) {
      list.textContent = "";
      options = [];
      matchCommands(commands(), query, core.normalize).forEach(function (command) {
        addOption(command.label, command.kind, function () {
          /* The page behind a modal dialog is inert: close first, then act. */
          if (!command.keep) close();
          command.run();
        }, command.vincenzo ? "palette-option-vincenzo" : "");
      });
      if (items && query.trim()) {
        searchIndex(items, query, lang, core.searchPosts).forEach(function (item) {
          var meta = kinds[item.kind] || "";
          if (item.lang && item.lang !== lang) meta += " · " + item.lang.toUpperCase();
          addOption(item.title, meta, function () { window.location.href = item.url; });
        });
      }
      if (!options.length) {
        var empty = document.createElement("li");
        empty.className = "palette-empty";
        empty.textContent = t.empty;
        list.appendChild(empty);
      }
      setActive(0);
    }

    function activate(index) {
      if (index >= 0 && options[index]) options[index].run();
    }

    function loadIndex() {
      if (!indexPromise) {
        indexPromise = fetch("/search-index.json")
          .then(function (response) {
            if (!response.ok) throw new Error("index " + response.status);
            return response.json();
          })
          .catch(function () {
            output.textContent = t.error;
            indexPromise = null;
            return [];
          });
      }
      return indexPromise;
    }

    var latest = 0;
    function update() {
      var query = input.value;
      var ticket = ++latest;
      render(query, null);
      if (!query.trim()) return;
      loadIndex().then(function (items) {
        if (ticket === latest) render(query, items);
      });
    }

    /* ---- open / close ---- */
    function open() {
      if (dialog.open) return;
      lastFocus = document.activeElement;
      input.value = "";
      output.textContent = "";
      output.classList.remove("palette-vincenzo");
      render("", null);
      dialog.showModal();
      input.focus();
      loadIndex();
    }

    function close() {
      if (dialog.open) dialog.close();
    }

    dialog.addEventListener("close", function () {
      /* The close event is asynchronous: ignore it if the palette reopened since. */
      if (dialog.open) return;
      if (lastFocus && lastFocus !== document.body && lastFocus.isConnected) lastFocus.focus();
      /* Never leave focus on the hidden input: "/" would then be typed into it. */
      if (dialog.contains(document.activeElement)) document.activeElement.blur();
    });
    /* A click on the backdrop lands on the dialog element itself. */
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) close();
    });

    input.addEventListener("input", update);
    input.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") { event.preventDefault(); setActive(activeIndex + 1); }
      else if (event.key === "ArrowUp") { event.preventDefault(); setActive(activeIndex - 1); }
      else if (event.key === "Home" && options.length) { event.preventDefault(); setActive(0); }
      else if (event.key === "End" && options.length) { event.preventDefault(); setActive(options.length - 1); }
      else if (event.key === "Enter") { event.preventDefault(); activate(activeIndex); }
    });

    opener.addEventListener("click", open);
    document.addEventListener("keydown", function (event) {
      var shortcut = (event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === "k";
      /* The palette's own input still counts as "not typing" in the instant
         between Escape and the dialog's asynchronous close event. */
      var slash = event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey &&
        (!isTypingTarget(event.target) || dialog.contains(event.target));
      if ((shortcut || slash) && !dialog.open) {
        event.preventDefault();
        open();
      }
    });
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  }

  return { matchCommands: matchCommands, searchIndex: searchIndex, isTypingTarget: isTypingTarget };
});
