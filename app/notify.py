"""Notification helpers — write a Notification row and (optionally) email."""
import logging

from flask import current_app, url_for
from flask_mail import Message

from .extensions import db, mail
from .models import Notification, User

log = logging.getLogger(__name__)


def _send_email(user, title, body, link):
    """Best-effort email send. Never raises; logs and moves on."""
    if not current_app.config.get("MAIL_SERVER"):
        return
    if not user or not user.email:
        return
    try:
        msg = Message(subject=f"[Lost & Found] {title}", recipients=[user.email])
        text = body or title
        if link:
            external = url_for("main.index", _external=True).rstrip("/") + link
            text = f"{text}\n\nView: {external}"
        msg.body = text
        mail.send(msg)
    except Exception as e:  # noqa: BLE001
        log.warning("Email send failed for %s: %s", user.email, e)


def notify(user_id, title, body=None, link=None):
    """Create one in-app notification (committed immediately) and email if configured."""
    user = db.session.get(User, user_id)
    if not user:
        return
    notif = Notification(user_id=user_id, title=title, body=body, link=link)
    db.session.add(notif)
    db.session.commit()
    _send_email(user, title, body, link)


def notify_staff(title, body=None, link=None):
    """Notify every staff/admin user."""
    for user in User.query.filter(User.role.in_(["staff", "admin"])).all():
        notify(user.user_id, title, body, link)
