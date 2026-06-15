/**
 * ForecastChart.jsx
 * Displays historical monthly spending beside the next-month forecast.
 */

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchExpenseForecast } from "../api/expenseApi";

/**
 * Format numeric values as compact finance-style labels for chart tooltips.
 *
 * The helper guards against NaN and unexpected string values so the chart never
 * displays broken labels if an API response is malformed.
 */
function formatAmount(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "0.00";
  }

  return numericValue.toLocaleString(undefined, {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  });
}

/**
 * Convert a backend number-like value into a safe Recharts value.
 *
 * Recharts expects finite numbers. Returning zero for invalid values keeps the
 * UI stable while backend validation/logging handles the root cause.
 */
function toChartNumber(value) {
  const numericValue = Number(value);

  return Number.isFinite(numericValue) ? numericValue : 0;
}

/**
 * Render an expense forecast chart using the API's moving-average forecast.
 *
 * The component only needs a window prop, making it reusable on dashboard,
 * reports, or analytics pages without knowing the backend implementation.
 */
export default function ForecastChart({ windowSize = 3 }) {
  const [payload, setPayload] = useState({
    history: [],
    forecast: [],
    method: "",
    forecast_month: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  /**
   * Load forecast data when the component mounts or the averaging window
   * changes. AbortController cancels stale requests instead of letting slow
   * responses update a newer chart state.
   */
  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setError("");

    fetchExpenseForecast(windowSize, { signal: controller.signal })
      .then((forecastPayload) => {
        setPayload({
          history: Array.isArray(forecastPayload.history) ? forecastPayload.history : [],
          forecast: Array.isArray(forecastPayload.forecast) ? forecastPayload.forecast : [],
          method: forecastPayload.method || "",
          forecast_month: forecastPayload.forecast_month || "",
        });
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [windowSize]);

  /**
   * Convert API history/forecast rows into a compact chart shape.
   *
   * Each row compares the latest actual month for a category against the
   * predicted next-month amount for that same category.
   */
  const chartRows = useMemo(() => {
    return payload.forecast.map((forecastRow) => {
      const actualRows = payload.history.filter(
        (row) => row.category === forecastRow.category,
      );
      const latestActual = actualRows.at(-1);

      return {
        category: forecastRow.category || "Uncategorized",
        latestActual: latestActual ? toChartNumber(latestActual.amount) : 0,
        forecast: toChartNumber(forecastRow.forecast_amount),
      };
    });
  }, [payload]);

  if (loading) {
    return (
      <section className="panel forecastSkeleton" aria-busy="true">
        <header className="panelHeader">
          <h2>Next Month Forecast</h2>
        </header>
        <div className="skeletonLine" />
        <div className="skeletonChart" />
      </section>
    );
  }

  if (error) {
    return (
      <section className="panel error" role="alert">
        {error}
      </section>
    );
  }

  if (chartRows.length === 0) {
    return (
      <section className="panel">
        <header className="panelHeader">
          <h2>Next Month Forecast</h2>
        </header>
        <p>No expense history is available yet.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <header className="panelHeader">
        <h2>Next Month Forecast</h2>
        <span>
          {payload.forecast_month} - {payload.method}
        </span>
      </header>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={chartRows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="category" />
          <YAxis />
          <Tooltip formatter={(value) => formatAmount(value)} />
          <Legend />
          <Bar dataKey="latestActual" fill="#7c8cff" name="Latest Actual" />
          <Bar dataKey="forecast" fill="#ff8c42" name="Forecast" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
