/**
 * BudgetAlerts.jsx
 * Shows monthly category budget usage with visual progress alerts.
 */

import { useEffect, useMemo, useState } from "react";
import { fetchBudgetAlerts, fetchCategories, upsertBudgetLimit } from "../api/expenseApi";

/**
 * Return the current month in YYYY-MM format for month inputs and API queries.
 */
function currentMonthKey() {
  return new Date().toISOString().slice(0, 7);
}

/**
 * Map backend alert status to a CSS class for progress-bar styling.
 */
function statusClass(status) {
  if (status === "danger") return "budgetDanger";
  if (status === "warning") return "budgetWarning";
  return "budgetSuccess";
}

/**
 * Render category budget progress bars and a small budget limit form.
 */
export default function BudgetAlerts() {
  const [month, setMonth] = useState(currentMonthKey());
  const [alerts, setAlerts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({
    category: "",
    limit_amount: "",
  });
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  /**
   * Load main expense categories from the backend.
   */
  useEffect(() => {
    fetchCategories()
      .then((payload) => {
        const mainCategories = Object.keys(payload.expense_categories || {});

        setCategories(mainCategories);
        setForm((currentForm) => ({
          ...currentForm,
          category: currentForm.category || mainCategories[0] || "",
        }));
      })
      .catch((err) => setError(err.message));
  }, []);

  /**
   * Load budget alert rows for the selected month.
   */
  async function loadAlerts(selectedMonth = month) {
    setLoading(true);
    setError("");

    try {
      const payload = await fetchBudgetAlerts(selectedMonth);
      setAlerts(payload.alerts || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  /**
   * Refresh alerts whenever the user changes month.
   */
  useEffect(() => {
    loadAlerts(month);
  }, [month]);

  /**
   * Save a category budget and refresh the visual progress list.
   */
  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("Saving budget...");
    setError("");

    try {
      await upsertBudgetLimit({
        month,
        category: form.category,
        limit_amount: Number(form.limit_amount),
      });
      setStatus("Budget saved.");
      setForm((currentForm) => ({ ...currentForm, limit_amount: "" }));
      await loadAlerts(month);
    } catch (err) {
      setError(err.message);
      setStatus("");
    }
  }

  /**
   * Sort severe alerts first so the user sees urgent categories immediately.
   */
  const sortedAlerts = useMemo(() => {
    return [...alerts].sort((first, second) => {
      return Number(second.percentage_used || 0) - Number(first.percentage_used || 0);
    });
  }, [alerts]);

  return (
    <section className="panel">
      <header className="panelHeader">
        <h2>Budget Alerts</h2>
        <input type="month" value={month} onChange={(event) => setMonth(event.target.value)} />
      </header>

      <form className="formGrid" onSubmit={handleSubmit}>
        <label>
          Category
          <select
            value={form.category}
            onChange={(event) => setForm({ ...form, category: event.target.value })}
            required
          >
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>

        <label>
          Monthly Limit
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={form.limit_amount}
            onChange={(event) => setForm({ ...form, limit_amount: event.target.value })}
            required
          />
        </label>

        <button type="submit">Save Budget</button>
      </form>

      {status && <p className="status">{status}</p>}
      {error && <p className="error">{error}</p>}
      {loading && <p className="status">Loading budget alerts...</p>}

      {!loading && sortedAlerts.length === 0 && <p>No category budgets set for this month.</p>}

      <div className="budgetList">
        {sortedAlerts.map((alert) => {
          const percentage = Math.min(Number(alert.percentage_used || 0), 100);

          return (
            <article className="budgetRow" key={`${alert.month}-${alert.category}`}>
              <div className="budgetRowHeader">
                <strong>{alert.category}</strong>
                <span>
                  {alert.spent.toFixed(2)} / {alert.limit_amount.toFixed(2)}
                </span>
              </div>

              <div className="progressTrack" aria-label={`${alert.category} budget usage`}>
                <div
                  className={`progressFill ${statusClass(alert.status)}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>

              <p className={alert.status === "danger" ? "error" : "status"}>
                {alert.percentage_used.toFixed(1)}% used
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
