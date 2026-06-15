"""
Transaction import/export helpers.

Pandas is used here because it gives reliable CSV/Excel parsing, validation,
and serialization without duplicating spreadsheet handling logic in routes.
"""

from __future__ import annotations

import math
import re
from datetime import date
from io import BytesIO

import pandas as pd
from flask import current_app

from expense_tracker.models.transaction_model import Transaction
from expense_tracker.utils.constants import (
    first_sub_category_for,
    is_valid_expense_category,
    is_valid_income_category,
)


REQUIRED_IMPORT_COLUMNS = {"category", "amount"}
OPTIONAL_IMPORT_COLUMNS = {"sub_category", "description", "currency_code", "exchange_rate", "base_amount"}
DEFAULT_MAX_IMPORT_ROWS = 5000

COLUMN_ALIASES = {
    "date": "entry_date",
    "transaction_date": "entry_date",
    "entrydate": "entry_date",
    "entry_date": "entry_date",
    "month": "entry_date",
    "type": "entry_type",
    "transaction_type": "entry_type",
    "entrytype": "entry_type",
    "entry_type": "entry_type",
    "main_category": "category",
    "categories": "category",
    "category": "category",
    "sub_category": "sub_category",
    "subcategory": "sub_category",
    "sub-category": "sub_category",
    "amount": "amount",
    "value": "amount",
    "price": "amount",
    "description": "description",
    "desc": "description",
    "note": "description",
    "notes": "description",
    "currency": "currency_code",
    "currency_code": "currency_code",
    "exchange_rate": "exchange_rate",
    "rate": "exchange_rate",
    "base_amount": "base_amount",
}

LEGACY_CATEGORY_MAP = {
    "rent": ("Housing & Utilities", "Rent"),
    "food": ("Food & Dining", "Dining Out"),
    "grocery": ("Food & Dining", "Groceries"),
    "groceries": ("Food & Dining", "Groceries"),
    "fuel": ("Transportation", "Fuel"),
    "transport": ("Transportation", "Fuel"),
    "transportation": ("Transportation", "Fuel"),
    "entertainment": ("Personal & Lifestyle", "Entertainment"),
    "shopping": ("Personal & Lifestyle", "Shopping"),
    "bills": ("Housing & Utilities", "Utilities"),
    "utilities": ("Housing & Utilities", "Utilities"),
    "other": ("Miscellaneous", "Unexpected Expenses"),
    "misc": ("Miscellaneous", "Unexpected Expenses"),
    "miscellaneous": ("Miscellaneous", "Unexpected Expenses"),
}


def _canonical_column_name(column: object) -> str:
    """
    Convert spreadsheet headers into app column names.

    Old exports used headers such as Date/Type/Category/Amount, while the new
    database uses entry_date/entry_type/category/amount. A centralized alias map
    lets old files import without forcing the user to manually rename columns.
    """

    normalized = str(column).strip().lower().replace(" ", "_")

    return COLUMN_ALIASES.get(normalized, normalized)


def _is_blank(value) -> bool:
    """
    Return true for empty spreadsheet cells, including pandas NaN values.
    """

    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except TypeError:
        pass

    return str(value).strip() == ""


def _clean_amount(value) -> float:
    """
    Parse amount values from old exports and user-edited spreadsheets.

    Supports plain numbers, comma-separated numbers, and strings like
    "PKR 1,250.00". Negative amounts are converted to positive values because
    transaction direction is controlled by entry_type.
    """

    if _is_blank(value):
        raise ValueError("amount is required")

    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return abs(round(float(value), 2))

    text = str(value).strip()
    cleaned = re.sub(r"[^0-9.\-]", "", text.replace(",", ""))

    if cleaned in {"", "-", ".", "-."}:
        raise ValueError("amount must be numeric")

    return abs(round(float(cleaned), 2))


def _normalize_entry_type(value) -> str:
    """
    Normalize transaction type and default missing old-data rows to expense.

    Old expense-only files may not include a Type column. Defaulting to expense
    lets users import historical spending while still preserving income rows
    when Type/entry_type is present.
    """

    if _is_blank(value):
        return "expense"

    normalized = str(value).strip().lower()

    if normalized in {"income", "credit", "in", "earning", "earnings"}:
        return "income"

    if normalized in {"expense", "expenses", "debit", "out", "spend", "spent"}:
        return "expense"

    return normalized


def _normalize_category_pair(category_value, sub_category_value, entry_type: str) -> tuple[str, str]:
    """
    Map old category labels into the current main/sub-category structure.

    This keeps legacy files like "Food" or "Transport" importable after the app
    moved to a two-tier category system.
    """

    category = "" if _is_blank(category_value) else str(category_value).strip()
    sub_category = "" if _is_blank(sub_category_value) else str(sub_category_value).strip()
    legacy_pair = LEGACY_CATEGORY_MAP.get(category.lower())

    if legacy_pair and entry_type == "expense":
        mapped_category, mapped_sub_category = legacy_pair
        return mapped_category, sub_category or mapped_sub_category

    return category, sub_category or first_sub_category_for(category)


def _parse_import_date(value) -> date:
    """
    Parse an import date or use today's date when the old file has no date.

    If a Date column exists and contains a bad value, validation reports that as
    an error. If the column/cell is blank, the app saves the transaction under
    the current date as requested.
    """

    if _is_blank(value):
        return date.today()

    return pd.to_datetime(value).date()


def transactions_to_frame(transactions) -> pd.DataFrame:
    """
    Convert transaction rows into a pandas DataFrame for CSV/Excel export.
    """

    columns = [
        "entry_date",
        "entry_type",
        "category",
        "sub_category",
        "amount",
        "description",
        "currency_code",
        "exchange_rate",
        "base_amount",
    ]
    rows = [
        {
            # Export only user-facing fields and omit internal ids by default so
            # a downloaded file can be safely re-imported after light editing.
            "entry_date": tx.entry_date.isoformat(),
            "entry_type": tx.entry_type,
            "category": tx.category,
            "sub_category": tx.sub_category or "",
            "amount": round(float(tx.amount), 2),
            "description": tx.description or "",
            "currency_code": tx.currency_code,
            "exchange_rate": float(tx.exchange_rate or 1.0),
            "base_amount": tx.base_amount,
        }
        for tx in transactions
    ]

    return pd.DataFrame(rows, columns=columns)


def dataframe_to_download(frame: pd.DataFrame, export_format: str) -> tuple[BytesIO, str, str]:
    """
    Serialize a DataFrame into CSV or Excel bytes for Flask send_file.
    """

    output = BytesIO()

    if export_format == "xlsx":
        frame.to_excel(output, index=False, engine="openpyxl")
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "transactions.xlsx"
    else:
        output.write(frame.to_csv(index=False).encode("utf-8"))
        mimetype = "text/csv"
        filename = "transactions.csv"

    output.seek(0)

    return output, mimetype, filename


def read_transaction_upload(file_storage) -> pd.DataFrame:
    """
    Read uploaded CSV/XLSX content into a DataFrame.
    """

    filename = (file_storage.filename or "").lower()

    try:
        if filename.endswith(".xlsx"):
            frame = pd.read_excel(file_storage)

        elif filename.endswith(".csv"):
            frame = pd.read_csv(file_storage)

        else:
            raise ValueError("Only CSV and XLSX files are supported.")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Uploaded file could not be read. Please upload a valid CSV or XLSX file.") from exc

    # Normalize spreadsheet headers so old exports and new imports both map to
    # the canonical database field names used by validation and model creation.
    frame.columns = [_canonical_column_name(column) for column in frame.columns]

    # If a user provides both old and new versions of a column, such as Date
    # and entry_date, keep the first non-empty value for the canonical field so
    # downstream row access always returns a single scalar.
    if frame.columns.duplicated().any():
        frame = frame.T.groupby(level=0).first().T

    return frame


def validate_import_frame(frame: pd.DataFrame) -> list[str]:
    """
    Validate required columns and row-level values before creating DB objects.
    """

    errors = []
    max_import_rows = int(current_app.config.get("MAX_IMPORT_ROWS", DEFAULT_MAX_IMPORT_ROWS))
    missing = REQUIRED_IMPORT_COLUMNS - set(frame.columns)
    allowed_columns = REQUIRED_IMPORT_COLUMNS | OPTIONAL_IMPORT_COLUMNS | {"entry_date", "entry_type"}

    if missing:
        errors.append(f"Missing required columns: {', '.join(sorted(missing))}.")
        return errors

    if frame.empty:
        errors.append("Import file has no transaction rows.")

    if len(frame.index) > max_import_rows:
        errors.append(f"Import is limited to {max_import_rows} rows at a time.")

    for index, row in frame.iterrows():
        row_number = index + 2
        entry_type = _normalize_entry_type(row.get("entry_type", "expense"))
        category, effective_sub_category = _normalize_category_pair(
            row.get("category"),
            row.get("sub_category", ""),
            entry_type,
        )

        if entry_type not in {"income", "expense"}:
            errors.append(f"Row {row_number}: entry_type must be income or expense.")

        if not category:
            errors.append(f"Row {row_number}: category is required.")
        elif entry_type == "income" and not is_valid_income_category(category, effective_sub_category):
            errors.append(
                f"Row {row_number}: category/sub_category '{category}/{effective_sub_category}' is not valid for income."
            )
        elif entry_type == "expense" and not is_valid_expense_category(category, effective_sub_category):
            errors.append(
                f"Row {row_number}: category/sub_category '{category}/{effective_sub_category}' is not valid for expense."
            )

        try:
            amount = _clean_amount(row["amount"])
            if amount <= 0:
                errors.append(f"Row {row_number}: amount must be greater than zero.")
        except (TypeError, ValueError):
            errors.append(f"Row {row_number}: amount must be numeric.")

        try:
            _parse_import_date(row.get("entry_date"))
        except (TypeError, ValueError):
            errors.append(f"Row {row_number}: entry_date must be a valid date.")

        if "currency_code" in frame.columns:
            currency_code = str(row.get("currency_code") or "PKR").strip().upper()

            if len(currency_code) != 3:
                errors.append(f"Row {row_number}: currency_code must be a three-letter code.")

        if "exchange_rate" in frame.columns:
            try:
                exchange_rate = float(row.get("exchange_rate") or 1.0)

                if exchange_rate <= 0:
                    errors.append(f"Row {row_number}: exchange_rate must be greater than zero.")
            except (TypeError, ValueError):
                errors.append(f"Row {row_number}: exchange_rate must be numeric.")

        if len(errors) >= 100:
            errors.append("Validation stopped after 100 errors. Fix these and upload again.")
            break

    return errors


def frame_to_transactions(frame: pd.DataFrame, user_id: int) -> list[Transaction]:
    """
    Convert a validated import DataFrame into Transaction model instances.
    """

    transactions = []

    for _, row in frame.iterrows():
        entry_date = _parse_import_date(row.get("entry_date"))
        currency_code = str(row.get("currency_code", "PKR") or "PKR").upper()
        exchange_rate = float(row.get("exchange_rate", 1.0) or 1.0)
        entry_type = _normalize_entry_type(row.get("entry_type", "expense"))
        category, sub_category = _normalize_category_pair(
            row.get("category"),
            row.get("sub_category", ""),
            entry_type,
        )

        transactions.append(
            Transaction(
                user_id=user_id,
                entry_date=entry_date or date.today(),
                entry_type=entry_type,
                category=category,
                sub_category=sub_category,
                amount=_clean_amount(row["amount"]),
                description="" if _is_blank(row.get("description", "")) else str(row.get("description", "")).strip(),
                currency_code=currency_code[:3],
                exchange_rate=exchange_rate,
            )
        )

    return transactions
