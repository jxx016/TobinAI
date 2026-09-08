-- Allow vendor_outreach rows to exist before SMS is sent (human approve gate).
-- New inserts set sent_at = NULL until POST /webhook/approve-outreach (or AUTO_OUTREACH=true).

ALTER TABLE vendor_outreach ALTER COLUMN sent_at DROP DEFAULT;
