-- Full database initialisation for Docker deployment
-- Runs once when the PostgreSQL volume is first created.
-- Subsequent starts skip this file; create_all() in main.py is a no-op.

-- Enum type (created explicitly because the SQLAlchemy model uses create_type=False)
DO $$ BEGIN
    CREATE TYPE application_status AS ENUM (
        'yet_to_apply',
        'applied_waiting',
        'job_offered',
        'job_accepted',
        'application_rejected',
        'job_rejected'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- jobs (base columns only — FK columns to generated_cvs / generated_cover_letters added below)
CREATE TABLE IF NOT EXISTS jobs (
    id                          SERIAL PRIMARY KEY,
    role                        VARCHAR(255),
    company                     VARCHAR(255),
    department                  VARCHAR(255),
    opening_date                DATE,
    closing_date                DATE,
    application_date            DATE,
    last_update                 DATE,
    status                      application_status,
    url                         TEXT,
    cv                          TEXT,
    cover_letter                TEXT,
    other_questions             TEXT,
    location                    VARCHAR(255),
    salary                      VARCHAR(255),
    notes                       TEXT,
    parsed_skills               TEXT[],
    parsed_requirements         TEXT[],
    parsed_responsibilities     TEXT[],
    experience_level            VARCHAR(50),
    salary_min                  INTEGER,
    salary_max                  INTEGER,
    salary_currency             VARCHAR(10),
    net_salary_yearly           NUMERIC(10, 2),
    net_salary_monthly          NUMERIC(10, 2),
    workplace_type              VARCHAR(50),
    employment_type             VARCHAR(50),
    recruiter_name              VARCHAR(255),
    recruiter_email             VARCHAR(255),
    recruiter_linkedin          VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_jobs_parsed_skills    ON jobs USING GIN(parsed_skills);
CREATE INDEX IF NOT EXISTS idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX IF NOT EXISTS idx_jobs_salary_range     ON jobs(salary_min, salary_max);

-- lego_blocks
CREATE TABLE IF NOT EXISTS lego_blocks (
    id              SERIAL PRIMARY KEY,
    category        VARCHAR(100) NOT NULL,
    subcategory     VARCHAR(100),
    title           VARCHAR(255) NOT NULL,
    content         TEXT NOT NULL,
    skills          TEXT[],
    keywords        TEXT[],
    strength_level  INTEGER,
    role_types      TEXT[],
    company_types   TEXT[],
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lego_blocks_category   ON lego_blocks(category);
CREATE INDEX IF NOT EXISTS idx_lego_blocks_role_types ON lego_blocks USING GIN(role_types);
CREATE INDEX IF NOT EXISTS idx_lego_blocks_skills     ON lego_blocks USING GIN(skills);

-- generated_cvs (references jobs)
CREATE TABLE IF NOT EXISTS generated_cvs (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    selected_blocks INTEGER[],
    customizations  JSONB,
    latex           TEXT,
    pdf_path        TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_generated_cvs_job_id ON generated_cvs(job_id);

-- generated_cover_letters (references jobs)
CREATE TABLE IF NOT EXISTS generated_cover_letters (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    template_used   VARCHAR(100),
    pdf_path        TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_generated_cover_letters_job_id ON generated_cover_letters(job_id);

-- Now safe to add circular FK columns back to jobs
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cv_id           INTEGER REFERENCES generated_cvs(id) ON DELETE SET NULL;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generated_cover_letter_id INTEGER REFERENCES generated_cover_letters(id) ON DELETE SET NULL;

-- tax_configs
CREATE TABLE IF NOT EXISTS tax_configs (
    id                  SERIAL PRIMARY KEY,
    tax_year            INTEGER NOT NULL,
    country             VARCHAR(2) NOT NULL,
    personal_allowance  NUMERIC(10, 2),
    basic_rate          NUMERIC(5, 2),
    higher_rate         NUMERIC(5, 2),
    additional_rate     NUMERIC(5, 2),
    thresholds          JSONB,
    ni_rates            JSONB,
    student_loan_config JSONB,
    is_active           INTEGER DEFAULT 1,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tax_year_country UNIQUE (tax_year, country, is_active)
);

CREATE INDEX IF NOT EXISTS idx_tax_configs_year_country ON tax_configs(tax_year, country);
CREATE INDEX IF NOT EXISTS idx_tax_configs_is_active    ON tax_configs(is_active);

-- contact_history
CREATE TABLE IF NOT EXISTS contact_history (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    contacted_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    contact_method  VARCHAR(50) NOT NULL,
    message_content TEXT,
    notes           TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contact_history_job_id ON contact_history(job_id);

-- Trigger: keep lego_blocks.updated_at current
CREATE OR REPLACE FUNCTION update_lego_blocks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_lego_blocks_updated_at ON lego_blocks;
CREATE TRIGGER trigger_lego_blocks_updated_at
    BEFORE UPDATE ON lego_blocks
    FOR EACH ROW EXECUTE FUNCTION update_lego_blocks_updated_at();

-- Seed: UK 2025/26 tax configuration
INSERT INTO tax_configs (
    tax_year, country, personal_allowance,
    basic_rate, higher_rate, additional_rate,
    thresholds, ni_rates, student_loan_config, is_active
) VALUES (
    2025, 'GB', 12570.00, 20.00, 40.00, 45.00,
    '{"basic": 50270, "higher": 125140}'::jsonb,
    '{"employee_primary": 12.00, "employee_upper": 2.00, "threshold_primary": 12570, "threshold_upper": 50270}'::jsonb,
    '{"plan_1_threshold": 22015, "plan_2_threshold": 27295, "plan_4_threshold": 27660, "postgrad_threshold": 21000, "repayment_rate": 9.00}'::jsonb,
    1
) ON CONFLICT (tax_year, country, is_active) DO NOTHING;
