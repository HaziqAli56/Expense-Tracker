/**
 * expenseApi.js
 * Centralized API helpers keep React components focused on UI state instead of
 * repeating fetch configuration and response parsing.
 */

/**
 * Parse a JSON response and throw a useful error for non-2xx API responses.
 */
async function parseJsonResponse(response) {
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(payload.error || "Request failed.");
    error.details = payload.details || [];
    throw error;
  }

  return payload;
}

/**
 * Fetch centralized category configuration for transaction forms.
 */
export async function fetchCategories() {
  const response = await fetch("/api/categories", {
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Create a transaction through the JSON API.
 */
export async function createTransaction(payload) {
  const response = await fetch("/api/transactions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Fetch expense forecast data for the authenticated user.
 */
export async function fetchExpenseForecast(window = 3, options = {}) {
  // URLSearchParams prevents malformed query strings if the window value later
  // comes from a dropdown, slider, or saved user preference.
  const params = new URLSearchParams({ window: String(window) });
  const response = await fetch(`/api/forecast/expenses?${params}`, {
    credentials: "include",
    signal: options.signal,
  });

  return parseJsonResponse(response);
}

/**
 * Upload a receipt image and return OCR-extracted draft transaction fields.
 */
export async function scanReceipt(file) {
  const formData = new FormData();
  formData.append("receipt", file);

  const response = await fetch("/api/receipts/scan", {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Save a user-verified receipt draft as a transaction.
 */
export async function commitReceiptTransaction(payload) {
  const response = await fetch("/api/receipts/commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Download transaction history in CSV or XLSX format.
 */
export function exportTransactions(format) {
  // Encoding through URLSearchParams keeps this safe if the UI later adds more
  // export query options such as date ranges or selected columns.
  const params = new URLSearchParams({ format });
  window.location.href = `/api/data/transactions/export?${params}`;
}

/**
 * Upload a CSV/XLSX file for bulk transaction import.
 */
export async function importTransactions(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/data/transactions/import", {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Fetch a currency conversion preview for transaction entry forms.
 */
export async function convertCurrency(amount, sourceCurrency, baseCurrency) {
  const params = new URLSearchParams({
    amount,
    from: sourceCurrency,
    to: baseCurrency,
  });

  const response = await fetch(`/api/currency/convert?${params}`, {
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Fetch the backend-approved currency list for searchable dropdowns.
 */
export async function fetchSupportedCurrencies() {
  const response = await fetch("/api/currency/supported", {
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Fetch current budget alert progress for the selected month.
 */
export async function fetchBudgetAlerts(month) {
  const suffix = month ? `?month=${month}` : "";
  const response = await fetch(`/api/budgets/alerts${suffix}`, {
    credentials: "include",
  });

  return parseJsonResponse(response);
}

/**
 * Create or update a category budget for the authenticated user.
 */
export async function upsertBudgetLimit(payload) {
  const response = await fetch("/api/budgets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include",
  });

  return parseJsonResponse(response);
}
