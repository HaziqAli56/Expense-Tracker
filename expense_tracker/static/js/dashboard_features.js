/**
 * dashboard_features.js
 * --------------------------------------------------------------------------
 * Frontend controller for advanced dashboard features.
 *
 * Responsibilities:
 * - Fetch the expense forecast API and render a Chart.js bar chart.
 * - Fetch category budget alerts and render color-coded progress bars.
 * - Save category budgets through the JSON API without a full page reload.
 *
 * All API calls include credentials so Flask-Login sessions are sent with the
 * request. The backend still performs all ownership checks and validation.
 * --------------------------------------------------------------------------
 */

(function () {
  var forecastChart = null;

  /**
   * Return an element by id.
   *
   * @param {string} id - DOM id to look up.
   * @returns {HTMLElement|null} Matching element or null.
   */
  function byId(id) {
    return document.getElementById(id);
  }

  /**
   * Update a small status alert.
   *
   * @param {string} id - Alert element id.
   * @param {string} message - User-facing status text.
   * @param {"info"|"success"|"warning"|"danger"} tone - Bootstrap alert tone.
   */
  function setStatus(id, message, tone) {
    var element = byId(id);

    if (!element) {
      return;
    }

    element.className = "alert alert-" + (tone || "info") + " py-2 small";
    element.textContent = message;
    element.classList.remove("d-none");
  }

  /**
   * Hide a status alert when there is useful content below it.
   *
   * @param {string} id - Alert element id.
   */
  function hideStatus(id) {
    var element = byId(id);

    if (element) {
      element.classList.add("d-none");
    }
  }

  /**
   * Clamp a percentage for progress bar width while keeping the raw value text.
   *
   * @param {number} value - Raw percentage returned by the API.
   * @returns {number} Width-safe percentage between 0 and 100.
   */
  function clampProgress(value) {
    if (!Number.isFinite(value)) {
      return 0;
    }

    return Math.max(0, Math.min(value, 100));
  }

  /**
   * Choose a Bootstrap progress class from backend alert status.
   *
   * @param {string} status - success, warning, or danger.
   * @returns {string} Bootstrap progress color class.
   */
  function progressClassForStatus(status) {
    if (status === "danger") {
      return "bg-danger";
    }

    if (status === "warning") {
      return "bg-warning";
    }

    return "bg-success";
  }

  /**
   * Render the forecast response into a bar chart and summary message.
   *
   * @param {object} payload - Forecast API response.
   */
  function renderForecast(payload) {
    var canvas = byId("forecastChart");
    var forecastRows = Array.isArray(payload.forecast) ? payload.forecast : [];

    if (!canvas) {
      return;
    }

    if (!forecastRows.length) {
      setStatus(
        "forecastStatus",
        "Not enough expense history yet. Add a few months of expenses to generate a forecast.",
        "warning"
      );
      return;
    }

    hideStatus("forecastStatus");

    if (forecastChart) {
      forecastChart.destroy();
    }

    forecastChart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: forecastRows.map(function (row) {
          return row.category;
        }),
        datasets: [
          {
            label: "Forecast for " + (payload.forecast_month || "next month"),
            data: forecastRows.map(function (row) {
              return row.forecast_amount || 0;
            }),
            backgroundColor: "#EAB308",
            borderColor: "#FACC15",
            borderWidth: 1,
          },
        ],
      },
      options: {
        plugins: {
          legend: {
            position: "top",
          },
        },
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  }

  /**
   * Load forecast data from Flask and render it.
   */
  async function loadForecast() {
    var config = window.DASHBOARD_FEATURE_CONFIG || {};

    try {
      setStatus("forecastStatus", "Loading forecast...", "info");

      var response = await fetch((config.forecastUrl || "/api/forecast/expenses") + "?window=3&months_back=24", {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(payload.error || "Forecast could not be loaded.");
      }

      renderForecast(payload);
    } catch (error) {
      console.error("[dashboard-features] Forecast load failed", error);
      setStatus("forecastStatus", error.message || "Forecast could not be loaded.", "danger");
    }
  }

  /**
   * Render one category budget alert row.
   *
   * @param {object} alert - Budget alert record returned by the API.
   * @returns {HTMLElement} Rendered alert element.
   */
  function createBudgetAlertItem(alert) {
    var wrapper = document.createElement("div");
    var header = document.createElement("div");
    var textGroup = document.createElement("div");
    var title = document.createElement("div");
    var subtitle = document.createElement("div");
    var badge = document.createElement("span");
    var progress = document.createElement("div");
    var progressBar = document.createElement("div");
    var rawPercentage = Number(alert.percentage_used || 0);
    var widthPercentage = clampProgress(rawPercentage);
    var status = alert.status || "success";

    wrapper.className = "border border-white border-opacity-10 rounded-4 p-3";
    header.className = "d-flex justify-content-between gap-3 mb-2";
    title.className = "fw-semibold";
    title.textContent = alert.category || "Unknown category";
    subtitle.className = "text-muted small";
    subtitle.textContent =
      "PKR " +
      Number(alert.spent || 0).toFixed(2) +
      " spent of PKR " +
      Number(alert.limit_amount || 0).toFixed(2);
    badge.className = "badge text-bg-" + status;
    badge.textContent = rawPercentage.toFixed(1) + "%";
    progress.className = "progress";
    progress.style.height = "16px";
    progressBar.className = "progress-bar " + progressClassForStatus(status);
    progressBar.setAttribute("role", "progressbar");
    progressBar.setAttribute("aria-valuenow", String(widthPercentage));
    progressBar.setAttribute("aria-valuemin", "0");
    progressBar.setAttribute("aria-valuemax", "100");
    progressBar.style.width = widthPercentage + "%";

    textGroup.appendChild(title);
    textGroup.appendChild(subtitle);
    header.appendChild(textGroup);
    header.appendChild(badge);
    progress.appendChild(progressBar);
    wrapper.appendChild(header);
    wrapper.appendChild(progress);

    if (rawPercentage >= 90) {
      var warning = document.createElement("div");

      warning.className = "small text-danger mt-2 fw-semibold";
      warning.textContent = "Warning: this category is close to or over budget.";
      wrapper.appendChild(warning);
    }

    return wrapper;
  }

  /**
   * Fetch and render all current-month category budget alerts.
   */
  async function loadBudgetAlerts() {
    var config = window.DASHBOARD_FEATURE_CONFIG || {};
    var list = byId("budgetAlertList");
    var url = (config.budgetAlertsUrl || "/api/budgets/alerts") + "?month=" + encodeURIComponent(config.currentMonth || "");

    if (!list) {
      return;
    }

    try {
      setStatus("budgetAlertStatus", "Loading budget alerts...", "info");

      var response = await fetch(url, {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(payload.error || "Budget alerts could not be loaded.");
      }

      list.innerHTML = "";

      if (!payload.alerts || !payload.alerts.length) {
        setStatus("budgetAlertStatus", "No category budgets yet. Save one above to enable alerts.", "warning");
        return;
      }

      hideStatus("budgetAlertStatus");

      payload.alerts.forEach(function (alert) {
        list.appendChild(createBudgetAlertItem(alert));
      });
    } catch (error) {
      console.error("[dashboard-features] Budget alerts load failed", error);
      setStatus("budgetAlertStatus", error.message || "Budget alerts could not be loaded.", "danger");
    }
  }

  /**
   * Save a category budget through the JSON API.
   *
   * @param {SubmitEvent} event - Form submit event.
   */
  async function saveCategoryBudget(event) {
    var config = window.DASHBOARD_FEATURE_CONFIG || {};
    var categoryInput = byId("budgetCategory");
    var limitInput = byId("budgetLimitAmount");

    event.preventDefault();

    try {
      setStatus("budgetAlertStatus", "Saving category budget...", "info");

      var response = await fetch(config.budgetSaveUrl || "/api/budgets", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          category: categoryInput ? categoryInput.value : "",
          limit_amount: limitInput ? limitInput.value : "",
          month: config.currentMonth,
        }),
      });
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(payload.error || "Category budget could not be saved.");
      }

      if (limitInput) {
        limitInput.value = "";
      }

      setStatus("budgetAlertStatus", "Category budget saved.", "success");
      await loadBudgetAlerts();
    } catch (error) {
      console.error("[dashboard-features] Category budget save failed", error);
      setStatus("budgetAlertStatus", error.message || "Category budget could not be saved.", "danger");
    }
  }

  /**
   * Initialize dashboard advanced feature widgets.
   */
  window.initDashboardAdvancedFeatures = function () {
    var refreshForecastButton = byId("refreshForecastBtn");
    var budgetForm = byId("categoryBudgetForm");

    if (refreshForecastButton) {
      refreshForecastButton.addEventListener("click", loadForecast);
    }

    if (budgetForm) {
      budgetForm.addEventListener("submit", saveCategoryBudget);
    }

    loadForecast();
    loadBudgetAlerts();
  };
})();
