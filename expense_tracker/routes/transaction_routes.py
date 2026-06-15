"""
Transaction routes and APIs.
This module supports both the existing server-rendered transaction pages and
JSON endpoints used by the React frontend. All transaction writes validate
amounts, dates, entry type, and the two-tier expense category relationship.
"""

from __future__ import annotations

import math
from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from expense_tracker.extensions import db
from expense_tracker.models.transaction_model import Transaction
from expense_tracker.utils.constants import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    first_sub_category_for,
    get_expense_category_map,
    get_income_category_map,
    is_valid_expense_category,
    is_valid_income_category,
)
from expense_tracker.utils.currency import fetch_exchange_rate


transaction_bp = Blueprint("transactions", __name__, url_prefix="/transactions")
transaction_api_bp = Blueprint("transaction_api", __name__, url_prefix="/api")


def _parse_date(value: str | None) -> date | None:
    """Parse a browser/API date string in YYYY-MM-DD format."""
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_positive_amount(value) -> tuple[float | None, str | None]:
    """Parse and validate a positive transaction amount."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None, "Amount must be numeric."

    if not math.isfinite(amount) or amount <= 0:
        return None, "Amount must be greater than zero."

    return round(amount, 2), None


def _parse_currency_fields(source: dict | None = None) -> tuple[str, float]:
    """Parse currency metadata from JSON or form data."""
    source = source or request.form
    base_currency = current_app.config["DEFAULT_BASE_CURRENCY"]
    currency_code = (source.get("currency_code") or base_currency).strip().upper()
    exchange_rate_raw = str(source.get("exchange_rate") or "").strip()

    if len(currency_code) != 3 or not currency_code.isalpha():
        currency_code = base_currency

    if exchange_rate_raw:
        try:
            exchange_rate = float(exchange_rate_raw)
        except ValueError:
            exchange_rate = 1.0
    else:
        try:
            exchange_rate = fetch_exchange_rate(currency_code, base_currency)
        except Exception:
            exchange_rate = 1.0

    if not math.isfinite(exchange_rate) or exchange_rate <= 0:
        exchange_rate = 1.0

    return currency_code, exchange_rate


def _validate_category_fields(entry_type: str, category: str, sub_category: str | None) -> tuple[str | None, str | None, str | None]:
    """Validate category fields for income and expense transactions."""
    clean_entry_type = (entry_type or "").strip().lower()
    clean_category = (category or "").strip()
    clean_sub_category = (sub_category or "").strip()

    if clean_entry_type not in {"income", "expense"}:
        return None, None, "Type must be either income or expense."

    if clean_entry_type == "income":
        if not clean_sub_category:
            clean_sub_category = first_sub_category_for(clean_category)

        if not is_valid_income_category(clean_category, clean_sub_category):
            return None, None, "Invalid income category."

        return clean_category, clean_sub_category, None

    if not is_valid_expense_category(clean_category, clean_sub_category):
        return None, None, "Invalid expense category or sub-category."

    return clean_category, clean_sub_category, None


def _tx_form_draft() -> dict[str, str]:
    """Return submitted form values for refilling."""
    return {
        "amount": (request.form.get("amount") or "").strip(),
        "entry_date": (request.form.get("entry_date") or "").strip(),
        "entry_type": (request.form.get("entry_type") or "").strip(),
        "category": (request.form.get("category") or "").strip(),
        "sub_category": (request.form.get("sub_category") or "").strip(),
        "description": (request.form.get("description") or "").strip(),
        "currency_code": (request.form.get("currency_code") or current_app.config["DEFAULT_BASE_CURRENCY"]).strip().upper(),
        "exchange_rate": (request.form.get("exchange_rate") or "1").strip(),
    }


def _render_transaction_form(form_title: str, action: str, transaction=None, form_draft=None, etype=None):
    """
    Render the shared add/edit form with centralized category data.
    FIX: etype parameter added to prevent 'Undefined' JSON serialization errors.
    """
    # Determine the entry type for the template
    current_etype = etype or (transaction.entry_type if transaction else "expense")
    
    return render_template(
        "transactions/form.html",
        form_title=form_title,
        action=action,
        expense_categories=EXPENSE_CATEGORIES,
        expense_category_map=get_expense_category_map(),
        income_categories=INCOME_CATEGORIES,
        transaction=transaction,
        form_draft=form_draft,
        etype=current_etype,
    )


def _apply_transaction_payload(transaction: Transaction, payload: dict, default_date: date | None = None) -> tuple[bool, str | None]:
    """Validate payload data and apply it to a Transaction instance."""
    amount, amount_error = _parse_positive_amount(payload.get("amount"))

    if amount_error:
        return False, amount_error

    entry_type = (payload.get("entry_type") or "").strip().lower()
    category, sub_category, category_error = _validate_category_fields(
        entry_type=entry_type,
        category=payload.get("category"),
        sub_category=payload.get("sub_category"),
    )

    if category_error:
        return False, category_error

    entry_date = _parse_date(payload.get("entry_date")) or default_date or date.today()
    currency_code, exchange_rate = _parse_currency_fields(payload)

    transaction.amount = amount
    transaction.entry_type = entry_type
    transaction.category = category
    transaction.sub_category = sub_category
    transaction.description = (payload.get("description") or "").strip()
    transaction.entry_date = entry_date
    transaction.currency_code = currency_code
    transaction.exchange_rate = exchange_rate

    return True, None


@transaction_api_bp.get("/categories")
@transaction_api_bp.get("/get-categories")
@login_required
def api_categories():
    """Return centralized category configuration for React/JS dependent dropdowns."""
    return jsonify(
        {
            "expense_categories": get_expense_category_map(),
            "income_category_map": get_income_category_map(),
            "income_categories": INCOME_CATEGORIES,
        }
    )


@transaction_api_bp.get("/transactions")
@login_required
def api_list_transactions():
    """Return the authenticated user's transactions as JSON."""
    transactions = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.entry_date.desc(), Transaction.id.desc())
        .all()
    )

    return jsonify({"transactions": [transaction.to_dict() for transaction in transactions]})


@transaction_api_bp.post("/transactions")
@login_required
def api_create_transaction():
    """Create a transaction from a JSON payload."""
    payload = request.get_json(silent=True) or {}
    transaction = Transaction(user_id=current_user.id)
    is_valid, error = _apply_transaction_payload(transaction, payload)

    if not is_valid:
        return jsonify({"error": error}), 400

    db.session.add(transaction)
    db.session.commit()

    return jsonify({"transaction": transaction.to_dict()}), 201


@transaction_bp.route("/")
@login_required
def list_transactions():
    """Render the current user's transaction history with filters."""
    query = Transaction.query.filter_by(user_id=current_user.id)
    display_from = request.args.get("date_from") or ""
    display_to = request.args.get("date_to") or ""
    date_from = _parse_date(display_from or None)
    date_to = _parse_date(display_to or None)
    category = (request.args.get("category") or "").strip()
    sub_category = (request.args.get("sub_category") or "").strip()
    entry_type = (request.args.get("entry_type") or "").strip()

    if date_from and date_to and date_from > date_to:
        flash("From date must be earlier than or equal to the To date.", "warning")
    else:
        if date_from:
            query = query.filter(Transaction.entry_date >= date_from)
        if date_to:
            query = query.filter(Transaction.entry_date <= date_to)

    if category:
        query = query.filter(Transaction.category == category)
    if sub_category:
        query = query.filter(Transaction.sub_category == sub_category)
    if entry_type in {"income", "expense"}:
        query = query.filter(Transaction.entry_type == entry_type)

    transactions = query.order_by(Transaction.entry_date.desc(), Transaction.id.desc()).all()
    filter_categories = sorted(set(EXPENSE_CATEGORIES + INCOME_CATEGORIES))

    return render_template(
        "transactions/list.html",
        transactions=transactions,
        expense_categories=EXPENSE_CATEGORIES,
        expense_category_map=get_expense_category_map(),
        income_categories=INCOME_CATEGORIES,
        filter_categories=filter_categories,
        filters={
            "date_from": display_from,
            "date_to": display_to,
            "category": category,
            "sub_category": sub_category,
            "entry_type": entry_type,
        },
    )


@transaction_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Create a transaction from the server-rendered form."""
    if request.method == "POST":
        transaction = Transaction(user_id=current_user.id)
        is_valid, error = _apply_transaction_payload(transaction, request.form)

        if not is_valid:
            flash(error, "danger")
            return _render_transaction_form(
                form_title="New Transaction",
                action=url_for("transactions.add"),
                form_draft=_tx_form_draft(),
            )

        db.session.add(transaction)
        db.session.commit()
        flash("Transaction saved successfully.", "success")

        return redirect(url_for("transactions.list_transactions"))

    return _render_transaction_form(
        form_title="New Transaction",
        action=url_for("transactions.add"),
    )


@transaction_bp.route("/<int:tx_id>/edit", methods=["GET", "POST"])
@login_required
def edit(tx_id: int):
    """Update an owned transaction from the server-rendered form."""
    transaction = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first()

    if transaction is None:
        abort(404)

    if request.method == "POST":
        is_valid, error = _apply_transaction_payload(
            transaction,
            request.form,
            default_date=transaction.entry_date,
        )

        if not is_valid:
            flash(error, "danger")
            return _render_transaction_form(
                form_title="Transaction edit",
                action=url_for("transactions.edit", tx_id=transaction.id),
                transaction=transaction,
                form_draft=_tx_form_draft(),
                etype=transaction.entry_type, # Fixed etype propagation
            )

        db.session.commit()
        flash("Transaction updated successfully.", "success")

        return redirect(url_for("transactions.list_transactions"))

    return _render_transaction_form(
        form_title="Transaction edit",
        action=url_for("transactions.edit", tx_id=transaction.id),
        transaction=transaction,
        etype=transaction.entry_type, # Fixed etype propagation
    )


@transaction_bp.route("/<int:tx_id>/delete", methods=["POST"])
@login_required
def delete(tx_id: int):
    """Delete one owned transaction."""
    transaction = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first()

    if transaction is None:
        abort(404)

    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted successfully.", "info")

    return redirect(url_for("transactions.list_transactions"))
