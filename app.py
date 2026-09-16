"""NEXGEN Web POS — Cloud Online Admin Portal Entry Point.

Clean, lightweight cloud deployment for PythonAnywhere & remote browser access.
"""

import os
import sys
import time
from dotenv import load_dotenv
from flask import Blueprint, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Load environment
env_file = os.path.join(HERE, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)

from website import create_app

TEMPLATES_DIR = os.path.join(HERE, "templates")
STATIC_DIR = os.path.join(HERE, "static")
VENDOR_DIR = os.path.join(HERE, "vendor")

_START_TIME = int(time.time())

def _current_asset_version() -> int:
    return _START_TIME

def build_app():
    app = create_app()

    # Asset blueprint with aggressive browser caching
    assets = Blueprint("web_assets", __name__, url_prefix="/assets")

    @assets.route("/vendor/<path:filename>")
    def serve_vendor(filename: str):
        return send_from_directory(VENDOR_DIR, filename, max_age=31536000)

    @assets.route("/<path:filename>")
    def serve_static(filename: str):
        return send_from_directory(STATIC_DIR, filename, max_age=31536000)

    app.register_blueprint(assets)

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(STATIC_DIR, "box_logo.png", mimetype="image/png")

    @app.context_processor
    def inject_asset_helpers():
        v = _START_TIME
        return {
            "asset": lambda path: f"/assets/{path.lstrip('/')}?v={v}",
            "vendor": lambda path: f"/assets/vendor/{path.lstrip('/')}?v={v}",
            "asset_version": v,
        }

    return app

app = build_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5005"))
    app.run(host="0.0.0.0", port=port, debug=True)
