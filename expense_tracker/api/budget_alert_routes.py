"""
Budget alert API routes.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import extract, func

from expense_tracker.extensions import db
from expense_tracker.models.budget_model import Budget
from expense_tracker.models.transaction_model import Transaction
from expense_tracker.utils.constants import EXPENSE_CATEGORIES


budget_alert_api_bp = Blueprint("budget_alert_api", __name__, url_prefix="/api/budgets")


def _current_month() -> str:
    """
    Return the current month key in YYYY-MM format.
    """

    return date.today().strftime("%Y-%m")


def _parse_month_key(value: str | None) -> tuple[int, int, str] | None:
    """
    Parse a YYYY-MM month key into year/month integers and its normalized key.

    Returning None for bad input lets routes respond with a clean 400 instead
    of raising ValueError and producing a generic server error.
    """

    month_key = (value or _current_month()).strip()

    try:
        year_text, month_text = month_key.split("-", 1)
        year = int(year_text)
        month_number = int(month_text)
    except ValueError:
        return None

    if year < 2000 or month_number < 1 or month_number > 12:
        return None

    return year, month_number, f"{year:04d}-{month_number:02d}"


def _status_for_percentage(percentage: float) -> str:
    """
    Map budget usage percentage to visual alert status.
    """

    if percentage >= 90:
        return "danger"
    if percentage >= 70:
        return "warning"
    return "success"


@budget_alert_api_bp.post("")
@login_required
def upsert_category_budget():
    """
    Create or update a category monthly spending limit for the current user.
    """

    payload = request.get_json(silent=True) or {}
    category = (payload.get("category") or "").strip()
    parsed_month = _parse_month_key(payload.get("month"))

    try:
        limit_amount = round(float(payload.get("limit_amount")), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "A numeric limit_amount is required."}), 400

    if parsed_month is None:
        return jsonify({"error": "month must use YYYY-MM format."}), 400

    _, _, month = parsed_month

    if not category:
        return jsonify({"error": "Category is required."}), 400

    if category not in EXPENSE_CATEGORIES:
        return jsonify({"error": "Category must be a valid main expense category."}), 400

    if limit_amount <= 0:
        return jsonify({"error": "limit_amount must be greater than zero."}), 400

    budget = Budget.query.filter_by(
        user_id=current_user.id,
        month=month,
        category=category,
    ).first()

    if budget is None:
        budget = Budget(
            user_id=current_user.id,
            month=month,
            category=category,
        )
        db.session.add(budget)

    budget.limit_amount = limit_amount
    db.session.commit()

    return jsonify({"budget": budget.to_dict()})


@budget_alert_api_bp.get("/alerts")
@login_required
def budget_alerts():
    """
    Return current-month category budget usage with visual alert metadata.
    """

    parsed_month = _parse_month_key(request.args.get("month"))

    if parsed_month is None:
        return jsonify({"error": "month must use YYYY-MM format."}), 400

    year, month_number, month = parsed_month

    budgets = Budget.query.filter_by(user_id=current_user.id, month=month).filter(
        Budget.category.isnot(None)
    ).all()

    alerts = []

    for budget in budgets:
        spent = (
            db.session.query(func.coalesce(func.sum(Transaction.amount * Transaction.exchange_rate), 0.0))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.entry_type == "expense",
                Transaction.category == budget.category,
                extract("year", Transaction.entry_date) == year,
                extract("month", Transaction.entry_date) == month_number,
            )
            .scalar()
        )

        limit_amount = budget.effective_limit
        percentage = round((float(spent) / limit_amount) * 100, 2) if limit_amount else 0

        alerts.append(
            {
                "category": budget.category,
                "month": month,
                "spent": round(float(spent), 2),
                "limit_amount": limit_amount,
                "percentage_used": percentage,
                "status": _status_for_percentage(percentage),
            }
        )

    return jsonify({"alerts": alerts})
