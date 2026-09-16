#!/usr/bin/env python3
"""NEXGEN POS_V2 — SQLite to Supabase Real-Time Sync Engine.

Continuously mirrors local POS transactions, catalog changes, recipe inventory,
and audit logs from local SQLite pos.db to online Supabase PostgreSQL database.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, date
from typing import Dict, Any, List

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from dotenv import load_dotenv
load_dotenv(os.path.join(HERE, ".env"))

from supabase_client import get_supabase_client, is_supabase_configured

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SupabaseSync")


def serialize_model(obj) -> Dict[str, Any]:
    """Convert an SQLAlchemy model instance into a JSON-serializable dictionary."""
    if obj is None:
        return {}
    res = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, (datetime, date)):
            val = val.isoformat()
        res[col.name] = val
    return res


def sync_table(client, model_class, table_name: str, batch_size: int = 500, exclude_fields: List[str] = None, max_records: int = None) -> int:
    """Bulk upsert records from a local SQLite SQLAlchemy model into Supabase."""
    try:
        query = model_class.query
        total = query.count()
        if total == 0:
            return 0

        if max_records and total > max_records:
            # Sync only the most recent N records
            total = max_records
            min_id_record = model_class.query.order_by(model_class.id.desc()).offset(max_records - 1).first()
            if min_id_record:
                query = query.filter(model_class.id >= min_id_record.id)

        synced = 0
        offset = 0
        exclude_set = set(exclude_fields or [])
        exclude_set.update(['processing_user_id', 'processing_started_at', 'processing_last_seen_at'])

        while offset < total:
            batch = query.order_by(model_class.id.asc()).offset(offset).limit(batch_size).all()
            if not batch:
                break
            
            payload = []
            for item in batch:
                data = serialize_model(item)
                for k in exclude_set:
                    data.pop(k, None)
                payload.append(data)

            if payload:
                max_retries = 5
                while max_retries > 0:
                    try:
                        client.table(table_name).upsert(payload).execute()
                        break
                    except Exception as up_exc:
                        err_msg = str(up_exc)
                        import re
                        match = re.search(r"Could not find the '([^']+)' column", err_msg)
                        if match:
                            missing_col = match.group(1)
                            logger.info(f"  [Auto-Heal] Excluding column '{missing_col}' not present in Supabase table '{table_name}'")
                            exclude_set.add(missing_col)
                            for row in payload:
                                row.pop(missing_col, None)
                            max_retries -= 1
                        else:
                            raise up_exc
                synced += len(payload)
                
            offset += batch_size
            
        logger.info(f"  [OK] {table_name}: Synced {synced:,} / {total:,} records")
        return synced
    except Exception as exc:
        logger.error(f"  [ERROR] {table_name} sync error: {exc}")
        return 0


def sync_all_data(client, app) -> Dict[str, int]:
    """Sync all catalog, operations, and audit tables from SQLite to Supabase."""
    from website.models import (
        User, Category, Product, Order, OrderItem, Settlement,
        ActivityLog, OrderAuditLog, ReceiptSettings, RLCSettings
    )
    import sqlite3
    
    results = {}
    with app.app_context():
        logger.info("=== Starting Supabase Full Data Sync ===")
        
        # 1. Categories & Products
        results['categories'] = sync_table(client, Category, 'categories')
        results['products'] = sync_table(client, Product, 'products')
        results['users'] = sync_table(client, User, 'users')
        
        # 2. Recipe & Raw Material Ingredients
        try:
            db_path = os.path.join(HERE, 'instance', 'pos.db')
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute("SELECT id, product_id, product_name, raw_material_name, consumed_quantity, uom, category, raw_material_code FROM product_recipe_ingredient")
            recipe_rows = []
            for r in cur.fetchall():
                recipe_rows.append({
                    'id': r[0], 'product_id': r[1], 'product_name': r[2],
                    'raw_material_name': r[3], 'consumed_quantity': r[4],
                    'uom': r[5], 'category': r[6], 'raw_material_code': r[7]
                })
            con.close()
            if recipe_rows:
                client.table('product_recipe_ingredient').upsert(recipe_rows).execute()
                results['product_recipe_ingredient'] = len(recipe_rows)
                logger.info(f"  [OK] product_recipe_ingredient: Synced {len(recipe_rows):,} records")
        except Exception as e:
            logger.warning(f"  [WARN] product_recipe_ingredient error: {e}")

        # 3. Orders, Order Items, Settlements
        results['orders'] = sync_table(client, Order, 'orders', batch_size=500)
        results['order_items'] = sync_table(client, OrderItem, 'order_items', batch_size=1000)
        results['settlements'] = sync_table(client, Settlement, 'settlements', batch_size=500, exclude_fields=['card_swipe_json'])
        
        # 4. Audit & Activity Logs
        results['order_audit_logs'] = sync_table(client, OrderAuditLog, 'order_audit_logs', batch_size=1000)
        
        # Activity Logs (synthesize action field if existing table requires action NOT NULL)
        try:
            act_query = ActivityLog.query.order_by(ActivityLog.id.desc()).limit(5000).all()
            act_rows = []
            for item in act_query:
                d = serialize_model(item)
                d['action'] = d.get('event_type') or d.get('description') or 'Activity'
                act_rows.append(d)
            if act_rows:
                # Upsert in chunks of 500
                chunk_size = 500
                total_act_synced = 0
                excluded_act_cols = set()
                for i in range(0, len(act_rows), chunk_size):
                    chunk = act_rows[i:i + chunk_size]
                    for c in chunk:
                        for bad in excluded_act_cols:
                            c.pop(bad, None)
                    max_retries = 8
                    while max_retries > 0:
                        try:
                            client.table('activity_logs').upsert(chunk).execute()
                            total_act_synced += len(chunk)
                            break
                        except Exception as err:
                            err_str = str(err)
                            import re
                            m = re.search(r"Could not find the '([^']+)' column", err_str)
                            if m:
                                bad_col = m.group(1)
                                excluded_act_cols.add(bad_col)
                                for c in chunk:
                                    c.pop(bad_col, None)
                                max_retries -= 1
                            else:
                                logger.warning(f"  [WARN] activity_logs chunk warning: {err_str}")
                                break
                results['activity_logs'] = total_act_synced
                logger.info(f"  [OK] activity_logs: Synced {total_act_synced:,} records")
        except Exception as act_exc:
            logger.warning(f"  [WARN] activity_logs sync error: {act_exc}")
        try:
            settings_obj = ReceiptSettings.query.first()
            if settings_obj:
                allowed_cols = {'id', 'store_name', 'address', 'tin', 'min_number', 'serial_number', 'pos_number', 'header_text', 'footer_text', 'vat_reg_tin', 'accreditation_no', 'date_issued', 'valid_until', 'ptu_no'}
                raw_data = serialize_model(settings_obj)
                clean_payload = {k: v for k, v in raw_data.items() if k in allowed_cols}
                if 'header_text' not in clean_payload and hasattr(settings_obj, 'header_lines'):
                    clean_payload['header_text'] = getattr(settings_obj, 'header_lines')
                if 'footer_text' not in clean_payload and hasattr(settings_obj, 'footer_lines'):
                    clean_payload['footer_text'] = getattr(settings_obj, 'footer_lines')
                if 'address' not in clean_payload and hasattr(settings_obj, 'store_location'):
                    clean_payload['address'] = getattr(settings_obj, 'store_location')
                if clean_payload:
                    client.table('receipt_settings').upsert(clean_payload).execute()
                    results['receipt_settings'] = 1
                    logger.info("  [OK] receipt_settings: Synced store metadata")
        except Exception as exc:
            logger.warning(f"  [WARN] receipt_settings sync error: {exc}")
            
        logger.info("=== Full Sync Completed Successfully ===")
    return results


def run_continuous_sync(interval_seconds: int = 30):
    """Run continuous background synchronization loop every N seconds."""
    if not is_supabase_configured():
        logger.error("Supabase credentials not configured in .env (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY).")
        return

    client = get_supabase_client()
    if not client:
        logger.error("Could not initialize Supabase client.")
        return

    from website import create_app
    app = create_app()

    logger.info(f"Starting NEXGEN POS_V2 -> Supabase Sync Loop (Interval: {interval_seconds}s)...")
    
    while True:
        try:
            sync_all_data(client, app)
        except Exception as exc:
            logger.error(f"Sync iteration error: {exc}")
            
        logger.info(f"Sleeping for {interval_seconds}s until next sync cycle...")
        time.sleep(interval_seconds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="NEXGEN POS_V2 Supabase Sync Engine")
    parser.add_argument('--interval', type=int, default=30, help="Sync loop interval in seconds (default: 30)")
    parser.add_argument('--once', action='store_true', help="Run single one-shot sync and exit")
    args = parser.parse_args()

    if args.once:
        if not is_supabase_configured():
            logger.error("Supabase credentials not configured in .env.")
            sys.exit(1)
        client = get_supabase_client()
        from website import create_app
        app = create_app()
        sync_all_data(client, app)
    else:
        run_continuous_sync(interval_seconds=args.interval)
