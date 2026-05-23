from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from . import matches_bp
from ..decorators import staff_required
from ..extensions import db
from ..models import Match, LostReport, FoundItem
from ..notify import notify


@matches_bp.route("/")
@login_required
def index():
    """Match list. Students see only matches tied to THEIR lost reports;
    staff and admin see all matches in the system.
    """
    query = Match.query.order_by(Match.matched_at.desc())
    if current_user.role not in ("staff", "admin"):
        query = query.join(LostReport).filter(
            LostReport.user_id == current_user.user_id
        )
    matches = query.all()
    return render_template("matches/list.html", matches=matches)


@matches_bp.route("/<int:match_id>")
@login_required
def detail(match_id):
    match = Match.query.get_or_404(match_id)

    is_authorized = (
        match.lost_report.user_id == current_user.user_id
        or current_user.role in ("staff", "admin")
    )
    if not is_authorized:
        abort(403)

    return render_template("matches/detail.html", match=match)


@matches_bp.route("/confirm", methods=["POST"])
@login_required
@staff_required
def confirm():
    lost_id = request.form.get("lost_report_id", type=int)
    found_id = request.form.get("found_item_id", type=int)
    score = request.form.get("score", type=float)

    if not lost_id or not found_id:
        flash("Missing report or item.", "danger")
        return redirect(url_for("matches.index"))

    lost_report = LostReport.query.get_or_404(lost_id)
    found_item = FoundItem.query.get_or_404(found_id)

    if lost_report.match or found_item.match:
        flash("One of these items is already matched.", "warning")
        return redirect(request.referrer or url_for("matches.index"))

    match = Match(
        lost_report_id=lost_id,
        found_item_id=found_id,
        confidence_score=score,
    )
    lost_report.status = "matched"
    found_item.status = "matched"
    db.session.add(match)
    db.session.commit()

    notify(
        user_id=lost_report.user_id,
        title="Your lost item may have been found",
        body=(
            f"We matched your report '{lost_report.item_name}' "
            f"with a found item: '{found_item.item_name}'. "
            "Open the report to claim it."
        ),
        link=url_for("reports.detail", report_id=lost_report.report_id),
    )

    flash("Items matched. The owner has been notified.", "success")
    return redirect(url_for("matches.detail", match_id=match.match_id))


@matches_bp.route("/<int:match_id>/dissolve", methods=["POST"])
@login_required
@staff_required
def dissolve(match_id):
    match = Match.query.get_or_404(match_id)

    if any(c.status == "released" for c in match.claims):
        flash("Cannot dissolve — item has already been released to a claimant.", "danger")
        return redirect(url_for("matches.detail", match_id=match_id))

    match.lost_report.status = "reported"
    match.found_item.status = "logged"
    db.session.delete(match)
    db.session.commit()
    flash("Match dissolved.", "info")
    return redirect(url_for("matches.index"))
