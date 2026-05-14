from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, SubmitField, DateField
from wtforms.validators import DataRequired, NumberRange

from expense_tracker.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES


class TransactionForm(FlaskForm):

    amount = DecimalField(
        'Amount',
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message='Amount positive hona chahiye')
        ]
    )

    entry_type = SelectField(
        'Type',
        choices=[
            ('income', 'Income'),
            ('expense', 'Expense')
        ],
        validators=[DataRequired()]
    )

    category = SelectField(
        'Category',
        choices=[]
    )

    description = StringField('Description')

    entry_date = DateField(
        'Date',
        validators=[DataRequired()]
    )

    submit = SubmitField('Save Transaction')