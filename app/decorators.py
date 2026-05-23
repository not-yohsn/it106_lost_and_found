from functools import wraps

from flask import abort
from flask_login import current_user


def staff_required(view):
    """Allow only authenticated users with role 'staff' or 'admin'."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ("staff", "admin"):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Allow only authenticated users with role 'admin'."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped
