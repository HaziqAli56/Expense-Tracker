"""
SQLAlchemy models package exports.

Teacher note: `User` aur `Transaction` classes `db.Model` hain — inka matlab
SQLite database mein `users` aur `transactions` tables map hoti hain.
"""

from expense_tracker.models.transaction_model import Transaction
from expense_tracker.models.user_model import User
from .budget_model import Budget

__all__ = ["User", "Transaction"]
