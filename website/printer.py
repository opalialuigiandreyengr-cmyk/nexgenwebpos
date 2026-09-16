"""NEXGEN Web POS — Cloud Mock Printer Module.

Provides no-op stubs for printing operations in cloud/web hosting environments.
"""

import logging

logger = logging.getLogger(__name__)

class DummyPrinterManager:
    def __init__(self, name="Cloud Dummy Printer"):
        self.name = name
        self.usb_enabled = False
        self.usb_vendor_id = 0
        self.usb_product_id = 0

    def is_connected(self):
        return False

    def get_status(self):
        return {"connected": False, "status": "Cloud Mode", "connection_type": "none"}

    def has_usb_fallback_available(self):
        return False

    def _usb_connection_candidates(self):
        return []

_cashier_printer_manager = DummyPrinterManager("Cashier")
_kitchen_printer_manager = DummyPrinterManager("Kitchen")

def invalidate_printer_discovery():
    pass

def save_discovered_printer_config(*args, **kwargs):
    pass

def print_receipt(*args, **kwargs):
    logger.info("Print receipt called in cloud admin mode (no physical printer).")
    return False

def print_kitchen_ticket(*args, **kwargs):
    return False

def print_z_reading(*args, **kwargs):
    return False

def print_x_reading(*args, **kwargs):
    return False

def open_cash_drawer(*args, **kwargs):
    return False

def print_item_sales_report(*args, **kwargs):
    return False

def print_takeout_pickup_delivery_report(*args, **kwargs):
    return False

def print_cancelled_void_refund_report(*args, **kwargs):
    return False

def print_cashier_accountability(*args, **kwargs):
    return False

def print_customer_bill(*args, **kwargs):
    return False

def reprint_invoice(*args, **kwargs):
    return False

def print_void_order(*args, **kwargs):
    return False

def get_printer_status():
    return {
        "success": True,
        "cashier": {"connected": False, "message": "Cloud Admin Mode"},
        "kitchen": {"connected": False, "message": "Cloud Admin Mode"}
    }
