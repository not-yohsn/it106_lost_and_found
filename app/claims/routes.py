import csv
import io
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, abort, Response
from flask_login import login_required, current_user

from . import claims_bp
from .forms import ClaimForm
from ..decorators import staff_required
from ..exports import build_xlsx, render_pdf
from ..extensions import db
from ..models import Claim, Match
from ..notify import notify, notify_staff


def _is_staff():
    return current_user.role in ("staff", "admin")


@claims_bp.route("/")
@login_required
def index():
    query = Claim.query.order_by(Claim.submitted_at.desc())
    if not _is_staff():
        query = query.filter_by(claimant_id=current_user.user_id)
    return render_template("claims/list.html", claims=query.all())


@claims_bp.route("/new/<int:match_id>", methods=["GET", "POST"])
@login_required
def new(match_id):
    match = Match.query.get_or_404(match_id)

    if match.lost_report.user_id != current_user.user_id:
        flash("Only the lost-report owner can claim this item.", "danger")
        return redirect(url_for("matches.detail", match_id=match_id))

    if match.found_item.status == "released":
        flash("This item has already been released.", "warning")
        return redirect(url_for("matches.detail", match_id=match_id))

    form = ClaimForm()
    if form.validate_on_submit():
        claim = Claim(
            match_id=match_id,
            claimant_id=current_user.user_id,
            notes=form.notes.data or None,
        )
        db.session.add(claim)
        db.session.commit()

        notify_staff(
            title=f"New claim on '{match.lost_report.item_name}'",
            body=f"{current_user.name} submitted a claim — review needed.",
            link=url_for("claims.detail", claim_id=claim.claim_id),
        )

        flash("Claim submitted. Staff will review it shortly.", "success")
        return redirect(url_for("claims.detail", claim_id=claim.claim_id))

    return render_template("claims/new.html", form=form, match=match)


@claims_bp.route("/<int:claim_id>")
@login_required
def detail(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    if claim.claimant_id != current_user.user_id and not _is_staff():
        abort(403)
    return render_template("claims/detail.html", claim=claim)


@claims_bp.route("/<int:claim_id>/approve", methods=["POST"])
@login_required
@staff_required
def approve(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    if claim.status != "pending":
        flash(f"Claim is already {claim.status}.", "warning")
        return redirect(url_for("claims.detail", claim_id=claim_id))
    claim.status = "approved"
    claim.verified_by = current_user.user_id
    claim.resolved_at = datetime.now(timezone.utc)
    db.session.commit()

    notify(
        user_id=claim.claimant_id,
        title="Your claim was approved",
        body=(
            f"Your claim on '{claim.match.lost_report.item_name}' was approved. "
            "Visit the office to pick up your item."
        ),
        link=url_for("claims.detail", claim_id=claim.claim_id),
    )

    flash("Claim approved. Mark as released when the item is handed over.", "success")
    return redirect(url_for("claims.detail", claim_id=claim_id))


@claims_bp.route("/<int:claim_id>/reject", methods=["POST"])
@login_required
@staff_required
def reject(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    if claim.status not in ("pending", "approved"):
        flash(f"Claim is already {claim.status}.", "warning")
        return redirect(url_for("claims.detail", claim_id=claim_id))
    claim.status = "rejected"
    claim.verified_by = current_user.user_id
    claim.resolved_at = datetime.now(timezone.utc)
    db.session.commit()

    notify(
        user_id=claim.claimant_id,
        title="Your claim was not approved",
        body=f"Your claim on '{claim.match.lost_report.item_name}' was rejected by staff.",
        link=url_for("claims.detail", claim_id=claim.claim_id),
    )

    flash("Claim rejected.", "info")
    return redirect(url_for("claims.detail", claim_id=claim_id))


@claims_bp.route("/<int:claim_id>/release", methods=["POST"])
@login_required
@staff_required
def release(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    if claim.status != "approved":
        flash("Only approved claims can be released.", "danger")
        return redirect(url_for("claims.detail", claim_id=claim_id))
    claim.status = "released"
    claim.resolved_at = datetime.now(timezone.utc)
    claim.match.lost_report.status = "closed"
    claim.match.found_item.status = "released"
    db.session.commit()

    notify(
        user_id=claim.claimant_id,
        title="Item released",
        body=(
            f"Your item '{claim.match.lost_report.item_name}' has been released. "
            "The case is now closed. Thanks for using Lost & Found!"
        ),
        link=url_for("claims.detail", claim_id=claim.claim_id),
    )

    flash("Item marked as released. Lost report closed.", "success")
    return redirect(url_for("claims.detail", claim_id=claim_id))


@claims_bp.route("/export.csv")
@login_required
@staff_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "claim_id", "lost_item", "found_item", "claimant_name", "claimant_email",
        "status", "submitted_at", "resolved_at", "verified_by", "notes",
    ])
    for c in Claim.query.order_by(Claim.submitted_at.desc()).all():
        writer.writerow([
            c.claim_id,
            c.match.lost_report.item_name,
            c.match.found_item.item_name,
            c.claimant.name,
            c.claimant.email,
            c.status,
            c.submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
            c.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if c.resolved_at else "",
            c.verifier.name if c.verifier else "",
            c.notes or "",
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=claims.csv"},
    )


@claims_bp.route("/export.xlsx")
@login_required
@staff_required
def export_xlsx():
    headers = [
        "Claim ID", "Lost Item", "Found Item", "Claimant Name", "Claimant Email",
        "Status", "Submitted At", "Resolved At", "Verified By", "Notes",
    ]
    rows = (
        (
            c.claim_id,
            c.match.lost_report.item_name,
            c.match.found_item.item_name,
            c.claimant.name,
            c.claimant.email,
            c.status,
            c.submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
            c.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if c.resolved_at else "",
            c.verifier.name if c.verifier else "",
            c.notes or "",
        )
        for c in Claim.query.order_by(Claim.submitted_at.desc()).all()
    )
    payload = build_xlsx("Claims", headers, rows)
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=claims.xlsx"},
    )


@claims_bp.route("/<int:claim_id>/receipt.pdf")
@login_required
def receipt_pdf(claim_id):
    """Printable receipt for a released claim — proof of property handover."""
    claim = Claim.query.get_or_404(claim_id)
    if claim.claimant_id != current_user.user_id and not _is_staff():
        abort(403)
    html = render_template("claims/receipt.html", claim=claim)
    payload = render_pdf(html)
    return Response(
        payload,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=claim_{claim_id}_receipt.pdf",
        },
    )
