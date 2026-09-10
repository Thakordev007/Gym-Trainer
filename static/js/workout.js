/**
 * workout.js — workout detail page (mark complete / add weight-reps-notes)
 * and the active workout session page (rest timer + set tracker).
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initDetailControls();
    initSessionTimer();
    initSetTracker();
  });

  /* ---------- Workout detail page controls ---------- */
  function initDetailControls() {
    document.querySelectorAll(".detail-exercise").forEach(function (card) {
      const id = card.dataset.id;
      const completeBtn = card.querySelector(".detail-exercise__head button");
      if (completeBtn && id) {
        completeBtn.addEventListener("click", function () {
          completeBtn.disabled = true;
          fetch("/dashboard/exercise/" + id + "/toggle/", { method: "POST", headers: window.FitAI.csrfHeaders() })
            .then(function (r) { return r.json(); })
            .then(function (data) {
              completeBtn.disabled = false;
              if (!data.ok) return;
              card.classList.toggle("is-complete", data.done);
              completeBtn.innerHTML = data.done
                ? '<i class="bi bi-check2-all"></i> Completed'
                : '<i class="bi bi-check2"></i> Mark Complete';
              card.style.opacity = data.done ? "0.7" : "1";
            })
            .catch(function () { completeBtn.disabled = false; });
        });
      }

      const [addWeightBtn, addRepsBtn, addNotesBtn] = card.querySelectorAll(".detail-exercise__controls button");
      const weightEl = card.querySelector(".detail-exercise__grid div:nth-child(4) strong");
      const repsEl = card.querySelector(".detail-exercise__grid div:nth-child(2) strong");

      function saveLog(payload) {
        if (!id) return;
        fetch("/dashboard/exercise/" + id + "/log/", {
          method: "POST", headers: window.FitAI.csrfHeaders(), body: JSON.stringify(payload),
        });
      }

      if (addWeightBtn && weightEl) {
        addWeightBtn.addEventListener("click", function () {
          const current = parseFloat(weightEl.textContent) || 0;
          const next = current + 2.5;
          weightEl.textContent = next + " kg";
          saveLog({ weight_kg: next });
        });
      }
      if (addRepsBtn && repsEl) {
        addRepsBtn.addEventListener("click", function () {
          const current = parseInt(repsEl.textContent, 10) || 0;
          const next = current + 1;
          repsEl.textContent = next;
          saveLog({ reps: next });
        });
      }
      if (addNotesBtn) {
        addNotesBtn.addEventListener("click", function () {
          const note = window.prompt("Add a note for this exercise:");
          if (note) {
            addNotesBtn.setAttribute("title", note);
            saveLog({ notes: note });
          }
        });
      }
    });
  }

  /* ---------- Active workout session: rest timer ---------- */
  function initSessionTimer() {
    const display = document.getElementById("timerDisplay");
    if (!display) return;
    const shell = document.querySelector(".session-shell");
    const defaultSeconds = (shell && parseInt(shell.dataset.restSeconds, 10)) || 45;

    let seconds = defaultSeconds;
    let intervalId = null;

    function render() {
      const m = Math.floor(seconds / 60).toString().padStart(2, "0");
      const s = (seconds % 60).toString().padStart(2, "0");
      display.textContent = m + ":" + s;
    }

    document.getElementById("timerStartBtn").addEventListener("click", function () {
      if (intervalId) return;
      intervalId = setInterval(function () {
        seconds = Math.max(0, seconds - 1);
        render();
        if (seconds === 0) {
          clearInterval(intervalId);
          intervalId = null;
        }
      }, 1000);
    });

    document.getElementById("timerPauseBtn").addEventListener("click", function () {
      clearInterval(intervalId);
      intervalId = null;
    });

    document.getElementById("timerResetBtn").addEventListener("click", function () {
      clearInterval(intervalId);
      intervalId = null;
      seconds = defaultSeconds;
      render();
    });

    render();
  }

  /* ---------- Active workout session: set tracker ---------- */
  function initSetTracker() {
    const completeBtn = document.getElementById("completeSetBtn");
    if (!completeBtn) return;
    const success = document.getElementById("sessionSuccess");
    const shell = completeBtn.closest(".session-shell");
    const exId = shell ? shell.dataset.id : null;
    const weightInput = document.getElementById("sessionWeight");
    const repsInput = document.getElementById("sessionReps");
    const setLabel = document.querySelector(".session-shell .pill");

    completeBtn.addEventListener("click", function () {
      if (!exId) return;
      completeBtn.disabled = true;
      fetch("/dashboard/workout-session/complete-set/", {
        method: "POST", headers: window.FitAI.csrfHeaders(),
        body: JSON.stringify({
          ex: exId,
          weight_kg: weightInput ? weightInput.value : 0,
          reps: repsInput ? repsInput.value : 0,
        }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          completeBtn.disabled = false;
          if (!data.ok) return;
          const current = document.querySelector(".set-pill.is-current");
          if (current) {
            current.classList.remove("is-current");
            current.classList.add("is-done");
            current.innerHTML = current.textContent.trim() + ' <i class="bi bi-check-lg"></i>';
            const next = current.nextElementSibling;
            if (next && !next.classList.contains("is-done")) {
              next.classList.add("is-current");
            }
          }
          if (setLabel) {
            setLabel.textContent = "Set " + Math.min(data.sets_completed + 1, data.total_sets) + " of " + data.total_sets;
          }
          success.hidden = false;
          setTimeout(function () { success.hidden = true; }, 2200);
        })
        .catch(function () { completeBtn.disabled = false; });
    });
  }
})();
