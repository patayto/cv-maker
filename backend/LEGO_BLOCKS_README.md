# Lego Blocks Import System

The Lego Blocks system provides a structured way to manage, search, and rank CV achievements for tailored job applications.

## Overview

The system parses a markdown file (`cv_lego_blocks_master.md`) containing categorized achievements and converts them into structured `LegoBlock` objects that can be:
- Searched by skills, role type, category, or keywords
- Ranked by relevance to job requirements
- Filtered by strength level (essential, strong, good)
- Organized by category for easy browsing

## Files

### Core Module
- **`lego_blocks.py`** - Main module containing:
  - `LegoBlock` dataclass - Represents a single achievement
  - `LegoBlockManager` - Parser, search, and ranking engine

### Scripts
- **`scripts/import_lego_blocks.py`** - Import script with multiple output formats
- **`test_lego_blocks.py`** - Quick test/demo script

## Data Structure

Each `LegoBlock` contains:

```python
@dataclass
class LegoBlock:
    category: str              # e.g., "SYSTEM ARCHITECTURE & DESIGN"
    subcategory: Optional[str] # Optional subcategory
    title: str                 # Achievement title
    content: str               # The actual achievement text (bold text from markdown)
    skills: List[str]          # Extracted/inferred skills
    keywords: List[str]        # Technology terms, metrics, important keywords
    strength_level: str        # "essential", "strong", or "good"
    role_types: List[str]      # Suitable roles: ML Engineer, Backend, etc.
    company_types: List[str]   # Big Tech, Startup, etc.
```

## Markdown Format

The parser expects this format:

```markdown
## 🏗️ CATEGORY NAME

### Achievement Title
**The actual achievement content with metrics and details**

### Another Achievement
**More achievement content**

## 🤖 ANOTHER CATEGORY

### Achievement in this category
**Content here**
```

Key points:
- `## ` with optional emoji = category header
- `### ` = achievement title
- `**bold text**` = achievement content (what gets extracted)
- The parser automatically extracts keywords, infers skills, and determines strength levels

## Usage

### 1. Import Script

Basic usage (console output):
```bash
cd backend
python -m scripts.import_lego_blocks
```

JSON output:
```bash
python -m scripts.import_lego_blocks --output json --json-file lego_blocks.json
```

Custom file path:
```bash
python -m scripts.import_lego_blocks --file /path/to/cv_lego_blocks_master.md
```

With demonstrations:
```bash
python -m scripts.import_lego_blocks --demo-search --demo-rank
```

All options:
```bash
python -m scripts.import_lego_blocks --help
```

### 2. Quick Test

```bash
cd backend
python test_lego_blocks.py
```

### 3. Programmatic Usage

```python
from lego_blocks import LegoBlockManager

# Initialize manager
manager = LegoBlockManager()

# Import blocks from markdown
blocks = manager.import_from_markdown("/path/to/cv_lego_blocks_master.md")

# Search by role type
ml_blocks = manager.search_blocks(role_type="ML Engineer")

# Search by skills
python_blocks = manager.search_blocks(skills=["Python", "Machine Learning"])

# Search by category
arch_blocks = manager.search_blocks(category="SYSTEM ARCHITECTURE")

# Search essential blocks only
top_blocks = manager.search_blocks(strength_level="essential")

# Combine filters
senior_ml_blocks = manager.search_blocks(
    role_type="ML Engineer",
    strength_level="strong",
    skills=["Python", "TensorFlow"]
)

# Rank blocks for a job
job_requirements = ["machine learning", "python", "AWS", "scalability"]
ranked_blocks = manager.rank_blocks(
    blocks,
    job_requirements=job_requirements,
    required_skills=["Python", "Machine Learning"],
    preferred_role="ML Engineer"
)

# Top 10 matches
for block, score in ranked_blocks[:10]:
    print(f"[{score:.1f}] {block.title}")

# Get statistics
stats = manager.get_summary_stats()
print(f"Total blocks: {stats['total_blocks']}")
print(f"Categories: {stats['categories']}")

# Group by category
grouped = manager.get_blocks_by_category()
for category, blocks in grouped.items():
    print(f"{category}: {len(blocks)} blocks")
```

## Search & Ranking

### Search Filters

The `search_blocks()` method supports:
- **skills** - Match any skill in the list
- **role_type** - Filter by specific role
- **category** - Filter by category (partial match)
- **keywords** - Search in content and keywords
- **strength_level** - Minimum strength level

### Ranking Algorithm

The `rank_blocks()` method scores blocks based on:

1. **Job Requirements Match** (0-3 points per requirement)
   - In content: 3.0 points
   - In title: 2.0 points
   - In keywords: 1.5 points

2. **Required Skills Match** (0-2.5 points per skill)
   - In skills list: 2.5 points
   - In content: 1.5 points

3. **Role Type Match** (+2.0 points)
   - If preferred role matches block's role types

4. **Strength Level Boost**
   - Essential: +2.0 points
   - Strong: +1.0 points
   - Good: +0.5 points

5. **Keyword Density Bonus**
   - +0.5 points per matching requirement keyword

Results are sorted by total score (descending).

## Automatic Extraction & Inference

### Keyword Extraction
Automatically extracts:
- Technology terms (Java, Python, Spark, AWS, etc.)
- Acronyms (ML, AI, API, ETL, CI/CD, etc.)
- Metrics (1B+ users, $10M, 80%, etc.)
- Business terms (countries, engineers, services, etc.)

### Skill Inference
Skills are inferred from:
- Category-based defaults (each category has typical skills)
- Explicit technology mentions in content
- Context clues (e.g., "ML" → "Machine Learning")

### Role Type Inference
Role types are determined by:
- Category mapping (e.g., ML category → ML Engineer)
- Content analysis (mentions of "team", "led", "architected")
- Technology stack (full-stack indicators, ML mentions, etc.)

### Company Type Inference
Company types based on:
- Scale indicators (1B+, petabyte, international) → Big Tech
- Innovation keywords (0-to-1, MVP, sole engineer) → Startup
- Business metrics ($, revenue, cost savings) → Product-focused
- ML/AI content → ML/AI Company

### Strength Level Determination
Strength level scored on:
- Impact metrics (high numbers, dollar amounts)
- Leadership verbs (led, architected, built)
- Scope words (zero, 100%, complete)
- Score ranges: 5+ = essential, 3-4 = strong, 0-2 = good

## Integration with JobHunt Application

### Future Database Schema

```sql
CREATE TABLE lego_blocks (
    id SERIAL PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    subcategory VARCHAR(255),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    skills TEXT[],
    keywords TEXT[],
    strength_level VARCHAR(50),
    role_types TEXT[],
    company_types TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lego_blocks_category ON lego_blocks(category);
CREATE INDEX idx_lego_blocks_strength ON lego_blocks(strength_level);
CREATE INDEX idx_lego_blocks_skills ON lego_blocks USING GIN(skills);
CREATE INDEX idx_lego_blocks_role_types ON lego_blocks USING GIN(role_types);
```

### Integration with CV Generation

The Lego Blocks can be integrated with the existing `jobs` table workflow:

1. When a job is added, parse requirements from the job description
2. Use `rank_blocks()` to find the most relevant achievements
3. Present top-ranked blocks to the user for CV customization
4. Generate a tailored CV using selected blocks

Example flow:
```python
# Get job details
job = get_job(job_id)

# Parse job requirements (could use existing job_parser.py)
requirements = extract_requirements(job.notes)
required_skills = extract_skills(job.notes)

# Rank blocks
manager = LegoBlockManager()
manager.import_from_markdown("cv_lego_blocks_master.md")

ranked = manager.rank_blocks(
    manager.blocks,
    job_requirements=requirements,
    required_skills=required_skills,
    preferred_role=job.role
)

# Get top 10 achievements for this role
top_achievements = [block for block, score in ranked[:10]]

# Generate CV with these achievements
generate_cv(job, top_achievements)
```

## Example Output

### Console Output
```
================================================================================
LEGO BLOCKS IMPORT SUMMARY
================================================================================

Total Blocks: 67
Categories: 14

Strength Distribution:
  Essential: 15
  Strong: 28
  Good: 24

Top Skills:
  Machine Learning: 12
  System Design: 10
  Leadership: 9
  AWS: 8
  Python: 7

Top Role Types:
  Senior Engineer: 25
  ML Engineer: 18
  Backend Engineer: 15
  Staff Engineer: 12
  Full-Stack Engineer: 8
```

### JSON Output
```json
{
  "total_blocks": 67,
  "blocks": [
    {
      "category": "SYSTEM ARCHITECTURE & DESIGN",
      "subcategory": null,
      "title": "Predictive Demographics - Complete System Build",
      "content": "Architected and built complete predictive demographics backend system...",
      "skills": ["System Design", "Architecture", "Microservices", "Spark", "AWS"],
      "keywords": ["20TB+", "EMR", "Spark", "ML training", "1 applied scientist"],
      "strength_level": "essential",
      "role_types": ["Backend Engineer", "Software Engineer", "Systems Engineer", "Staff Engineer"],
      "company_types": ["Big Tech", "Startup", "Scale-up"]
    }
  ]
}
```

## Testing

Run the test script to verify functionality:

```bash
cd backend
python test_lego_blocks.py
```

This will:
1. Import all blocks from the markdown file
2. Display summary statistics
3. Show sample blocks from each category
4. Test search functionality
5. Test ranking functionality

## Customization Notes from Source File

The original markdown file includes customization notes for different roles:

### For ML Engineer Roles - Emphasize:
- ML System Cost Savings & Accuracy
- Multi-Model Strategy
- Model Voting Mechanism
- Shadow Pipeline Innovation
- International Scale

### For Backend Engineer Roles - Emphasize:
- System Architecture blocks
- Scale & Performance blocks
- DevOps & Operational Excellence
- Real-Time High-Throughput Monitoring

### For Full-Stack Roles - Emphasize:
- Full-Stack Development blocks
- Persona Builder
- Private Audiences Feature
- Both frontend and backend experience

### For Senior/Staff Roles - Emphasize:
- Technical Leadership & Mentoring
- Team Building & Scaling
- Cross-Functional Collaboration
- Principal Engineer Collaboration
- Subject Matter Expert Role

These customization notes can guide the ranking algorithm or be used to filter blocks programmatically.

## License

Part of the JobHunt CV Maker application.
