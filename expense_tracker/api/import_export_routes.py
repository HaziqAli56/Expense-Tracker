"""
Transaction import/export API routes.
"""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from expense_tracker.extensions import db
from expense_tracker.models.transaction_model import Transaction
from expense_tracker.utils.import_export import (
    dataframe_to_download,
    frame_to_transactions,
    read_transaction_upload,
    transactions_to_frame,
    validate_import_frame,
)


data_api_bp = Blueprint("data_api", __name__, url_prefix="/api/data")


@data_api_bp.get("/transactions/export")
@login_required
def export_transactions():
    """
    Export the current user's transactions as CSV or Excel.
    """

    export_format = (request.args.get("format") or "csv").lower()

    if export_format not in {"csv", "xlsx"}:
        return jsonify({"error": "format must be csv or xlsx."}), 400

    transactions = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.entry_date.desc(), Transaction.id.desc())
        .all()
    )

    frame = transactions_to_frame(transactions)
    output, mimetype, filename = dataframe_to_download(frame, export_format)
    dated_filename = f"{datetime.utcnow().strftime('%Y%m%d')}_{filename}"

    return send_file(
        output,
        mimetype=mimetype,
        as_attachment=True,
        download_name=dated_filename,
    )


@data_api_bp.post("/transactions/import")
@login_required
def import_transactions():
    """
    Validate and bulk import transactions from uploaded CSV/XLSX data.
    """

    uploaded = request.files.get("file")

    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "A CSV or XLSX file is required."}), 400

    filename = secure_filename(uploaded.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in current_app.config["ALLOWED_IMPORT_EXTENSIONS"]:
        return jsonify({"error": "Only CSV and XLSX files are supported."}), 400

    try:
        frame = read_transaction_upload(uploaded)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    errors = validate_import_frame(frame)

    if errors:
        return jsonify({"error": "Import validation failed.", "details": errors}), 422

    transactions = frame_to_transactions(frame, current_user.id)
    db.session.add_all(transactions)
    db.session.commit()

    return jsonify(
        {
            "imported_count": len(transactions),
            "max_rows": current_app.config["MAX_IMPORT_ROWS"],
            "max_upload_size_mb": round(current_app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024), 1),
        }
    ), 201
