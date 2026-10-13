/* Runs before the first paint (loaded without defer in <head>) so the page
   never flashes the wrong theme. Choice order: the visitor's saved choice,
   then the system preference, then Night. External file, not inline, so the
   Content-Security-Policy needs no hash. */
(function () {
  "use strict";
  var theme = null;
  try { theme = localStorage.getItem("theme"); } catch (e) { /* storage blocked */ }
  if (theme !== "light" && theme !== "dark") {
    theme = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  document.documentElement.setAttribute("data-theme", theme);
})();
