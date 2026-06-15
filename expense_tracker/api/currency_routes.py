"""
Currency API routes.
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required

from expense_tracker.utils.currency import SUPPORTED_CURRENCIES, convert_amount, fetch_exchange_rate


currency_api_bp = Blueprint("currency_api", __name__, url_prefix="/api/currency")


@currency_api_bp.get("/supported")
@login_required
def supported_currencies():
    """
    Return currencies supported by the transaction entry UI.

    The list is deliberately served by the backend so React dropdowns and
    server validation can be kept in sync as the product grows.
    """

    return jsonify(
        {
            "base_currency": current_app.config["DEFAULT_BASE_CURRENCY"],
            "currencies": SUPPORTED_CURRENCIES,
        }
    )


@currency_api_bp.get("/rate")
@login_required
def exchange_rate():
    """
    Return a live or cached exchange rate between two currencies.
    """

    source = request.args.get("from") or ""
    target = request.args.get("to") or current_app.config["DEFAULT_BASE_CURRENCY"]

    try:
        rate = fetch_exchange_rate(source, target)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        current_app.logger.exception("Exchange-rate lookup failed.")
        return jsonify({"error": "Exchange rate is unavailable.", "detail": str(exc)}), 502

    return jsonify({"from": source.upper(), "to": target.upper(), "exchange_rate": rate})


@currency_api_bp.get("/convert")
@login_required
def convert_currency():
    """
    Convert a supplied amount between currencies for transaction forms.
    """

    try:
        amount = float(request.args.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "A numeric amount is required."}), 400

    source = request.args.get("from") or ""
    target = request.args.get("to") or current_app.config["DEFAULT_BASE_CURRENCY"]

    try:
        payload = convert_amount(amount, source, target)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        current_app.logger.exception("Currency conversion failed.")
        return jsonify({"error": "Currency conversion is unavailable.", "detail": str(exc)}), 502

    return jsonify(payload)
