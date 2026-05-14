"""
Authentication routes (Controller): register, login, logout.

Flow:
- GET: HTML form dikhata hai (Jinja template render)
- POST: form fields read karke DB update / session login karta hai
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from expense_tracker.extensions import db
from expense_tracker.models.user_model import User
from expense_tracker.utils.http_helpers import safe_internal_redirect

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Naya user banata hai (username unique)."""
    # Agar pehle se login ho to dashboard bhej do
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    last_username = ""
    if request.method == "POST":
        # HTML form fields (name attributes) yahan read hoti hain
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        last_username = username

        if not username or not password:
            flash("Username aur password zaroori hain.", "danger")
        elif password != confirm:
            flash("Password match nahi ho raha.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Ye username pehle se maujood hai.", "warning")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account ban gaya — ab login karein.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", last_username=last_username)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Credentials verify karke Flask-Login session start karta hai."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    last_username = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        last_username = username
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Username ya password ghalat hai.", "danger")
        else:
            login_user(user)
            # ?next= sirf internal path ho (open redirect se bachao)
            next_page = request.args.get("next")
            if next_page:
                return safe_internal_redirect(next_page, "dashboard.home")
            return redirect(url_for("dashboard.home"))

    return render_template("auth/login.html", last_username=last_username)


@auth_bp.route("/logout")
def logout():
    """Session clear karke guest mode."""
    logout_user()
    flash("Logout ho gaye.", "info")
    return redirect(url_for("auth.login"))
