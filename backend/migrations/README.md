# Database Migrations

This directory contains SQL migration scripts for the JobHunt application database schema.

## Running Migrations

To apply the migration to your database, connect to PostgreSQL and run:

```bash
psql -d cv_maker_db -f 001_add_jobhunt_tables.sql
```

Or from within a PostgreSQL session:

```sql
\i /Users/filipe/workspace/jobhunt/cv_maker/backend/migrations/001_add_jobhunt_tables.sql
```

## Migration: 001_add_jobhunt_tables.sql

**Date:** 2025-12-21

**Description:** Adds new tables and extends the jobs table with enhanced features for the JobHunt application.

### New Tables Created

1. **lego_blocks** - Reusable CV content blocks
   - Stores modular content pieces that can be combined to create customized CVs
   - Includes categorization, skills tagging, and role/company type filtering

2. **generated_cvs** - CV generation tracking
   - Links to specific job applications
   - Stores which lego blocks were used
   - Tracks custom modifications and PDF output

3. **generated_cover_letters** - Cover letter tracking
   - Links to specific job applications
   - Stores generated content and template used

4. **tax_configs** - Tax calculation parameters
   - Stores tax rates, thresholds, and NI rates by year and country
   - Enables net salary calculations from gross salary

### Jobs Table Extensions

New columns added to the existing `jobs` table:

**Parsed Job Data:**
- `parsed_skills` - Array of skills extracted from job posting
- `parsed_requirements` - Array of requirements
- `parsed_responsibilities` - Array of responsibilities

**Salary Information:**
- `experience_level` - Job seniority level
- `salary_min` / `salary_max` - Salary range boundaries
- `salary_currency` - Currency code (e.g., GBP, USD)
- `net_salary_yearly` / `net_salary_monthly` - Calculated net salaries

**Relationships:**
- `generated_cv_id` - Foreign key to generated_cvs
- `generated_cover_letter_id` - Foreign key to generated_cover_letters

### Sample Data

The migration includes sample UK tax configuration for 2025/26 tax year with:
- Personal allowance: £12,570
- Tax rates: 20% (basic), 40% (higher), 45% (additional)
- National Insurance rates and thresholds
- Student loan repayment thresholds

## Rollback

If you need to undo this migration:

```sql
-- Drop new tables
DROP TABLE IF EXISTS tax_configs CASCADE;
DROP TABLE IF EXISTS generated_cover_letters CASCADE;
DROP TABLE IF EXISTS generated_cvs CASCADE;
DROP TABLE IF EXISTS lego_blocks CASCADE;

-- Remove new columns from jobs table
ALTER TABLE jobs
  DROP COLUMN IF EXISTS parsed_skills,
  DROP COLUMN IF EXISTS parsed_requirements,
  DROP COLUMN IF EXISTS parsed_responsibilities,
  DROP COLUMN IF EXISTS experience_level,
  DROP COLUMN IF EXISTS salary_min,
  DROP COLUMN IF EXISTS salary_max,
  DROP COLUMN IF EXISTS salary_currency,
  DROP COLUMN IF EXISTS net_salary_yearly,
  DROP COLUMN IF EXISTS net_salary_monthly,
  DROP COLUMN IF EXISTS generated_cv_id,
  DROP COLUMN IF EXISTS generated_cover_letter_id;

-- Drop the trigger and function
DROP TRIGGER IF EXISTS trigger_lego_blocks_updated_at ON lego_blocks;
DROP FUNCTION IF EXISTS update_lego_blocks_updated_at();
```

## Notes

- All new tables use `SERIAL` for auto-incrementing primary keys
- Appropriate foreign key constraints are set with `ON DELETE CASCADE` or `ON DELETE SET NULL`
- GIN indexes are created for array columns to enable efficient searches
- A trigger automatically updates the `updated_at` timestamp on lego_blocks
- The migration is idempotent - it can be run multiple times safely using `IF NOT EXISTS` clauses
