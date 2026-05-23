from flask import Blueprint

matches_bp = Blueprint(
    "matches", __name__, template_folder="../templates/matches"
)

from . import routes  # noqa: E402, F401
