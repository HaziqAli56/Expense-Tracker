"""
Budget model.

The model keeps the existing monthly total-budget behavior and adds category
budget limits for modern budget alert APIs.
"""

from __future__ import annotations

from datetime import datetime

from expense_tracker.extensions import db


class Budget(db.Model):
    """
    SQLAlchemy model for user budget limits.
    """

    __tablename__ = "budgets"

    # Primary key uniquely identifies a budget rule.
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key keeps every budget scoped to a specific authenticated user.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Month is stored as YYYY-MM so queries can target monthly reporting windows.
    month = db.Column(db.String(20), nullable=False, index=True)

    # Amount preserves compatibility with the existing total monthly budget UI.
    amount = db.Column(db.Float, nullable=True)

    # Category enables per-category budget limits and alert calculations.
    category = db.Column(db.String(64), nullable=True, index=True)

    # Limit amount is the category-specific maximum spending target.
    limit_amount = db.Column(db.Float, nullable=True)

    # Created timestamp supports sorting and audit/debug workflows.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        # One category budget per user/month/category avoids duplicate alerts.
        db.UniqueConstraint(
            "user_id",
            "month",
            "category",
            name="uq_budget_user_month_category",
        ),
    )

    @property
    def effective_limit(self) -> float:
        """
        Return the category limit when present, otherwise the legacy amount.
        """

        return float(self.limit_amount if self.limit_amount is not None else self.amount or 0)

    def to_dict(self) -> dict:
        """
        Serialize budget metadata for API consumers.
        """

        return {
            "id": self.id,
            "user_id": self.user_id,
            "month": self.month,
            "category": self.category,
            "limit_amount": self.effective_limit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """
        Return a concise debug representation for shell/log inspection.
        """

        return f"<Budget {self.month} {self.category or 'total'}: {self.effective_limit}>"
