"""
HTTP helpers — chhoti security / UX utilities (alag file = teacher ko explain asaan).
"""

from __future__ import annotations

from urllib.parse import urlparse

from flask import redirect, url_for


def safe_internal_redirect(next_url: str | None, default_endpoint: str, **default_values):
    """
    Login ke baad `?next=` open-redirect attack na ban jaye is liye sirf internal
    relative paths allow (same-site navigation).
    """
    if not next_url or not isinstance(next_url, str):
        return redirect(url_for(default_endpoint, **default_values))

    next_url = next_url.strip()
    # Sirf path allow: `/dashboard` OK — `//evil.com` ya `https://...` reject
    if not next_url.startswith("/") or next_url.startswith("//"):
        return redirect(url_for(default_endpoint, **default_values))

    parsed = urlparse(next_url)
    if parsed.netloc:
        return redirect(url_for(default_endpoint, **default_values))

    return redirect(next_url)
