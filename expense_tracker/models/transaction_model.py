"""
Transaction model.

Each transaction belongs to one user and stores both the entered amount and the
currency metadata needed to convert that amount into the user's dashboard/base
currency.
"""

from __future__ import annotations

from datetime import date

from expense_tracker.extensions import db


class Transaction(db.Model):
    """
    SQLAlchemy model for income and expense rows.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        # Forecasting, reports, and dashboard widgets commonly filter one
        # user's expense rows by date. This composite index lets PostgreSQL
        # satisfy that query pattern without scanning unrelated transactions.
        db.Index(
            "ix_transactions_user_type_date",
            "user_id",
            "entry_type",
            "entry_date",
        ),
        # Dashboard charts and reports commonly group expenses by the main and
        # sub-category pair for one user, so this index supports that access
        # pattern without changing application-level query safety.
        db.Index(
            "ix_transactions_user_category_subcategory",
            "user_id",
            "category",
            "sub_category",
        ),
    )

    # Primary key uniquely identifies each transaction row.
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key enforces that every transaction belongs to an existing user.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Amount stores the original value entered by the user.
    amount = db.Column(db.Float, nullable=False)

    # Entry type intentionally stays simple so imports and forms can validate it.
    entry_type = db.Column(db.String(20), nullable=False)

    # Category stores the main category, such as "Food & Dining".
    category = db.Column(db.String(80), nullable=False)

    # Sub-category stores the dependent second tier, such as "Groceries".
    sub_category = db.Column(db.String(80), nullable=True)

    # Optional description can store user notes or receipt merchant text.
    description = db.Column(db.String(255), default="")

    # Date is indexed because filtering/reporting by time is a core workflow.
    entry_date = db.Column(db.Date, nullable=False, default=date.today, index=True)

    # ISO-style currency code records the currency used at entry time.
    currency_code = db.Column(db.String(3), nullable=False, default="PKR")

    # Exchange rate records the conversion rate to the user's base currency.
    exchange_rate = db.Column(db.Float, nullable=False, default=1.0)

    @property
    def base_amount(self) -> float:
        """
        Return the amount converted into the user's base/dashboard currency.

        Keeping this as a property avoids duplicating converted values while
        still making reports and forecasts easy to calculate.
        """

        return round(float(self.amount) * float(self.exchange_rate or 1.0), 2)

    def to_dict(self) -> dict:
        """
        Serialize the transaction for JSON API responses.
        """

        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": round(float(self.amount), 2),
            "base_amount": self.base_amount,
            "entry_type": self.entry_type,
            "category": self.category,
            "sub_category": self.sub_category or "",
            "description": self.description or "",
            "entry_date": self.entry_date.isoformat(),
            "currency_code": self.currency_code,
            "exchange_rate": float(self.exchange_rate or 1.0),
        }

    def __repr__(self) -> str:
        """
        Return a concise debug representation for shell/log inspection.
        """

        return (
            f"<Transaction {self.entry_type} {self.amount} {self.currency_code} "
            f"{self.category}/{self.sub_category or '-'}>"
        )
