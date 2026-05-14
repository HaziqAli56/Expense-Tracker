
"""
Chart helper functions — Controller se call hoti hain,
View (Chart.js) ko data deti hain.

Separation of concerns:
route file lambi na ho,
aggregation logic yahan rakhi.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


# ==========================================
# EXPENSES BY CATEGORY
# Pie Chart
# ==========================================

def expenses_by_category(
    transactions_query
) -> dict[str, Any]:

    totals: dict[str, float] = defaultdict(float)

    for t in transactions_query:

        if t.entry_type == "expense":

            category = t.category or "Other"

            totals[category] += float(
                t.amount or 0
            )

    if not totals:

        return {
            "labels": [],
            "values": []
        }

    labels = list(totals.keys())

    values = [

        round(totals[k], 2)

        for k in labels
    ]

    return {

        "labels": labels,

        "values": values

    }


# ==========================================
# INCOME VS EXPENSE
# Doughnut / Bar Chart
# ==========================================

def income_vs_expense(
    transactions_query
) -> dict[str, Any]:

    income = 0
    expense = 0

    for t in transactions_query:

        if t.entry_type == "income":

            income += float(
                t.amount or 0
            )

        elif t.entry_type == "expense":

            expense += float(
                t.amount or 0
            )

    return {

        "labels": [
            "Income",
            "Expense"
        ],

        "values": [

            round(income, 2),

            round(expense, 2)

        ]

    }


# ==========================================
# MONTHLY EXPENSES
# Bar Chart
# ==========================================

def monthly_expenses(
    transactions_query
) -> dict[str, Any]:

    monthly: dict[str, float] = defaultdict(float)

    for t in transactions_query:

        if t.entry_type == "expense":

            month = t.entry_date.strftime(
                "%b %Y"
            )

            monthly[month] += float(
                t.amount or 0
            )

    if not monthly:

        return {
            "labels": [],
            "values": []
        }

    labels = list(monthly.keys())

    values = [

        round(monthly[k], 2)

        for k in labels
    ]

    return {

        "labels": labels,

        "values": values

    }


# ==========================================
# SPENDING TREND
# Line Graph
# ==========================================

def spending_trend(
    transactions_query
) -> dict[str, Any]:

    trend: dict[str, float] = defaultdict(float)

    for t in transactions_query:

        if t.entry_type == "expense":

            date = t.entry_date.strftime(
                "%d %b"
            )

            trend[date] += float(
                t.amount or 0
            )

    if not trend:

        return {
            "labels": [],
            "values": []
        }

    labels = list(trend.keys())

    values = [

        round(trend[k], 2)

        for k in labels
    ]

    return {

        "labels": labels,

        "values": values

    }


# ==========================================
# BUDGET PROGRESS
# Doughnut Chart
# ==========================================

def budget_progress(
    budget_amount,
    total_expense
) -> dict[str, Any]:

    remaining = max(
        budget_amount - total_expense,
        0
    )

    return {

        "labels": [

            "Used",
            "Remaining"

        ],

        "values": [

            round(total_expense, 2),

            round(remaining, 2)

        ]

    }
