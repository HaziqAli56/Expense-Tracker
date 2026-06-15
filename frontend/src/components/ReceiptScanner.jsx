/**
 * ReceiptScanner.jsx
 * Provides drag-and-drop OCR upload and a verification form before saving.
 */

import { useEffect, useState } from "react";
import { commitReceiptTransaction, fetchCategories, scanReceipt } from "../api/expenseApi";

/**
 * Render a receipt upload workflow with editable extracted values.
 */
export default function ReceiptScanner() {
  const [categoryMap, setCategoryMap] = useState({});
  const [draft, setDraft] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  /**
   * Load expense categories so receipt verification matches transaction entry.
   */
  useEffect(() => {
    fetchCategories()
      .then((payload) => setCategoryMap(payload.expense_categories || {}))
      .catch((err) => setError(err.message));
  }, []);

  /**
   * Upload the selected file to the OCR endpoint and store the editable draft.
   */
  async function handleFile(file) {
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please upload a receipt image.");
      return;
    }

    setError("");
    setStatus("Scanning receipt...");

    try {
      const result = await scanReceipt(file);
      const fallbackCategory = Object.keys(categoryMap)[0] || result.category || "";
      const category = categoryMap[result.category] ? result.category : fallbackCategory;
      const subCategories = categoryMap[category] || [];
      const subCategory = subCategories.includes(result.sub_category)
        ? result.sub_category
        : subCategories[0] || "";

      setDraft({
        ...result,
        category,
        sub_category: subCategory,
      });
      setStatus("Review the extracted details before saving.");
    } catch (err) {
      setError(err.message);
      setStatus("");
    }
  }

  /**
   * Save the verified draft as a transaction.
   */
  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setStatus("Saving transaction...");

    try {
      await commitReceiptTransaction(draft);
      setDraft(null);
      setStatus("Receipt transaction saved.");
    } catch (err) {
      setError(err.message);
      setStatus("");
    }
  }

  /**
   * Update one field in the editable OCR draft.
   */
  function updateDraft(field, value) {
    setDraft((currentDraft) => ({
      ...currentDraft,
      [field]: value,
    }));
  }

  /**
   * Update main category and reset sub-category to a valid dependent option.
   */
  function updateCategory(category) {
    const subCategories = categoryMap[category] || [];

    setDraft((currentDraft) => ({
      ...currentDraft,
      category,
      sub_category: subCategories[0] || "",
    }));
  }

  const mainCategories = Object.keys(categoryMap);
  const subCategories = draft ? categoryMap[draft.category] || [] : [];

  return (
    <section className="panel">
      <h2>Receipt Scanner</h2>

      <label
        className={`dropZone ${isDragging ? "dropZoneActive" : ""}`}
        onDragEnter={() => setIsDragging(true)}
        onDragLeave={() => setIsDragging(false)}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          handleFile(event.dataTransfer.files[0]);
        }}
      >
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp"
          hidden
          onChange={(event) => handleFile(event.target.files[0])}
        />
        Drop receipt image here or click to upload
      </label>

      {status && <p className="status">{status}</p>}
      {error && <p className="error">{error}</p>}

      {draft && (
        <form className="formGrid" onSubmit={handleSubmit}>
          <label>
            Date
            <input
              type="date"
              value={draft.entry_date || ""}
              onChange={(event) => updateDraft("entry_date", event.target.value)}
            />
          </label>

          <label>
            Amount
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={draft.amount || ""}
              onChange={(event) => updateDraft("amount", event.target.value)}
            />
          </label>

          <label>
            Main Category
            <select
              value={draft.category || ""}
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
              value={draft.sub_category || ""}
              onChange={(event) => updateDraft("sub_category", event.target.value)}
              disabled={!draft.category}
              required
            >
              {subCategories.map((subCategory) => (
                <option key={subCategory} value={subCategory}>
                  {subCategory}
                </option>
              ))}
            </select>
          </label>

          <label>
            Currency
            <input
              maxLength="3"
              value={draft.currency_code || "PKR"}
              onChange={(event) => updateDraft("currency_code", event.target.value.toUpperCase())}
            />
          </label>

          <label>
            Exchange Rate
            <input
              type="number"
              min="0.000001"
              step="0.000001"
              value={draft.exchange_rate || "1"}
              onChange={(event) => updateDraft("exchange_rate", event.target.value)}
            />
          </label>

          <label className="formGridWide">
            Description
            <textarea
              value={draft.description || ""}
              onChange={(event) => updateDraft("description", event.target.value)}
            />
          </label>

          {draft.raw_text && (
            <details className="formGridWide">
              <summary>OCR text</summary>
              <pre>{draft.raw_text}</pre>
            </details>
          )}

          <button type="submit">Save Verified Transaction</button>
        </form>
      )}
    </section>
  );
}
