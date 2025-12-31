-- Migration: Add contact tracking functionality
-- This migration adds recruiter contact fields to jobs table and creates contact_history table

-- Add recruiter contact fields to jobs table
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS recruiter_name VARCHAR(255);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS recruiter_email VARCHAR(255);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS recruiter_linkedin VARCHAR(500);

-- Create contact_history table for tracking all contact interactions
CREATE TABLE IF NOT EXISTS contact_history (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    contacted_at TIMESTAMP NOT NULL,
    contact_method VARCHAR(50) NOT NULL,  -- Email, LinkedIn, Phone, In-person, etc.
    message_content TEXT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index on job_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_contact_history_job_id ON contact_history(job_id);

-- Verify migration
SELECT 'Migration completed successfully!' as status;

-- Show added columns to jobs table
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'jobs'
  AND column_name IN ('recruiter_name', 'recruiter_email', 'recruiter_linkedin')
ORDER BY column_name;

-- Show contact_history table structure
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'contact_history'
ORDER BY ordinal_position;
