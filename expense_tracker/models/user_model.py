"""
User model (SQLite table: `users`).

Flask-Login ke liye `UserMixin` add kiya gaya hai taake `is_authenticated`, `get_id`,
etc. built-in mil jayein.

Password plain text DB mein kabhi save nahi — sirf hash store hota hai.
"""

from __future__ import annotations

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from expense_tracker.extensions import db


class User(UserMixin, db.Model):
    """ORM class ↔ relational table `users`."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Ek user ki bohat si transactions — `lazy="dynamic"` se query object milta hai
    transactions = db.relationship(
        "Transaction",
        backref="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        """Signup / reset flow: plain password se hash generate karke save."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Login: user ke diye hue password ko stored hash se match karta hai."""
        return check_password_hash(self.password_hash, password)
