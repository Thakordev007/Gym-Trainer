/**
 * dashboard.js — interactions shared by dashboard, workout-plan, diet-plan,
 * progress, and activity pages.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initExerciseChecks();
    initActivityFilters();
    initMealAIButtons();
    drawLineChart("weightChart", (window.DEMO_WEIGHT_HISTORY || []).map(function (p) { return p.value; }));
    drawLineChart("adminGrowthChart", window.ADMIN_GROWTH_DATA || [1200, 1850, 2400, 3100, 3700, 4382]);
    drawLineChart("adminProgressChart", window.ADMIN_PROGRESS_DATA || [820, 990, 1050, 1240, 1400, 1610]);
  });

  /* CSRF headers for fetch() calls come from window.FitAI.csrfHeaders() in main.js */

  /* ---------- Mark exercise complete (dashboard + workout detail) ---------- */
  function initExerciseChecks() {
    document.querySelectorAll("[data-exercise] .exercise-card__check").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const card = btn.closest(".exercise-card");
        const id = card.dataset.id;
        if (!id) return;
        btn.disabled = true;
        fetch("/dashboard/exercise/" + id + "/toggle/", { method: "POST", headers: window.FitAI.csrfHeaders() })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            btn.disabled = false;
            if (!data.ok) return;
            card.classList.toggle("is-done", data.done);
            btn.setAttribute("aria-pressed", String(data.done));
            btn.querySelector("i").className = data.done ? "bi bi-check-circle-fill" : "bi bi-circle";
          })
          .catch(function () { btn.disabled = false; });
      });
    });
  }

  /* ---------- Activity page filters ---------- */
  function initActivityFilters() {
    const chips = document.querySelectorAll(".filter-chip");
    if (!chips.length) return;
    const items = document.querySelectorAll(".timeline-item");

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        chips.forEach(function (c) { c.classList.remove("is-active"); });
        chip.classList.add("is-active");
        const filter = chip.dataset.filter;

        items.forEach(function (item) {
          const show = filter === "all" || item.dataset.type === filter;
          item.style.display = show ? "flex" : "none";
        });

        document.querySelectorAll(".timeline-group").forEach(function (group) {
          const visible = Array.prototype.slice
            .call(group.querySelectorAll(".timeline-item"))
            .some(function (i) { return i.style.display !== "none"; });
          group.style.display = visible ? "block" : "none";
        });
      });
    });
  }

  /* ---------- Diet plan: "Ask AI for a meal alternative" ---------- */
  function initMealAIButtons() {
    document.querySelectorAll(".ask-ai-meal").forEach(function (btn) {
      btn.addEventListener("click", function () {
        window.location.href = "/ai-assistant/?prompt=" + encodeURIComponent("Suggest an alternative for this meal");
      });
    });
  }

  /* ---------- Minimal dependency-free line chart for progress/admin ---------- */
  function drawLineChart(svgId, values) {
    const svg = document.getElementById(svgId);
    if (!svg || !values || !values.length) return;

    const width = 600, height = 220, padding = 30;
    const min = Math.min.apply(null, values);
    const max = Math.max.apply(null, values);
    const range = max - min || 1;
    const stepX = (width - padding * 2) / (values.length - 1 || 1);

    const points = values.map(function (v, i) {
      const x = padding + i * stepX;
      const y = height - padding - ((v - min) / range) * (height - padding * 2);
      return [x, y];
    });

    const pathD = points
      .map(function (p, i) { return (i === 0 ? "M" : "L") + p[0].toFixed(1) + "," + p[1].toFixed(1); })
      .join(" ");

    const areaD =
      pathD +
      " L" + points[points.length - 1][0].toFixed(1) + "," + (height - padding) +
      " L" + points[0][0].toFixed(1) + "," + (height - padding) + " Z";

    const dots = points
      .map(function (p) {
        return '<circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="4.5" fill="var(--lime)" stroke="var(--surface)" stroke-width="2"></circle>';
      })
      .join("");

    svg.innerHTML =
      '<defs><linearGradient id="' + svgId + 'Fade" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0%" stop-color="var(--lime)" stop-opacity="0.35"></stop>' +
      '<stop offset="100%" stop-color="var(--lime)" stop-opacity="0"></stop>' +
      "</linearGradient></defs>" +
      '<path d="' + areaD + '" fill="url(#' + svgId + 'Fade)"></path>' +
      '<path d="' + pathD + '" fill="none" stroke="var(--lime)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>' +
      dots;
  }
})();
