"""
Import CV lego blocks from markdown file into the database.

This script reads cv_lego_blocks_master.md and imports the content into the lego_blocks table.
It's idempotent - safe to run multiple times (will skip duplicates based on title).

Usage:
    uv run python import_cv_data.py
"""

import re
from pathlib import Path
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, LegoBlock


def parse_markdown_file(file_path: str) -> list[dict]:
    """
    Parse the markdown file and extract lego blocks.

    Returns a list of dictionaries with:
    - category: The category name (from ## headers)
    - title: The block title (from ### headers)
    - content: The block content (bold text after title)
    - skills: Extracted keywords/skills from content
    """
    blocks = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_category = None
    current_title = None

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines, horizontal rules, and metadata
        if not line or line.startswith('---') or line.startswith('*Note:'):
            continue

        # Parse category (## headers with emoji)
        if line.startswith('## ') and not line.startswith('## Master'):
            # Remove emoji and clean category name
            category = re.sub(r'[🏗️🤖📊💰👥🤝🌍⚙️🚀💻📚💼🎓🔧📝🎯]', '', line[3:]).strip()
            # Skip metadata sections
            if category in ['NOTES ON CUSTOMIZATION', 'ACHIEVEMENT THEMES BY COMPANY TYPE']:
                current_category = None
            else:
                current_category = category
            continue

        # Parse title (### headers)
        if line.startswith('### ') and current_category:
            current_title = line[4:].strip()

            # Look ahead to next line for content (should be bold text)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # Extract content from bold markers
                if next_line.startswith('**') and next_line.endswith('**'):
                    content = next_line[2:-2].strip()

                    # Extract skills/keywords from content
                    skills = extract_skills(content)

                    blocks.append({
                        'category': current_category,
                        'title': current_title,
                        'content': content,
                        'skills': skills
                    })

    return blocks


def extract_skills(content: str) -> list[str]:
    """
    Extract technical skills and keywords from content.

    Simple extraction based on common patterns:
    - Technologies (Spark, EMR, ML, etc.)
    - Programming languages
    - AWS services
    - Common engineering terms
    """
    skills = set()

    # Common technical terms to look for
    tech_keywords = [
        'Spark', 'EMR', 'ML', 'Machine Learning', 'TensorFlow', 'Python', 'Java',
        'Kotlin', 'Scala', 'JavaScript', 'TypeScript', 'SQL', 'PostgreSQL',
        'AWS', 'S3', 'Lambda', 'DynamoDB', 'ElasticSearch', 'SageMaker',
        'API', 'REST', 'microservices', 'CI/CD', 'Docker', 'Kubernetes',
        'React', 'Spring', 'FastAPI', 'Django',
        'ETL', 'data pipeline', 'batch processing', 'real-time',
        'CloudFormation', 'CDK', 'Bootstrap', 'SpringMVC'
    ]

    content_lower = content.lower()

    for keyword in tech_keywords:
        if keyword.lower() in content_lower:
            skills.add(keyword)

    return sorted(list(skills))


def import_blocks(db: Session, blocks: list[dict]) -> tuple[int, int]:
    """
    Import lego blocks into the database.

    Returns:
        (inserted_count, skipped_count)
    """
    inserted = 0
    skipped = 0

    for block_data in blocks:
        # Check if block already exists (by title)
        existing = db.query(LegoBlock).filter(
            LegoBlock.title == block_data['title']
        ).first()

        if existing:
            skipped += 1
            continue

        # Create new lego block
        new_block = LegoBlock(
            category=block_data['category'],
            title=block_data['title'],
            content=block_data['content'],
            skills=block_data['skills'],
            keywords=block_data['skills'],  # Same as skills for now
        )

        db.add(new_block)
        inserted += 1

    db.commit()
    return inserted, skipped


def main():
    """Main import function."""
    # Path to markdown file (relative to project root)
    project_root = Path(__file__).parent.parent.parent
    md_file = project_root / "my-cv-app" / "amazon evidence" / "cv_lego_blocks_master.md"

    if not md_file.exists():
        print(f"Error: File not found: {md_file}")
        return

    print(f"Reading lego blocks from: {md_file}")

    # Parse markdown file
    blocks = parse_markdown_file(str(md_file))
    print(f"Parsed {len(blocks)} lego blocks from markdown file")

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Import blocks into database
    db = SessionLocal()
    try:
        inserted, skipped = import_blocks(db, blocks)
        print(f"\nImport complete:")
        print(f"  - Inserted: {inserted} new blocks")
        print(f"  - Skipped: {skipped} existing blocks")
        print(f"  - Total: {len(blocks)} blocks processed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
