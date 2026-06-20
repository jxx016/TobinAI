-- Run this in Supabase SQL editor to add the vendor_outreach table

CREATE TABLE IF NOT EXISTS vendor_outreach (
  id              SERIAL PRIMARY KEY,
  request_id      TEXT REFERENCES maintenance_requests(request_id) ON DELETE CASCADE,
  vendor_phone    TEXT NOT NULL,
  vendor_name     TEXT,
  source          TEXT DEFAULT 'google_places', -- 'database' or 'google_places'
  place_id        TEXT,
  sent_at         TIMESTAMPTZ DEFAULT NOW(),
  replied_at      TIMESTAMPTZ,
  accepted        BOOLEAN,
  UNIQUE (request_id, vendor_phone)
);

CREATE INDEX IF NOT EXISTS idx_vendor_outreach_request ON vendor_outreach(request_id);
CREATE INDEX IF NOT EXISTS idx_vendor_outreach_phone ON vendor_outreach(vendor_phone);
