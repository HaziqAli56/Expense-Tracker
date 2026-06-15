/**
 * transaction_list.js
 * --------------------------------------------------------------------------
 * Frontend helpers for the Transaction History page.
 *
 * Responsibilities:
 * - Upload CSV/XLSX files to the secure import API.
 * - Show validation errors from pandas/backend import checks.
 * - Refresh the page after a successful import so the new rows are visible.
 * --------------------------------------------------------------------------
 */

(function () {
  /**
   * Return an element by id.
   *
   * @param {string} id - DOM id to find.
   * @returns {HTMLElement|null} Matching element or null.
   */
  function byId(id) {
    return document.getElementById(id);
  }

  /**
   * Show import status inside the modal.
   *
   * @param {string} message - User-facing status text.
   * @param {"info"|"success"|"warning"|"danger"} tone - Bootstrap alert tone.
   */
  function setImportStatus(message, tone) {
    var status = byId("transactionImportStatus");

    if (!status) {
      return;
    }

    status.className = "alert alert-" + (tone || "info") + " py-2 small";
    status.textContent = message;
  }

  /**
   * Convert API validation details into a concise readable message.
   *
   * @param {object} payload - JSON response returned by the import API.
   * @returns {string} Human-readable error message.
   */
  function importErrorMessage(payload) {
    if (Array.isArray(payload.details) && payload.details.length) {
      return payload.error + " " + payload.details.slice(0, 4).join(" ");
    }

    return payload.error || "Import failed.";
  }

  /**
   * Validate the file extension before uploading to save a pointless request.
   *
   * Backend validation remains authoritative; this is only a UX improvement.
   *
   * @param {File} file - Selected import file.
   * @returns {boolean} Whether the extension is allowed.
   */
  function isAllowedImportFile(file) {
    var name = file && file.name ? file.name.toLowerCase() : "";

    return name.endsWith(".csv") || name.endsWith(".xlsx");
  }

  /**
   * Check the selected file against the backend-configured upload limit.
   *
   * @param {File} file - Selected import file.
   * @returns {boolean} Whether the file can be uploaded.
   */
  function isWithinUploadLimit(file) {
    var config = window.TRANSACTION_LIST_CONFIG || {};
    var maxBytes = Number(config.maxUploadBytes || 5 * 1024 * 1024);

    return file && file.size <= maxBytes;
  }

  /**
   * Format the configured upload limit for status messages.
   *
   * @returns {string} Human-readable size in MB.
   */
  function uploadLimitLabel() {
    var config = window.TRANSACTION_LIST_CONFIG || {};
    var maxBytes = Number(config.maxUploadBytes || 5 * 1024 * 1024);

    return (maxBytes / 1024 / 1024).toFixed(0) + " MB";
  }

  /**
   * Upload the selected import file and refresh the table on success.
   *
   * @param {SubmitEvent} event - Modal form submit event.
   */
  async function uploadImport(event) {
    var config = window.TRANSACTION_LIST_CONFIG || {};
    var fileInput = byId("transactionImportFile");
    var submitButton = byId("transactionImportSubmit");
    var file = fileInput && fileInput.files ? fileInput.files[0] : null;

    event.preventDefault();

    if (!file) {
      setImportStatus("Please choose a CSV or XLSX file first.", "warning");
      return;
    }

    if (!isAllowedImportFile(file)) {
      setImportStatus("Only CSV and XLSX files are supported.", "danger");
      return;
    }

    if (!isWithinUploadLimit(file)) {
      setImportStatus("Import file is too large. Maximum allowed size is " + uploadLimitLabel() + ".", "danger");
      return;
    }

    try {
      var formData = new FormData();

      formData.append("file", file);
      setImportStatus("Uploading and validating file...", "info");

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Uploading...";
      }

      var response = await fetch(config.importUrl || "/api/data/transactions/import", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(importErrorMessage(payload));
      }

      setImportStatus((payload.imported_count || 0) + " transactions imported. Refreshing table...", "success");
      window.setTimeout(function () {
        window.location.reload();
      }, 900);
    } catch (error) {
      console.error("[transaction-list] Import failed", error);
      setImportStatus(error.message || "Import failed. Please check the file format.", "danger");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = "Upload Import";
      }
    }
  }

  /**
   * Initialize transaction list tools.
   */
  window.initTransactionListTools = function () {
    var form = byId("transactionImportForm");

    if (form) {
      form.addEventListener("submit", uploadImport);
    }
  };
})();
