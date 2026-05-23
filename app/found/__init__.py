from flask import Blueprint

found_bp = Blueprint(
    "found", __name__, template_folder="../templates/found"
)

from . import routes  # noqa: E402, F401
