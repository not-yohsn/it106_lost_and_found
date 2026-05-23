"""Pytest fixtures for the Lost & Found app.

Tests run against an in-memory SQLite database so they are fast and
independent of the local MariaDB instance. A fresh DB is built once per
session; each test gets a clean transaction rollback via the `db` fixture.
"""
from datetime import date

import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.config import Config
from app.extensions import db as _db
from app.models import (
    Claim, FoundItem, LostReport, Match, Notification, User,
)


class TestConfig(Config):
    TESTING = True
    # In-memory SQLite + StaticPool so every connection sees the SAME
    # :memory: database. Without StaticPool, SQLAlchemy's default pool
    # may hand out a fresh connection (= fresh empty DB) to the request
    # handler that's separate from the one the fixture wrote to.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_ENABLED = False
    CACHE_TYPE = "NullCache"
    TALISMAN_FORCE_HTTPS = False


@pytest.fixture
def app():
    """Fresh Flask app + fresh in-memory SQLite per test.

    Function-scoped to guarantee complete isolation: no shared
    SQLAlchemy identity map, no shared rate-limiter counters, no
    shared session state between tests. Slightly slower than a
    session-scoped app but eliminates an entire class of cross-test
    bugs (stale ORM cache, leaked auth tokens, etc).
    """
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


def _make_user(name, email, role, password):
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    _db.session.add(user)
    _db.session.flush()
    return user


@pytest.fixture
def admin(app):
    with app.app_context():
        user = _make_user("Admin User", "admin@test.local", "admin", "Admin123!")
        _db.session.commit()
        return {"id": user.user_id, "email": user.email, "password": "Admin123!"}


@pytest.fixture
def student(app):
    with app.app_context():
        user = _make_user("Test Student", "student@test.local", "student", "Student123!")
        _db.session.commit()
        return {"id": user.user_id, "email": user.email, "password": "Student123!"}


@pytest.fixture
def student2(app):
    with app.app_context():
        user = _make_user("Other Student", "student2@test.local", "student", "Student123!")
        _db.session.commit()
        return {"id": user.user_id, "email": user.email, "password": "Student123!"}


def _login_and_get_token(client, email, password):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()["token"]


@pytest.fixture
def admin_token(client, admin):
    return _login_and_get_token(client, admin["email"], admin["password"])


@pytest.fixture
def student_token(client, student):
    return _login_and_get_token(client, student["email"], student["password"])


@pytest.fixture
def student2_token(client, student2):
    return _login_and_get_token(client, student2["email"], student2["password"])


@pytest.fixture
def auth_admin(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_student(student_token):
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
def auth_student2(student2_token):
    return {"Authorization": f"Bearer {student2_token}"}


@pytest.fixture
def sample_lost_report(app, student):
    """A 'Black Backpack' report owned by the `student` fixture."""
    with app.app_context():
        report = LostReport(
            user_id=student["id"],
            item_name="Black Backpack",
            description="Has my laptop inside.",
            category="bag",
            location="Library 2F",
            date_lost=date(2026, 5, 16),
        )
        _db.session.add(report)
        _db.session.commit()
        return report.report_id


@pytest.fixture
def sample_found_item(app, admin):
    with app.app_context():
        item = FoundItem(
            logged_by=admin["id"],
            item_name="Black Backpack (found)",
            description="Black with a red zipper.",
            category="bag",
            location_found="Library 2F",
            date_found=date(2026, 5, 16),
        )
        _db.session.add(item)
        _db.session.commit()
        return item.item_id


@pytest.fixture
def sample_match_and_claim(app, sample_lost_report, sample_found_item, student):
    """A confirmed match with a pending claim filed by the `student`."""
    with app.app_context():
        match = Match(
            lost_report_id=sample_lost_report,
            found_item_id=sample_found_item,
            confidence_score=0.85,
        )
        _db.session.add(match)
        _db.session.flush()
        claim = Claim(
            match_id=match.match_id,
            claimant_id=student["id"],
            notes="This is my bag.",
            status="pending",
        )
        _db.session.add(claim)
        _db.session.commit()
        return {"match_id": match.match_id, "claim_id": claim.claim_id}
