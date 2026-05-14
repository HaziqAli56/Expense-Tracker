"""
Transaction model (SQLite table: `transactions`).

Har row ek income ya expense entry represent karti hai aur `user_id` foreign key
se `users.id` se link hoti hai (relational integrity).
"""

from __future__ import annotations

from datetime import date

from expense_tracker.extensions import db


class Transaction(db.Model):
    """ORM class ↔ relational table `transactions`."""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    # ForeignKey: relational DB rule — ye user exist karna chahiye
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    amount = db.Column(db.Float, nullable=False)
    # "income" ya "expense" — string enum jaisa use (simple university scope)
    entry_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255), default="")
    entry_date = db.Column(db.Date, nullable=False, default=date.today, index=True)

    def __repr__(self) -> str:
        """Debug / shell mein object print karne par readable string."""
        return f"<Transaction {self.entry_type} {self.amount} {self.category}>"
