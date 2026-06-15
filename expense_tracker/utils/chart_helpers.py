"""
Chart aggregation helpers.

Routes call these helpers to keep dashboard aggregation separate from request
handling and template rendering. Expense category charts group by the main
category tier while transaction rows preserve sub-category detail.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _transaction_amount(transaction) -> float:
    """
    Return the dashboard/base-currency amount for a transaction.

    `base_amount` is preferred because multi-currency transactions should be
    summarized in one dashboard currency. The fallback keeps older test doubles
    or simple objects working.
    """

    return float(getattr(transaction, "base_amount", transaction.amount) or 0)


def expenses_by_category(transactions_query) -> dict[str, Any]:
    """
    Aggregate expense totals by main category.

    The two-tier category system stores `category` as the main category and
    `sub_category` as the dependent detail, so dashboard pie charts group by the
    main category to keep the top-level view readable.
    """

    totals: dict[str, float] = defaultdict(float)

    for transaction in transactions_query:
        if transaction.entry_type == "expense":
            category = transaction.category or "Miscellaneous"
            totals[category] += _transaction_amount(transaction)

    labels = list(totals.keys())

    return {
        "labels": labels,
        "values": [round(totals[label], 2) for label in labels],
    }


def income_vs_expense(transactions_query) -> dict[str, Any]:
    """
    Aggregate income and expense totals for a summary chart.
    """

    income = 0.0
    expense = 0.0

    for transaction in transactions_query:
        if transaction.entry_type == "income":
            income += _transaction_amount(transaction)
        elif transaction.entry_type == "expense":
            expense += _transaction_amount(transaction)

    return {
        "labels": ["Income", "Expense"],
        "values": [round(income, 2), round(expense, 2)],
    }


def monthly_expenses(transactions_query) -> dict[str, Any]:
    """
    Aggregate expense totals by month label.
    """

    monthly: dict[str, float] = defaultdict(float)

    for transaction in transactions_query:
        if transaction.entry_type == "expense":
            month = transaction.entry_date.strftime("%b %Y")
            monthly[month] += _transaction_amount(transaction)

    labels = list(monthly.keys())

    return {
        "labels": labels,
        "values": [round(monthly[label], 2) for label in labels],
    }


def spending_trend(transactions_query) -> dict[str, Any]:
    """
    Aggregate expense totals by day label for trend charts.
    """

    trend: dict[str, float] = defaultdict(float)

    for transaction in transactions_query:
        if transaction.entry_type == "expense":
            day_label = transaction.entry_date.strftime("%d %b")
            trend[day_label] += _transaction_amount(transaction)

    labels = list(trend.keys())

    return {
        "labels": labels,
        "values": [round(trend[label], 2) for label in labels],
    }


def budget_progress(budget_amount, total_expense) -> dict[str, Any]:
    """
    Build used/remaining budget values for a doughnut chart.
    """

    budget_value = float(budget_amount or 0)
    expense_value = float(total_expense or 0)
    remaining = max(budget_value - expense_value, 0)

    return {
        "labels": ["Used", "Remaining"],
        "values": [round(expense_value, 2), round(remaining, 2)],
    }
