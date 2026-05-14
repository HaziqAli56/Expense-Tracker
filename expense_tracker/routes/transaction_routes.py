"""
Transaction routes (Controller): list + filters, create, update, delete (CRUD).

Security rule: queries mein `user_id=current_user.id` lagaya gaya hai taake
koi user doosre ki rows edit/delete na kar sake (even if URL guess kare).
"""

from __future__ import annotations

import math
from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from expense_tracker.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from expense_tracker.extensions import db
from expense_tracker.models.transaction_model import Transaction

transaction_bp = Blueprint("transactions", __name__, url_prefix="/transactions")


def _tx_form_draft() -> dict[str, str]:
    """POST fail hone par form values wapas UI ko dene ke liye."""
    return {
        "amount": (request.form.get("amount") or "").strip(),
        "entry_date": (request.form.get("entry_date") or "").strip(),
        "entry_type": (request.form.get("entry_type") or "").strip(),
        "category": (request.form.get("category") or "").strip(),
        "description": (request.form.get("description") or "").strip(),
    }


def _parse_date(value: str | None):
    """
    HTML `<input type="date">` se `YYYY-MM-DD` string aati hai.
    Invalid string par None return — caller default choose karega.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@transaction_bp.route("/")
@login_required
def list_transactions():
    """GET query params se filter + ordered list render."""
    q = Transaction.query.filter_by(user_id=current_user.id)

    display_from = request.args.get("date_from") or ""
    display_to = request.args.get("date_to") or ""
    date_from = _parse_date(display_from or None)
    date_to = _parse_date(display_to or None)
    category = (request.args.get("category") or "").strip()
    entry_type = (request.args.get("entry_type") or "").strip()

    q_date_from, q_date_to = date_from, date_to
    if date_from and date_to and date_from > date_to:
        flash("From date ko To date se pehle / barabar hona chahiye.", "warning")
        q_date_from = q_date_to = None

    if q_date_from:
        q = q.filter(Transaction.entry_date >= q_date_from)
    if q_date_to:
        q = q.filter(Transaction.entry_date <= q_date_to)
    if category:
        q = q.filter(Transaction.category == category)
    if entry_type in ("income", "expense"):
        q = q.filter(Transaction.entry_type == entry_type)

    items = q.order_by(Transaction.entry_date.desc(), Transaction.id.desc()).all()
    all_categories = sorted(set(EXPENSE_CATEGORIES + INCOME_CATEGORIES))

    return render_template(
        "transactions/list.html",
        transactions=items,
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
        filter_categories=all_categories,
        filters={
            "date_from": display_from,
            "date_to": display_to,
            "category": category,
            "entry_type": entry_type,
        },
    )


@transaction_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Nayi transaction insert — server-side validation (categories whitelist)."""
    if request.method == "POST":
        amount_raw = request.form.get("amount")
        entry_type = (request.form.get("entry_type") or "").strip()
        category = (request.form.get("category") or "").strip()
        description = (request.form.get("description") or "").strip()
        entry_date = _parse_date(request.form.get("entry_date")) or date.today()

        try:
            amount = float(amount_raw)
        except (TypeError, ValueError):
            amount = float("nan")

        valid_cats = INCOME_CATEGORIES if entry_type == "income" else EXPENSE_CATEGORIES
        if not math.isfinite(amount) or amount <= 0:
            flash("Amount valid positive number hona chahiye.", "danger")
            return render_template(
                "transactions/form.html",
                form_title="Nayi transaction",
                action=url_for("transactions.add"),
                expense_categories=EXPENSE_CATEGORIES,
                income_categories=INCOME_CATEGORIES,
                transaction=None,
                form_draft=_tx_form_draft(),
            )
        if entry_type not in ("income", "expense"):
            flash("Type income ya expense hona chahiye.", "danger")
            return render_template(
                "transactions/form.html",
                form_title="Nayi transaction",
                action=url_for("transactions.add"),
                expense_categories=EXPENSE_CATEGORIES,
                income_categories=INCOME_CATEGORIES,
                transaction=None,
                form_draft=_tx_form_draft(),
            )
        if category not in valid_cats:
            flash("Category invalid hai.", "danger")
            return render_template(
                "transactions/form.html",
                form_title="Nayi transaction",
                action=url_for("transactions.add"),
                expense_categories=EXPENSE_CATEGORIES,
                income_categories=INCOME_CATEGORIES,
                transaction=None,
                form_draft=_tx_form_draft(),
            )

        amount = round(amount, 2)
        t = Transaction(
            user_id=current_user.id,
            amount=amount,
            entry_type=entry_type,
            category=category,
            description=description,
            entry_date=entry_date,
        )
        db.session.add(t)
        db.session.commit()
        flash("Transaction save ho gayi.", "success")
        return redirect(url_for("transactions.list_transactions"))

    return render_template(
        "transactions/form.html",
        form_title="Nayi transaction",
        action=url_for("transactions.add"),
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
        transaction=None,
        form_draft=None,
    )


@transaction_bp.route("/<int:tx_id>/edit", methods=["GET", "POST"])
@login_required
def edit(tx_id: int):
    """Sirf apni row update — mismatch par 404."""
    t = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first()
    if t is None:
        abort(404)

    if request.method == "POST":
        amount_raw = request.form.get("amount")
        entry_type = (request.form.get("entry_type") or "").strip()
        category = (request.form.get("category") or "").strip()
        description = (request.form.get("description") or "").strip()
        entry_date = _parse_date(request.form.get("entry_date")) or t.entry_date

        try:
            amount = float(amount_raw)
        except (TypeError, ValueError):
            amount = float("nan")

        valid_cats = INCOME_CATEGORIES if entry_type == "income" else EXPENSE_CATEGORIES
        if not math.isfinite(amount) or amount <= 0:
            flash("Amount valid positive number hona chahiye.", "danger")
            return render_template(
                "transactions/form.html",
                form_title="Transaction edit",
                action=url_for("transactions.edit", tx_id=t.id),
                expense_categories=EXPENSE_CATEGORIES,
                income_categories=INCOME_CATEGORIES,
                transaction=t,
                form_draft=_tx_form_draft(),
            )
        if entry_type not in ("income", "expense"):
            flash("Type income ya expense hona chahiye.", "danger")
            return render_template(
                "transactions/form.html",
                form_title="Transaction edit",
                action=url_for("transactions.edit", tx_id=t.id),
                expense_categories=EXPENSE_CATEGORIES,
                income_categories=INCOME_CATEGORIES,
                transaction=t,
                form_draft=_tx_form_draft(),
            )
        if category not in valid_cats:
            flash("Category invalid hai.", "danger")
            return render_template(
                "transactions/form.html",
                form_title="Transaction edit",
                action=url_for("transactions.edit", tx_id=t.id),
                expense_categories=EXPENSE_CATEGORIES,
                income_categories=INCOME_CATEGORIES,
                transaction=t,
                form_draft=_tx_form_draft(),
            )

        amount = round(amount, 2)
        t.amount = amount
        t.entry_type = entry_type
        t.category = category
        t.description = description
        t.entry_date = entry_date
        db.session.commit()
        flash("Transaction update ho gayi.", "success")
        return redirect(url_for("transactions.list_transactions"))

    return render_template(
        "transactions/form.html",
        form_title="Transaction edit",
        action=url_for("transactions.edit", tx_id=t.id),
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
        transaction=t,
        form_draft=None,
    )


@transaction_bp.route("/<int:tx_id>/delete", methods=["POST"])
@login_required
def delete(tx_id: int):
    """POST-only delete (CSRF production mein add karna best practice hai)."""
    t = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first()
    if t is None:
        abort(404)
    db.session.delete(t)
    db.session.commit()
    flash("Transaction delete ho gayi.", "info")
    return redirect(url_for("transactions.list_transactions"))
