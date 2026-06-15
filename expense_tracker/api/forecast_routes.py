"""
Forecast API routes.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from expense_tracker.models.transaction_model import Transaction
from expense_tracker.utils.forecasting import forecast_next_month_expenses


forecast_api_bp = Blueprint("forecast_api", __name__, url_prefix="/api/forecast")


def _parse_positive_int_query(name: str, default: int, minimum: int, maximum: int) -> tuple[int | None, str | None]:
    """
    Parse and validate a bounded positive integer query parameter.

    Strict validation is used instead of silently falling back to defaults so
    API consumers can quickly detect broken UI state, malformed requests, or
    abusive inputs.
    """

    raw_value = request.args.get(name)

    if raw_value is None or raw_value == "":
        return default, None

    try:
        parsed_value = int(raw_value)
    except (TypeError, ValueError):
        return None, f"{name} must be an integer."

    if parsed_value < minimum or parsed_value > maximum:
        return None, f"{name} must be between {minimum} and {maximum}."

    return parsed_value, None


def _first_day_months_ago(months_back: int) -> date:
    """
    Return the first day of the month N months before the current month.

    The forecast endpoint only needs recent history for charts and moving
    averages. Applying this cutoff in SQL protects the API from loading a very
    large transaction table into pandas.
    """

    today = date.today()
    month_index = today.year * 12 + today.month - months_back
    year = (month_index - 1) // 12
    month = (month_index - 1) % 12 + 1

    return date(year, month, 1)


@forecast_api_bp.get("/expenses")
@login_required
def expense_forecast():
    """
    Return category-level next-month expense forecasts for the current user.
    """

    # `window` controls the moving-average size. It is bounded because larger
    # windows do not improve this lightweight model and can hide recent changes.
    window, window_error = _parse_positive_int_query(
        name="window",
        default=3,
        minimum=1,
        maximum=12,
    )

    if window_error:
        return jsonify({"error": window_error}), 400

    # `months_back` controls the history returned to the chart. Keeping this
    # separate from `window` allows a chart to show more context while the model
    # still averages a smaller number of months.
    months_back, months_back_error = _parse_positive_int_query(
        name="months_back",
        default=24,
        minimum=1,
        maximum=60,
    )

    if months_back_error:
        return jsonify({"error": months_back_error}), 400

    cutoff_date = _first_day_months_ago(months_back)

    # Filter by current_user.id server-side so users can never request or infer
    # another account's transaction history. Filtering expenses in SQL also
    # avoids sending income rows into the forecasting utility.
    try:
        transactions = (
            Transaction.query.filter(
                Transaction.user_id == current_user.id,
                Transaction.entry_type == "expense",
                Transaction.entry_date >= cutoff_date,
            )
            .order_by(Transaction.entry_date.asc(), Transaction.id.asc())
            .all()
        )

        # The utility returns a JSON-safe dict containing historical monthly
        # totals, per-category predictions, algorithm metadata, and the forecast
        # month used by the React chart.
        payload = forecast_next_month_expenses(transactions, window=window)
    except Exception:
        current_app.logger.exception("Expense forecast generation failed.")
        return jsonify({"error": "Expense forecast could not be generated."}), 500

    return jsonify(payload)
