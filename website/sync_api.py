"""REST Sync API Blueprint for NEXGEN Web POS.

Provides secure HTTP endpoints for bi-directional synchronization
between Local POS terminals and the cloud Web POS (PythonAnywhere)
running on SQLite.
"""

import os
import logging
import json
from datetime import datetime, date
from functools import wraps
from flask import Blueprint, request, jsonify
from .models import (
    db, User, Product, Category, Order, OrderItem, Settlement,
    ActivityLog, ReceiptSettings, RLCSettings, GiftCertificate,
    OrderAuditLog, ZReading
)

logger = logging.getLogger("SyncAPI")

sync_api = Blueprint('sync_api', __name__, url_prefix='/api/sync')

DEFAULT_SYNC_TOKEN = "nexgen-sync-secure-token-2026"


def require_sync_auth(f):
    """Authenticate incoming synchronization requests using a shared secret token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected_token = os.environ.get('SYNC_API_TOKEN', DEFAULT_SYNC_TOKEN).strip()
        auth_header = request.headers.get('X-Sync-Token', '').strip()

        if not auth_header or auth_header != expected_token:
            logger.warning("Unauthorized sync request rejected from %s", request.remote_addr)
            return jsonify({"success": False, "error": "Unauthorized: invalid sync token"}), 401

        return f(*args, **kwargs)
    return decorated


def _serialize_model(obj):
    """Convert an SQLAlchemy model instance into a JSON-serializable dictionary."""
    if obj is None:
        return None
    res = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, (datetime, date)):
            val = val.isoformat()
        res[col.name] = val
    return res


def _upsert_record(model_class, payload, primary_key='id', unique_key=None):
    """Safely upsert a record into local SQLite database."""
    pk_val = payload.get(primary_key)
    existing = None

    if pk_val is not None:
        existing = db.session.get(model_class, pk_val)

    if not existing and unique_key and payload.get(unique_key):
        existing = model_class.query.filter(getattr(model_class, unique_key) == payload[unique_key]).first()

    cols = {c.name for c in model_class.__table__.columns}
    clean_data = {k: v for k, v in payload.items() if k in cols}

    # Convert datetime strings back to datetime objects if needed
    for c in model_class.__table__.columns:
        if c.name in clean_data and clean_data[c.name] is not None:
            if hasattr(c.type, 'python_type') and issubclass(c.type.python_type, datetime):
                if isinstance(clean_data[c.name], str):
                    try:
                        clean_data[c.name] = datetime.fromisoformat(clean_data[c.name])
                    except Exception:
                        pass
            elif hasattr(c.type, 'python_type') and issubclass(c.type.python_type, date):
                if isinstance(clean_data[c.name], str):
                    try:
                        clean_data[c.name] = date.fromisoformat(clean_data[c.name])
                    except Exception:
                        pass

    if existing:
        for k, v in clean_data.items():
            if k != primary_key:
                setattr(existing, k, v)
        return existing
    else:
        new_instance = model_class(**clean_data)
        db.session.add(new_instance)
        return new_instance


@sync_api.route('/ping', methods=['GET'])
def sync_ping():
    """Lightweight health check and connectivity ping."""
    return jsonify({
        "success": True,
        "status": "ready",
        "service": "nexgenwebpos-sync",
        "orders_count": Order.query.count(),
        "products_count": Product.query.count(),
        "users_count": User.query.count(),
        "server_time": datetime.utcnow().isoformat()
    })


@sync_api.route('/recover', methods=['GET', 'POST'])
def sync_recover():
    """Recover database from stale locks or WAL corruption on PythonAnywhere NFS."""
    try:
        from sqlalchemy import text
        db.session.rollback()
        db.session.execute(text("PRAGMA journal_mode=DELETE;"))
        db.session.execute(text("PRAGMA busy_timeout=15000;"))
        db.session.commit()
        return jsonify({"success": True, "message": "Database recovered to DELETE mode and locks cleared."})
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500



@sync_api.route('/push', methods=['POST'])
@require_sync_auth
def sync_push():
    """Receive and apply a batch of mutation events from Local POS."""
    data = request.get_json(silent=True)
    if not data or 'items' not in data:
        return jsonify({"success": False, "error": "Missing 'items' in request body"}), 400

    items = data.get('items', [])
    processed_count = 0
    errors = []

    for item in items:
        table_name = item.get('table_name')
        action = (item.get('action') or 'INSERT').upper()
        record_id = item.get('record_id')
        raw_payload = item.get('payload') or {}
        payload = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload

        try:
            if action == 'DELETE':
                model_map = {
                    'orders': Order, 'order': Order,
                    'users': User, 'user': User,
                    'products': Product, 'product': Product,
                    'categories': Category, 'category': Category,
                    'receipt_settings': ReceiptSettings,
                    'order_items': OrderItem, 'order_item': OrderItem,
                    'settlements': Settlement, 'settlement': Settlement,
                    'z_reading': ZReading, 'z_readings': ZReading,
                    'order_audit_logs': OrderAuditLog, 'order_audit_log': OrderAuditLog,
                    'activity_logs': ActivityLog, 'activity_log': ActivityLog,
                }
                model_cls = model_map.get(table_name)
                if model_cls and record_id:
                    existing = db.session.get(model_cls, record_id)
                    if existing:
                        db.session.delete(existing)
                processed_count += 1
                continue

            if table_name in ('orders', 'order'):
                items_payload = payload.pop('items', [])
                settlement_payload = payload.pop('settlement', None)

                # 1. Upsert Order
                order_inst = _upsert_record(Order, payload, primary_key='id', unique_key='order_no')
                db.session.flush()

                # 2. Upsert Order Items
                for o_item in items_payload:
                    o_item['order_id'] = order_inst.id
                    _upsert_record(OrderItem, o_item, primary_key='id')

                # 3. Upsert Settlement
                if settlement_payload:
                    settlement_payload['order_id'] = order_inst.id
                    _upsert_record(Settlement, settlement_payload, primary_key='id')

            elif table_name in ('users', 'user'):
                _upsert_record(User, payload, primary_key='id', unique_key='username')

            elif table_name in ('products', 'product'):
                _upsert_record(Product, payload, primary_key='id', unique_key='name')

            elif table_name in ('categories', 'category'):
                _upsert_record(Category, payload, primary_key='id', unique_key='name')

            elif table_name in ('activity_logs', 'activity_log'):
                if not payload.get('action'):
                    payload['action'] = payload.get('event_type') or 'Activity'
                _upsert_record(ActivityLog, payload, primary_key='id')

            elif table_name in ('receipt_settings', 'receipt_setting'):
                _upsert_record(ReceiptSettings, payload, primary_key='id')

            elif table_name in ('order_audit_logs', 'order_audit_log'):
                _upsert_record(OrderAuditLog, payload, primary_key='id')

            elif table_name in ('z_reading', 'z_readings'):
                _upsert_record(ZReading, payload, primary_key='id')

            elif table_name in ('order_items', 'order_item'):
                _upsert_record(OrderItem, payload, primary_key='id')

            elif table_name in ('settlements', 'settlement'):
                _upsert_record(Settlement, payload, primary_key='id')

            processed_count += 1

        except Exception as exc:
            db.session.rollback()
            logger.error("Sync error processing %s#%s: %s", table_name, record_id, exc)
            errors.append({"table": table_name, "id": record_id, "error": str(exc)})

    try:
        db.session.commit()
    except Exception as commit_exc:
        db.session.rollback()
        logger.error("Failed to commit sync push batch: %s", commit_exc)
        return jsonify({"success": False, "error": str(commit_exc)}), 500

    return jsonify({
        "success": len(errors) == 0,
        "processed": processed_count,
        "errors": errors
    })


@sync_api.route('/pull', methods=['GET'])
@require_sync_auth
def sync_pull():
    """Serve master catalog data (Users, Categories, Products, Settings) to Local POS."""
    try:
        users = [_serialize_model(u) for u in User.query.filter(User.status != 'deleted').all()]
        categories = [_serialize_model(c) for c in Category.query.all()]
        products = [_serialize_model(p) for p in Product.query.all()]
        settings = _serialize_model(ReceiptSettings.query.first())

        return jsonify({
            "success": True,
            "data": {
                "users": users,
                "categories": categories,
                "products": products,
                "receipt_settings": settings
            },
            "pulled_at": datetime.utcnow().isoformat()
        })
    except Exception as exc:
        logger.error("Error serving sync pull: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500
