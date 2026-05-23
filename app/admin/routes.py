from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import admin_bp
from ..decorators import admin_required
from ..extensions import db
from ..models import User

VALID_ROLES = ("student", "staff", "admin")


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")

    if new_role not in VALID_ROLES:
        flash("Invalid role.", "danger")
        return redirect(url_for("admin.users"))

    if user.user_id == current_user.user_id and new_role != "admin":
        flash("You can't demote yourself — ask another admin to do it.", "warning")
        return redirect(url_for("admin.users"))

    if user.role == new_role:
        flash(f"{user.name} is already {new_role}.", "info")
        return redirect(url_for("admin.users"))

    user.role = new_role
    db.session.commit()
    flash(f"{user.name} is now {new_role}.", "success")
    return redirect(url_for("admin.users"))
