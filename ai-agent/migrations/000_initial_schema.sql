-- ============================================================
-- TobinAI - Full Schema
-- Run this in Supabase SQL Editor
-- ============================================================

-- Vendors table
CREATE TABLE IF NOT EXISTS vendors (
  id              SERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  phone           TEXT,
  email           TEXT,
  specialty       TEXT NOT NULL, -- hvac, plumbing, electrical, general
  rating          NUMERIC(3,1) DEFAULT 5.0,
  hourly_rate     NUMERIC(8,2),
  is_primary      BOOLEAN DEFAULT false,
  is_active       BOOLEAN DEFAULT true,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Maintenance requests table
CREATE TABLE IF NOT EXISTS maintenance_requests (
  id                  SERIAL PRIMARY KEY,
  request_id          TEXT UNIQUE NOT NULL,
  tenant_name         TEXT,
  tenant_phone        TEXT,
  property_address    TEXT,
  apartment_unit      TEXT,
  issue_description   TEXT,
  category            TEXT,
  urgency             TEXT,
  summary             TEXT,
  handyman_notes      TEXT,
  requires_photos     BOOLEAN DEFAULT false,
  estimated_time      TEXT,
  status              TEXT DEFAULT 'pending',
  ai_processed_at     TIMESTAMPTZ,
  vendor_assigned_at  TIMESTAMPTZ,
  last_updated_at     TIMESTAMPTZ DEFAULT NOW(),
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor outreach tracking
CREATE TABLE IF NOT EXISTS vendor_outreach (
  id              SERIAL PRIMARY KEY,
  request_id      TEXT REFERENCES maintenance_requests(request_id) ON DELETE CASCADE,
  vendor_phone    TEXT NOT NULL,
  vendor_name     TEXT,
  source          TEXT DEFAULT 'google_places',
  place_id        TEXT,
  sent_at         TIMESTAMPTZ DEFAULT NOW(),
  replied_at      TIMESTAMPTZ,
  accepted        BOOLEAN,
  UNIQUE (request_id, vendor_phone)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_requests_request_id ON maintenance_requests(request_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON maintenance_requests(status);
CREATE INDEX IF NOT EXISTS idx_vendors_specialty ON vendors(specialty);
CREATE INDEX IF NOT EXISTS idx_outreach_request ON vendor_outreach(request_id);
CREATE INDEX IF NOT EXISTS idx_outreach_phone ON vendor_outreach(vendor_phone);

-- Sample vendors (optional - delete if you have real ones)
INSERT INTO vendors (name, phone, email, specialty, rating, is_primary, is_active) VALUES
  ('Mike HVAC Services',     '+15551234567', 'mike@hvac.com',     'hvac',       4.8, true,  true),
  ('City Plumbing Co',       '+15552345678', 'info@cityplumb.com','plumbing',   4.7, true,  true),
  ('Bright Electric',        '+15553456789', 'jobs@brightelec.com','electrical', 4.9, true,  true),
  ('All-Around Handyman',    '+15554567890', 'fix@allround.com',  'general',    4.6, true,  true)
ON CONFLICT DO NOTHING;
