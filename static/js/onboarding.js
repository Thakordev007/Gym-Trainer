/**
 * onboarding.js — multi-step fitness onboarding wizard.
 * Each step posts straight to its Django endpoint (session-backed), so
 * refreshing or coming back later doesn't lose progress like the old
 * sessionStorage-only version did.
 */
(function () {
  "use strict";

  function csrfHeaders() {
    return (window.FitAI && window.FitAI.csrfHeaders) ? window.FitAI.csrfHeaders() : { "Content-Type": "application/json" };
  }

  function postStep(url, payload, onError) {
    return fetch(url, { method: "POST", headers: csrfHeaders(), body: JSON.stringify(payload) })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.ok) {
          window.location.href = data.redirect;
        } else if (onError) {
          onError(data.errors || {});
        }
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initGoalStep();
    initBodyDetailsStep();
    initPreferencesStep();
    initEquipmentStep();
    initSummaryStep();
  });

  /* ---------- Step 1: Goal ---------- */
  function initGoalStep() {
    const grid = document.getElementById("goalGrid");
    if (!grid) return;
    const nextBtn = document.getElementById("goalNextBtn");
    const error = document.getElementById("goalError");

    const cards = Array.prototype.slice.call(grid.querySelectorAll(".goal-card"));
    let selectedGoal = null;
    cards.forEach(function (card) {
      card.addEventListener("click", function () { selectGoal(card); });
    });

    function selectGoal(selected) {
      cards.forEach(function (c) { c.setAttribute("aria-checked", "false"); });
      selected.setAttribute("aria-checked", "true");
      selectedGoal = selected.dataset.value;
      error.textContent = "";
    }

    nextBtn.addEventListener("click", function () {
      if (!selectedGoal) {
        error.textContent = "Please select a fitness goal to continue.";
        return;
      }
      nextBtn.disabled = true;
      postStep("/onboarding/goal/", { goal: selectedGoal }, function (errors) {
        nextBtn.disabled = false;
        error.textContent = errors.goal || "Something went wrong.";
      });
    });
  }

  /* ---------- Step 2: Body details ---------- */
  function initBodyDetailsStep() {
    const form = document.getElementById("bodyDetailsForm");
    if (!form) return;
    const nextBtn = document.getElementById("bodyNextBtn");

    document.querySelectorAll(".unit-toggle").forEach(function (group) {
      const buttons = Array.prototype.slice.call(group.querySelectorAll("button"));
      buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
          buttons.forEach(function (b) { b.classList.remove("is-active"); });
          btn.classList.add("is-active");
        });
      });
    });

    const segmented = document.querySelector(".segmented");
    let fitnessLevel = "Beginner";
    if (segmented) {
      const buttons = Array.prototype.slice.call(segmented.querySelectorAll("button"));
      buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
          buttons.forEach(function (b) { b.classList.remove("is-active"); });
          btn.classList.add("is-active");
          fitnessLevel = btn.dataset.value;
        });
      });
    }

    nextBtn.addEventListener("click", function () {
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      nextBtn.disabled = true;
      postStep("/onboarding/body-details/", {
        age: document.getElementById("age").value,
        gender: document.getElementById("gender").value,
        height: document.getElementById("height").value,
        heightUnit: activeUnit("height"),
        weight: document.getElementById("weight").value,
        weightUnit: activeUnit("weight"),
        targetWeight: document.getElementById("targetWeight").value,
        targetWeightUnit: activeUnit("targetWeight"),
        fitnessLevel: fitnessLevel,
        activityLevel: document.getElementById("activityLevel").value,
        measurements: document.getElementById("measurements").value
      }, function (errors) {
        nextBtn.disabled = false;
        window.alert(Object.values(errors)[0] || "Please check your details and try again.");
      });
    });

    function activeUnit(group) {
      const el = document.querySelector('.unit-toggle[data-unit-group="' + group + '"] .is-active');
      return el ? el.dataset.unit : "";
    }
  }

  /* ---------- Step 3: Preferences ---------- */
  function initPreferencesStep() {
    const panel = document.getElementById("locationChoice");
    if (!panel) return;
    const nextBtn = document.getElementById("prefNextBtn");
    const error = document.getElementById("prefError");

    const groups = {
      location: setupChoiceRow("locationChoice"),
      days: setupChoiceRow("daysChoice"),
      duration: setupChoiceRow("durationChoice"),
      time: setupChoiceRow("timeChoice")
    };

    function setupChoiceRow(id) {
      const row = document.getElementById(id);
      const buttons = Array.prototype.slice.call(row.querySelectorAll("button"));
      let value = null;
      buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
          buttons.forEach(function (b) { b.classList.remove("is-active"); });
          btn.classList.add("is-active");
          value = btn.dataset.value;
        });
      });
      return { get: function () { return value; } };
    }

    nextBtn.addEventListener("click", function () {
      const location = groups.location.get();
      const days = groups.days.get();
      const duration = groups.duration.get();
      const time = groups.time.get();

      if (!location || !days || !duration || !time) {
        error.textContent = "Please answer all four questions to continue.";
        return;
      }
      error.textContent = "";
      nextBtn.disabled = true;
      postStep("/onboarding/workout-preferences/", {
        workoutLocation: location,
        workoutDays: parseInt(days, 10),
        workoutDuration: duration,
        workoutTime: time
      }, function (errors) {
        nextBtn.disabled = false;
        error.textContent = Object.values(errors)[0] || "Something went wrong.";
      });
    });
  }

  /* ---------- Step 4: Equipment ---------- */
  function initEquipmentStep() {
    const gymSection = document.getElementById("gymEquipmentSection");
    if (!gymSection) return;
    const homeSection = document.getElementById("homeEquipmentSection");
    const nextBtn = document.getElementById("equipNextBtn");
    const error = document.getElementById("equipError");

    // Show gym/home sections based on how far the user got — since we no
    // longer keep client-side state, default to showing both sections
    // (harmless: the user just checks whichever applies to them).
    gymSection.hidden = false;
    homeSection.hidden = false;

    nextBtn.addEventListener("click", function () {
      const checked = Array.prototype.slice
        .call(document.querySelectorAll(".equip-card input:checked"))
        .map(function (i) { return i.value; });

      if (checked.length === 0) {
        error.textContent = "Select at least one equipment option.";
        return;
      }
      error.textContent = "";
      nextBtn.disabled = true;
      postStep("/onboarding/equipment/", { equipment: checked }, function (errors) {
        nextBtn.disabled = false;
        error.textContent = errors.equipment || "Something went wrong.";
      });
    });
  }

  /* ---------- Step 5: Summary (rendered server-side; just wire the button) ---------- */
  function initSummaryStep() {
    const btn = document.getElementById("generatePlanBtn");
    if (!btn) return;
    btn.addEventListener("click", function () {
      btn.disabled = true;
      btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Building your plan…';
      fetch("/onboarding/generate/", { method: "POST", headers: csrfHeaders() })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            window.location.href = data.redirect;
          } else {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-stars"></i> Generate My Fitness Plan';
            window.alert("Something went wrong generating your plan. Please try again.");
          }
        })
        .catch(function () {
          btn.disabled = false;
          btn.innerHTML = '<i class="bi bi-stars"></i> Generate My Fitness Plan';
        });
    });
  }
})();
