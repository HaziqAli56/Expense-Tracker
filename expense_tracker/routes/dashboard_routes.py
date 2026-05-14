
"""
Dashboard route (Controller): totals + chart JSON for the View.

Data aggregation yahan hoti hai.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    render_template,
    make_response,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    current_user,
    login_required
)

from reportlab.pdfgen import canvas

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

    expense_chart = expenses_by_category(
        txs
    )

    income_chart = income_vs_expense(
        txs
    )

    monthly_chart = monthly_expenses(
        txs
    )

    trend_chart = spending_trend(
        txs
    )

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

    # ======================
    # HAS CHART
    # ======================

    has_chart = bool(
        expense_chart.get("labels")
    )

    return render_template(

        "dashboard.html",

        total_income=round(
            total_income,
            2
        ),

        total_expense=round(
            total_expense,
            2
        ),

        balance=round(
            balance,
            2
        ),

        expense_chart=expense_chart,

        income_chart=income_chart,

        monthly_chart=monthly_chart,

        trend_chart=trend_chart,

        budget_chart=budget_chart,

        latest_budget=latest_budget,

        has_chart=has_chart

    )


# ==========================================
# PDF REPORT
# ==========================================

@dashboard_bp.route(
    "/report/pdf"
)
@login_required
def generate_pdf():

    response = make_response()

    response.headers[
        "Content-Type"
    ] = "application/pdf"

    response.headers[
        "Content-Disposition"
    ] = (
        "attachment; filename=report.pdf"
    )

    p = canvas.Canvas(response)

    # TITLE
    p.setFont(
        "Helvetica-Bold",
        18
    )

    p.drawString(

        100,
        800,

        "Expense Tracker Report"

    )

    # USERNAME
    p.setFont(
        "Helvetica",
        12
    )

    p.drawString(

        100,
        760,

        f"User: {current_user.username}"

    )

    # TOTAL INCOME
    total_income = sum(

        t.amount
        for t in current_user.transactions.all()

        if t.entry_type == "income"

    )

    # TOTAL EXPENSE
    total_expense = sum(

        t.amount
        for t in current_user.transactions.all()

        if t.entry_type == "expense"

    )

    balance = total_income - total_expense

    # REPORT DATA
    p.drawString(

        100,
        720,

        f"Total Income: {total_income}"

    )

    p.drawString(

        100,
        690,

        f"Total Expense: {total_expense}"

    )

    p.drawString(

        100,
        660,

        f"Balance: {balance}"

    )

    p.save()

    return response


# ==========================================
# SAVE BUDGET
# ==========================================

@dashboard_bp.route(
    "/budget",
    methods=["POST"]
)
@login_required
def set_budget():

    amount = request.form.get(
        "amount"
    )

    month = request.form.get(
        "month"
    )

    budget = Budget(

        user_id=current_user.id,

        month=month,

        amount=float(amount)

    )

    db.session.add(
        budget
    )

    db.session.commit()

    flash(

        "Budget saved successfully!",

        "success"

    )

    return redirect(

        url_for(
            "dashboard.home"
        )

    )
