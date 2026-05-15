
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_required
)

from expense_tracker.extensions import db
from expense_tracker.models.budget_model import Budget


budget_bp = Blueprint(
    "budget",
    __name__,
    url_prefix="/budget"
)


@budget_bp.route("/set", methods=["POST"])
@login_required
def set_budget():

    amount = request.form.get("amount")

    try:
        amount = float(amount)

        if amount <= 0:

            flash(
                "Budget amount must be greater than 0.",
                "danger"
            )

            return redirect(url_for("dashboard.index"))

    except ValueError:

        flash(
            "Invalid budget amount.",
            "danger"
        )

        return redirect(url_for("dashboard.index"))
    
    selected_month = request.form.get("month")
    if not selected_month:
        selected_month = datetime.now().strftime("%Y-%m")


    existing_budget = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month
    ).first()

    if existing_budget:

        existing_budget.amount = amount

        flash(
            "Monthly budget updated successfully.",
            "success"
        )

    else:

        new_budget = Budget(
            user_id=current_user.id,
            month=current_month,
            amount=amount
        )

        db.session.add(new_budget)

        flash(
            "Monthly budget set successfully.",
            "success"
        )

    db.session.commit()

    return redirect(url_for("dashboard.index"))