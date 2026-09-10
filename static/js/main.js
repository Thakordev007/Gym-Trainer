/**
 * main.js — global interactions shared across every page:
 * mobile hamburger nav, dashboard sidebar drawer, notifications dropdown,
 * profile dropdown, and small utility helpers.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    initHamburger();
    initSidebarDrawer();
    initNotifications();
    initTodayDate();
  }

  /* ---------- Public marketing nav (hamburger) ---------- */
function initHamburger() {

    const btn = document.getElementById("hamburgerBtn");
    const nav = document.getElementById("mobileNav");

    if (!btn || !nav) {
        return;
    }


    btn.addEventListener("click", function () {

        const isOpen = nav.classList.toggle("is-open");

        btn.setAttribute(
            "aria-expanded",
            isOpen ? "true" : "false"
        );


        const icon = btn.querySelector("i");

        if (icon) {

            icon.className = isOpen
                ? "bi bi-x-lg"
                : "bi bi-list";

        }

    });


    /* Close when clicking menu link */

    nav.querySelectorAll("a").forEach(function (link) {

        link.addEventListener("click", function () {

            nav.classList.remove("is-open");

            btn.setAttribute(
                "aria-expanded",
                "false"
            );


            const icon = btn.querySelector("i");

            if (icon) {
                icon.className = "bi bi-list";
            }

        });

    });


    /* Reset when returning to desktop */

    window.addEventListener("resize", function () {

        if (window.innerWidth > 768) {

            nav.classList.remove("is-open");

            btn.setAttribute(
                "aria-expanded",
                "false"
            );

            const icon = btn.querySelector("i");

            if (icon) {
                icon.className = "bi bi-list";
            }

        }

    });

}

  /* ---------- Dashboard / admin off-canvas sidebar ---------- */
  function initSidebarDrawer() {
    const toggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar") || document.querySelector(".admin-sidebar");
    if (!toggle || !sidebar) return;

    let backdrop = document.querySelector(".sidebar-backdrop");
    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.className = "sidebar-backdrop";
      document.body.appendChild(backdrop);
    }

    function closeSidebar() {
      sidebar.classList.remove("is-open");
      backdrop.classList.remove("is-open");
    }

    toggle.addEventListener("click", function () {
      sidebar.classList.add("is-open");
      backdrop.classList.add("is-open");
    });
    backdrop.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeSidebar();
    });
  }

  /* ---------- Notification dropdown ---------- */
  function initNotifications() {
    const btn = document.getElementById("notifBtn");
    const dropdown = document.getElementById("notifDropdown");
    if (!btn || !dropdown) return;

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const isOpen = !dropdown.hidden;
      dropdown.hidden = isOpen;
      btn.setAttribute("aria-expanded", String(!isOpen));
    });

    document.addEventListener("click", function (e) {
      if (!dropdown.hidden && !dropdown.contains(e.target) && e.target !== btn) {
        dropdown.hidden = true;
        btn.setAttribute("aria-expanded", "false");
      }
    });

    const markAllBtn = document.getElementById("markAllReadBtn");
    if (markAllBtn) {
      markAllBtn.addEventListener("click", function () {
        dropdown.querySelectorAll(".notif-item.unread").forEach(function (item) {
          item.classList.remove("unread");
        });
        const badge = btn.querySelector(".badge-dot");
        if (badge) badge.remove();
        fetch("/dashboard/notifications/mark-all-read/", { method: "POST", headers: window.FitAI.csrfHeaders() });
      });
    }
  }

  /* ---------- CSRF helper shared by every page's fetch() calls ---------- */
  function getCookie(name) {
    const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? match.pop() : "";
  }

  /* ---------- Today's date in dashboard header ---------- */
  function initTodayDate() {
    const el = document.getElementById("todayDate");
    if (!el) return;
    const today = new Date();
    el.textContent = today.toLocaleDateString(undefined, {
      weekday: "long",
      month: "short",
      day: "numeric"
    });
  }

  /* Expose small helpers other scripts can reuse */
  window.FitAI = window.FitAI || {};
  window.FitAI.qs = function (sel, ctx) {
    return (ctx || document).querySelector(sel);
  };
  window.FitAI.qsa = function (sel, ctx) {
    return Array.prototype.slice.call((ctx || document).querySelectorAll(sel));
  };
  window.FitAI.csrfHeaders = function (extra) {
    return Object.assign({ "X-CSRFToken": getCookie("csrftoken"), "Content-Type": "application/json" }, extra || {});
  };
})();
