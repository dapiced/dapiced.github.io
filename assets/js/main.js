/* dapiced.github.io - starfield, typed roles, sky widgets */
(function () {
  "use strict";

  /* ---------- starfield canvas ---------- */
  var canvas = document.getElementById("starfield");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (canvas && canvas.getContext) {
    var ctx = canvas.getContext("2d");
    var stars = [];
    var meteor = null;
    var STAR_COUNT = 160;

    /* ✦ Vincenzo D'Apice (1937-2022) - the golden star of this sky.
       /blog/2026/07/a-star-for-my-father/ */
    var gold = { x: 0, y: 0 };
    var goldHover = false;

    /* Night / Dawn: at dawn the stars and shooting stars fade out and only
       Vincenzo's star remains. `night` eases toward 1 (Night) or 0 (Dawn). */
    function isDawn() { return document.documentElement.getAttribute("data-theme") === "light"; }
    var night = isDawn() ? 0 : 1;

    /* Once per visit, his star twinkles "PAPA" in Morse (.--. .- .--. .-),
       an echo of the signal sent across space and time in Interstellar.
       Clicking or tapping the star sends the signal again.
       During the signal the star burns brighter with a wider halo ("on")
       and almost goes out between symbols ("off"), so it reads clearly.
       Timing follows the standard: dot = 1 unit, dash = 3, gap inside a
       letter = 1, gap between letters = 3. */
    var MORSE_UNIT_MS = 240;
    var MORSE_DELAY_MS = 9000;
    var morse = (function () {
      var letters = { P: ".--.", A: ".-" };
      var steps = [];               // [isOn, durationInUnits]
      "PAPA".split("").forEach(function (letter, li) {
        if (li > 0) steps.push([false, 3]);
        letters[letter].split("").forEach(function (sym, si) {
          if (si > 0) steps.push([false, 1]);
          steps.push([true, sym === "." ? 1 : 3]);
        });
      });
      return steps;
    })();
    var morseStart = null;          // timestamp (ms) when the sequence began
    var MORSE_ON = 2.2;             // brightness while a dot/dash is lit
    var MORSE_OFF = 0.12;           // brightness in the gaps
    var MORSE_HALO = 2.2;           // halo radius multiplier while lit

    function morsePulse(t) {
      if (morseStart === null) return null;
      var units = (t - morseStart) / MORSE_UNIT_MS;
      for (var i = 0; i < morse.length; i++) {
        if (units < morse[i][1]) return morse[i][0] ? MORSE_ON : MORSE_OFF;
        units -= morse[i][1];
      }
      morseStart = null;            // sequence finished: back to normal twinkle
      return null;
    }

    function morseAlreadyPlayed() {
      try {
        if (sessionStorage.getItem("papa-morse")) return true;
        sessionStorage.setItem("papa-morse", "1");
      } catch (e) { /* storage blocked: play it, at most once per page */ }
      return false;
    }

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gold.x = canvas.width * 0.76;
      gold.y = canvas.height * 0.22;
    }

    function drawGold(pulse, haloScale) {
      var radius = 16 * (haloScale || 1);
      /* blend from night gold to a deeper dawn gold that reads on a light sky */
      var core = night > 0.5 ? "255,233,168" : "176,118,8";
      var glow = night > 0.5 ? "227,179,65" : "184,134,11";
      var halo = ctx.createRadialGradient(gold.x, gold.y, 0, gold.x, gold.y, radius);
      halo.addColorStop(0, "rgba(" + core + "," + Math.min(1, 0.7 * pulse) + ")");
      halo.addColorStop(0.4, "rgba(" + glow + "," + Math.min(1, 0.28 * pulse) + ")");
      halo.addColorStop(1, "rgba(" + glow + ",0)");
      ctx.globalAlpha = 1;
      ctx.fillStyle = halo;
      ctx.beginPath();
      ctx.arc(gold.x, gold.y, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = night > 0.5 ? "#ffe9a8" : "#a86f00";
      ctx.beginPath();
      ctx.arc(gold.x, gold.y, 1.7 + 0.6 * pulse, 0, Math.PI * 2);
      ctx.fill();
    }

    function makeStars() {
      stars = [];
      for (var i = 0; i < STAR_COUNT; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          r: Math.random() * 1.3 + 0.3,
          base: Math.random() * 0.5 + 0.3,
          amp: Math.random() * 0.45,
          phase: Math.random() * Math.PI * 2,
          speed: Math.random() * 1.2 + 0.4
        });
      }
    }

    function spawnMeteor() {
      meteor = {
        x: Math.random() * canvas.width * 0.7,
        y: Math.random() * canvas.height * 0.25,
        vx: 7 + Math.random() * 5,
        vy: 2.5 + Math.random() * 2,
        life: 1
      };
    }

    /* ~30 fps is plenty for twinkling and halves the CPU/battery cost;
       a shooting star switches to the screen's full rate so it stays smooth.
       Meteor motion is scaled by elapsed time (STEP_MS = one 60 Hz frame),
       so it crosses the sky at the same speed on any refresh rate. */
    var FRAME_MS = 1000 / 30;
    var STEP_MS = 1000 / 60;
    var lastFrame = 0;
    var rafId = null;

    function draw(t) {
      rafId = requestAnimationFrame(draw);
      // 1 ms of slack: a 60 Hz frame two ticks later is 33.33 ms, not 33.34
      if (!meteor && t - lastFrame < FRAME_MS - 1) return;
      var steps = lastFrame ? Math.min((t - lastFrame) / STEP_MS, 4) : 1;
      lastFrame = t;
      /* ~1.2 s fade between Night and Dawn */
      var target = isDawn() ? 0 : 1;
      night += Math.max(-0.028 * steps, Math.min(0.028 * steps, target - night));
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      var sec = t / 1000;

      for (var i = 0; i < stars.length; i++) {
        var s = stars[i];
        /* under reduced motion only the golden star moves (click replay) */
        var alpha = reduceMotion ? s.base : s.base + s.amp * Math.sin(sec * s.speed + s.phase);
        ctx.globalAlpha = Math.max(0.05, Math.min(1, alpha)) * night;
        if (night <= 0.01) break;
        ctx.fillStyle = "#dbe9ff";
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
      }

      var signal = morsePulse(t);
      if (signal !== null) {
        drawGold(signal, signal === MORSE_ON ? MORSE_HALO : 1);
      } else if (reduceMotion) {
        /* a replay requested under reduced motion is over: back to still */
        stop();
        drawStatic();
        return;
      } else {
        drawGold((goldHover ? 1.0 : 0.7) + 0.3 * Math.sin(sec * 1.1));
      }

      if (meteor) {
        var m = meteor;
        var grad = ctx.createLinearGradient(m.x - m.vx * 10, m.y - m.vy * 10, m.x, m.y);
        grad.addColorStop(0, "rgba(230,241,255,0)");
        grad.addColorStop(1, "rgba(230,241,255," + (0.85 * m.life) + ")");
        ctx.globalAlpha = night;
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(m.x - m.vx * 10, m.y - m.vy * 10);
        ctx.lineTo(m.x, m.y);
        ctx.stroke();
        m.x += m.vx * steps;
        m.y += m.vy * steps;
        m.life -= 0.012 * steps;
        if (m.life <= 0 || m.x > canvas.width + 150) meteor = null;
      } else if (!reduceMotion && night > 0.5 && Math.random() < 0.0025 * steps) {   // ~one every 7 s
        spawnMeteor();
      }

      ctx.globalAlpha = 1;
    }

    function start() {
      if (rafId === null) rafId = requestAnimationFrame(draw);
    }

    function stop() {
      if (rafId !== null) cancelAnimationFrame(rafId);
      rafId = null;
    }

    function drawStatic() {
      night = isDawn() ? 0 : 1;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (var i = 0; night > 0 && i < stars.length; i++) {
        var s = stars[i];
        ctx.globalAlpha = s.base;
        ctx.fillStyle = "#dbe9ff";
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
      }
      drawGold(goldHover ? 1.15 : 0.85);
      ctx.globalAlpha = 1;
    }

    resize();
    makeStars();
    window.addEventListener("resize", function () {
      resize();
      makeStars();
      if (reduceMotion) drawStatic();
    });

    /* hovering (or tapping) near his star reveals his name;
       clicking (or tapping) it sends "PAPA" again */
    var tip = document.createElement("div");
    tip.className = "gold-tip";
    tip.setAttribute("aria-hidden", "true");
    var french = document.documentElement.lang === "fr";
    tip.innerHTML = '<span class="tip-name">✦ Vincenzo D’Apice</span>' +
                    '<span class="tip-sub">1937-2022 · ' + (french ? "l’étoile de papa" : "Papa’s star") + "</span>";
    document.body.appendChild(tip);

    function revealNear(e) {
      var reach = e.pointerType === "touch" ? 36 : 24;
      var near = Math.hypot(e.clientX - gold.x, e.clientY - gold.y) < reach;
      if (near !== goldHover) {
        goldHover = near;
        tip.classList.toggle("visible", near);
        document.body.classList.toggle("gold-near", near);
        if (reduceMotion) drawStatic();
      }
      if (near) {
        tip.style.left = gold.x + "px";
        tip.style.top = (gold.y + 18) + "px";
      }
    }
    window.addEventListener("pointermove", revealNear, { passive: true });
    window.addEventListener("pointerdown", function (e) {
      revealNear(e);
      /* a click is an explicit request, so it plays even under reduced
         motion (only for the 7 s of the signal); one signal at a time */
      if (goldHover && morseStart === null && !document.hidden) {
        morseStart = performance.now();
        if (reduceMotion) start();
      }
    }, { passive: true });

    /* redraw the still sky when the theme changes under reduced motion */
    document.addEventListener("themechange", function () { if (reduceMotion && rafId === null) drawStatic(); });

    if (reduceMotion) {
      drawStatic();
    } else {
      start();
      /* no animation while the tab is hidden */
      document.addEventListener("visibilitychange", function () {
        if (document.hidden) stop(); else start();
      });
      if (!morseAlreadyPlayed()) {
        setTimeout(function () {
          if (!document.hidden) morseStart = performance.now();
        }, MORSE_DELAY_MS);
      }
    }
  }

  /* ---------- Night / Dawn switch ----------
     theme-init.js already applied the saved or system theme before paint. */
  var themeToggle = document.querySelector(".theme-toggle");
  var themeMeta = document.querySelector('meta[name="theme-color"]');
  function applyTheme(theme, save) {
    document.documentElement.setAttribute("data-theme", theme);
    if (themeMeta) themeMeta.setAttribute("content", theme === "light" ? "#f6f4ef" : "#04060f");
    if (themeToggle) {
      themeToggle.setAttribute("aria-label", themeToggle.getAttribute(
        theme === "light" ? "data-label-to-dark" : "data-label-to-light"));
    }
    if (save) {
      try { localStorage.setItem("theme", theme); } catch (e) { /* storage blocked */ }
    }
    document.dispatchEvent(new CustomEvent("themechange", { detail: theme }));
  }
  applyTheme(document.documentElement.getAttribute("data-theme") || "dark", false);
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var dawn = document.documentElement.getAttribute("data-theme") === "light";
      applyTheme(dawn ? "dark" : "light", true);
    });
  }
  /* follow the system while the visitor has not chosen explicitly */
  if (window.matchMedia) {
    var systemLight = window.matchMedia("(prefers-color-scheme: light)");
    var follow = function (e) {
      var saved = null;
      try { saved = localStorage.getItem("theme"); } catch (err) { /* ignore */ }
      if (saved !== "light" && saved !== "dark") applyTheme(e.matches ? "light" : "dark", false);
    };
    if (systemLight.addEventListener) systemLight.addEventListener("change", follow);
  }

  /* ---------- typed roles ---------- */
  var rolesEl = document.getElementById("typed-roles");
  if (rolesEl) {
    var roles = [
      "Developer - Azure Infrastructure AI",
      "25+ years automating complex systems",
      "MLOps · DataOps · Infrastructure as Code",
      "Kaggle competitor · Data Science student",
      "Stargazer - of night skies and repositories"
    ];
    var ri = 0, ci = 0, deleting = false;

    function typeTick() {
      var word = roles[ri];
      if (!deleting) {
        ci++;
        if (ci === word.length) {
          deleting = true;
          rolesEl.textContent = word.slice(0, ci);
          setTimeout(typeTick, 2200);
          return;
        }
      } else {
        ci--;
        if (ci === 0) {
          deleting = false;
          ri = (ri + 1) % roles.length;
        }
      }
      rolesEl.textContent = word.slice(0, ci);
      setTimeout(typeTick, deleting ? 28 : 55);
    }

    /* The first role is already in the HTML (readable without JavaScript and
       by screen readers through the .sr-only text): pause on it, then erase. */
    if (!reduceMotion) {
      ci = roles[0].length;
      deleting = true;
      setTimeout(typeTick, 2200);
    }
  }

  /* ---------- scroll reveal ---------- */
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("visible");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("visible"); });
  }

  /* ---------- mobile nav ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") links.classList.remove("open");
    });
  }

  /* ---------- printable resume ---------- */
  var printResume = document.querySelector("[data-print-resume]");
  if (printResume) {
    printResume.addEventListener("click", function () {
      window.print();
    });
  }

  /* ---------- visitor counts (GoatCounter) ---------- */
  function fetchCount(path, onCount) {
    fetch("https://dapiced.goatcounter.com/counter/" + path + ".json")
      .then(function (r) {
        if (!r.ok) throw new Error("counter " + r.status);
        return r.json();
      })
      .then(function (d) {
        var n = d.count_unique || d.count;
        if (n && n !== "0") onCount(n);
      })
      .catch(function () { /* no data yet - badge stays hidden */ });
  }

  /* on a post page: count under the title */
  var pv = document.getElementById("post-views");
  if (pv) {
    fetchCount(location.pathname, function (n) {
      document.getElementById("post-views-n").textContent = n;
      pv.hidden = false;
    });
  }

  /* on post lists (blog index, homepage preview): count per item */
  document.querySelectorAll(".list-views").forEach(function (el) {
    fetchCount(el.getAttribute("data-path"), function (n) {
      el.querySelector(".list-views-n").textContent = n;
      el.hidden = false;
    });
  });

  /* ---------- Vincenzo's star, live over Montréal ----------
     Real celestial mechanics: sidereal time -> hour angle -> alt/az
     for RA 00h49m55.1s, DEC +41°11'56.1" seen from Montréal.     */
  var starStatus = document.getElementById("star-status");
  if (starStatus) {
    var D2R = Math.PI / 180;
    var updateStar = function () {
      var RA = 0.83197;               // hours
      var DEC = 41.1989 * D2R;
      var LAT = 45.5019 * D2R;        // Montréal
      var LON = -73.5674;             // degrees east
      var d = Date.now() / 86400000 + 2440587.5 - 2451545.0;
      var gmst = ((18.697374558 + 24.06570982441908 * d) % 24 + 24) % 24;
      var lst = (gmst + LON / 15 + 24) % 24;
      var ha = (((lst - RA) * 15 + 540) % 360) - 180;
      var haR = ha * D2R;
      var alt = Math.asin(
        Math.sin(LAT) * Math.sin(DEC) +
        Math.cos(LAT) * Math.cos(DEC) * Math.cos(haR)
      ) / D2R;
      var az = Math.atan2(
        -Math.sin(haR) * Math.cos(DEC),
        Math.sin(DEC) * Math.cos(LAT) - Math.cos(DEC) * Math.cos(haR) * Math.sin(LAT)
      ) / D2R;
      az = (az + 360) % 360;
      var french = document.documentElement.lang === "fr";
      var index = Math.round(az / 45) % 8;
      var msg;
      if (french) {
        var dirFr = ["nord", "nord-est", "est", "sud-est", "sud", "sud-ouest", "ouest", "nord-ouest"][index];
        var toward = /^[aeiou]/.test(dirFr) ? "vers l’" + dirFr : "vers le " + dirFr;
        if (alt > 5) {
          msg = "✦ En ce moment, l’étoile de Vincenzo brille à " + Math.round(alt) +
                "° au-dessus de l’horizon de Montréal, " + toward + ". Levez les yeux.";
        } else if (alt > 0) {
          msg = "✦ En ce moment, l’étoile de Vincenzo frôle l’horizon de Montréal, " + toward + ".";
        } else {
          msg = "✦ L’étoile de Vincenzo est brièvement sous l’horizon. Elle revient dans quelques heures : " +
                "elle ne quitte presque jamais le ciel de Montréal.";
        }
      } else {
        var dir = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"][index];
        if (alt > 5) {
          msg = "✦ Right now, Vincenzo’s star shines " + Math.round(alt) +
                "° above Montréal’s horizon, to the " + dir + " - look up.";
        } else if (alt > 0) {
          msg = "✦ Right now, Vincenzo’s star is skimming Montréal’s horizon to the " + dir + ".";
        } else {
          msg = "✦ Vincenzo’s star is briefly below the horizon - it returns within hours. " +
                "It almost never leaves Montréal’s sky.";
        }
      }
      starStatus.textContent = msg;
    };
    updateStar();
    setInterval(updateStar, 60000);
  }

  /* ---------- 12 September: Vincenzo's birthday (1937) ---------- */
  var today = new Date();
  if (today.getMonth() === 8 && today.getDate() === 12) {
    var motto = document.getElementById("motto");
    if (motto) motto.classList.add("vincenzo-day");
  }

  /* ---------- footer year ---------- */
  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
