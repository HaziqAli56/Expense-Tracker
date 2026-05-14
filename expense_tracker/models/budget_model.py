
from expense_tracker.extensions import db


class Budget(db.Model):

    __tablename__ = "budgets"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    month = db.Column(
        db.String(20),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )
