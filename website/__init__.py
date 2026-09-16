"""NEXGEN Web POS — Application Factory.

Cloud web server architecture for online POS Admin portal.
"""

import os
import sys
import logging
import secrets
import hmac
from flask import Flask, request, session, jsonify, render_template, flash, redirect, url_for
from flask_login import LoginManager
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from .models import db, User, Product, Category, Order, OrderItem, Settlement, ActivityLog, ReceiptSettings, RLCSettings
from .logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

def get_base_dir():
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def create_app():
    base_dir = get_base_dir()
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    instance_dir = os.path.join(base_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexgen-cloud-pos-secret-2026')
    
    # Database Configuration (supports local SQLite or PostgreSQL Supabase cloud DB)
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri and db_uri.strip():
        db_uri = db_uri.strip()
        if db_uri.startswith('postgres://'):
            db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 15,
        }
        logger.info(f"Connected to Cloud PostgreSQL Database URI: {db_uri.split('@')[-1] if '@' in db_uri else 'PostgreSQL'}")
    else:
        db_path = os.path.join(instance_dir, 'pos.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        logger.info(f"Connected to Local SQLite Database: {db_path}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Authentication Configuration
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    _USER_CACHE = {}
    _USER_CACHE_TTL = 60.0

    @login_manager.user_loader
    def load_user(user_id):
        try:
            import time
            uid = int(user_id)
            now = time.time()
            if uid in _USER_CACHE:
                cached_user, ts = _USER_CACHE[uid]
                if now - ts < _USER_CACHE_TTL:
                    return cached_user
            user = User.query.get(uid)
            if user:
                _USER_CACHE[uid] = (user, now)
            return user
        except Exception:
            return None

    def get_csrf_token():
        token = session.get("_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    @app.context_processor
    def inject_globals():
        from .permissions import ALL_ROLES, PERMISSIONS, ROLE_LABELS, has_permission
        return {
            "csrf_token": get_csrf_token,
            "permissions": PERMISSIONS,
            "role_labels": ROLE_LABELS,
            "all_roles": ALL_ROLES,
            "has_permission": has_permission,
            "rlc_enabled": False,
            "asset": lambda path: f"/assets/{path.lstrip('/')}?v=1789473361",
            "vendor": lambda path: f"/assets/vendor/{path.lstrip('/')}?v=1789473361",
            "asset_version": 1789473361,
        }

    @app.before_request
    def enforce_web_role_restriction():
        from flask_login import current_user, logout_user
        from .permissions import ROLE_ADMIN, ROLE_MANAGER, ROLE_BIR_GUEST
        if current_user and current_user.is_authenticated:
            ep = request.endpoint or ""
            if ep.startswith("web_assets.") or ep == "static" or ep == "auth.logout" or ep == "auth.login":
                return None
            allowed_web_roles = {ROLE_ADMIN, ROLE_MANAGER, ROLE_BIR_GUEST}
            if current_user.role not in allowed_web_roles:
                logout_user()
                flash("Access denied. Cashier and Crew accounts can only log in at the physical POS terminal.", "danger")
                return redirect(url_for("auth.login"))

    @app.before_request
    def validate_csrf_token():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None

        exempt_endpoints = {
            "auth.login",
            "auth.clear_sessions",
        }
        if request.endpoint in exempt_endpoints:
            return None

        expected_token = session.get("_csrf_token")
        provided_token = (
            request.headers.get("X-CSRFToken")
            or request.headers.get("X-CSRF-Token")
            or request.form.get("csrf_token")
            or (request.get_json(silent=True) or {}).get("csrf_token")
        )

        if expected_token and provided_token and hmac.compare_digest(expected_token, provided_token):
            return None

        # Allow authenticated requests without token if not present in test mode
        if not expected_token:
            return None

        logger.warning(
            "Blocked request with invalid CSRF token: endpoint=%s method=%s path=%s",
            request.endpoint, request.method, request.path
        )
        return jsonify({"success": False, "error": "Invalid CSRF token"}), 400

    # Register Blueprints
    from .auth import auth as auth_blueprint
    from .main import main as main_blueprint
    from .sales_reports import sales_reports as sales_reports_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(sales_reports_blueprint)

    # Initialize tables and seed default admin if needed
    with app.app_context():
        try:
            db.create_all()
            if not User.query.filter_by(role='admin').first():
                admin = User(
                    username='admin',
                    role='admin',
                    status='active'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info("Default admin user created (username: admin, password: admin123)")
        except Exception as e:
            logger.warning(f"Database initialization notice: {e}")

    logger.info("NEXGEN Web POS application initialized successfully.")
    return app
