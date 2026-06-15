"""
Backward-compatible category exports.

New code should import from `expense_tracker.utils.constants`. This module stays
in place because older routes, templates, and scripts already import
`expense_tracker.constants`.
"""

from expense_tracker.utils.constants import (
    EXPENSE_CATEGORIES,
    EXPENSE_CATEGORY_MAP,
    INCOME_CATEGORIES,
    INCOME_CATEGORY_MAP,
    first_sub_category_for,
    get_expense_category_map,
    get_income_category_map,
    is_valid_expense_category,
    is_valid_income_category,
)


__all__ = [
    "EXPENSE_CATEGORIES",
    "EXPENSE_CATEGORY_MAP",
    "INCOME_CATEGORIES",
    "INCOME_CATEGORY_MAP",
    "first_sub_category_for",
    "get_expense_category_map",
    "get_income_category_map",
    "is_valid_expense_category",
    "is_valid_income_category",
]
