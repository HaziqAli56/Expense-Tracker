"""
Receipt OCR and parsing helpers.

The OCR layer extracts raw text from images, while parsing uses conservative
regular expressions so users can verify/edit extracted data before saving.
"""

from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError
import pytesseract
from pytesseract import TesseractNotFoundError


DATE_PATTERNS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d.%m.%Y",
    "%m.%d.%Y",
]

CATEGORY_KEYWORDS = {
    ("Food & Dining", "Groceries"): ["grocery", "market", "mart", "supermarket"],
    ("Food & Dining", "Dining Out"): ["restaurant", "cafe", "coffee", "pizza", "burger"],
    ("Food & Dining", "Snacks & Takeaway"): ["takeaway", "snack", "bakery"],
    ("Transportation", "Fuel"): ["fuel", "petrol", "gas station"],
    ("Transportation", "Ride-Hailing"): ["uber", "careem", "taxi"],
    ("Housing & Utilities", "Rent"): ["rent", "lease"],
    ("Personal & Lifestyle", "Entertainment"): ["cinema", "movie", "netflix", "game", "ticket", "theatre"],
}

TOTAL_LINE_PATTERN = re.compile(
    r"\b(grand\s+total|total\s+amount|amount\s+due|balance\s+due|total)\b",
    re.IGNORECASE,
)

AMOUNT_PATTERN = re.compile(
    r"(?<!\d)(?:rs\.?|pkr|usd|\$)?\s*(\d{1,9}(?:,\d{3})*(?:\.\d{1,2})?)(?!\d)",
    re.IGNORECASE,
)

WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files\PDF24\tesseract\tesseract.exe",
]


def _configure_tesseract_binary() -> None:
    """
    Point pytesseract to a real Tesseract executable when it is not in PATH.

    Windows installs often place tesseract.exe under Program Files without
    adding it to PATH. The app first respects the explicit TESSERACT_CMD config,
    then checks common install locations. If none exist, pytesseract will raise
    a clear TesseractNotFoundError that the API converts into a helpful message.
    """

    configured_path = current_app.config.get("TESSERACT_CMD")
    candidate_paths = [configured_path] if configured_path else []
    candidate_paths.extend(WINDOWS_TESSERACT_PATHS)

    for candidate in candidate_paths:
        if candidate and Path(candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = candidate
            return


def extract_text_from_receipt(file_stream) -> str:
    """
    Run OCR over an uploaded receipt image stream.

    Pillow validates that the file is an image before pytesseract receives it,
    which reduces the chance of passing arbitrary payloads into the OCR tool.
    """

    _configure_tesseract_binary()

    try:
        image = Image.open(file_stream)
        image.verify()
        file_stream.seek(0)
        image = Image.open(file_stream).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Uploaded file is not a valid receipt image.") from exc

    # Convert to grayscale and auto-contrast to improve OCR accuracy on faded
    # thermal receipts without requiring heavy image-processing dependencies.
    image = ImageOps.autocontrast(ImageOps.grayscale(image))

    # Upscale small mobile screenshots/photos so OCR has more pixel detail to
    # work with. Larger images are left untouched to avoid unnecessary memory.
    if image.width < 1400:
        scale = 1400 / max(image.width, 1)
        image = image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.Resampling.LANCZOS,
        )

    try:
        # Try multiple page segmentation modes because receipts vary: some are
        # dense blocks, some are sparse screenshots, and some are camera photos.
        ocr_attempts = [
            pytesseract.image_to_string(image, config="--psm 6"),
            pytesseract.image_to_string(image, config="--psm 11"),
            pytesseract.image_to_string(image, config="--psm 4"),
        ]
        text = max(ocr_attempts, key=lambda value: len(value.strip()))
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is installed but not reachable. Set TESSERACT_CMD in .env to the full tesseract.exe path."
        ) from exc

    if not text.strip():
        raise ValueError("No readable text was detected in the receipt image.")

    return text


def _parse_receipt_date(text: str) -> str | None:
    """
    Find a likely receipt date and return it in ISO format.
    """

    candidates = re.findall(r"\b\d{1,4}[./-]\d{1,2}[./-]\d{1,4}\b", text)

    for candidate in candidates:
        for pattern in DATE_PATTERNS:
            try:
                parsed_date = datetime.strptime(candidate, pattern).date()

                # Receipts should not produce far-future dates; skipping them
                # prevents invoice numbers such as 2099/01/01 from winning.
                if parsed_date.year <= datetime.utcnow().year + 1:
                    return parsed_date.isoformat()
            except ValueError:
                continue

    return None


def _parse_receipt_total(text: str) -> float | None:
    """
    Extract the most likely total amount from receipt text.
    """

    total_lines = [
        line
        for line in text.splitlines()
        if TOTAL_LINE_PATTERN.search(line)
    ]

    # Prefer explicit total lines. If OCR misses labels, fall back to all text
    # and choose the largest plausible amount, which is usually the receipt sum.
    search_space = "\n".join(total_lines) if total_lines else text
    amounts = AMOUNT_PATTERN.findall(search_space)

    if not amounts:
        return None

    numeric_amounts = [
        float(value.replace(",", ""))
        for value in amounts
        if float(value.replace(",", "")) > 0
    ]

    if not numeric_amounts:
        return None

    return round(max(numeric_amounts), 2)


def _guess_category_pair(text: str) -> tuple[str, str]:
    """
    Guess the expense category pair using simple merchant/keyword matching.
    """

    lowered = text.lower()

    for category_pair, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category_pair

    return "Miscellaneous", "Unexpected Expenses"


def parse_receipt_text(text: str) -> dict:
    """
    Convert OCR text into editable transaction draft fields.
    """

    normalized_text = text.strip()
    category, sub_category = _guess_category_pair(normalized_text)

    return {
        "entry_date": _parse_receipt_date(normalized_text),
        "amount": _parse_receipt_total(normalized_text),
        "entry_type": "expense",
        "category": category,
        "sub_category": sub_category,
        "description": "Imported from receipt scan",
        "raw_text": normalized_text,
    }
