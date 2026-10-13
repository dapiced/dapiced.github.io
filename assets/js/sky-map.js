/* "Montréal tonight": the naked-eye sky above Montréal at a chosen time,
   with Vincenzo's star (ν Andromedae) in gold.

   Data: /assets/data/sky-catalog.json (tools/sky-map/build_catalog.py),
   fetched only when the chart scrolls into view.
   Maths: sidereal time -> hour angle -> altitude/azimuth (same formulas as
   the footer status in main.js), then a stereographic projection centred on
   the zenith: the horizon is the outer circle, north at the top, east on the
   left, as seen lying on your back. */
(function (root, factory) {
  var api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.SkyMap = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var D2R = Math.PI / 180;
  var MONTREAL = { lat: 45.5019, lon: -73.5674 };

  /* Local sidereal time in degrees for a date and an east longitude. */
  function siderealDegrees(date, lon) {
    var d = date.getTime() / 86400000 + 2440587.5 - 2451545.0;
    var gmst = 280.46061837 + 360.98564736629 * d;
    return (((gmst + lon) % 360) + 360) % 360;
  }

  /* Equatorial (degrees) -> horizontal {alt, az} in degrees; azimuth from
     north through east. */
  function horizontal(ra, dec, lst, lat) {
    var h = (lst - ra) * D2R;
    var d = dec * D2R;
    var p = lat * D2R;
    var alt = Math.asin(Math.sin(p) * Math.sin(d) + Math.cos(p) * Math.cos(d) * Math.cos(h));
    var az = Math.atan2(-Math.sin(h) * Math.cos(d), Math.sin(d) * Math.cos(p) - Math.cos(d) * Math.cos(h) * Math.sin(p));
    return { alt: alt / D2R, az: ((az / D2R) + 360) % 360 };
  }

  /* Zenith-centred stereographic projection; the horizon maps to radius 1. */
  function project(alt, az) {
    var r = Math.tan((90 - alt) * D2R / 2);
    return { x: -r * Math.sin(az * D2R), y: -r * Math.cos(az * D2R) };
  }

  function compass(az, names) {
    return names[Math.round(az / 45) % 8];
  }

  function init(figure) {
    var canvas = figure.querySelector("canvas");
    var slider = figure.querySelector(".sky-map-time");
    var output = figure.querySelector(".sky-map-clock");
    var now = figure.querySelector(".sky-map-now");
    var status = figure.querySelector(".sky-map-status");
    var t = figure.dataset;
    var dirs = t.directions.split(",");
    var catalog = null;
    var ctx = canvas.getContext("2d");

    var timeFormat = new Intl.DateTimeFormat(t.locale, {
      weekday: "short", hour: "2-digit", minute: "2-digit", timeZone: "America/Toronto",
    });

    function colours() {
      var css = getComputedStyle(document.documentElement);
      var get = function (name) { return css.getPropertyValue(name).trim(); };
      return { bg: get("--bg2") || "#0b1226", text: get("--text"), muted: get("--muted"),
               line: get("--border"), gold: get("--gold"), star: get("--heading") };
    }

    function when() {
      return new Date(Date.now() + Number(slider.value) * 3600000);
    }

    function draw() {
      if (!catalog) return;
      var date = when();
      var size = canvas.clientWidth;
      var dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(size * dpr);
      canvas.height = Math.round(size * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var c = colours();
      var R = size / 2 - 22;
      var cx = size / 2;
      var cy = size / 2;
      var lst = siderealDegrees(date, MONTREAL.lon);
      function xy(p) { return [cx + p.x * R, cy + p.y * R]; }

      ctx.clearRect(0, 0, size, size);
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.fillStyle = c.bg;
      ctx.fill();
      ctx.clip();

      // Altitude rings at 30° and 60°.
      ctx.strokeStyle = c.line;
      ctx.lineWidth = 1;
      [30, 60].forEach(function (alt) {
        ctx.beginPath();
        ctx.arc(cx, cy, Math.tan((90 - alt) * D2R / 2) * R, 0, Math.PI * 2);
        ctx.stroke();
      });

      // Constellation figures.
      ctx.globalAlpha = 0.55;
      Object.keys(catalog.lines).forEach(function (name) {
        catalog.lines[name].forEach(function (segment) {
          ctx.beginPath();
          var drawing = false;
          segment.forEach(function (point) {
            var h = horizontal(point[0], point[1], lst, MONTREAL.lat);
            if (h.alt < -10) { drawing = false; return; }
            var p = xy(project(h.alt, h.az));
            if (drawing) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]);
            drawing = true;
          });
          ctx.stroke();
        });
      });
      ctx.globalAlpha = 1;

      // Stars: brighter is bigger.
      ctx.fillStyle = c.star;
      catalog.stars.forEach(function (star, index) {
        if (index === catalog.vincenzo) return;
        var h = horizontal(star[0], star[1], lst, MONTREAL.lat);
        if (h.alt < 0) return;
        var p = xy(project(h.alt, h.az));
        var r = Math.max(0.6, 2.9 - 0.5 * star[2]) * (size / 600);
        ctx.globalAlpha = Math.min(1, 0.45 + (5 - star[2]) * 0.14);
        ctx.beginPath();
        ctx.arc(p[0], p[1], r, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1;
      ctx.restore();

      // Horizon and cardinal points.
      ctx.strokeStyle = c.muted;
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = c.muted;
      ctx.font = "12px " + getComputedStyle(document.body).getPropertyValue("--mono");
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      [0, 90, 180, 270].forEach(function (az) {
        var p = project(0, az);  // on the horizon circle, then 12 px outside it
        ctx.fillText(dirs[az / 45], cx + p.x * (R + 12), cy + p.y * (R + 12));
      });

      // Vincenzo's star, gold, with its name.
      var v = catalog.stars[catalog.vincenzo];
      var hv = horizontal(v[0], v[1], lst, MONTREAL.lat);
      if (hv.alt >= 0) {
        var pv = xy(project(hv.alt, hv.az));
        ctx.fillStyle = c.gold;
        ctx.globalAlpha = 0.25;
        ctx.beginPath();
        ctx.arc(pv[0], pv[1], 9, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.beginPath();
        ctx.arc(pv[0], pv[1], 3.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.textAlign = "left";
        ctx.fillText("Vincenzo", pv[0] + 12, pv[1]);
      }

      var clock = timeFormat.format(date);
      output.textContent = clock;
      var where = hv.alt >= 0
        ? t.statusUp.replace("{alt}", Math.round(hv.alt)).replace("{dir}", compass(hv.az, dirs))
        : t.statusDown;
      status.textContent = where;
      canvas.setAttribute("aria-label", t.label.replace("{time}", clock) + " " + where);
    }

    function load() {
      fetch(t.catalog)
        .then(function (response) { if (!response.ok) throw new Error(response.status); return response.json(); })
        .then(function (data) { catalog = data; figure.classList.add("is-ready"); draw(); })
        .catch(function () { status.textContent = t.error; });
    }

    slider.addEventListener("input", draw);
    now.addEventListener("click", function () { slider.value = "0"; draw(); });
    window.addEventListener("resize", draw);
    new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    setInterval(function () { if (slider.value === "0") draw(); }, 60000);

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries.some(function (e) { return e.isIntersecting; })) { io.disconnect(); load(); }
      }, { rootMargin: "200px" });
      io.observe(figure);
    } else {
      load();
    }
  }

  if (typeof document !== "undefined") {
    var start = function () { document.querySelectorAll(".sky-map").forEach(init); };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
    else start();
  }

  return { siderealDegrees: siderealDegrees, horizontal: horizontal, project: project, compass: compass };
});
