"""
Authentication WTForms.

This module keeps input validation close to the form definitions so routes stay
small and every authentication endpoint applies the same security rules.
"""

from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from expense_tracker.models.user_model import User


PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
)


def validate_password_strength(form, field) -> None:
    """
    Enforce the shared password policy for registration and reset flows.

    WTForms calls this validator automatically. Raising ValidationError surfaces
    the message through form.errors without allowing weak credentials into the DB.
    """

    if not PASSWORD_PATTERN.match(field.data or ""):
        raise ValidationError(
            "Password must be at least 8 characters and include uppercase, "
            "lowercase, number, and special character (@$!%*?&)."
        )


class RegistrationForm(FlaskForm):
    """
    Validate all fields required to create a new authenticated user account.
    """

    # Full name gives the product a human-friendly display value.
    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(),
            Length(min=2, max=120),
        ],
    )

    # Email is the unique login identifier and reset-password destination.
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=255),
        ],
    )

    # Phone number is optional contact metadata with a conservative max length.
    phone_number = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(max=30),
        ],
    )

    # Password applies the shared strength validator before hashing.
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            validate_password_strength,
        ],
    )

    # Confirmation prevents accidental password typos during account creation.
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
    )

    submit = SubmitField("Create Account")

    def validate_email(self, field) -> None:
        """
        Prevent duplicate accounts from sharing the same email address.
        """

        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    """
    Validate credentials before the route checks the password hash.
    """

    # Email replaces username as the professional account identifier.
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=255),
        ],
    )

    # Password is checked against the stored Werkzeug hash in the route.
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
        ],
    )

    submit = SubmitField("Login")


class ForgotPasswordForm(FlaskForm):
    """
    Validate the email address submitted to request a reset link.
    """

    # Only an email is required; responses remain generic to avoid enumeration.
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=255),
        ],
    )

    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    """
    Validate a replacement password after token verification succeeds.
    """

    # Reset password uses the exact same policy as registration.
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            validate_password_strength,
        ],
    )

    # Confirmation avoids locking users out with an accidental typo.
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
    )

    submit = SubmitField("Reset Password")
