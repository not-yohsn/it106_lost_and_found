"""POST /api/v2/auth/login and /logout (Smorest variant)."""
from flask_smorest import Blueprint, abort

from ...extensions import db, limiter
from ...models import User
from .auth_helpers import api_login_required, _resolve_current_api_user
from .schemas import LoginRequestSchema, TokenResponseSchema

blp = Blueprint(
    "auth_v2", __name__,
    url_prefix="/api/v2/auth",
    description="Bearer-token authentication for the v2 API.",
)


@blp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
@blp.arguments(LoginRequestSchema)
@blp.response(200, TokenResponseSchema)
@blp.alt_response(401, description="Wrong email or password.")
def login(payload):
    """Validate credentials and issue a fresh Bearer token."""
    user = User.query.filter_by(email=payload["email"].lower()).first()
    if user is None or not user.check_password(payload["password"]):
        abort(401, message="invalid_credentials")
    raw_token = user.set_api_token()
    db.session.commit()
    return {"token": raw_token, "user": user}


@blp.route("/logout", methods=["POST"])
@blp.response(204)
@api_login_required
def logout():
    """Invalidate the caller's Bearer token."""
    user = _resolve_current_api_user()
    if user is not None:
        user.clear_api_token()
        db.session.commit()
    return ""
