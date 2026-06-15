/**
 * TransactionEntryForm.jsx
 * React transaction form with dependent main category and sub-category fields.
 */

import { useEffect, useMemo, useState } from "react";
import { createTransaction, fetchCategories } from "../api/expenseApi";
import CurrencySelect from "./CurrencySelect";

/**
 * Return today's date in YYYY-MM-DD format for the date input default.
 */
function todayInputValue() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Render a production-style transaction entry form.
 *
 * Categories are loaded from Flask at runtime so React never hardcodes business
 * taxonomy. Both income and expense entries use a valid main category and
 * dependent sub-category.
 */
export default function TransactionEntryForm({ onSaved }) {
  const [categoryConfig, setCategoryConfig] = useState({
    expense_categories: {},
    income_category_map: {},
    income_categories: [],
  });
  const [form, setForm] = useState({
    amount: "",
    entry_type: "expense",
    category: "",
    sub_category: "",
    description: "",
    entry_date: todayInputValue(),
    currency_code: "PKR",
    exchange_rate: 1,
  });
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  /**
   * Fetch centralized category options from the backend on mount.
   */
  useEffect(() => {
    let ignore = false;

    fetchCategories()
      .then((payload) => {
        if (ignore) return;

        const expenseCategories = payload.expense_categories || {};
        const firstMainCategory = Object.keys(expenseCategories)[0] || "";
        const firstSubCategory = expenseCategories[firstMainCategory]?.[0] || "";

        setCategoryConfig({
          expense_categories: expenseCategories,
          income_category_map: payload.income_category_map || {},
          income_categories: payload.income_categories || [],
        });
        setForm((currentForm) => ({
          ...currentForm,
          category: firstMainCategory,
          sub_category: firstSubCategory,
        }));
      })
      .catch((err) => setError(err.message))
      .finally(() => {
        if (!ignore) {
          setLoadingCategories(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  /**
   * Update one form field while preserving the rest of the draft state.
   */
  function updateField(field, value) {
    setForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }));
  }

  /**
   * Switch the form between income and expense category modes.
   */
  function updateEntryType(entryType) {
    const expenseCategories = categoryConfig.expense_categories;
    const incomeCategoryMap = categoryConfig.income_category_map;
    const firstExpenseCategory = Object.keys(expenseCategories)[0] || "";
    const firstIncomeCategory = Object.keys(incomeCategoryMap)[0] || "";
    const nextCategory = entryType === "income" ? firstIncomeCategory : firstExpenseCategory;
    const categoryMap = entryType === "income" ? incomeCategoryMap : expenseCategories;
    const nextSubCategory = categoryMap[nextCategory]?.[0] || "";

    setForm((currentForm) => ({
      ...currentForm,
      entry_type: entryType,
      category: nextCategory,
      sub_category: nextSubCategory,
    }));
  }

  /**
   * Update the main category and reset the dependent sub-category.
   */
  function updateCategory(category) {
    const categoryMap = form.entry_type === "income"
      ? categoryConfig.income_category_map
      : categoryConfig.expense_categories;
    const subCategories = categoryMap[category] || [];

    setForm((currentForm) => ({
      ...currentForm,
      category,
      sub_category: subCategories[0] || "",
    }));
  }

  /**
   * Validate and submit the JSON payload to Flask.
   */
  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setStatus("");

    try {
      const payload = {
        ...form,
        amount: Number(form.amount),
        exchange_rate: Number(form.exchange_rate || 1),
      };
      const result = await createTransaction(payload);

      setStatus("Transaction saved.");
      setForm((currentForm) => ({
        ...currentForm,
        amount: "",
        description: "",
      }));
      onSaved?.(result.transaction);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const mainCategories = useMemo(() => {
    if (form.entry_type === "income") {
      return categoryConfig.income_categories;
    }

    return Object.keys(categoryConfig.expense_categories);
  }, [categoryConfig, form.entry_type]);

  const activeCategoryMap = form.entry_type === "income"
    ? categoryConfig.income_category_map
    : categoryConfig.expense_categories;
  const subCategories = activeCategoryMap[form.category] || [];
  const subCategoryDisabled = !form.category || subCategories.length === 0;

  if (loadingCategories) {
    return <section className="panel" aria-busy="true">Loading categories...</section>;
  }

  return (
    <form className="formGrid" onSubmit={handleSubmit}>
      <label>
        Type
        <select
          value={form.entry_type}
          onChange={(event) => updateEntryType(event.target.value)}
        >
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>
      </label>

      <label>
        Amount
        <input
          type="number"
          min="0.01"
          step="0.01"
          value={form.amount}
          onChange={(event) => updateField("amount", event.target.value)}
          required
        />
      </label>

      <CurrencySelect
        amount={form.amount}
        currencyCode={form.currency_code}
        exchangeRate={form.exchange_rate}
        onCurrencyChange={(value) => updateField("currency_code", value)}
        onExchangeRateChange={(value) => updateField("exchange_rate", value)}
      />

      <label>
        Main Category
        <select
          value={form.category}
          onChange={(event) => updateCategory(event.target.value)}
          required
        >
          {mainCategories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </label>

      <label>
        Sub-category
        <select
          value={form.sub_category}
          onChange={(event) => updateField("sub_category", event.target.value)}
          disabled={subCategoryDisabled}
          required={!subCategoryDisabled}
        >
          {subCategories.map((subCategory) => (
            <option key={subCategory} value={subCategory}>
              {subCategory}
            </option>
          ))}
        </select>
      </label>

      <label>
        Date
        <input
          type="date"
          value={form.entry_date}
          onChange={(event) => updateField("entry_date", event.target.value)}
          required
        />
      </label>

      <label className="formGridWide">
        Description
        <textarea
          value={form.description}
          onChange={(event) => updateField("description", event.target.value)}
        />
      </label>

      {status && <p className="status">{status}</p>}
      {error && <p className="error">{error}</p>}

      <button type="submit" disabled={saving}>
        {saving ? "Saving..." : "Save Transaction"}
      </button>
    </form>
  );
}
