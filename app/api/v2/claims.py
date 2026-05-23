"""GET / POST /api/v2/claims — Smorest variant."""
from flask import g
from flask_smorest import Blueprint, abort

from ...extensions import db
from ...models import Claim, Match
from .auth_helpers import api_login_required
from .schemas import (
    ClaimSchema, ClaimCreateSchema,
    PaginationQuerySchema, paginated,
)

blp = Blueprint(
    "claims_v2", __name__,
    url_prefix="/api/v2/claims",
    description="Owner claims against confirmed matches.",
)


@blp.route("", methods=["GET"])
@blp.arguments(PaginationQuerySchema, location="query")
@blp.response(200, paginated(ClaimSchema))
@api_login_required
def list_claims(args):
    """List claims — students see only their own; staff/admin see all."""
    query = Claim.query.order_by(Claim.submitted_at.desc())
    if g.current_api_user.role not in ("staff", "admin"):
        query = query.filter_by(claimant_id=g.current_api_user.user_id)
    pagination = query.paginate(
        page=args["page"], per_page=args["per_page"], error_out=False
    )
    return {
        "data": pagination.items,
        "page": args["page"],
        "per_page": args["per_page"],
        "total": pagination.total,
    }


@blp.route("/<int:claim_id>", methods=["GET"])
@blp.response(200, ClaimSchema)
@blp.alt_response(404, description="Claim not found.")
@blp.alt_response(403, description="Not the claimant.")
@api_login_required
def get_claim(claim_id):
    """Fetch a single claim."""
    claim = db.session.get(Claim, claim_id)
    if claim is None:
        abort(404, message="not_found")
    if claim.claimant_id != g.current_api_user.user_id and g.current_api_user.role not in ("staff", "admin"):
        abort(403, message="forbidden")
    return claim


@blp.route("", methods=["POST"])
@blp.arguments(ClaimCreateSchema)
@blp.response(201, ClaimSchema)
@blp.alt_response(400, description="match_id does not exist.")
@api_login_required
def create_claim(payload):
    """File a new claim. Claimant is set from the caller's token."""
    if db.session.get(Match, payload["match_id"]) is None:
        abort(400, message="match_id_not_found")
    claim = Claim(
        match_id=payload["match_id"],
        claimant_id=g.current_api_user.user_id,
        notes=payload.get("notes"),
        status="pending",
    )
    db.session.add(claim)
    db.session.commit()
    return claim
