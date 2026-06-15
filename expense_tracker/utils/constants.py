"""
Central business constants for transaction categories.

This module is the single source of truth for category data used by Flask
routes, validation helpers, import/export code, dashboard aggregation, and any
future AI/context generation scripts.
"""

from __future__ import annotations

from types import MappingProxyType


# Main expense categories mapped to their allowed sub-categories.
EXPENSE_CATEGORY_MAP = MappingProxyType(
    {
        "Housing & Utilities": [
            "Rent",
            "Utilities",
            "Internet & Mobile",
            "Home Maintenance",
            "Property & Legal",
        ],
        "Transportation": [
            "Fuel",
            "Vehicle Maintenance",
            "Ride-Hailing",
            "Tolls & Parking",
        ],
        "Food & Dining": [
            "Groceries",
            "Dining Out",
            "Snacks & Takeaway",
        ],
        "Education & Professional": [
            "University & Tuition",
            "Exams & Certifications",
            "Tech & Subscriptions",
            "Hardware",
        ],
        "Health & Wellness": [
            "Medical & Pharmacy",
            "Family Health",
            "Fitness",
        ],
        "Personal & Lifestyle": [
            "Family Support",
            "Shopping",
            "Entertainment",
        ],
        "Miscellaneous": [
            "Charity & Zakat",
            "Bank Charges",
            "Unexpected Expenses",
        ],
    }
)

# Income categories also use sub-categories so the transaction form never needs
# to disable the sub-category field for income entries.
INCOME_CATEGORY_MAP = MappingProxyType(
    {
        "Salary": [
            "Monthly Salary",
            "Bonus",
            "Allowance",
        ],
        "Freelance": [
            "Client Payment",
            "Project Advance",
            "Platform Payout",
        ],
        "Investment": [
            "Dividends",
            "Capital Gains",
            "Profit Share",
        ],
        "Other": [
            "Gift",
            "Refund",
            "Misc Income",
        ],
    }
)

# Compatibility list used by older code that expects flat income categories.
INCOME_CATEGORIES = list(INCOME_CATEGORY_MAP.keys())

# Compatibility list used by legacy templates, filters, and reports that expect
# a flat category collection.
EXPENSE_CATEGORIES = list(EXPENSE_CATEGORY_MAP.keys())


def get_expense_category_map() -> dict[str, list[str]]:
    """
    Return a JSON-serializable copy of the expense category hierarchy.

    A copy is returned so callers cannot mutate the module-level source of truth
    accidentally during request handling or tests.
    """

    return {
        category: list(sub_categories)
        for category, sub_categories in EXPENSE_CATEGORY_MAP.items()
    }


def get_income_category_map() -> dict[str, list[str]]:
    """
    Return a JSON-serializable copy of the income category hierarchy.
    """

    return {
        category: list(sub_categories)
        for category, sub_categories in INCOME_CATEGORY_MAP.items()
    }


def is_valid_expense_category(category: str | None, sub_category: str | None) -> bool:
    """
    Validate that a main expense category and sub-category pair is allowed.

    Centralized validation prevents routes, imports, OCR, and future APIs from
    each implementing slightly different rules.
    """

    clean_category = (category or "").strip()
    clean_sub_category = (sub_category or "").strip()

    return clean_sub_category in EXPENSE_CATEGORY_MAP.get(clean_category, [])


def is_valid_income_category(category: str | None, sub_category: str | None = None) -> bool:
    """
    Validate an income category and optional sub-category pair.
    """

    clean_category = (category or "").strip()
    clean_sub_category = (sub_category or "").strip()

    if sub_category is None:
        return clean_category in INCOME_CATEGORY_MAP

    return clean_sub_category in INCOME_CATEGORY_MAP.get(clean_category, [])


def first_sub_category_for(category: str | None) -> str:
    """
    Return the default sub-category for a main expense category.

    This is useful for migrations, legacy form defaults, and fallback handling
    when older rows only have a main category.
    """

    clean_category = (category or "").strip()
    sub_categories = EXPENSE_CATEGORY_MAP.get(clean_category, [])

    if not sub_categories:
        sub_categories = INCOME_CATEGORY_MAP.get(clean_category, [])

    return sub_categories[0] if sub_categories else ""
