"""
Authentication utility functions.

Token generation and email delivery are isolated here so routes can focus on
HTTP control flow while security-sensitive behavior remains reusable and tested
in one place.
"""

from __future__ import annotations

from flask import current_app, render_template, url_for
from flask_mail import Message
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from expense_tracker.extensions import mail


RESET_TOKEN_SALT = "password-reset"
RESET_TOKEN_MAX_AGE_SECONDS = 2 * 60 * 60


def _password_reset_serializer() -> URLSafeTimedSerializer:
    """
    Build a serializer using the app secret key and a dedicated reset salt.

    A separate salt prevents reset tokens from being confused with any other
    signed token the application may introduce later.
    """

    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_password_reset_token(user_id: int) -> str:
    """
    Generate a signed password-reset token containing only the user id.

    The token does not store the password or email address; it only carries the
    minimum identifier needed to find the account after signature validation.
    """

    serializer = _password_reset_serializer()

    return serializer.dumps(
        {"user_id": user_id},
        salt=RESET_TOKEN_SALT,
    )


def verify_password_reset_token(token: str) -> tuple[int | None, str | None]:
    """
    Validate a reset token and return the embedded user id plus failure reason.

    Tokens expire after exactly two hours. Returning a small reason code lets the
    route show clear user-facing flash messages while keeping token parsing
    centralized and auditable.
    """

    serializer = _password_reset_serializer()

    try:
        payload = serializer.loads(
            token,
            salt=RESET_TOKEN_SALT,
            max_age=RESET_TOKEN_MAX_AGE_SECONDS,
        )
    except SignatureExpired:
        return None, "expired"
    except BadSignature:
        return None, "invalid"

    return payload.get("user_id"), None


def build_password_reset_url(user) -> str:
    """
    Build the absolute password-reset URL for a user.

    Keeping URL generation separate from delivery lets routes and tests inspect
    the exact link when SMTP delivery fails during local development.
    """

    token = generate_password_reset_token(user.id)

    return url_for(
        "auth.reset_password",
        token=token,
        _external=True,
    )


def _validate_mail_settings() -> None:
    """
    Fail fast when SMTP settings are obviously incomplete.

    Flask-Mail otherwise tries the default localhost:25 server, which usually
    fails silently from the user's point of view in local development. Raising a
    clear RuntimeError lets the route show a helpful UI message and log the
    missing configuration.
    """

    mail_server = current_app.config.get("MAIL_SERVER")
    default_sender = current_app.config.get("MAIL_DEFAULT_SENDER")

    if not mail_server:
        raise RuntimeError("MAIL_SERVER is not configured.")

    if not default_sender:
        raise RuntimeError("MAIL_DEFAULT_SENDER is not configured.")


def send_password_reset_email(user) -> str:
    """
    Send a password-reset email containing the secure two-hour token link.

    The reset URL is generated externally so email clients receive an absolute
    link that works outside the current browser session. The URL is returned so
    callers can log it during debugging without duplicating token logic.
    """

    _validate_mail_settings()
    reset_url = build_password_reset_url(user)

    message = Message(
        subject="Reset your Expense Tracker password",
        recipients=[user.email],
        sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
    )

    # Plain-text body is reliable across mail clients and avoids HTML-only risk.
    message.body = render_template(
        "auth/email/reset_password.txt",
        user=user,
        reset_url=reset_url,
        expires_hours=2,
    )

    mail.send(message)

    return reset_url
