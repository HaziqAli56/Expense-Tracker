from io import BytesIO, StringIO
import csv

from flask import (
    Blueprint,
    make_response,
    request,
    send_file
)

from flask_login import (
    login_required,
    current_user
)

from openpyxl import Workbook

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table
)

from reportlab.lib.styles import getSampleStyleSheet

from expense_tracker.models.transaction_model import Transaction


report_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


@report_bp.route("/export")
@login_required
def export_report():

    format_type = request.args.get(
        "format",
        "pdf"
    )

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).all()

    # ================= PDF =================

    if format_type == "pdf":

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter
        )

        styles = getSampleStyleSheet()

        elements = []

        title = Paragraph(
            "Expense Tracker Report",
            styles['Title']
        )

        elements.append(title)

        elements.append(Spacer(1, 20))

        data = [
            [
                "Date",
                "Type",
                "Category",
                "Amount"
            ]
        ]

        for t in transactions:

            data.append([
                str(t.entry_date),
                t.entry_type,
                t.category,
                f"PKR {t.amount}"
            ])

        table = Table(data)

        elements.append(table)

        doc.build(elements)

        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="expense_report.pdf",
            mimetype="application/pdf"
        )

    # ================= CSV =================

    elif format_type == "csv":

        output = StringIO()

        writer = csv.writer(output)

        writer.writerow([
            "Date",
            "Type",
            "Category",
            "Amount"
        ])

        for t in transactions:

            writer.writerow([
                t.entry_date,
                t.entry_type,
                t.category,
                t.amount
            ])

        response = make_response(
            output.getvalue()
        )

        response.headers[
            "Content-Disposition"
        ] = "attachment; filename=expense_report.csv"

        response.headers[
            "Content-type"
        ] = "text/csv"

        return response

    # ================= EXCEL =================

    elif format_type == "excel":

        wb = Workbook()

        ws = wb.active

        ws.title = "Expense Report"

        ws.append([
            "Date",
            "Type",
            "Category",
            "Amount"
        ])

        for t in transactions:

            ws.append([
                str(t.entry_date),
                t.entry_type,
                t.category,
                t.amount
            ])

        output = BytesIO()

        wb.save(output)

        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="expense_report.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    return "Invalid format selected"