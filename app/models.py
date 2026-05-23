from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, login_manager


def _utcnow():
    """Timezone-aware UTC now — replaces the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    role = db.Column(
        db.Enum("student", "staff", "admin", name="user_role"),
        nullable=False,
        default="student",
    )
    password_hash = db.Column(db.String(255), nullable=False)
    api_token_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    lost_reports = db.relationship(
        "LostReport", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Notification.created_at.desc()",
    )

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_api_token(self):
        """Generate, hash-store, and return a new raw token. Replaces any prior token."""
        import secrets
        raw_token = secrets.token_hex(32)
        self.api_token_hash = generate_password_hash(raw_token)
        return raw_token

    def clear_api_token(self):
        self.api_token_hash = None

    def check_api_token(self, raw_token):
        if not self.api_token_hash:
            return False
        return check_password_hash(self.api_token_hash, raw_token)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Finder(db.Model):
    __tablename__ = "finders"

    finder_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=_utcnow)

    found_items = db.relationship("FoundItem", back_populates="finder")

    def to_dict(self):
        return {
            "finder_id": self.finder_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class LostReport(db.Model):
    __tablename__ = "lost_reports"

    report_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    item_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(60))
    location = db.Column(db.String(120))
    date_lost = db.Column(db.Date)
    photo_path = db.Column(db.String(255))
    status = db.Column(
        db.Enum("reported", "matched", "claimed", "closed", name="lost_status"),
        default="reported",
    )
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", back_populates="lost_reports")
    match = db.relationship("Match", back_populates="lost_report", uselist=False)

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "user_id": self.user_id,
            "item_name": self.item_name,
            "description": self.description,
            "category": self.category,
            "location": self.location,
            "date_lost": self.date_lost.isoformat() if self.date_lost else None,
            "photo_path": self.photo_path,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class FoundItem(db.Model):
    __tablename__ = "found_items"

    item_id = db.Column(db.Integer, primary_key=True)
    finder_id = db.Column(db.Integer, db.ForeignKey("finders.finder_id"))
    logged_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    item_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(60))
    location_found = db.Column(db.String(120))
    date_found = db.Column(db.Date)
    photo_path = db.Column(db.String(255))
    status = db.Column(
        db.Enum("logged", "matched", "released", name="found_status"),
        default="logged",
    )
    created_at = db.Column(db.DateTime, default=_utcnow)

    finder = db.relationship("Finder", back_populates="found_items")
    match = db.relationship("Match", back_populates="found_item", uselist=False)

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "finder_id": self.finder_id,
            "logged_by": self.logged_by,
            "item_name": self.item_name,
            "description": self.description,
            "category": self.category,
            "location_found": self.location_found,
            "date_found": self.date_found.isoformat() if self.date_found else None,
            "photo_path": self.photo_path,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class Match(db.Model):
    __tablename__ = "matches"

    match_id = db.Column(db.Integer, primary_key=True)
    lost_report_id = db.Column(
        db.Integer, db.ForeignKey("lost_reports.report_id"), unique=True, nullable=False
    )
    found_item_id = db.Column(
        db.Integer, db.ForeignKey("found_items.item_id"), unique=True, nullable=False
    )
    matched_at = db.Column(db.DateTime, default=_utcnow)
    confidence_score = db.Column(db.Float)

    lost_report = db.relationship("LostReport", back_populates="match")
    found_item = db.relationship("FoundItem", back_populates="match")
    claims = db.relationship("Claim", back_populates="match", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "match_id": self.match_id,
            "lost_report_id": self.lost_report_id,
            "found_item_id": self.found_item_id,
            "matched_at": self.matched_at.isoformat() + "Z" if self.matched_at else None,
            "confidence_score": self.confidence_score,
        }


class Claim(db.Model):
    __tablename__ = "claims"

    claim_id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.match_id"), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    status = db.Column(
        db.Enum("pending", "approved", "rejected", "released", name="claim_status"),
        default="pending",
    )
    notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=_utcnow)
    resolved_at = db.Column(db.DateTime)

    match = db.relationship("Match", back_populates="claims")
    claimant = db.relationship("User", foreign_keys=[claimant_id])
    verifier = db.relationship("User", foreign_keys=[verified_by])

    def to_dict(self):
        return {
            "claim_id": self.claim_id,
            "match_id": self.match_id,
            "claimant_id": self.claimant_id,
            "verified_by": self.verified_by,
            "status": self.status,
            "notes": self.notes,
            "submitted_at": self.submitted_at.isoformat() + "Z" if self.submitted_at else None,
            "resolved_at": self.resolved_at.isoformat() + "Z" if self.resolved_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True
    )
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "link": self.link,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
