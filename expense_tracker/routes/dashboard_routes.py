"""
Dashboard routes.

This module renders the existing Flask dashboard and exposes a JSON summary API
for frontend consumers. Dashboard category aggregation groups by the main
category tier while transaction records still preserve sub-category detail.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import extract

from expense_tracker.extensions import db
from expense_tracker.models.budget_model import Budget
from expense_tracker.models.transaction_model import Transaction
from expense_tracker.utils.chart_helpers import (
    budget_progress,
    expenses_by_category,
    income_vs_expense,
    monthly_expenses,
    spending_trend,
)
from expense_tracker.utils.constants import EXPENSE_CATEGORIES


dashboard_bp = Blueprint("dashboard", __name__)


def _dashboard_totals(transactions) -> tuple[float, float, float]:
    """
    Calculate income, expense, and balance in the dashboard/base currency.

    Using `base_amount` keeps multi-currency entries consistent across totals,
    charts, reports, and budget progress.
    """

    total_income = sum(
        transaction.base_amount
        for transaction in transactions
        if transaction.entry_type == "income"
    )
    total_expense = sum(
        transaction.base_amount
        for transaction in transactions
        if transaction.entry_type == "expense"
    )

    return total_income, total_expense, total_income - total_expense


def _current_month_transactions_query():
    """
    Return the authenticated user's transactions for the current month/year.

    Dashboard summary cards and monthly budget progress should use the current
    calendar month so the numbers align with monthly budgeting decisions instead
    of showing lifetime totals.
    """

    today = date.today()

    return current_user.transactions.filter(
        extract("year", Transaction.entry_date) == today.year,
        extract("month", Transaction.entry_date) == today.month,
    )


@dashboard_bp.route("/")
@login_required
def home():
    """
    Render the authenticated user's dashboard.
    """

    # Full history stays available for charts that show trends over time.
    transactions = current_user.transactions.all()

    # Top summary cards intentionally use current-month data only.
    current_month_transactions = _current_month_transactions_query().all()
    total_income, total_expense, balance = _dashboard_totals(current_month_transactions)
    expense_chart = expenses_by_category(transactions)
    current_month_key = date.today().strftime("%Y-%m")
    latest_budget = (
        Budget.query.filter_by(
            user_id=current_user.id,
            month=current_month_key,
            category=None,
        )
        .order_by(Budget.id.desc())
        .first()
    )
    budget_chart = (
        budget_progress(latest_budget.amount, total_expense)
        if latest_budget
        else None
    )

    return render_template(
        "dashboard.html",
        summary_month=date.today().strftime("%B %Y"),
        current_month_key=current_month_key,
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        balance=round(balance, 2),
        expense_chart=expense_chart,
        income_chart=income_vs_expense(transactions),
        monthly_chart=monthly_expenses(transactions),
        trend_chart=spending_trend(transactions),
        budget_chart=budget_chart,
        latest_budget=latest_budget,
        expense_categories=EXPENSE_CATEGORIES,
        has_chart=bool(expense_chart.get("labels")),
    )


@dashboard_bp.get("/api/dashboard/summary")
@login_required
def api_dashboard_summary():
    """
    Return dashboard summary data for React/API consumers.
    """

    transactions = current_user.transactions.all()
    current_month_transactions = _current_month_transactions_query().all()
    total_income, total_expense, balance = _dashboard_totals(current_month_transactions)

    return jsonify(
        {
            "summary_month": date.today().strftime("%Y-%m"),
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "balance": round(balance, 2),
            "expenses_by_category": expenses_by_category(transactions),
            "income_vs_expense": income_vs_expense(transactions),
            "monthly_expenses": monthly_expenses(transactions),
            "spending_trend": spending_trend(transactions),
        }
    )


@dashboard_bp.route("/budget", methods=["POST"])
@login_required
def set_budget():
    """
    Save a legacy total monthly budget from the server-rendered dashboard.
    """

    amount_raw = request.form.get("amount")
    month = request.form.get("month")

    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        flash("Invalid budget amount.", "danger")
        return redirect(url_for("dashboard.home"))

    if amount <= 0:
        flash("Budget amount must be greater than zero.", "danger")
        return redirect(url_for("dashboard.home"))

    budget = Budget.query.filter_by(
        user_id=current_user.id,
        month=month,
        category=None,
    ).first()

    if budget is None:
        budget = Budget(
            user_id=current_user.id,
            month=month,
            category=None,
        )
        db.session.add(budget)

    budget.amount = amount
    db.session.commit()
    flash("Budget saved successfully!", "success")

    return redirect(url_for("dashboard.home"))
