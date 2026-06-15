/**
 * CurrencySelect.jsx
 * Searchable currency dropdown with live exchange-rate preview support.
 */

import { useEffect, useMemo, useState } from "react";
import { convertCurrency, fetchSupportedCurrencies } from "../api/expenseApi";

/**
 * Render a searchable currency picker for transaction forms.
 *
 * The parent owns the selected values so this component can be used inside
 * create/edit forms without coupling it to a specific form library.
 */
export default function CurrencySelect({
  amount,
  currencyCode,
  exchangeRate,
  onCurrencyChange,
  onExchangeRateChange,
}) {
  const [baseCurrency, setBaseCurrency] = useState("PKR");
  const [currencies, setCurrencies] = useState([]);
  const [query, setQuery] = useState("");
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");

  /**
   * Load the currency list once so dropdown options come from the backend.
   */
  useEffect(() => {
    fetchSupportedCurrencies()
      .then((payload) => {
        setBaseCurrency(payload.base_currency || "PKR");
        setCurrencies(payload.currencies || []);
      })
      .catch((err) => setError(err.message));
  }, []);

  /**
   * Filter currencies by code or name while preserving the complete list in
   * state for future searches.
   */
  const filteredCurrencies = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return currencies;
    }

    return currencies.filter((currency) => {
      return (
        currency.code.toLowerCase().includes(normalizedQuery) ||
        currency.name.toLowerCase().includes(normalizedQuery)
      );
    });
  }, [currencies, query]);

  /**
   * Refresh the conversion preview whenever amount or selected currency changes.
   */
  useEffect(() => {
    if (!amount || !currencyCode) {
      setPreview(null);
      return;
    }

    let ignore = false;

    convertCurrency(amount, currencyCode, baseCurrency)
      .then((payload) => {
        if (!ignore) {
          setPreview(payload);
          onExchangeRateChange(payload.exchange_rate);
          setError("");
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.message);
        }
      });

    return () => {
      ignore = true;
    };
  }, [amount, baseCurrency, currencyCode]);

  return (
    <div className="currencySelect">
      <label>
        Search Currency
        <input
          value={query}
          placeholder="USD, Euro, PKR..."
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>

      <label>
        Currency
        <select
          value={currencyCode}
          onChange={(event) => onCurrencyChange(event.target.value)}
        >
          {filteredCurrencies.map((currency) => (
            <option key={currency.code} value={currency.code}>
              {currency.code} - {currency.name}
            </option>
          ))}
        </select>
      </label>

      <input type="hidden" name="currency_code" value={currencyCode} />
      <input type="hidden" name="exchange_rate" value={exchangeRate || 1} />

      {preview && (
        <p className="status">
          {currencyCode} {Number(amount || 0).toFixed(2)} = {baseCurrency}{" "}
          {Number(preview.converted_amount || 0).toFixed(2)}
        </p>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
