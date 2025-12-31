#!/usr/bin/env python3
"""
Import Lego Blocks from markdown file into the application.

Usage:
    python -m scripts.import_lego_blocks [--output json|console|db] [--file PATH]

Options:
    --output: Output format (json, console, db). Default: console
    --file: Path to markdown file. Default: auto-detect cv_lego_blocks_master.md
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import List

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lego_blocks import LegoBlockManager, LegoBlock


def find_markdown_file() -> Path:
    """Auto-detect the cv_lego_blocks_master.md file in the workspace"""
    possible_paths = [
        # Relative to backend/scripts/
        Path(__file__).parent.parent.parent.parent / "my-cv-app" / "amazon evidence" / "cv_lego_blocks_master.md",
        # Absolute path based on workspace structure
        Path("/Users/filipe/workspace/jobhunt/my-cv-app/amazon evidence/cv_lego_blocks_master.md"),
        # Current directory
        Path("cv_lego_blocks_master.md"),
        # Parent directories
        Path("../cv_lego_blocks_master.md"),
        Path("../../cv_lego_blocks_master.md"),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find cv_lego_blocks_master.md. "
        "Please specify the path with --file option."
    )


def output_console(blocks: List[LegoBlock], manager: LegoBlockManager):
    """Output blocks to console with formatting"""
    print("\n" + "=" * 80)
    print("LEGO BLOCKS IMPORT SUMMARY")
    print("=" * 80)

    # Summary stats
    stats = manager.get_summary_stats()
    print(f"\nTotal Blocks: {stats['total_blocks']}")
    print(f"Categories: {stats['categories']}")
    print(f"\nStrength Distribution:")
    for level, count in stats['strength_breakdown'].items():
        print(f"  {level.capitalize()}: {count}")

    print(f"\nTop Skills:")
    for skill, count in list(stats['top_skills'].items())[:5]:
        print(f"  {skill}: {count}")

    print(f"\nTop Role Types:")
    for role, count in list(stats['top_role_types'].items())[:5]:
        print(f"  {role}: {count}")

    # Category breakdown
    print(f"\n{'=' * 80}")
    print("CATEGORY BREAKDOWN")
    print("=" * 80)

    grouped = manager.get_blocks_by_category()
    for category, category_blocks in grouped.items():
        print(f"\n{category} ({len(category_blocks)} blocks)")
        print("-" * 80)
        for block in category_blocks[:3]:  # Show first 3 per category
            print(f"\n  Title: {block.title}")
            print(f"  Strength: {block.strength_level}")
            print(f"  Skills: {', '.join(block.skills[:5])}")
            print(f"  Role Types: {', '.join(block.role_types[:3])}")
            print(f"  Content: {block.content[:100]}...")
        if len(category_blocks) > 3:
            print(f"\n  ... and {len(category_blocks) - 3} more blocks")

    print("\n" + "=" * 80)


def output_json(blocks: List[LegoBlock], output_file: str = None):
    """Output blocks to JSON file"""
    data = {
        "total_blocks": len(blocks),
        "blocks": [
            {
                "category": b.category,
                "subcategory": b.subcategory,
                "title": b.title,
                "content": b.content,
                "skills": b.skills,
                "keywords": b.keywords,
                "strength_level": b.strength_level,
                "role_types": b.role_types,
                "company_types": b.company_types,
            }
            for b in blocks
        ]
    }

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Exported {len(blocks)} blocks to {output_file}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def output_database(blocks: List[LegoBlock], manager: LegoBlockManager):
    """Output blocks to database (placeholder for future implementation)"""
    print("\n⚠️  Database output not yet implemented.")
    print("This would insert blocks into a PostgreSQL table.")
    print("\nSuggested schema:")
    print("""
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
    """)
    print(f"\nWould insert {len(blocks)} blocks.")


def demonstrate_search(manager: LegoBlockManager):
    """Demonstrate search capabilities"""
    print("\n" + "=" * 80)
    print("SEARCH DEMONSTRATIONS")
    print("=" * 80)

    # Search by role type
    print("\n1. Search for ML Engineer roles:")
    ml_blocks = manager.search_blocks(role_type="ML Engineer")
    print(f"   Found {len(ml_blocks)} blocks")
    for block in ml_blocks[:3]:
        print(f"   - {block.title}")

    # Search by skills
    print("\n2. Search for Python + Machine Learning:")
    skill_blocks = manager.search_blocks(skills=["Python", "Machine Learning"])
    print(f"   Found {len(skill_blocks)} blocks")
    for block in skill_blocks[:3]:
        print(f"   - {block.title}")

    # Search by category
    print("\n3. Search for System Architecture:")
    arch_blocks = manager.search_blocks(category="SYSTEM ARCHITECTURE")
    print(f"   Found {len(arch_blocks)} blocks")
    for block in arch_blocks[:3]:
        print(f"   - {block.title}")

    # Search essential blocks
    print("\n4. Search for essential strength blocks:")
    essential_blocks = manager.search_blocks(strength_level="essential")
    print(f"   Found {len(essential_blocks)} blocks")
    for block in essential_blocks[:5]:
        print(f"   - {block.title} (Category: {block.category})")


def demonstrate_ranking(manager: LegoBlockManager):
    """Demonstrate ranking capabilities"""
    print("\n" + "=" * 80)
    print("RANKING DEMONSTRATION")
    print("=" * 80)

    # Simulate a job description
    job_requirements = [
        "machine learning",
        "python",
        "distributed systems",
        "leadership",
        "AWS",
        "team building",
        "scalability"
    ]

    print("\nSimulated Job Requirements:")
    for req in job_requirements:
        print(f"  - {req}")

    # Rank all blocks
    ranked = manager.rank_blocks(
        manager.blocks,
        job_requirements=job_requirements,
        required_skills=["Python", "Machine Learning", "AWS"],
        preferred_role="ML Engineer"
    )

    print(f"\nTop 10 Matching Blocks:")
    print("-" * 80)
    for i, (block, score) in enumerate(ranked[:10], 1):
        print(f"{i}. [{score:.1f}] {block.title}")
        print(f"   Category: {block.category}")
        print(f"   Skills: {', '.join(block.skills[:4])}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Import Lego Blocks from markdown file",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--output',
        choices=['console', 'json', 'db'],
        default='console',
        help='Output format (default: console)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to cv_lego_blocks_master.md file'
    )
    parser.add_argument(
        '--json-file',
        type=str,
        help='Output JSON file path (when using --output json)'
    )
    parser.add_argument(
        '--demo-search',
        action='store_true',
        help='Run search demonstrations'
    )
    parser.add_argument(
        '--demo-rank',
        action='store_true',
        help='Run ranking demonstration'
    )

    args = parser.parse_args()

    try:
        # Find markdown file
        if args.file:
            markdown_path = Path(args.file)
            if not markdown_path.exists():
                print(f"Error: File not found: {markdown_path}")
                sys.exit(1)
        else:
            try:
                markdown_path = find_markdown_file()
                print(f"Found markdown file: {markdown_path}")
            except FileNotFoundError as e:
                print(f"Error: {e}")
                sys.exit(1)

        # Import blocks
        print(f"\nImporting blocks from: {markdown_path}")
        manager = LegoBlockManager()
        blocks = manager.import_from_markdown(str(markdown_path))

        if not blocks:
            print("Warning: No blocks imported. Check the file format.")
            sys.exit(1)

        print(f"✓ Successfully imported {len(blocks)} blocks")

        # Output based on format
        if args.output == 'console':
            output_console(blocks, manager)
        elif args.output == 'json':
            output_json(blocks, args.json_file)
        elif args.output == 'db':
            output_database(blocks, manager)

        # Run demonstrations if requested
        if args.demo_search:
            demonstrate_search(manager)

        if args.demo_rank:
            demonstrate_ranking(manager)

        print("\n✓ Import completed successfully!\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
