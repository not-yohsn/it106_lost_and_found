from flask import render_template
from flask_login import login_required, current_user

from . import main_bp
from ..stats import my_stats, system_stats


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    is_staff = current_user.role in ("staff", "admin")
    ctx = {"user": current_user}
    if is_staff:
        ctx["stats"] = system_stats()
    else:
        ctx["my"] = my_stats(current_user.user_id)
    return render_template("main/dashboard.html", **ctx)
