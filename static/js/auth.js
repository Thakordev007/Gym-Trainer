/**
 * auth.js — login, register, forgot-password, and admin-login interactions.
 * Submits real fetch() POSTs to the backend and displays server-side
 * validation errors in the existing .field-error spans.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initPasswordToggles();
    initPasswordStrength();
    initRegisterForm();
    initLoginForm();
    initForgotForm();
    initAdminLoginForm();
    initProfileEditForm();
    initPreferencesForm();
    initChangePasswordForm();
  });

  function csrfHeaders() {
    return (window.FitAI && window.FitAI.csrfHeaders) ? window.FitAI.csrfHeaders() : { "Content-Type": "application/json" };
  }

  function clearErrors(form) {
    form.querySelectorAll(".field-error").forEach(function (el) { el.textContent = ""; });
  }

  function showErrors(form, errors) {
    clearErrors(form);
    Object.keys(errors).forEach(function (field) {
      const el = document.getElementById(field + "Error");
      if (el) {
        el.textContent = errors[field];
      } else {
        window.alert(errors[field]);
      }
    });
  }

  function submitJSON(url, payload) {
    return fetch(url, { method: "POST", headers: csrfHeaders(), body: JSON.stringify(payload) })
      .then(function (r) { return r.json().then(function (data) { return { status: r.status, data: data }; }); });
  }

  /* ---------- Show / hide password ---------- */
  function initPasswordToggles() {
    document.querySelectorAll(".toggle-visibility").forEach(function (btn) {
      btn.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        const inputId = btn.getAttribute("data-toggle-for");
        const input = document.getElementById(inputId);
        if (!input) return;
        const icon = btn.querySelector("i");
        if (input.type === "password") {
          input.type = "text";
          if (icon) icon.className = "bi bi-eye-slash";
          btn.setAttribute("aria-label", "Hide password");
        } else {
          input.type = "password";
          if (icon) icon.className = "bi bi-eye";
          btn.setAttribute("aria-label", "Show password");
        }
      });
    });
  }

  /* ---------- Password strength meter ---------- */
  function initPasswordStrength() {
    const pwd = document.getElementById("password");
    const bar = document.querySelector("#passwordStrength .password-strength__bar span");
    const label = document.querySelector("#passwordStrength .password-strength__label");
    if (!pwd || !bar || !label) return;

    pwd.addEventListener("input", function () {
      const score = scorePassword(pwd.value);
      const levels = [
        { min: 0, width: "0%", color: "var(--red)", text: "Enter a password" },
        { min: 1, width: "25%", color: "var(--red)", text: "Weak" },
        { min: 2, width: "55%", color: "var(--amber)", text: "Fair" },
        { min: 3, width: "80%", color: "var(--green)", text: "Good" },
        { min: 4, width: "100%", color: "var(--green)", text: "Strong" }
      ];
      const level = levels.filter(function (l) { return score >= l.min; }).pop();
      bar.style.width = level.width;
      bar.style.background = level.color;
      label.textContent = level.text;
    });
  }

  function scorePassword(value) {
    let score = 0;
    if (value.length >= 8) score++;
    if (/[A-Z]/.test(value)) score++;
    if (/[0-9]/.test(value)) score++;
    if (/[^A-Za-z0-9]/.test(value)) score++;
    return value.length === 0 ? 0 : Math.max(score, value.length >= 8 ? 1 : 0);
  }

  /* ---------- Register form ---------- */
  function initRegisterForm() {
    const form = document.getElementById("registerForm");
    if (!form) return;

    const password = document.getElementById("password");
    const confirm = document.getElementById("confirmPassword");
    const confirmError = document.getElementById("confirmPasswordError");

    function validateConfirm() {
      if (confirm.value && confirm.value !== password.value) {
        confirm.classList.add("is-invalid");
        confirmError.textContent = "Passwords do not match.";
        return false;
      }
      confirm.classList.remove("is-invalid");
      confirmError.textContent = "";
      return true;
    }

    confirm.addEventListener("input", validateConfirm);
    password.addEventListener("input", validateConfirm);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      if (!validateConfirm()) return;

      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitJSON("/register/", {
        fullName: form.fullName.value,
        username: form.username.value,
        mobile: form.mobile.value,
        email: form.email.value,
        password: password.value,
        confirmPassword: confirm.value,
        agreeTerms: form.agreeTerms.checked,
      }).then(function (res) {
        submitBtn.disabled = false;
        if (res.data.ok) {
          window.location.href = res.data.redirect;
        } else {
          showErrors(form, res.data.errors || {});
        }
      }).catch(function () { submitBtn.disabled = false; });
    });
  }

  /* ---------- Login form ---------- */
  function initLoginForm() {
    const form = document.getElementById("loginForm");
    if (!form) return;

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitJSON("/login/", {
        loginId: form.loginId.value,
        loginPassword: form.loginPassword.value,
      }).then(function (res) {
        submitBtn.disabled = false;
        if (res.data.ok) {
          window.location.href = res.data.redirect;
        } else {
          showErrors(form, res.data.errors || {});
        }
      }).catch(function () { submitBtn.disabled = false; });
    });
  }

  /* ---------- Forgot password ---------- */
  function initForgotForm() {
    const form = document.getElementById("forgotForm");
    if (!form) return;
    const success = document.getElementById("resetSuccess");

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitJSON("/forgot-password/", { resetEmail: form.resetEmail.value }).then(function (res) {
        submitBtn.disabled = false;
        if (res.data.ok) {
          form.hidden = true;
          success.hidden = false;
        } else {
          showErrors(form, res.data.errors || {});
        }
      }).catch(function () { submitBtn.disabled = false; });
    });
  }

  /* ---------- Admin login ---------- */
  function initAdminLoginForm() {
    const form = document.getElementById("adminLoginForm");
    if (!form) return;

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitJSON("/admin-panel/login/", {
        adminUser: form.adminUser.value,
        adminPassword: form.adminPassword.value,
      }).then(function (res) {
        submitBtn.disabled = false;
        if (res.data.ok) {
          window.location.href = res.data.redirect;
        } else {
          showErrors(form, res.data.errors || {});
        }
      }).catch(function () { submitBtn.disabled = false; });
    });
  }
  /* ---------- Profile edit ---------- */
  function initProfileEditForm() {
    const form = document.getElementById("profileEditForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitJSON("/dashboard/profile/edit/", {
        fullName: form.fullName.value, email: form.email.value, mobile: form.mobile.value,
        age: form.age.value || null, gender: form.gender.value, height: form.height.value || null,
      }).then(function (res) {
        submitBtn.disabled = false;
        if (res.data.ok) window.location.href = res.data.redirect;
        else showErrors(form, res.data.errors || {});
      }).catch(function () { submitBtn.disabled = false; });
    });
  }

  /* ---------- Fitness preferences edit ---------- */
  function initPreferencesForm() {
    const form = document.getElementById("preferencesForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitJSON("/dashboard/profile/preferences/", {
        weight: form.weight.value, targetWeight: form.targetWeight.value, goal: form.goal.value,
        fitnessLevel: form.fitnessLevel.value, workoutDays: form.workoutDays.value, workoutLocation: form.workoutLocation.value,
      }).then(function (res) {
        submitBtn.disabled = false;
        if (res.data.ok) window.location.href = res.data.redirect;
        else showErrors(form, res.data.errors || {});
      }).catch(function () { submitBtn.disabled = false; });
    });
  }

  /* ---------- Change password ---------- */
  function initChangePasswordForm() {
    const form = document.getElementById("changePasswordForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitJSON("/dashboard/profile/change-password/", {
        currentPassword: form.currentPassword.value, newPassword: form.newPassword.value,
        confirmNewPassword: form.confirmNewPassword.value,
      }).then(function (res) {
        submitBtn.disabled = false;
        if (res.data.ok) window.location.href = res.data.redirect;
        else showErrors(form, res.data.errors || {});
      }).catch(function () { submitBtn.disabled = false; });
    });
  }
})();
