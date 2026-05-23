from flask import Blueprint

claims_bp = Blueprint(
    "claims", __name__, template_folder="../templates/claims"
)

from . import routes  # noqa: E402, F401
