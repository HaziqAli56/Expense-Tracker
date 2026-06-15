"""
Expense forecasting utilities.

This module keeps forecasting math outside Flask routes so the algorithm can be
unit tested independently and later replaced with a heavier model if needed.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

DEFAULT_FORECAST_RESPONSE = {
    "history": [],
    "forecast": [],
}


def _next_month_label(reference_date: date | None = None) -> str:
    """
    Return the YYYY-MM label for the month being predicted.

    The API exposes this label so the frontend does not have to duplicate date
    logic or accidentally disagree with the backend about the forecast period.
    """

    today = reference_date or date.today()
    next_month = pd.Timestamp(today).to_period("M") + 1

    return str(next_month)


def _empty_forecast_payload(window: int) -> dict:
    """
    Return a consistent empty response shape for users with no valid expenses.

    A shared helper prevents empty-history responses from drifting as metadata
    fields are added over time.
    """

    return {
        **DEFAULT_FORECAST_RESPONSE,
        "method": f"{window}_month_moving_average",
        "forecast_month": _next_month_label(),
    }


def forecast_next_month_expenses(transactions: Iterable, window: int = 3) -> dict:
    """
    Forecast next month's expense totals per category.

    The algorithm intentionally uses a moving average because personal finance
    datasets are often small. A simple average over recent monthly category
    totals is transparent, quick to compute, and avoids overfitting sparse data.
    """

    safe_window = min(max(int(window or 3), 1), 12)

    rows = []

    for tx in transactions:
        try:
            amount = float(getattr(tx, "base_amount", tx.amount) or 0)
        except (TypeError, ValueError):
            # Legacy or manually edited rows with non-numeric amounts are
            # ignored so one corrupted record cannot break every forecast.
            continue

        rows.append(
            {
                # SQLAlchemy Date values are converted by pandas below so
                # grouping by calendar month is consistent across Python and
                # PostgreSQL.
                "entry_date": tx.entry_date,
                # Blank categories are normalized to "Uncategorized" so chart
                # labels stay readable even if older imported data was
                # incomplete.
                "category": (tx.category or "Uncategorized").strip() or "Uncategorized",
                # base_amount allows multi-currency rows to be forecast in the
                # user's dashboard currency while still working for basic rows.
                "amount": amount,
            }
        )

    # Return a stable JSON shape for new users instead of making the React chart
    # handle missing keys or special-case empty server responses.
    if not rows:
        return _empty_forecast_payload(safe_window)

    frame = pd.DataFrame(rows)

    # Invalid dates are coerced to NaT and dropped so one bad legacy row does
    # not break the whole forecast endpoint.
    frame["entry_date"] = pd.to_datetime(frame["entry_date"], errors="coerce")
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    frame = frame.dropna(subset=["entry_date"])
    frame = frame[frame["amount"].notna()]
    frame = frame[frame["amount"] > 0]

    if frame.empty:
        return _empty_forecast_payload(safe_window)

    # Convert transaction dates to month labels before grouping, because the
    # frontend wants compact strings like "2026-06" rather than raw dates.
    frame["month"] = frame["entry_date"].dt.to_period("M").astype(str)

    monthly = (
        frame.groupby(["month", "category"], as_index=False)["amount"]
        .sum()
        .sort_values(["category", "month"])
    )

    # Round actual monthly totals after aggregation to avoid accumulating small
    # floating-point artifacts in JSON responses.
    monthly["amount"] = monthly["amount"].round(2)

    forecast_rows = []
    forecast_month = _next_month_label()

    # Forecast each category independently because rent, food, shopping, and
    # bills usually have very different spending patterns.
    for category, category_frame in monthly.groupby("category", sort=True):
        recent_months = category_frame.tail(safe_window)
        predicted_amount = round(float(recent_months["amount"].mean()), 2)

        forecast_rows.append(
            {
                "category": category,
                "forecast_amount": predicted_amount,
                "months_used": int(len(recent_months)),
                "forecast_month": forecast_month,
            }
        )

    return {
        "history": monthly.to_dict(orient="records"),
        "forecast": forecast_rows,
        "method": f"{safe_window}_month_moving_average",
        "forecast_month": forecast_month,
    }
