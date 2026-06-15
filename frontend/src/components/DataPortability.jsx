/**
 * DataPortability.jsx
 * Provides CSV/XLSX export buttons and a modal-style bulk import workflow.
 */

import { useRef, useState } from "react";
import { exportTransactions, importTransactions } from "../api/expenseApi";

/**
 * Render import/export controls for transaction history.
 *
 * Keeping this workflow in a focused component makes it easy to place on a
 * settings page, reports page, or dashboard utility panel.
 */
export default function DataPortability() {
  const fileInputRef = useRef(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [details, setDetails] = useState([]);

  /**
   * Store the selected spreadsheet file and clear previous import messages.
   */
  function handleFileChange(event) {
    setSelectedFile(event.target.files[0] || null);
    setStatus("");
    setError("");
    setDetails([]);
  }

  /**
   * Upload the selected CSV/XLSX file to the backend import endpoint.
   */
  async function handleImportSubmit(event) {
    event.preventDefault();

    if (!selectedFile) {
      setError("Choose a CSV or XLSX file first.");
      return;
    }

    setStatus("Importing transactions...");
    setError("");
    setDetails([]);

    try {
      const result = await importTransactions(selectedFile);
      setStatus(`${result.imported_count} transactions imported.`);
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      setError(err.message);
      setDetails(err.details || []);
      setStatus("");
    }
  }

  return (
    <section className="panel">
      <header className="panelHeader">
        <h2>Data Import & Export</h2>
      </header>

      <div className="buttonRow">
        <button type="button" onClick={() => exportTransactions("csv")}>
          Export CSV
        </button>
        <button type="button" onClick={() => exportTransactions("xlsx")}>
          Export Excel
        </button>
        <button type="button" onClick={() => setIsModalOpen(true)}>
          Import File
        </button>
      </div>

      {isModalOpen && (
        <div className="modalBackdrop" role="dialog" aria-modal="true">
          <form className="modalPanel" onSubmit={handleImportSubmit}>
            <header className="panelHeader">
              <h3>Import Transactions</h3>
              <button type="button" onClick={() => setIsModalOpen(false)}>
                Close
              </button>
            </header>

            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
            />

            {status && <p className="status">{status}</p>}
            {error && <p className="error">{error}</p>}

            {details.length > 0 && (
              <ul className="errorList">
                {details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            )}

            <button type="submit">Upload and Import</button>
          </form>
        </div>
      )}
    </section>
  );
}
