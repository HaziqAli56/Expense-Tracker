/**
 * transaction_form.js — client-side UX helper
 *
 * Server final validation karta hai; yahan sirf dropdown categories
 * income/expense toggle ke mutabiq update hoti hain + default date fill.
 */
(function () {
  /** `<select>` ko options se rebuild karta hai */
  function fillCategorySelect(selectEl, categories, selected) {
    selectEl.innerHTML = "";
    categories.forEach(function (c) {
      var opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      if (selected && selected === c) opt.selected = true;
      selectEl.appendChild(opt);
    });
    if (!selected && categories.length) selectEl.selectedIndex = 0;
  }

  /** Radio buttons se current entry type read */
  function currentType() {
    var income = document.getElementById("type_income");
    return income && income.checked ? "income" : "expense";
  }

  /** Page load par call: template ne `window.*` globals set kiye hote hain */
  window.initTransactionForm = function () {
    var category = document.getElementById("category");
    if (!category) return;

    var expenseCats = window.EXPENSE_CATEGORIES || [];
    var incomeCats = window.INCOME_CATEGORIES || [];
    var initialType = window.INITIAL_TYPE || "income";
    var initialCat = window.INITIAL_CATEGORY || "";

    function syncCategories() {
      var t = currentType();
      var list = t === "income" ? incomeCats : expenseCats;
      var keep = initialCat && list.indexOf(initialCat) >= 0 ? initialCat : "";
      fillCategorySelect(category, list, keep);
      initialCat = "";
    }

    document.querySelectorAll('input[name="entry_type"]').forEach(function (r) {
      r.addEventListener("change", syncCategories);
    });

    if (initialType === "expense") {
      var exp = document.getElementById("type_expense");
      var inc = document.getElementById("type_income");
      if (exp && inc) {
        exp.checked = true;
        inc.checked = false;
      }
    }
    syncCategories();

    var dateInput = document.getElementById("entry_date");
    if (dateInput && !dateInput.value) {
      var d = new Date();
      var pad = function (n) { return n < 10 ? "0" + n : "" + n; };
      dateInput.value = d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
    }
  };
})();
