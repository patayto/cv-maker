-- Migration: Add enhanced features (Task 1)
-- This migration adds columns and tables for:
-- - Enhanced job parsing (skills, requirements, responsibilities)
-- - Salary tracking
-- - CV generation
-- - Cover letter generation
-- - Tax configuration

-- ============================================
-- 1. Add new columns to jobs table
-- ============================================

-- Add parsed job information columns
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS parsed_skills TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS parsed_requirements TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS parsed_responsibilities TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS experience_level VARCHAR(50);

-- Add salary tracking columns
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_min INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_max INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_currency VARCHAR(10);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS net_salary_yearly NUMERIC(10, 2);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS net_salary_monthly NUMERIC(10, 2);

-- Add foreign keys for generated content (will be added after creating tables)
-- ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cv_id INTEGER;
-- ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cover_letter_id INTEGER;


-- ============================================
-- 2. Create lego_blocks table
-- ============================================

CREATE TABLE IF NOT EXISTS lego_blocks (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    skills TEXT[],
    keywords TEXT[],
    strength_level INTEGER,
    role_types TEXT[],
    company_types TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster category lookups
CREATE INDEX IF NOT EXISTS idx_lego_blocks_category ON lego_blocks(category);


-- ============================================
-- 3. Create generated_cvs table
-- ============================================

CREATE TABLE IF NOT EXISTS generated_cvs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    selected_blocks INTEGER[],  -- Array of lego_block IDs
    customizations JSONB,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for job_id lookups
CREATE INDEX IF NOT EXISTS idx_generated_cvs_job_id ON generated_cvs(job_id);


-- ============================================
-- 4. Create generated_cover_letters table
-- ============================================

CREATE TABLE IF NOT EXISTS generated_cover_letters (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    template_used VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for job_id lookups
CREATE INDEX IF NOT EXISTS idx_generated_cover_letters_job_id ON generated_cover_letters(job_id);


-- ============================================
-- 5. Create tax_configs table
-- ============================================

CREATE TABLE IF NOT EXISTS tax_configs (
    id SERIAL PRIMARY KEY,
    tax_year INTEGER NOT NULL,
    country VARCHAR(2) NOT NULL,  -- ISO country code
    personal_allowance NUMERIC(10, 2),
    basic_rate NUMERIC(5, 2),
    higher_rate NUMERIC(5, 2),
    additional_rate NUMERIC(5, 2),
    thresholds JSONB,
    ni_rates JSONB,
    student_loan_config JSONB,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for active tax year lookups
CREATE INDEX IF NOT EXISTS idx_tax_configs_active ON tax_configs(tax_year, country, is_active);


-- ============================================
-- 6. Add foreign key columns to jobs table
-- ============================================

-- Now that generated_cvs and generated_cover_letters tables exist,
-- we can add the foreign key columns to jobs table
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cv_id INTEGER REFERENCES generated_cvs(id) ON DELETE SET NULL;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cover_letter_id INTEGER REFERENCES generated_cover_letters(id) ON DELETE SET NULL;


-- ============================================
-- 7. Insert default UK 2025/26 tax configuration
-- ============================================

INSERT INTO tax_configs (
    tax_year,
    country,
    personal_allowance,
    basic_rate,
    higher_rate,
    additional_rate,
    thresholds,
    ni_rates,
    student_loan_config,
    is_active
) VALUES (
    2025,
    'GB',
    12750.00,
    20.00,
    40.00,
    45.00,
    '{"basic": 50270, "higher": 125140}'::jsonb,
    '{"threshold": 12570, "rate_up_to_50270": 8.00, "rate_above_50270": 2.00}'::jsonb,
    '{"plan1": {"threshold": 24990, "rate": 9.00}, "plan2": {"threshold": 27295, "rate": 9.00}, "plan4": {"threshold": 31395, "rate": 9.00}}'::jsonb,
    1
)
ON CONFLICT DO NOTHING;


-- ============================================
-- Migration complete!
-- ============================================

-- Verify tables were created
SELECT 'Migration completed successfully!' as status;
SELECT 'Tables created:' as info;
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('lego_blocks', 'generated_cvs', 'generated_cover_letters', 'tax_configs')
ORDER BY table_name;

-- Verify new columns in jobs table
SELECT 'New columns in jobs table:' as info;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'jobs'
  AND column_name IN (
    'parsed_skills', 'parsed_requirements', 'parsed_responsibilities',
    'experience_level', 'salary_min', 'salary_max', 'salary_currency',
    'net_salary_yearly', 'net_salary_monthly',
    'generated_cv_id', 'generated_cover_letter_id'
  )
ORDER BY column_name;
