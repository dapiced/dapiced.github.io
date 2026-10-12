/* Renders ```mermaid code blocks with the self-hosted Mermaid build.
   The 3.5 MB library is only downloaded on pages that contain a diagram,
   and it is served from this site (no third-party CDN, CSP-friendly). */
(function () {
  "use strict";

  var blocks = document.querySelectorAll("code.language-mermaid");
  if (!blocks.length) return;

  var currentScript = document.currentScript;
  var src = currentScript && currentScript.getAttribute("data-mermaid-src");
  if (!src) return;

  blocks.forEach(function (code) {
    var pre = document.createElement("pre");
    pre.className = "mermaid";
    pre.textContent = code.textContent;
    var wrapper = code.closest("div.highlighter-rouge") || code.closest("pre") || code;
    wrapper.replaceWith(pre);
  });

  var lib = document.createElement("script");
  lib.src = src;
  lib.onload = function () {
    window.mermaid.initialize({ startOnLoad: false, theme: "dark" });
    window.mermaid.run({ querySelector: "pre.mermaid" });
  };
  document.head.appendChild(lib);
})();
