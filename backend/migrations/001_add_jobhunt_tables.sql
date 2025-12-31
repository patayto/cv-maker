-- Migration: 001_add_jobhunt_tables.sql
-- Description: Add new tables and columns for JobHunt application
-- Date: 2025-12-21

-- ========================================
-- PART 1: Create new tables
-- ========================================

-- Table: lego_blocks
-- Purpose: Store reusable CV content blocks for customizable CV generation
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

-- Add index for category searches
CREATE INDEX idx_lego_blocks_category ON lego_blocks(category);
CREATE INDEX idx_lego_blocks_role_types ON lego_blocks USING GIN(role_types);
CREATE INDEX idx_lego_blocks_skills ON lego_blocks USING GIN(skills);


-- Table: generated_cvs
-- Purpose: Track CV versions created for specific job applications
CREATE TABLE IF NOT EXISTS generated_cvs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    selected_blocks INTEGER[],
    customizations JSONB,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for job lookups
CREATE INDEX idx_generated_cvs_job_id ON generated_cvs(job_id);


-- Table: generated_cover_letters
-- Purpose: Track cover letters generated for specific job applications
CREATE TABLE IF NOT EXISTS generated_cover_letters (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    template_used VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for job lookups
CREATE INDEX idx_generated_cover_letters_job_id ON generated_cover_letters(job_id);


-- Table: tax_configs
-- Purpose: Store tax calculation parameters for net salary calculations
CREATE TABLE IF NOT EXISTS tax_configs (
    id SERIAL PRIMARY KEY,
    tax_year INTEGER NOT NULL,
    country VARCHAR(2) NOT NULL,
    personal_allowance NUMERIC(10, 2),
    basic_rate NUMERIC(5, 2),
    higher_rate NUMERIC(5, 2),
    additional_rate NUMERIC(5, 2),
    thresholds JSONB,
    ni_rates JSONB,
    student_loan_config JSONB,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tax_year_country UNIQUE (tax_year, country, is_active)
);

-- Add indexes for tax config lookups
CREATE INDEX idx_tax_configs_year_country ON tax_configs(tax_year, country);
CREATE INDEX idx_tax_configs_is_active ON tax_configs(is_active);


-- ========================================
-- PART 2: Extend jobs table with new columns
-- ========================================

-- Add parsed job data columns
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS parsed_skills TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS parsed_requirements TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS parsed_responsibilities TEXT[];

-- Add structured salary information
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS experience_level VARCHAR(50);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_min INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_max INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_currency VARCHAR(10);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS net_salary_yearly NUMERIC(10, 2);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS net_salary_monthly NUMERIC(10, 2);

-- Add foreign keys to generated CVs and cover letters
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cv_id INTEGER REFERENCES generated_cvs(id) ON DELETE SET NULL;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cover_letter_id INTEGER REFERENCES generated_cover_letters(id) ON DELETE SET NULL;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_jobs_parsed_skills ON jobs USING GIN(parsed_skills);
CREATE INDEX IF NOT EXISTS idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX IF NOT EXISTS idx_jobs_salary_range ON jobs(salary_min, salary_max);


-- ========================================
-- PART 3: Add comments for documentation
-- ========================================

COMMENT ON TABLE lego_blocks IS 'Reusable CV content blocks for customizable CV generation';
COMMENT ON COLUMN lego_blocks.category IS 'Main category (e.g., Experience, Skills, Education)';
COMMENT ON COLUMN lego_blocks.subcategory IS 'Optional subcategory for finer organization';
COMMENT ON COLUMN lego_blocks.strength_level IS 'Content strength rating from 1-5';
COMMENT ON COLUMN lego_blocks.role_types IS 'Types of roles this block is relevant for (e.g., backend, fullstack)';
COMMENT ON COLUMN lego_blocks.company_types IS 'Types of companies this block is relevant for (e.g., startup, enterprise)';

COMMENT ON TABLE generated_cvs IS 'Tracks CV versions created for specific job applications';
COMMENT ON COLUMN generated_cvs.selected_blocks IS 'Array of lego_block IDs used in this CV';
COMMENT ON COLUMN generated_cvs.customizations IS 'JSON object storing any custom modifications';

COMMENT ON TABLE generated_cover_letters IS 'Tracks cover letters generated for job applications';
COMMENT ON TABLE tax_configs IS 'Tax calculation parameters for net salary calculations';
COMMENT ON COLUMN tax_configs.country IS 'ISO 3166-1 alpha-2 country code';
COMMENT ON COLUMN tax_configs.is_active IS 'Boolean flag: 1=active, 0=inactive';

COMMENT ON COLUMN jobs.parsed_skills IS 'Skills extracted from job posting';
COMMENT ON COLUMN jobs.parsed_requirements IS 'Requirements extracted from job posting';
COMMENT ON COLUMN jobs.parsed_responsibilities IS 'Responsibilities extracted from job posting';
COMMENT ON COLUMN jobs.experience_level IS 'Experience level required (e.g., Junior, Mid, Senior)';
COMMENT ON COLUMN jobs.net_salary_yearly IS 'Calculated net yearly salary after tax';
COMMENT ON COLUMN jobs.net_salary_monthly IS 'Calculated net monthly salary after tax';


-- ========================================
-- PART 4: Create trigger for updating lego_blocks.updated_at
-- ========================================

CREATE OR REPLACE FUNCTION update_lego_blocks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_lego_blocks_updated_at
    BEFORE UPDATE ON lego_blocks
    FOR EACH ROW
    EXECUTE FUNCTION update_lego_blocks_updated_at();


-- ========================================
-- PART 5: Insert sample tax configuration for UK 2025/26
-- ========================================

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
    12570.00,
    20.00,
    40.00,
    45.00,
    '{"basic": 50270, "higher": 125140}'::jsonb,
    '{"employee_primary": 12.00, "employee_upper": 2.00, "threshold_primary": 12570, "threshold_upper": 50270}'::jsonb,
    '{"plan_1_threshold": 22015, "plan_2_threshold": 27295, "plan_4_threshold": 27660, "postgrad_threshold": 21000, "repayment_rate": 9.00}'::jsonb,
    1
) ON CONFLICT (tax_year, country, is_active) DO NOTHING;


-- ========================================
-- Migration complete
-- ========================================
