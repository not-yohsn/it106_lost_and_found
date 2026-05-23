import csv
import io

from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user

from . import found_bp
from .forms import FoundItemForm
from ..decorators import staff_required
from ..exports import build_xlsx
from ..extensions import db
from ..matching import find_matches_for_found
from ..models import FoundItem
from ..notify import notify, notify_staff
from ..utils import save_uploaded_image


@found_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    pagination = (
        FoundItem.query
        .order_by(FoundItem.created_at.desc())
        .paginate(page=page, per_page=12, error_out=False)
    )
    return render_template("found/list.html", pagination=pagination)


@found_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = FoundItemForm()
    if form.validate_on_submit():
        photo_path = save_uploaded_image(form.photo.data)
        item = FoundItem(
            logged_by=current_user.user_id,
            item_name=form.item_name.data,
            description=form.description.data or None,
            category=form.category.data,
            location_found=form.location_found.data or None,
            date_found=form.date_found.data,
            photo_path=photo_path,
        )
        db.session.add(item)
        db.session.commit()

        notify_staff(
            title=f"New found item: '{item.item_name}'",
            body=f"{current_user.name} logged a found {item.category or 'item'}.",
            link=url_for("found.detail", item_id=item.item_id),
        )

        candidates = find_matches_for_found(item, limit=10, min_score=0.3)
        already_notified = {current_user.user_id}
        for report, score, _ in candidates:
            if report.user_id in already_notified:
                continue
            already_notified.add(report.user_id)
            notify(
                user_id=report.user_id,
                title="A new found item might match your report",
                body=(
                    f"Someone just logged '{item.item_name}'. "
                    f"Match confidence: {int(score * 100)}%. "
                    "Open your report to check."
                ),
                link=url_for("reports.detail", report_id=report.report_id),
            )

        flash("Found item logged.", "success")
        return redirect(url_for("found.detail", item_id=item.item_id))
    return render_template("found/new.html", form=form)


@found_bp.route("/<int:item_id>")
@login_required
def detail(item_id):
    item = FoundItem.query.get_or_404(item_id)
    candidates = []
    if item.status == "logged":
        candidates = find_matches_for_found(item)
    return render_template("found/detail.html", item=item, candidates=candidates)


@found_bp.route("/export.csv")
@login_required
@staff_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "item_id", "item_name", "category", "location_found", "date_found",
        "status", "logged_by_user_id", "description", "created_at",
    ])
    for i in FoundItem.query.order_by(FoundItem.created_at.desc()).all():
        writer.writerow([
            i.item_id,
            i.item_name,
            i.category or "",
            i.location_found or "",
            i.date_found.isoformat() if i.date_found else "",
            i.status,
            i.logged_by or "",
            i.description or "",
            i.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=found_items.csv"},
    )


@found_bp.route("/export.xlsx")
@login_required
@staff_required
def export_xlsx():
    headers = [
        "Item ID", "Item", "Category", "Location Found", "Date Found",
        "Status", "Logged By", "Description", "Created At",
    ]
    rows = (
        (
            i.item_id,
            i.item_name,
            i.category or "",
            i.location_found or "",
            i.date_found.isoformat() if i.date_found else "",
            i.status,
            i.logged_by or "",
            i.description or "",
            i.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        for i in FoundItem.query.order_by(FoundItem.created_at.desc()).all()
    )
    payload = build_xlsx("Found Items", headers, rows)
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=found_items.xlsx"},
    )
