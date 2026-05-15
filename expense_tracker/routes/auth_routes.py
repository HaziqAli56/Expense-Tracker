"""
Authentication routes (Controller): register, login, logout.

Flow:
- GET: Show HTML form
- POST: Read form fields, update DB, and handle login session
"""

from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_user,
    logout_user
)

from expense_tracker.extensions import db
from expense_tracker.models.user_model import User
from expense_tracker.utils.http_helpers import safe_internal_redirect


auth_bp = Blueprint(
    "auth",
    __name__
)


# ==========================================
# REGISTER
# ==========================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # If already logged in
    if current_user.is_authenticated:
        return redirect(
            url_for("dashboard.home")
        )

    last_username = ""

    if request.method == "POST":

        username = (
            request.form.get("username") or ""
        ).strip()

        password = (
            request.form.get("password") or ""
        )

        confirm = (
            request.form.get("confirm_password") or ""
        )

        last_username = username

        # VALIDATION

        if not username or not password:

            flash(
                "Username and password are required.",
                "danger"
            )

        elif password != confirm:

            flash(
                "Passwords do not match.",
                "danger"
            )

        elif User.query.filter_by(
            username=username
        ).first():

            flash(
                "This username already exists.",
                "warning"
            )

        else:

            user = User(
                username=username
            )

            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash(
                "Account created successfully — please login.",
                "success"
            )

            return redirect(
                url_for("auth.login")
            )

    return render_template(
        "auth/register.html",
        last_username=last_username
    )


# ==========================================
# LOGIN
# ==========================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard.home")
        )

    last_username = ""

    if request.method == "POST":

        username = (
            request.form.get("username") or ""
        ).strip()

        password = (
            request.form.get("password") or ""
        )

        last_username = username

        user = User.query.filter_by(
            username=username
        ).first()

        # INVALID LOGIN

        if user is None or not user.check_password(password):

            flash(
                "Incorrect username or password.",
                "danger"
            )

        else:

            login_user(user)

            next_page = request.args.get("next")

            if next_page:

                return safe_internal_redirect(
                    next_page,
                    "dashboard.home"
                )

            return redirect(
                url_for("dashboard.home")
            )

    return render_template(
        "auth/login.html",
        last_username=last_username
    )


# ==========================================
# LOGOUT
# ==========================================

@auth_bp.route("/logout")
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "info"
    )

    return redirect(
        url_for("auth.login")
    )