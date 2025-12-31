-- Migration: Add workplace_type and employment_type columns
-- These fields track remote/hybrid/on-site status and full-time/part-time/contract type

-- Add workplace_type column (Remote, Hybrid, On-site)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS workplace_type VARCHAR(50);

-- Add employment_type column (Full-time, Part-time, Contract, Temporary, Internship, Volunteer)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS employment_type VARCHAR(50);

-- Verify columns were added
SELECT 'Migration completed successfully!' as status;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'jobs'
  AND column_name IN ('workplace_type', 'employment_type')
ORDER BY column_name;
