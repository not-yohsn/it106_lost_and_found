"""Bearer-token resolution for /api/v2 (mirrors v1's resolver)."""
from functools import wraps

from flask import g, request
from flask_login import current_user
from flask_smorest import abort

from ...models import User


def _resolve_current_api_user():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw_token = auth_header[len("Bearer "):].strip()
        if raw_token:
            users_with_tokens = User.query.filter(
                User.api_token_hash.isnot(None)
            ).all()
            for u in users_with_tokens:
                if u.check_api_token(raw_token):
                    return u
    if current_user.is_authenticated:
        return current_user
    return None


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _resolve_current_api_user()
        if user is None:
            abort(401, message="authentication_required")
        g.current_api_user = user
        return view(*args, **kwargs)
    return wrapped


def api_staff_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _resolve_current_api_user()
        if user is None:
            abort(401, message="authentication_required")
        if user.role not in ("staff", "admin"):
            abort(403, message="forbidden")
        g.current_api_user = user
        return view(*args, **kwargs)
    return wrapped
