-- ============================================================================
-- NEXGEN Web POS & POS_V2 — Complete Supabase PostgreSQL Database Schema
-- ----------------------------------------------------------------------------
-- Instructions:
-- 1. Open your Supabase Project: https://supabase.com/dashboard/project/qvgsbywlzjfkmgvkyauv
-- 2. Go to the "SQL Editor" on the left navigation bar.
-- 3. Paste this complete SQL script and click "Run".
-- ============================================================================

-- 1. Users table
CREATE TABLE IF NOT EXISTS public.users (
    id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    full_name TEXT,
    email TEXT,
    password_hash TEXT,
    role TEXT DEFAULT 'cashier',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Categories table
CREATE TABLE IF NOT EXISTS public.categories (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#3b82f6',
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Products table
CREATE TABLE IF NOT EXISTS public.products (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    category TEXT,
    status TEXT DEFAULT 'active',
    is_barcode_active BOOLEAN DEFAULT FALSE,
    barcode TEXT,
    uom TEXT DEFAULT 'pcs',
    raw_material_category TEXT,
    cost NUMERIC(12,2) DEFAULT 0.00,
    image_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Orders table
CREATE TABLE IF NOT EXISTS public.orders (
    id BIGINT PRIMARY KEY,
    order_no TEXT NOT NULL,
    invoice_no TEXT,
    customer_name TEXT,
    order_type TEXT DEFAULT 'dinein',
    status TEXT DEFAULT 'completed',
    tables TEXT,
    subtotal NUMERIC(12,2) DEFAULT 0.00,
    vat NUMERIC(12,2) DEFAULT 0.00,
    discount NUMERIC(12,2) DEFAULT 0.00,
    total NUMERIC(12,2) DEFAULT 0.00,
    reprint_count INT DEFAULT 0,
    timestamp TIMESTAMPTZ,
    crew_id INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    synced_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Order Items table
CREATE TABLE IF NOT EXISTS public.order_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT REFERENCES public.orders(id) ON DELETE CASCADE,
    product_id BIGINT,
    product_name TEXT NOT NULL,
    quantity NUMERIC(12,3) NOT NULL DEFAULT 1,
    price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    modifier TEXT,
    timestamp TIMESTAMPTZ
);

-- 6. Settlements table
CREATE TABLE IF NOT EXISTS public.settlements (
    id BIGINT PRIMARY KEY,
    order_id BIGINT REFERENCES public.orders(id) ON DELETE CASCADE,
    payment_method TEXT NOT NULL,
    card_type TEXT,
    cash_received NUMERIC(12,2),
    gift_check_amount NUMERIC(12,2),
    gift_check_number TEXT,
    cheque_amount NUMERIC(12,2),
    cheque_number TEXT,
    final_total NUMERIC(12,2) DEFAULT 0.00,
    tax_exempt_amount NUMERIC(12,2) DEFAULT 0.00,
    discount_amount NUMERIC(12,2) DEFAULT 0.00,
    vat_sales NUMERIC(12,2) DEFAULT 0.00,
    vat_exempt_sale NUMERIC(12,2) DEFAULT 0.00,
    zero_rated_sales NUMERIC(12,2) DEFAULT 0.00,
    total_sale NUMERIC(12,2) DEFAULT 0.00,
    vat_amount NUMERIC(12,2) DEFAULT 0.00,
    amount_due NUMERIC(12,2) DEFAULT 0.00,
    order_discount_type TEXT,
    regular_discount_percent NUMERIC(5,2),
    oth_discount_amount NUMERIC(12,2),
    discount_quantity INT,
    discount_name TEXT,
    discount_id TEXT,
    total_no_pax INT DEFAULT 1,
    discount_breakdown TEXT,
    cashier_id INT,
    manual_si_number TEXT,
    timestamp TIMESTAMPTZ
);

-- 7. Activity Logs table
CREATE TABLE IF NOT EXISTS public.activity_logs (
    id BIGINT PRIMARY KEY,
    user_id INT,
    event_type TEXT,
    description TEXT,
    order_id BIGINT,
    trxn_no TEXT,
    details TEXT,
    reference_no TEXT,
    date_range TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Order Audit Logs table
CREATE TABLE IF NOT EXISTS public.order_audit_logs (
    id BIGINT PRIMARY KEY,
    order_id BIGINT REFERENCES public.orders(id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    original_quantity NUMERIC(12,3) DEFAULT 0,
    modified_qty NUMERIC(12,3) DEFAULT 0,
    price NUMERIC(12,2) DEFAULT 0.00,
    reason TEXT,
    reference_no TEXT,
    event_type TEXT DEFAULT 'Void',
    cashier_id INT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Recipe & Raw Material Ingredients table
CREATE TABLE IF NOT EXISTS public.product_recipe_ingredient (
    id BIGINT PRIMARY KEY,
    product_id BIGINT DEFAULT 0,
    product_name TEXT NOT NULL,
    raw_material_name TEXT NOT NULL,
    consumed_quantity NUMERIC(12,4) DEFAULT 0,
    uom TEXT DEFAULT '',
    category TEXT DEFAULT '',
    raw_material_code TEXT DEFAULT ''
);

-- 10. Receipt Settings table
CREATE TABLE IF NOT EXISTS public.receipt_settings (
    id BIGINT PRIMARY KEY,
    store_name TEXT,
    address TEXT,
    tin TEXT,
    min_number TEXT,
    serial_number TEXT,
    pos_number TEXT,
    header_text TEXT,
    footer_text TEXT,
    vat_reg_tin TEXT,
    accreditation_no TEXT,
    date_issued TEXT,
    valid_until TEXT,
    ptu_no TEXT
);

-- 11. RLC SFTP Settings table
CREATE TABLE IF NOT EXISTS public.rlc_settings (
    id BIGINT PRIMARY KEY,
    is_active BOOLEAN DEFAULT FALSE,
    host TEXT,
    port INT DEFAULT 22,
    username TEXT,
    password TEXT,
    tenant_code TEXT,
    transfer_time TEXT
);

-- ============================================================================
-- Indexes for Ultra-Fast Query Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_orders_status_timestamp ON public.orders(status, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orders_order_no ON public.orders(order_no);
CREATE INDEX IF NOT EXISTS idx_orders_invoice_no ON public.orders(invoice_no);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON public.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_settlements_order_id ON public.settlements(order_id);
CREATE INDEX IF NOT EXISTS idx_settlements_timestamp ON public.settlements(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON public.activity_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_order_audit_logs_order_id ON public.order_audit_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON public.products(category);
CREATE INDEX IF NOT EXISTS idx_products_status ON public.products(status);

-- ============================================================================
-- Row Level Security (RLS) Configuration
-- ============================================================================
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_recipe_ingredient ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.receipt_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rlc_settings ENABLE ROW LEVEL SECURITY;

DO $$ 
DECLARE
    tbl text;
BEGIN
    FOR tbl IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS "Full Access for Service Role" ON public.%I', tbl);
        EXECUTE format('CREATE POLICY "Full Access for Service Role" ON public.%I FOR ALL TO service_role USING (true) WITH CHECK (true)', tbl);
        EXECUTE format('DROP POLICY IF EXISTS "Public Read Access" ON public.%I', tbl);
        EXECUTE format('CREATE POLICY "Public Read Access" ON public.%I FOR SELECT TO anon, authenticated USING (true)', tbl);
    END LOOP;
END $$;
