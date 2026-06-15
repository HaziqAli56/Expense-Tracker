"""
Authentication routes.

This controller owns account registration, login, logout, forgot-password, and
reset-password HTTP flow. Validation lives in WTForms and token/email behavior
lives in auth utilities to keep the route layer small and auditable.
"""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from expense_tracker.extensions import db
from expense_tracker.forms import (
    ForgotPasswordForm,
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
)
from expense_tracker.models.user_model import User
from expense_tracker.utils import (
    send_password_reset_email,
    verify_password_reset_token,
)
from expense_tracker.utils.http_helpers import safe_internal_redirect


auth_bp = Blueprint(
    "auth",
    __name__,
)


@auth_bp.route(
    "/register",
    methods=["GET", "POST"],
)
def register():
    """
    Create a new user account after validating identity and password strength.

    The username column is populated with the normalized email address to keep
    compatibility with older parts of the app that still reference username.
    """

    # Authenticated users should not create another account from this session.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = RegistrationForm()

    # WTForms validates required fields, email format, duplicates, and password policy.
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        user = User(
            full_name=form.full_name.data.strip(),
            email=email,
            username=email,
            phone_number=(form.phone_number.data or "").strip() or None,
        )

        # Store only a strong Werkzeug password hash, never the raw password.
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. Please login.",
            "success",
        )

        return redirect(url_for("auth.login"))

    # POST failures keep the user on the page and expose field-level messages.
    if request.method == "POST" and form.errors:
        flash(
            "Registration failed. Please correct the highlighted fields.",
            "danger",
        )

    return render_template(
        "auth/register.html",
        form=form,
    )


@auth_bp.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    """
    Authenticate a user with email and password.
    """

    # Logged-in users go directly to their dashboard.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = LoginForm()

    # Only after form validation do we query the database for the submitted email.
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        user = User.query.filter_by(email=email).first()

        # Use one generic error so attackers cannot distinguish email vs password failures.
        if user is None or not user.check_password(form.password.data):
            flash(
                "Incorrect email or password.",
                "danger",
            )
        else:
            login_user(user)

            next_page = request.args.get("next")

            # Safe redirect prevents open-redirect abuse from crafted next parameters.
            if next_page:
                return safe_internal_redirect(
                    next_page,
                    "dashboard.home",
                )

            return redirect(url_for("dashboard.home"))

    # Invalid form submissions get a clear flash while field errors stay inline.
    if request.method == "POST" and form.errors:
        flash(
            "Login failed. Please enter a valid email and password.",
            "danger",
        )

    return render_template(
        "auth/login.html",
        form=form,
    )


@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"],
)
def forgot_password():
    """
    Request a two-hour password reset link by email.
    """

    # Authenticated users can change sessions directly by logging out first.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = ForgotPasswordForm()

    # Always show a generic success message to avoid account enumeration.
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is not None:
            try:
                reset_url = send_password_reset_email(user)
                current_app.logger.info(
                    "Password reset email sent for user_id=%s",
                    user.id,
                )
                current_app.logger.debug(
                    "Password reset URL generated for user_id=%s: %s",
                    user.id,
                    reset_url,
                )
            except Exception as exc:
                current_app.logger.exception(
                    "Password reset email failed for user_id=%s",
                    user.id,
                )
                flash(
                    "Password reset email could not be sent because the mail service is not configured or reachable. Please check MAIL_* settings in .env.",
                    "danger",
                )

                return redirect(url_for("auth.forgot_password"))

        flash(
            "If an account exists for that email, a reset link has been sent.",
            "info",
        )

        return render_template(
            "auth/forgot_password.html",
            form=form,
            reset_sent=True,
            sent_email=email,
        )

    # Invalid email formats are safe to report because no account lookup happened.
    if request.method == "POST" and form.errors:
        flash(
            "Please enter a valid email address.",
            "danger",
        )

    return render_template(
        "auth/forgot_password.html",
        form=form,
        reset_sent=False,
        sent_email=None,
    )


@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"],
)
def reset_password(token: str):
    """
    Validate a reset token and allow the user to choose a new strong password.
    """

    # A logged-in user should not reset a password through an email-token flow.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    user_id, token_error = verify_password_reset_token(token)

    # Expired links are reported clearly so users know to request a new email.
    if token_error == "expired":
        flash(
            "This password reset link has expired. Please request a new one.",
            "danger",
        )

        return redirect(url_for("auth.forgot_password"))

    # Invalid links are treated separately from expired links for clearer support.
    if user_id is None:
        flash(
            "This password reset link is invalid.",
            "danger",
        )

        return redirect(url_for("auth.forgot_password"))

    user = db.session.get(User, user_id)

    # The token may be valid even if the account was deleted after email dispatch.
    if user is None:
        flash("This password reset link is invalid.", "danger")

        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    # The reset form applies the same password strength policy as registration.
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        flash(
            "Your password has been reset. Please login with the new password.",
            "success",
        )

        return redirect(url_for("auth.login"))

    # POST failures keep password-strength and confirmation errors visible inline.
    if request.method == "POST" and form.errors:
        flash(
            "Password reset failed. Please follow the password rules.",
            "danger",
        )

    return render_template(
        "auth/reset_password.html",
        form=form,
    )


@auth_bp.route("/logout")
def logout():
    """
    End the user's Flask-Login session and return them to the login screen.
    """

    logout_user()

    flash(
        "You have been logged out successfully.",
        "info",
    )

    return redirect(url_for("auth.login"))
