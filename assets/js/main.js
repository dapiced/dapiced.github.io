/* dapiced.github.io - starfield, typed roles, live projects */
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

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gold.x = canvas.width * 0.76;
      gold.y = canvas.height * 0.22;
    }

    function drawGold(pulse) {
      var halo = ctx.createRadialGradient(gold.x, gold.y, 0, gold.x, gold.y, 16);
      halo.addColorStop(0, "rgba(255,233,168," + 0.7 * pulse + ")");
      halo.addColorStop(0.4, "rgba(227,179,65," + 0.28 * pulse + ")");
      halo.addColorStop(1, "rgba(227,179,65,0)");
      ctx.globalAlpha = 1;
      ctx.fillStyle = halo;
      ctx.beginPath();
      ctx.arc(gold.x, gold.y, 16, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#ffe9a8";
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

    function draw(t) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      var sec = t / 1000;

      for (var i = 0; i < stars.length; i++) {
        var s = stars[i];
        var alpha = s.base + s.amp * Math.sin(sec * s.speed + s.phase);
        ctx.globalAlpha = Math.max(0.05, Math.min(1, alpha));
        ctx.fillStyle = "#dbe9ff";
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
      }

      drawGold((goldHover ? 1.0 : 0.7) + 0.3 * Math.sin(sec * 1.1));

      if (meteor) {
        var m = meteor;
        var grad = ctx.createLinearGradient(m.x - m.vx * 10, m.y - m.vy * 10, m.x, m.y);
        grad.addColorStop(0, "rgba(230,241,255,0)");
        grad.addColorStop(1, "rgba(230,241,255," + (0.85 * m.life) + ")");
        ctx.globalAlpha = 1;
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(m.x - m.vx * 10, m.y - m.vy * 10);
        ctx.lineTo(m.x, m.y);
        ctx.stroke();
        m.x += m.vx;
        m.y += m.vy;
        m.life -= 0.012;
        if (m.life <= 0 || m.x > canvas.width + 150) meteor = null;
      } else if (Math.random() < 0.0025) {
        spawnMeteor();
      }

      ctx.globalAlpha = 1;
      requestAnimationFrame(draw);
    }

    function drawStatic() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (var i = 0; i < stars.length; i++) {
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

    /* hovering near his star reveals his name */
    var tip = document.createElement("div");
    tip.className = "gold-tip";
    tip.setAttribute("aria-hidden", "true");
    tip.innerHTML = '<span class="tip-name">✦ Vincenzo D’Apice</span>' +
                    '<span class="tip-sub">1937-2022 · Papa’s star</span>';
    document.body.appendChild(tip);

    window.addEventListener("mousemove", function (e) {
      var near = Math.hypot(e.clientX - gold.x, e.clientY - gold.y) < 24;
      if (near !== goldHover) {
        goldHover = near;
        tip.classList.toggle("visible", near);
        if (reduceMotion) drawStatic();
      }
      if (near) {
        tip.style.left = gold.x + "px";
        tip.style.top = (gold.y + 18) + "px";
      }
    }, { passive: true });

    if (reduceMotion) {
      drawStatic();
    } else {
      requestAnimationFrame(draw);
    }
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

    if (reduceMotion) {
      rolesEl.textContent = roles[0];
    } else {
      typeTick();
    }
  }

  /* ---------- live projects from GitHub API ---------- */
  var grid = document.getElementById("projects-grid");
  if (grid) {
    var LANG_COLORS = {
      Python: "#3572A5", R: "#198CE7", HTML: "#e34c26", CSS: "#563d7c",
      Shell: "#89e051", JavaScript: "#f1e05a", PowerShell: "#012456",
      Jinja: "#a52a22", Dockerfile: "#384d54", Perl: "#0298c3",
      "Jupyter Notebook": "#DA5B0B"
    };

    fetch("https://api.github.com/users/dapiced/repos?per_page=100&sort=updated")
      .then(function (r) {
        if (!r.ok) throw new Error("GitHub API " + r.status);
        return r.json();
      })
      .then(function (repos) {
        var own = repos.filter(function (r) {
          return !r.fork && r.name !== "dapiced" && r.name !== "dapiced.github.io";
        });
        own.sort(function (a, b) {
          var d = b.stargazers_count - a.stargazers_count;
          return d !== 0 ? d : (a.updated_at < b.updated_at ? 1 : -1);
        });
        grid.innerHTML = "";
        own.slice(0, 9).forEach(function (repo) {
          var card = document.createElement("a");
          card.className = "project-card reveal";
          card.href = repo.html_url;
          card.target = "_blank";
          card.rel = "noopener";

          var name = document.createElement("span");
          name.className = "project-name";
          name.textContent = repo.name;

          var desc = document.createElement("span");
          desc.className = "project-desc";
          var d = (repo.description || "Automation project").replace(/\*\*/g, "");
          desc.textContent = d.length > 130 ? d.slice(0, 129) + "…" : d;

          var meta = document.createElement("span");
          meta.className = "project-meta";
          var parts = [];
          if (repo.language) {
            var dot = '<span class="lang-dot" style="background:' +
              (LANG_COLORS[repo.language] || "#bc8cff") + '"></span>';
            parts.push(dot + repo.language);
          } else if ((repo.topics || []).indexOf("ansible") !== -1) {
            parts.push('<span class="lang-dot" style="background:#EE0000"></span>Ansible');
          }
          parts.push("★ " + repo.stargazers_count);
          if (repo.forks_count > 0) parts.push("⑂ " + repo.forks_count);
          meta.innerHTML = parts.map(function (p) { return "<span>" + p + "</span>"; }).join("");

          card.appendChild(name);
          card.appendChild(desc);
          card.appendChild(meta);
          grid.appendChild(card);
          requestAnimationFrame(function () { card.classList.add("visible"); });
        });
      })
      .catch(function () {
        grid.innerHTML = '<p class="projects-note">Telemetry link temporarily down - ' +
          'browse everything directly on <a href="https://github.com/dapiced?tab=repositories">GitHub</a>.</p>';
      });
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
      var dirs = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"];
      var dir = dirs[Math.round(az / 45) % 8];
      var msg;
      if (alt > 5) {
        msg = "✦ Right now, Vincenzo’s star shines " + Math.round(alt) +
              "° above Montréal’s horizon, to the " + dir + " - look up.";
      } else if (alt > 0) {
        msg = "✦ Right now, Vincenzo’s star is skimming Montréal’s horizon to the " + dir + ".";
      } else {
        msg = "✦ Vincenzo’s star is briefly below the horizon - it returns within hours. " +
              "It almost never leaves Montréal’s sky.";
      }
      starStatus.textContent = msg;
    };
    updateStar();
    setInterval(updateStar, 60000);
  }

  /* ---------- footer year ---------- */
  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
