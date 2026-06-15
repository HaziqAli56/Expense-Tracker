"""
WTForms transaction form definition.

The current transaction routes use explicit validation helpers, but this form is
kept ready for views that prefer Flask-WTF. Category choices should be populated
from `expense_tracker.utils.constants` by the route before rendering.
"""

from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional


class TransactionForm(FlaskForm):
    """
    Form object for creating or editing a transaction.
    """

    amount = DecimalField(
        "Amount",
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Amount must be greater than zero."),
        ],
    )

    entry_type = SelectField(
        "Type",
        choices=[
            ("expense", "Expense"),
            ("income", "Income"),
        ],
        validators=[DataRequired()],
    )

    category = SelectField(
        "Main Category",
        choices=[],
        validators=[DataRequired()],
    )

    sub_category = SelectField(
        "Sub-category",
        choices=[],
        validators=[Optional()],
    )

    description = StringField("Description")

    entry_date = DateField(
        "Date",
        validators=[DataRequired()],
    )

    submit = SubmitField("Save Transaction")
