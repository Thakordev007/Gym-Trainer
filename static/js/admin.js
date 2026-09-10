/**
 * admin.js — custom admin panel interactions. Sidebar drawer + notifications
 * are already handled by main.js (shared selectors: #sidebarToggle,
 * .admin-sidebar). This file covers anything admin-specific.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initToggleUserButtons();
    initUserSearch();
    initBroadcastButton();
    initSettingsSave();
  });

  function csrfHeaders() {
    return (window.FitAI && window.FitAI.csrfHeaders) ? window.FitAI.csrfHeaders() : { "Content-Type": "application/json" };
  }

  /* ---------- Enable/Disable a user ---------- */
  function initToggleUserButtons() {
    document.querySelectorAll(".toggle-user-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const id = btn.dataset.id;
        if (!id) return;
        const confirmed = window.confirm("Change this user's account status?");
        if (!confirmed) return;
        btn.disabled = true;
        fetch("/admin-panel/users/" + id + "/toggle-active/", { method: "POST", headers: csrfHeaders() })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            btn.disabled = false;
            if (!data.ok) return;
            btn.textContent = data.is_active ? "Disable" : "Enable";
            const row = btn.closest("tr");
            const statusCell = row ? row.querySelector("[data-label='Status']") : null;
            if (statusCell) {
              statusCell.innerHTML = data.is_active
                ? '<span class="pill pill-green">Active</span>'
                : '<span class="pill pill-amber">Inactive</span>';
            }
          })
          .catch(function () { btn.disabled = false; });
      });
    });
  }

  /* ---------- Users list search (client-side filter of the rendered table) ---------- */
  function initUserSearch() {
    const input = document.getElementById("userSearch");
    if (!input) return;
    let timer = null;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        const url = new URL(window.location.href);
        if (input.value) url.searchParams.set("q", input.value);
        else url.searchParams.delete("q");
        window.location.href = url.toString();
      }, 500);
    });
  }

  /* ---------- New Broadcast ---------- */
  function initBroadcastButton() {
    const btn = document.getElementById("newBroadcastBtn");
    if (!btn) return;
    btn.addEventListener("click", function () {
      const text = window.prompt("Broadcast message to all users:");
      if (!text) return;
      btn.disabled = true;
      fetch("/admin-panel/notifications/broadcast/", {
        method: "POST", headers: csrfHeaders(), body: JSON.stringify({ text: text }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          btn.disabled = false;
          if (data.ok) {
            window.alert("Broadcast sent to " + data.sent_to + " users.");
            window.location.reload();
          }
        })
        .catch(function () { btn.disabled = false; });
    });
  }

  /* ---------- Settings save ---------- */
  function initSettingsSave() {
    const saveBtn = document.getElementById("saveAccountBtn");
    const nameInput = document.getElementById("adminName");
    const emailInput = document.getElementById("adminEmail");
    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        saveBtn.disabled = true;
        fetch("/admin-panel/settings/save/", {
          method: "POST", headers: csrfHeaders(),
          body: JSON.stringify({ name: nameInput.value, email: emailInput.value }),
        }).then(function () { saveBtn.disabled = false; });
      });
    }

    // Platform preference checkboxes auto-save on change.
    [["allowRegistrations", "allow_registrations"], ["aiAssistantEnabled", "ai_assistant_enabled"], ["maintenanceMode", "maintenance_mode"]]
      .forEach(function (pair) {
        const el = document.getElementById(pair[0]);
        if (!el) return;
        el.addEventListener("change", function () {
          const payload = {};
          payload[pair[1]] = el.checked;
          fetch("/admin-panel/settings/save/", { method: "POST", headers: csrfHeaders(), body: JSON.stringify(payload) });
        });
      });
  }
})();
