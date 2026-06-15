/**
 * auth_password.js
 * --------------------------------------------------------------------------
 * Client-side password strength feedback for registration and reset forms.
 * Server-side WTForms validation remains authoritative; this script only helps
 * users fix weak passwords before submitting.
 * --------------------------------------------------------------------------
 */

(function () {
  /**
   * Checks whether a password satisfies the same policy used by Python forms.
   *
   * @param {string} password - Password text entered by the user.
   * @returns {boolean} True when the password meets every policy requirement.
   */
  function isStrongPassword(password) {
    return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/.test(password);
  }

  /**
   * Updates the visible policy hint beside a password input.
   *
   * @param {HTMLInputElement} input - Password input being evaluated.
   */
  function bindPasswordPolicy(input) {
    var status = document.querySelector("[data-password-policy-status]");

    if (!status) {
      return;
    }

    /**
     * Repaints the policy message whenever password strength changes.
     */
    function updateStatus() {
      if (!input.value) {
        status.textContent = "Minimum 8 characters with uppercase, lowercase, number, and special character.";
        status.classList.remove("is-valid", "is-invalid");
        return;
      }

      if (isStrongPassword(input.value)) {
        status.textContent = "Password strength looks good.";
        status.classList.add("is-valid");
        status.classList.remove("is-invalid");
      } else {
        status.textContent = "Add uppercase, lowercase, number, special character, and use at least 8 characters.";
        status.classList.add("is-invalid");
        status.classList.remove("is-valid");
      }
    }

    input.addEventListener("input", updateStatus);
    updateStatus();
  }

  /**
   * Initializes all password fields that opt into policy feedback.
   */
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-password-policy]").forEach(bindPasswordPolicy);
  });
})();
