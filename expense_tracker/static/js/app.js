/**
 * app.js
 * --------------------------------------------------------------------------
 * Shared progressive-enhancement behavior for the Expense Tracker UI.
 * Keeps templates focused on Jinja markup while small interactions live in a
 * reusable JavaScript module.
 * --------------------------------------------------------------------------
 */

/* Creates a single namespace for UI helpers without polluting the global scope. */
window.ExpenseTrackerUI = window.ExpenseTrackerUI || {};

/**
 * Toggles one password input between hidden and visible states.
 *
 * @param {HTMLButtonElement} button - The button that controls visibility.
 */
window.ExpenseTrackerUI.bindPasswordToggle = function (button) {
  var targetSelector = button.getAttribute("data-password-toggle");
  var input = document.querySelector(targetSelector);
  var icon = button.querySelector("i");

  if (!input || !icon) {
    return;
  }

  button.addEventListener("click", function () {
    var nextType = input.type === "password" ? "text" : "password";

    input.type = nextType;
    icon.classList.toggle("bi-eye", nextType === "password");
    icon.classList.toggle("bi-eye-slash", nextType === "text");
  });
};

/**
 * Enables password visibility toggles declared with data-password-toggle.
 */
window.ExpenseTrackerUI.initPasswordToggles = function () {
  document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
    window.ExpenseTrackerUI.bindPasswordToggle(button);
  });
};

/**
 * Applies a loading label to forms marked for submit feedback.
 */
window.ExpenseTrackerUI.initSubmitFeedback = function () {
  document.querySelectorAll("[data-loading-form]").forEach(function (form) {
    form.addEventListener("submit", function () {
      var button = form.querySelector("[data-loading-label]");

      if (!button) {
        return;
      }

      button.disabled = true;
      button.textContent = button.getAttribute("data-loading-label");
    });
  });
};

/**
 * Boots shared UI interactions after the DOM is ready.
 */
document.addEventListener("DOMContentLoaded", function () {
  window.ExpenseTrackerUI.initPasswordToggles();
  window.ExpenseTrackerUI.initSubmitFeedback();
});
