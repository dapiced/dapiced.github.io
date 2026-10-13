/* "Signal lost" page: lists the pages the service worker kept (cache
   "pages-v1", see sw.js), so a reader without network knows what still opens. */
(function () {
  "use strict";
  var list = document.getElementById("offline-list");
  var root = document.querySelector(".offline-page");
  if (!list || !root) return;

  function empty() {
    var item = document.createElement("li");
    item.className = "post-item";
    item.textContent = root.getAttribute("data-offline-empty");
    list.appendChild(item);
  }

  if (!("caches" in window)) { empty(); return; }
  caches.open("pages-v1")
    .then(function (cache) { return cache.keys(); })
    .then(function (requests) {
      var paths = requests
        .map(function (request) { return new URL(request.url).pathname; })
        .filter(function (path) { return path !== "/offline/" && path !== "/fr/hors-ligne/"; })
        .sort();
      if (!paths.length) { empty(); return; }
      paths.forEach(function (path) {
        var item = document.createElement("li");
        item.className = "post-item";
        var link = document.createElement("a");
        link.className = "post-link";
        link.href = path;
        link.textContent = path === "/" ? "dominicdapice.com" : path;
        item.appendChild(link);
        list.appendChild(item);
      });
    })
    .catch(empty);
})();
