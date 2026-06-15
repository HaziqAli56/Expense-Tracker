/**
 * transaction_form.js
 * --------------------------------------------------------------------------
 * Dynamic Add/Edit Transaction page behavior.
 *
 * Responsibilities:
 * - Fetch main categories and sub-categories from Flask.
 * - Populate dependent category dropdowns.
 * - Apply Quick Data presets that fill type/category/sub-category.
 * - Upload receipt images for OCR-assisted field extraction.
 * - Upload CSV/XLSX files for bulk import.
 *
 * Server-side Flask validation remains authoritative. This script only improves
 * the page's interactivity and keeps the UI synchronized with backend data.
 * --------------------------------------------------------------------------
 */

(function () {
  var state = {
    expenseCategories: {},
    incomeCategoryMap: {},
    incomeCategories: [],
    currencies: [],
    baseCurrency: "PKR",
    initialCategory: "",
    initialSubCategory: "",
    initialCurrency: "",
    categoriesLoaded: false,
    currenciesLoaded: false,
  };

  /**
   * Return a page element by id.
   *
   * @param {string} id - DOM id to find.
   * @returns {HTMLElement|null} Matching element or null.
   */
  function byId(id) {
    return document.getElementById(id);
  }

  /**
   * Log a namespaced debug message for browser console checks.
   *
   * @param {...unknown} args - Values to log.
   */
  function logDebug() {
    console.log.apply(console, ["[transaction-form]"].concat(Array.prototype.slice.call(arguments)));
  }

  /**
   * Show a visible alert message above the form.
   *
   * @param {string} message - User-facing message.
   * @param {"error"|"success"|"info"} tone - Visual tone.
   */
  function showAlert(message, tone) {
    var alertEl = byId("transactionFormAlert");

    if (!alertEl) {
      return;
    }

    var toneClasses = {
      error: "border-rose-300/40 bg-rose-500/15 text-rose-100",
      success: "border-yellow-300/40 bg-yellow-500/15 text-yellow-100",
      info: "border-yellow-300/40 bg-yellow-500/15 text-yellow-100",
    };

    alertEl.className = "mb-5 rounded-2xl border px-4 py-3 text-sm " + (toneClasses[tone] || toneClasses.info);
    alertEl.textContent = message;
    alertEl.classList.remove("hidden");
  }

  /**
   * Hide the visible alert region.
   */
  function clearAlert() {
    var alertEl = byId("transactionFormAlert");

    if (alertEl) {
      alertEl.classList.add("hidden");
      alertEl.textContent = "";
    }
  }

  /**
   * Format a Date as yyyy-mm-dd for native date inputs.
   *
   * @param {Date} date - Date to format.
   * @returns {string} Input-compatible date string.
   */
  function formatDateInputValue(date) {
    var pad = function (number) {
      return number < 10 ? "0" + number : "" + number;
    };

    return date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate());
  }

  /**
   * Populate a select element with option values.
   *
   * @param {HTMLSelectElement} selectEl - Select to populate.
   * @param {string[]} options - Option values and labels.
   * @param {string} selectedValue - Preferred selected value.
   * @param {string} placeholder - Placeholder for empty states.
   */
  function fillSelect(selectEl, options, selectedValue, placeholder) {
    selectEl.innerHTML = "";

    if (!options.length && placeholder) {
      var placeholderOption = document.createElement("option");

      placeholderOption.value = "";
      placeholderOption.textContent = placeholder;
      selectEl.appendChild(placeholderOption);
      return;
    }

    options.forEach(function (optionValue) {
      var option = document.createElement("option");

      option.value = optionValue;
      option.textContent = optionValue;

      if (selectedValue && selectedValue === optionValue) {
        option.selected = true;
      }

      selectEl.appendChild(option);
    });

    if (!selectedValue && options.length) {
      selectEl.selectedIndex = 0;
    }
  }

  /**
   * Populate the currency dropdown from backend-supported currency metadata.
   *
   * @param {string} filterText - Optional search text typed by the user.
   */
  function fillCurrencySelect(filterText) {
    var currencySelect = byId("currency_code");
    var normalizedFilter = (filterText || "").trim().toUpperCase();
    var selectedCurrency = currencySelect ? currencySelect.value || state.initialCurrency || state.baseCurrency : state.baseCurrency;
    var filteredCurrencies = state.currencies.filter(function (currency) {
      var code = String(currency.code || "").toUpperCase();
      var name = String(currency.name || "").toUpperCase();

      return !normalizedFilter || code.indexOf(normalizedFilter) >= 0 || name.indexOf(normalizedFilter) >= 0;
    });

    if (!currencySelect) {
      return;
    }

    currencySelect.innerHTML = "";

    if (!filteredCurrencies.length) {
      var emptyOption = document.createElement("option");

      emptyOption.value = selectedCurrency;
      emptyOption.textContent = "No matching currencies";
      currencySelect.appendChild(emptyOption);
      return;
    }

    filteredCurrencies.forEach(function (currency) {
      var option = document.createElement("option");
      var code = String(currency.code || "").toUpperCase();

      option.value = code;
      option.textContent = code + " - " + (currency.name || code);

      if (code === selectedCurrency) {
        option.selected = true;
      }

      currencySelect.appendChild(option);
    });

    if (!currencySelect.value && filteredCurrencies.length) {
      currencySelect.value = filteredCurrencies[0].code;
    }
  }

  /**
   * Return true when the supplied category/sub-category pair is valid.
   *
   * @param {string} category - Main category.
   * @param {string} subCategory - Dependent sub-category.
   * @returns {boolean} Whether the pair exists in the fetched config.
   */
  function isValidExpensePair(category, subCategory) {
    var subCategories = state.expenseCategories[category] || [];

    return subCategories.indexOf(subCategory) >= 0;
  }

  /**
   * Add a short pop animation to a field group after automatic updates.
   *
   * @param {HTMLElement} element - Element to animate.
   */
  function popElement(element) {
    if (!element) {
      return;
    }

    element.classList.remove("transaction-autofill-pop");
    void element.offsetWidth;
    element.classList.add("transaction-autofill-pop");
  }

  /**
   * Return true when a selected file is under the configured upload limit.
   *
   * @param {File} file - Browser file object.
   * @returns {boolean} Whether file size is acceptable.
   */
  function isWithinUploadLimit(file) {
    var config = window.TRANSACTION_FORM_CONFIG || {};
    var maxBytes = Number(config.maxUploadBytes || 5 * 1024 * 1024);

    return file && file.size <= maxBytes;
  }

  /**
   * Format configured upload limit for user-facing messages.
   *
   * @returns {string} Human-readable MB size.
   */
  function uploadLimitLabel() {
    var config = window.TRANSACTION_FORM_CONFIG || {};
    var maxBytes = Number(config.maxUploadBytes || 5 * 1024 * 1024);

    return (maxBytes / 1024 / 1024).toFixed(0) + " MB";
  }

  /**
   * Enable or disable Quick Data buttons.
   *
   * Buttons start disabled because their presets must be validated against the
   * backend category response before users can apply them.
   *
   * @param {boolean} isEnabled - Whether buttons should be clickable.
   */
  function setQuickButtonsEnabled(isEnabled) {
    var quickButtons = document.querySelectorAll(".quick-data-btn");

    quickButtons.forEach(function (button) {
      button.disabled = !isEnabled;
      button.classList.toggle("opacity-50", !isEnabled);
      button.classList.toggle("cursor-not-allowed", !isEnabled);
    });
  }

  /**
   * Synchronize category options based on the selected transaction type.
   *
   * @param {string} preferredCategory - Category to select if valid.
   */
  function syncCategories(preferredCategory) {
    var typeSelect = byId("entry_type");
    var categorySelect = byId("category");
    var subCategorySelect = byId("sub_category");

    if (!typeSelect || !categorySelect || !subCategorySelect) {
      return;
    }

    var isExpense = typeSelect.value === "expense";
    var categoryMap = isExpense ? state.expenseCategories : state.incomeCategoryMap;
    var categories = Object.keys(categoryMap);
    var selectedCategory = categories.indexOf(preferredCategory) >= 0 ? preferredCategory : "";

    fillSelect(categorySelect, categories, selectedCategory, "No categories available");
    categorySelect.disabled = categories.length === 0;
    syncSubCategories(state.initialSubCategory);
  }

  /**
   * Synchronize sub-category options for the selected main category.
   *
   * @param {string} preferredSubCategory - Sub-category to select if valid.
   */
  function syncSubCategories(preferredSubCategory) {
    var typeSelect = byId("entry_type");
    var categorySelect = byId("category");
    var subCategorySelect = byId("sub_category");

    if (!typeSelect || !categorySelect || !subCategorySelect) {
      return;
    }

    var categoryMap = typeSelect.value === "expense" ? state.expenseCategories : state.incomeCategoryMap;
    var subCategories = categoryMap[categorySelect.value] || [];
    var selectedSubCategory = subCategories.indexOf(preferredSubCategory) >= 0 ? preferredSubCategory : "";

    fillSelect(subCategorySelect, subCategories, selectedSubCategory, "Select a category first");
    subCategorySelect.disabled = subCategories.length === 0;
    subCategorySelect.required = subCategories.length > 0;
  }

  /**
   * Fetch category configuration from Flask and initialize dropdowns.
   *
   * @returns {Promise<void>} Resolves after dropdown setup.
   */
  async function loadCategories() {
    var config = window.TRANSACTION_FORM_CONFIG || {};
    var categoriesUrl = config.categoriesUrl || "/api/categories";
    var categorySelect = byId("category");
    var subCategorySelect = byId("sub_category");

    try {
      var response = await fetch(categoriesUrl, {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Category API returned HTTP " + response.status);
      }

      var payload = await response.json();

      if (!payload.expense_categories || typeof payload.expense_categories !== "object") {
        throw new Error("Category API response is missing expense_categories.");
      }

      state.expenseCategories = payload.expense_categories;
      state.incomeCategoryMap = payload.income_category_map || {};
      state.incomeCategories = Array.isArray(payload.income_categories) ? payload.income_categories : [];
      state.initialCategory = config.initialCategory || "";
      state.initialSubCategory = config.initialSubCategory || "";
      state.categoriesLoaded = true;

      syncCategories(state.initialCategory);
      setQuickButtonsEnabled(true);
      clearAlert();
      logDebug("Categories loaded", payload);
    } catch (error) {
      console.error("[transaction-form] Failed to load categories", error);
      showAlert("Could not load categories. Please refresh the page or check the browser console.", "error");
      state.categoriesLoaded = false;
      setQuickButtonsEnabled(false);

      if (categorySelect) {
        categorySelect.disabled = true;
      }

      if (subCategorySelect) {
        subCategorySelect.disabled = true;
      }
    }
  }

  /**
   * Fetch supported currencies from Flask and initialize the currency dropdown.
   *
   * @returns {Promise<void>} Resolves when the dropdown is ready.
   */
  async function loadCurrencies() {
    var config = window.TRANSACTION_FORM_CONFIG || {};
    var currencySelect = byId("currency_code");

    if (!currencySelect) {
      return;
    }

    try {
      var response = await fetch(config.currencyUrl || "/api/currency/supported", {
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(payload.error || "Currency list could not be loaded.");
      }

      state.baseCurrency = payload.base_currency || config.baseCurrency || "PKR";
      state.initialCurrency = config.initialCurrency || state.baseCurrency;
      state.currencies = Array.isArray(payload.currencies) ? payload.currencies : [{ code: state.baseCurrency, name: state.baseCurrency }];
      state.currenciesLoaded = true;

      fillCurrencySelect("");
      currencySelect.value = state.initialCurrency;
      await updateExchangeRatePreview();
      logDebug("Currencies loaded", payload);
    } catch (error) {
      console.error("[transaction-form] Failed to load currencies", error);
      showAlert("Could not load currencies. Defaulting to " + (config.baseCurrency || "PKR") + ".", "error");
      state.baseCurrency = config.baseCurrency || "PKR";
      state.currencies = [{ code: state.baseCurrency, name: state.baseCurrency }];
      state.currenciesLoaded = false;
      fillCurrencySelect("");
    }
  }

  /**
   * Fetch and apply the selected currency exchange rate to the hidden form field.
   *
   * The backend revalidates exchange_rate during save; this preview simply
   * helps the user understand what dashboard/base-currency value will be used.
   */
  async function updateExchangeRatePreview() {
    var config = window.TRANSACTION_FORM_CONFIG || {};
    var currencySelect = byId("currency_code");
    var exchangeRateInput = byId("exchange_rate");
    var preview = byId("currencyPreview");
    var amountInput = byId("amount");
    var selectedCurrency = currencySelect ? currencySelect.value : state.baseCurrency;
    var baseCurrency = state.baseCurrency || config.baseCurrency || "PKR";
    var amount = amountInput && amountInput.value ? Number(amountInput.value) : 0;

    if (!currencySelect || !exchangeRateInput || !preview) {
      return;
    }

    if (selectedCurrency === baseCurrency) {
      exchangeRateInput.value = "1";
      preview.textContent = "Base currency selected. Dashboard amount will match the entered amount.";
      return;
    }

    try {
      preview.textContent = "Fetching live " + selectedCurrency + " to " + baseCurrency + " rate...";

      var response = await fetch(
        (config.rateUrl || "/api/currency/rate") +
          "?from=" +
          encodeURIComponent(selectedCurrency) +
          "&to=" +
          encodeURIComponent(baseCurrency),
        {
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
        }
      );
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(payload.error || "Exchange rate unavailable.");
      }

      var rate = Number(payload.exchange_rate || 1);
      var convertedAmount = amount > 0 ? " Approx. " + baseCurrency + " " + (amount * rate).toFixed(2) + "." : "";

      exchangeRateInput.value = rate.toString();
      preview.textContent = "1 " + selectedCurrency + " = " + rate.toFixed(4) + " " + baseCurrency + "." + convertedAmount;
    } catch (error) {
      console.error("[transaction-form] Exchange-rate lookup failed", error);
      exchangeRateInput.value = "1";
      preview.textContent = "Live exchange rate unavailable. The backend will safely fall back while saving.";
    }
  }

  /**
   * Apply a Quick Data preset to type/category/sub-category fields.
   *
   * @param {HTMLButtonElement} button - Clicked quick data button.
   */
  function applyQuickData(button) {
    var typeSelect = byId("entry_type");
    var categorySelect = byId("category");
    var subCategorySelect = byId("sub_category");
    var form = byId("transactionForm");
    var amountInput = byId("amount");
    var typeValue = button.dataset.type || "expense";
    var categoryValue = button.dataset.category || "";
    var subCategoryValue = button.dataset.subCategory || "";

    if (!typeSelect || !categorySelect || !subCategorySelect) {
      return;
    }

    if (button.disabled) {
      return;
    }

    if (typeValue === "expense" && !isValidExpensePair(categoryValue, subCategoryValue)) {
      showAlert("Quick Data preset is not valid for the current category configuration.", "error");
      console.error("[transaction-form] Invalid quick data preset", {
        category: categoryValue,
        subCategory: subCategoryValue,
      });
      return;
    }

    typeSelect.value = typeValue;
    syncCategories(categoryValue);
    categorySelect.value = categoryValue;
    syncSubCategories(subCategoryValue);
    subCategorySelect.value = subCategoryValue;
    clearAlert();

    popElement(form);
    popElement(button);

    if (amountInput) {
      amountInput.focus();
    }

    logDebug("Quick Data applied", {
      type: typeValue,
      category: categoryValue,
      subCategory: subCategoryValue,
    });
  }

  /**
   * Upload a receipt image to the OCR endpoint and apply extracted fields.
   *
   * @param {File} file - Receipt image selected by the user.
   */
  async function uploadReceipt(file) {
    var config = window.TRANSACTION_FORM_CONFIG || {};

    if (!file) {
      return;
    }

    if (!isWithinUploadLimit(file)) {
      showAlert("Receipt image is too large. Maximum allowed size is " + uploadLimitLabel() + ".", "error");
      return;
    }

    if (["image/png", "image/jpeg", "image/webp"].indexOf(file.type) < 0) {
      showAlert("Please choose a PNG, JPG/JPEG, or WEBP receipt image.", "error");
      return;
    }

    try {
      showAlert("Scanning receipt...", "info");

      if (!state.categoriesLoaded) {
        await loadCategories();
      }

      if (!state.categoriesLoaded) {
        throw new Error("Categories must load before receipt fields can be applied.");
      }

      var formData = new FormData();
      formData.append("receipt", file);

      var response = await fetch(config.receiptScanUrl || "/api/receipts/scan", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(payload.detail || payload.error || "Receipt scan failed.");
      }

      if (payload.amount) {
        byId("amount").value = payload.amount;
      }

      if (payload.entry_date) {
        byId("entry_date").value = payload.entry_date;
      }

      byId("entry_type").value = "expense";
      syncCategories(payload.category);

      if (payload.category && state.expenseCategories[payload.category]) {
        byId("category").value = payload.category;
        syncSubCategories(payload.sub_category);

        if (payload.sub_category && isValidExpensePair(payload.category, payload.sub_category)) {
          byId("sub_category").value = payload.sub_category;
        }
      }

      if (payload.description) {
        byId("description").value = payload.description;
      }

      popElement(byId("transactionForm"));
      showAlert("Receipt scanned. Please review the fields before saving.", "success");
      logDebug("Receipt scan applied", payload);
    } catch (error) {
      console.error("[transaction-form] Receipt upload failed", error);
      showAlert(error.message || "Receipt upload failed. Check the console for details.", "error");
    }
  }

  /**
   * Upload CSV/XLSX data to the bulk import endpoint.
   *
   * @param {File} file - CSV or XLSX file selected by the user.
   */
  async function uploadBulkFile(file) {
    var config = window.TRANSACTION_FORM_CONFIG || {};

    if (!file) {
      return;
    }

    if (!isWithinUploadLimit(file)) {
      showAlert("Import file is too large. Maximum allowed size is " + uploadLimitLabel() + ".", "error");
      return;
    }

    if (!/\.(csv|xlsx)$/i.test(file.name || "")) {
      showAlert("Please choose a CSV or XLSX import file.", "error");
      return;
    }

    try {
      showAlert("Uploading import file...", "info");

      var formData = new FormData();
      formData.append("file", file);

      var response = await fetch(config.importUrl || "/api/data/transactions/import", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      var payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok) {
        throw new Error(payload.error || "Import failed.");
      }

      showAlert((payload.imported_count || 0) + " transactions imported successfully.", "success");
      logDebug("Bulk import completed", payload);
    } catch (error) {
      console.error("[transaction-form] Bulk import failed", error);
      showAlert(error.message || "Bulk import failed. Check the console for details.", "error");
    }
  }

  /**
   * Attach event listeners to form controls after the DOM is available.
   */
  function bindEvents() {
    var typeSelect = byId("entry_type");
    var categorySelect = byId("category");
    var currencySelect = byId("currency_code");
    var currencySearch = byId("currencySearch");
    var amountInput = byId("amount");
    var receiptInput = byId("receiptUploadInput");
    var bulkImportInput = byId("bulkImportInput");
    var quickButtons = document.querySelectorAll(".quick-data-btn");

    if (typeSelect) {
      typeSelect.addEventListener("change", function () {
        syncCategories("");
      });
    }

    if (categorySelect) {
      categorySelect.addEventListener("change", function () {
        syncSubCategories("");
      });
    }

    if (currencySelect) {
      currencySelect.addEventListener("change", updateExchangeRatePreview);
    }

    if (currencySearch) {
      currencySearch.addEventListener("input", function () {
        fillCurrencySelect(currencySearch.value);
      });
    }

    if (amountInput) {
      amountInput.addEventListener("input", updateExchangeRatePreview);
    }

    if (receiptInput) {
      receiptInput.addEventListener("change", function (event) {
        uploadReceipt(event.target.files[0]);
        event.target.value = "";
      });
    }

    if (bulkImportInput) {
      bulkImportInput.addEventListener("change", function (event) {
        uploadBulkFile(event.target.files[0]);
        event.target.value = "";
      });
    }

    quickButtons.forEach(function (button) {
      button.className += " inline-flex items-center gap-2 rounded-2xl border border-white/15 bg-white/10 px-4 py-2 text-sm font-semibold text-slate-100 opacity-50 shadow-sm transition hover:-translate-y-0.5 hover:border-yellow-300/50 hover:bg-yellow-400/15 focus:outline-none focus:ring-4 focus:ring-yellow-300/20 disabled:cursor-not-allowed";
      button.addEventListener("click", function () {
        applyQuickData(button);
      });
    });
  }

  /**
   * Initialize all Add Transaction page behavior.
   */
  window.initTransactionForm = function () {
    var dateInput = byId("entry_date");
    var todayLabel = byId("transactionTodayLabel");

    bindEvents();
    setQuickButtonsEnabled(false);

    if (dateInput && !dateInput.value) {
      dateInput.value = formatDateInputValue(new Date());
    }

    if (todayLabel) {
      todayLabel.textContent = new Date().toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    }

    loadCategories();
    loadCurrencies();
  };
})();
