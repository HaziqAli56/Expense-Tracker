"""
Receipt scanning API routes.
"""

from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from expense_tracker.extensions import db
from expense_tracker.models.transaction_model import Transaction
from expense_tracker.utils.constants import first_sub_category_for, is_valid_expense_category
from expense_tracker.utils.receipt_ocr import extract_text_from_receipt, parse_receipt_text


receipt_api_bp = Blueprint("receipt_api", __name__, url_prefix="/api/receipts")


def _is_allowed_receipt(filename: str) -> bool:
    """
    Validate receipt extension before attempting OCR.
    """

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    return extension in current_app.config["ALLOWED_RECEIPT_EXTENSIONS"]


def _is_allowed_receipt_mimetype(mimetype: str | None) -> bool:
    """
    Validate the browser-provided image MIME type against supported formats.

    Extension validation catches obvious mistakes, while MIME validation blocks
    files such as renamed PDFs or scripts before Pillow/OCR tries to inspect
    their bytes.
    """

    if not mimetype:
        return False

    return mimetype.lower() in current_app.config["ALLOWED_RECEIPT_MIMETYPES"]


def _parse_verified_date(value: str | None) -> date:
    """
    Parse the user-reviewed date or fall back to today.

    The OCR draft can be incomplete, so commit accepts a missing date but never
    stores an invalid string in the Date column.
    """

    try:
        return datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        return date.today()


@receipt_api_bp.post("/scan")
@login_required
def scan_receipt():
    """
    Accept an uploaded receipt image and return editable extracted fields.
    """

    uploaded = request.files.get("receipt")

    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "A receipt image is required."}), 400

    filename = secure_filename(uploaded.filename)

    if not _is_allowed_receipt(filename):
        return jsonify({"error": "Only PNG, JPG, JPEG, and WEBP images are supported."}), 400

    if not _is_allowed_receipt_mimetype(uploaded.mimetype):
        return jsonify({"error": "Uploaded file MIME type must be PNG, JPG/JPEG, or WEBP."}), 400

    try:
        raw_text = extract_text_from_receipt(uploaded.stream)
        parsed = parse_receipt_text(raw_text)
    except Exception as exc:
        current_app.logger.exception("Receipt OCR failed.")
        return jsonify({"error": "Receipt could not be scanned.", "detail": str(exc)}), 422

    parsed["max_upload_size_mb"] = round(current_app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024), 1)

    return jsonify(parsed)


@receipt_api_bp.post("/commit")
@login_required
def commit_receipt_transaction():
    """
    Persist a user-verified receipt draft as an expense transaction.
    """

    payload = request.get_json(silent=True) or {}
    entry_date = _parse_verified_date(payload.get("entry_date"))

    try:
        amount = round(float(payload.get("amount")), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "A valid amount is required."}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero."}), 400

    category = (payload.get("category") or "Miscellaneous").strip()
    sub_category = (payload.get("sub_category") or "").strip()

    if not sub_category:
        sub_category = first_sub_category_for(category)

    if not is_valid_expense_category(category, sub_category):
        category = "Miscellaneous"
        sub_category = "Unexpected Expenses"

    try:
        exchange_rate = float(payload.get("exchange_rate") or 1.0)
    except (TypeError, ValueError):
        return jsonify({"error": "exchange_rate must be numeric."}), 400

    if exchange_rate <= 0:
        return jsonify({"error": "exchange_rate must be greater than zero."}), 400

    transaction = Transaction(
        user_id=current_user.id,
        entry_date=entry_date,
        entry_type="expense",
        category=category,
        sub_category=sub_category,
        amount=amount,
        description=(payload.get("description") or "Imported from receipt scan").strip(),
        currency_code=(payload.get("currency_code") or current_app.config["DEFAULT_BASE_CURRENCY"]).upper()[:3],
        exchange_rate=exchange_rate,
    )

    db.session.add(transaction)
    db.session.commit()

    return jsonify({"transaction": transaction.to_dict()}), 201
