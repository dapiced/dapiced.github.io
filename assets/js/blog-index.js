(function () {
  "use strict";

  var list = document.querySelector('ul#all-posts[data-initial="8"]');
  if (!list) return;

  var initialCount = Number.parseInt(list.dataset.initial, 10);
  var items = Array.from(list.querySelectorAll(".post-item"));
  if (!Number.isInteger(initialCount) || initialCount < 0 || items.length <= initialCount) return;

  var fragment = window.location.hash.slice(1);
  if (items.slice(initialCount).some(function (item) { return item.id === fragment; })) return;

  var hiddenItems = items.slice(initialCount);
  hiddenItems.forEach(function (item) { item.hidden = true; });

  var button = document.createElement("button");
  button.type = "button";
  button.className = "btn btn-ghost";
  button.setAttribute("aria-controls", "all-posts");
  button.setAttribute("aria-expanded", "false");
  button.textContent = list.dataset.showMoreTemplate.replace("{n}", list.dataset.hiddenCount);
  list.insertAdjacentElement("afterend", button);

  button.addEventListener("click", function () {
    items.forEach(function (item) { item.removeAttribute("hidden"); });
    button.setAttribute("aria-expanded", "true");
    hiddenItems[0].querySelector(".post-link").focus();
    button.remove();
  });
})();
