"""
Currency conversion utilities.

Exchange rates are fetched from a public API and cached in-process to reduce
network calls during normal dashboard/API usage.
"""

from __future__ import annotations
import os
from datetime import datetime, timedelta

import requests
from flask import current_app


_RATE_CACHE: dict[str, dict] = {}
_CACHE_TTL = timedelta(hours=6)
SUPPORTED_CURRENCIES = [
    {"code": "PKR", "name": "Pakistani Rupee"},
    {"code": "USD", "name": "US Dollar"},
    {"code": "EUR", "name": "Euro"},
    {"code": "GBP", "name": "British Pound"},
    {"code": "AED", "name": "UAE Dirham"},
    {"code": "SAR", "name": "Saudi Riyal"},
    {"code": "CAD", "name": "Canadian Dollar"},
    {"code": "AUD", "name": "Australian Dollar"},
    {"code": "INR", "name": "Indian Rupee"},
    {"code": "CNY", "name": "Chinese Yuan"},
]


def _normalize_currency_code(value: str) -> str:
    """
    Convert a user/API supplied currency value into a validated ISO-like code.
    """
    code = (value or "").strip().upper()

    if len(code) != 3 or not code.isalpha():
        raise ValueError("Currency codes must be three-letter ISO codes.")

    return code


def fetch_exchange_rate(source_currency: str, base_currency: str) -> float:
    """
    Return the rate needed to convert source_currency into base_currency.
    """
    source = _normalize_currency_code(source_currency)
    base = _normalize_currency_code(base_currency)

    if source == base:
        return 1.0

    cache_key = f"{source}:{base}"
    cached = _RATE_CACHE.get(cache_key)

    if cached and datetime.utcnow() - cached["created_at"] < _CACHE_TTL:
        return cached["rate"]

    # Environment variable se API key aur Base URL uthao
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    api_base = current_app.config.get("EXCHANGE_RATE_API_BASE", "https://v6.exchangerate-api.com/v6")
    
    # URL construction: Pair conversion (ExchangeRate-API format)
    url = f"{api_base}/{api_key}/pair/{source}/{base}"
    
    response = requests.get(url, timeout=8)
    response.raise_for_status()

    payload = response.json()
    
    # Rate extraction
    rate = float(payload.get("conversion_rate", 1.0))
    
    _RATE_CACHE[cache_key] = {"rate": rate, "created_at": datetime.utcnow()}

    return rate


def convert_amount(amount: float, source_currency: str, base_currency: str) -> dict:
    """
    Convert an amount and return both converted value and exchange rate.
    """
    source = _normalize_currency_code(source_currency)
    base = _normalize_currency_code(base_currency)
    rate = fetch_exchange_rate(source, base)

    return {
        "source_currency": source,
        "base_currency": base,
        "exchange_rate": rate,
        "converted_amount": round(float(amount) * rate, 2),
    }