"""
Dashboard route (Controller): totals + charts + budget.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    current_user,
    login_required
)

from expense_tracker.extensions import db
from expense_tracker.models.budget_model import Budget

from expense_tracker.utils.chart_helpers import (
    expenses_by_category,
    income_vs_expense,
    monthly_expenses,
    spending_trend,
    budget_progress
)

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


# ==========================================
# DASHBOARD HOME
# ==========================================

@dashboard_bp.route("/")
@login_required
def home():

    txs = current_user.transactions.all()

    # ======================
    # TOTALS
    # ======================

    total_income = sum(
        t.amount for t in txs
        if t.entry_type == "income"
    )

    total_expense = sum(
        t.amount for t in txs
        if t.entry_type == "expense"
    )

    balance = total_income - total_expense

    # ======================
    # CHARTS
    # ======================

    expense_chart = expenses_by_category(txs)

    income_chart = income_vs_expense(txs)

    monthly_chart = monthly_expenses(txs)

    trend_chart = spending_trend(txs)

    # ======================
    # BUDGET
    # ======================

    latest_budget = Budget.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Budget.id.desc()
    ).first()

    budget_chart = None

    if latest_budget:
        budget_chart = budget_progress(
            latest_budget.amount,
            total_expense
        )

    has_chart = bool(
        expense_chart.get("labels")
    )

    return render_template(
        "dashboard.html",

        total_income=round(total_income, 2),

        total_expense=round(total_expense, 2),

        balance=round(balance, 2),

        expense_chart=expense_chart,

        income_chart=income_chart,

        monthly_chart=monthly_chart,

        trend_chart=trend_chart,

        budget_chart=budget_chart,

        latest_budget=latest_budget,

        has_chart=has_chart
    )


# ==========================================
# SAVE BUDGET
# ==========================================

@dashboard_bp.route(
    "/budget",
    methods=["POST"]
)
@login_required
def set_budget():

    amount = request.form.get("amount")

    month = request.form.get("month")

    try:
        amount = float(amount)

    except (TypeError, ValueError):

        flash(
            "Invalid budget amount.",
            "danger"
        )

        return redirect(
            url_for("dashboard.home")
        )

    budget = Budget(
        user_id=current_user.id,
        month=month,
        amount=amount
    )

    db.session.add(budget)

    db.session.commit()

    flash(
        "Budget saved successfully!",
        "success"
    )

    return redirect(
        url_for("dashboard.home")
    )