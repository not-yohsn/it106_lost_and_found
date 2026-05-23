from flask import Flask
from flask_login import current_user

from .config import Config
from .extensions import (
    db, login_manager, mail, migrate,
    limiter, talisman, compress, cache,
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    mail.init_app(app)

    from . import models  # noqa: F401  (register models with SQLAlchemy)
    migrate.init_app(app, db)

    # Rate limiting (5/min on auth endpoints; 200/min default elsewhere).
    # Disabled in TestConfig via RATELIMIT_ENABLED=False.
    limiter.init_app(app)

    # Response compression (gzip/brotli).
    compress.init_app(app)

    # In-process cache for dashboard KPIs etc. Swap to Redis later via config.
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 60)
    cache.init_app(app)

    # HTTP security headers. CSP allows the CDNs the templates actually use
    # (Bootstrap, Google Fonts) plus unpkg for HTMX. force_https only when
    # an env flag is set, so the local Flask dev server still works.
    talisman.init_app(
        app,
        force_https=app.config.get("TALISMAN_FORCE_HTTPS", False),
        strict_transport_security=True,
        session_cookie_secure=app.config.get("TALISMAN_FORCE_HTTPS", False),
        content_security_policy={
            "default-src": "'self'",
            "img-src": ["'self'", "data:", "blob:"],
            "style-src": [
                "'self'", "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://fonts.googleapis.com",
            ],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "script-src": [
                "'self'", "'unsafe-inline'", "'unsafe-eval'",
                "https://cdn.jsdelivr.net",
                "https://unpkg.com",
            ],
            "connect-src": ["'self'", "https://cdn.jsdelivr.net"],
        },
        # NOTE: deliberately NOT using content_security_policy_nonce_in.
        # The CSP spec says when a nonce is set, 'unsafe-inline' is
        # ignored -- and Alpine.js's directive expressions rely on
        # runtime eval (new Function), which needs 'unsafe-eval'.
        # Trade-off accepted: slightly weaker CSP, but Alpine + inline
        # bootstrap scripts (page-progress bar) actually work in the
        # browser.
    )

    from .auth import auth_bp
    from .main import main_bp
    from .reports import reports_bp
    from .found import found_bp
    from .matches import matches_bp
    from .claims import claims_bp
    from .notifications import notifications_bp
    from .admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(found_bp, url_prefix="/found")
    app.register_blueprint(matches_bp, url_prefix="/matches")
    app.register_blueprint(claims_bp, url_prefix="/claims")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from .api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    # /api/v2 — Flask-Smorest blueprint with auto-generated OpenAPI/Swagger.
    app.config.setdefault("API_TITLE", "Lost & Found API")
    app.config.setdefault("API_VERSION", "v2")
    app.config.setdefault("OPENAPI_VERSION", "3.0.3")
    app.config.setdefault("OPENAPI_URL_PREFIX", "/api/v2")
    app.config.setdefault("OPENAPI_SWAGGER_UI_PATH", "/docs")
    app.config.setdefault(
        "OPENAPI_SWAGGER_UI_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )
    from .api.v2 import api_v2
    from .api.v2.auth import blp as v2_auth_blp
    from .api.v2.lost_reports import blp as v2_lost_blp
    from .api.v2.found_items import blp as v2_found_blp
    from .api.v2.claims import blp as v2_claims_blp
    api_v2.init_app(app)
    api_v2.register_blueprint(v2_auth_blp)
    api_v2.register_blueprint(v2_lost_blp)
    api_v2.register_blueprint(v2_found_blp)
    api_v2.register_blueprint(v2_claims_blp)

    @app.context_processor
    def inject_notification_state():
        """Provide the navbar with the unread count and the 5 latest
        notifications for the current user. Rendered server-side so the
        dropdown does NOT depend on JS / HTMX being able to fetch it.
        """
        if not current_user.is_authenticated:
            return {"unread_notifications": 0, "recent_notifications": []}
        from .models import Notification
        count = Notification.query.filter_by(
            user_id=current_user.user_id, is_read=False
        ).count()
        recent = (
            Notification.query
            .filter_by(user_id=current_user.user_id)
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )
        return {"unread_notifications": count, "recent_notifications": recent}

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables from the SQLAlchemy models."""
        db.create_all()
        print("Database initialized.")

    return app
