/* Renders ```mermaid code blocks with the self-hosted Mermaid build.
   The 3.5 MB library is only downloaded on pages that contain a diagram,
   and only when the first diagram comes near the viewport, so it never
   blocks the main thread while the reader starts the article. It is served
   from this site (no third-party CDN, CSP-friendly). */
(function () {
  "use strict";

  var blocks = document.querySelectorAll("code.language-mermaid");
  if (!blocks.length) return;

  var currentScript = document.currentScript;
  var src = currentScript && currentScript.getAttribute("data-mermaid-src");
  if (!src) return;

  var diagrams = [];
  blocks.forEach(function (code) {
    var pre = document.createElement("pre");
    pre.className = "mermaid";
    pre.tabIndex = 0;   // scrollable until rendered: keep it keyboard-reachable
    pre.textContent = code.textContent;
    var wrapper = code.closest("div.highlighter-rouge") || code.closest("pre") || code;
    wrapper.replaceWith(pre);
    diagrams.push(pre);
  });

  var requested = false;
  function load() {
    if (requested) return;
    requested = true;
    var lib = document.createElement("script");
    lib.src = src;
    lib.onload = function () {
      window.mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        /* the default dark label background (#585858) gives 4.4:1 with the
           label text; this one keeps edge labels above the WCAG AA 4.5:1 */
        themeVariables: { edgeLabelBackground: "#1f2a44" }
      });
      window.mermaid.run({ querySelector: "pre.mermaid" });
    };
    document.head.appendChild(lib);
  }

  if (!("IntersectionObserver" in window)) { load(); return; }
  var observer = new IntersectionObserver(function (entries) {
    if (entries.some(function (e) { return e.isIntersecting; })) {
      observer.disconnect();
      load();
    }
  }, { rootMargin: "800px 0px" });   // start well before the diagram is visible
  diagrams.forEach(function (d) { observer.observe(d); });
})();
