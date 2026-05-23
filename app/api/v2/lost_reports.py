"""GET/POST/PUT/DELETE /api/v2/lost-reports — Smorest variant."""
from flask import g
from flask_smorest import Blueprint, abort

from ...extensions import db
from ...models import LostReport
from .auth_helpers import api_login_required
from .schemas import (
    LostReportSchema, LostReportCreateSchema, LostReportUpdateSchema,
    PaginationQuerySchema, paginated,
)

blp = Blueprint(
    "lost_reports_v2", __name__,
    url_prefix="/api/v2/lost-reports",
    description="Student-submitted reports of missing items.",
)


@blp.route("", methods=["GET"])
@blp.arguments(PaginationQuerySchema, location="query")
@blp.response(200, paginated(LostReportSchema))
@api_login_required
def list_lost_reports(args):
    """List lost reports — paginated."""
    pagination = (
        LostReport.query
        .order_by(LostReport.created_at.desc())
        .paginate(page=args["page"], per_page=args["per_page"], error_out=False)
    )
    return {
        "data": pagination.items,
        "page": args["page"],
        "per_page": args["per_page"],
        "total": pagination.total,
    }


@blp.route("/<int:report_id>", methods=["GET"])
@blp.response(200, LostReportSchema)
@blp.alt_response(404, description="Report not found.")
@api_login_required
def get_lost_report(report_id):
    """Fetch a single lost report."""
    report = db.session.get(LostReport, report_id)
    if report is None:
        abort(404, message="not_found")
    return report


@blp.route("", methods=["POST"])
@blp.arguments(LostReportCreateSchema)
@blp.response(201, LostReportSchema)
@api_login_required
def create_lost_report(payload):
    """File a new lost report. Owner is set from the caller's token."""
    report = LostReport(user_id=g.current_api_user.user_id, **payload)
    db.session.add(report)
    db.session.commit()
    return report


@blp.route("/<int:report_id>", methods=["PUT"])
@blp.arguments(LostReportUpdateSchema)
@blp.response(200, LostReportSchema)
@blp.alt_response(404, description="Report not found.")
@blp.alt_response(403, description="Not the owner.")
@api_login_required
def update_lost_report(payload, report_id):
    """Partial-update a lost report (owner-only)."""
    report = db.session.get(LostReport, report_id)
    if report is None:
        abort(404, message="not_found")
    if report.user_id != g.current_api_user.user_id and g.current_api_user.role not in ("staff", "admin"):
        abort(403, message="forbidden")
    for key, value in payload.items():
        setattr(report, key, value)
    db.session.commit()
    return report


@blp.route("/<int:report_id>", methods=["DELETE"])
@blp.response(204)
@blp.alt_response(404, description="Report not found.")
@blp.alt_response(403, description="Not the owner.")
@api_login_required
def delete_lost_report(report_id):
    """Delete a lost report (owner-only)."""
    report = db.session.get(LostReport, report_id)
    if report is None:
        abort(404, message="not_found")
    if report.user_id != g.current_api_user.user_id and g.current_api_user.role not in ("staff", "admin"):
        abort(403, message="forbidden")
    db.session.delete(report)
    db.session.commit()
    return ""
