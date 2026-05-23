import csv
import io

from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user

from . import reports_bp
from .forms import LostReportForm
from ..decorators import staff_required
from ..exports import build_xlsx
from ..extensions import db
from ..matching import find_matches_for_lost
from ..models import LostReport
from ..notify import notify_staff
from ..utils import save_uploaded_image


def _is_authorized(report):
    """Owner of the report + staff/admin may see private details."""
    return (
        report.user_id == current_user.user_id
        or current_user.role in ("staff", "admin")
    )


@reports_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    mine = request.args.get("mine") == "1"
    query = LostReport.query.order_by(LostReport.created_at.desc())
    if mine:
        query = query.filter_by(user_id=current_user.user_id)
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    return render_template("reports/list.html", pagination=pagination, mine=mine)


@reports_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = LostReportForm()
    if form.validate_on_submit():
        photo_path = save_uploaded_image(form.photo.data)
        report = LostReport(
            user_id=current_user.user_id,
            item_name=form.item_name.data,
            description=form.description.data or None,
            category=form.category.data,
            location=form.location.data or None,
            date_lost=form.date_lost.data,
            photo_path=photo_path,
        )
        db.session.add(report)
        db.session.commit()

        notify_staff(
            title=f"New lost report: '{report.item_name}'",
            body=f"{current_user.name} reported a lost {report.category or 'item'}.",
            link=url_for("reports.detail", report_id=report.report_id),
        )

        flash("Lost report submitted.", "success")
        return redirect(url_for("reports.detail", report_id=report.report_id))
    return render_template("reports/new.html", form=form)


@reports_bp.route("/<int:report_id>")
@login_required
def detail(report_id):
    report = LostReport.query.get_or_404(report_id)
    is_authorized = _is_authorized(report)

    candidates = []
    if is_authorized and report.status == "reported":
        candidates = find_matches_for_lost(report)

    return render_template(
        "reports/detail.html",
        report=report,
        candidates=candidates,
        is_authorized=is_authorized,
    )


@reports_bp.route("/export.csv")
@login_required
@staff_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "report_id", "item_name", "category", "location", "date_lost",
        "status", "reporter_name", "reporter_email", "description", "created_at",
    ])
    for r in LostReport.query.order_by(LostReport.created_at.desc()).all():
        writer.writerow([
            r.report_id,
            r.item_name,
            r.category or "",
            r.location or "",
            r.date_lost.isoformat() if r.date_lost else "",
            r.status,
            r.user.name,
            r.user.email,
            r.description or "",
            r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=lost_reports.csv"},
    )


@reports_bp.route("/export.xlsx")
@login_required
@staff_required
def export_xlsx():
    headers = [
        "Report ID", "Item", "Category", "Location", "Date Lost",
        "Status", "Reporter Name", "Reporter Email", "Description", "Created At",
    ]
    rows = (
        (
            r.report_id,
            r.item_name,
            r.category or "",
            r.location or "",
            r.date_lost.isoformat() if r.date_lost else "",
            r.status,
            r.user.name,
            r.user.email,
            r.description or "",
            r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        for r in LostReport.query.order_by(LostReport.created_at.desc()).all()
    )
    payload = build_xlsx("Lost Reports", headers, rows)
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=lost_reports.xlsx"},
    )
