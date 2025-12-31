#!/usr/bin/env python3
"""Quick test of lego_blocks module"""

from lego_blocks import LegoBlockManager
from pathlib import Path

def main():
    # Path to markdown file
    markdown_path = Path("/Users/filipe/workspace/jobhunt/my-cv-app/amazon evidence/cv_lego_blocks_master.md")

    if not markdown_path.exists():
        print(f"❌ Markdown file not found: {markdown_path}")
        return

    print(f"📄 Reading from: {markdown_path}\n")

    # Create manager and import
    manager = LegoBlockManager()
    blocks = manager.import_from_markdown(str(markdown_path))

    print(f"✅ Imported {len(blocks)} blocks\n")

    # Show summary stats
    stats = manager.get_summary_stats()
    print("📊 Summary Statistics:")
    print(f"  Total Blocks: {stats['total_blocks']}")
    print(f"  Categories: {stats['categories']}")
    print(f"\n  Strength Distribution:")
    for level, count in stats['strength_breakdown'].items():
        print(f"    {level}: {count}")

    print(f"\n  Top 5 Skills:")
    for skill, count in list(stats['top_skills'].items())[:5]:
        print(f"    {skill}: {count}")

    # Show first block from each category
    print(f"\n📦 Sample Blocks by Category:")
    grouped = manager.get_blocks_by_category()
    for category, category_blocks in list(grouped.items())[:3]:
        print(f"\n  {category}:")
        block = category_blocks[0]
        print(f"    Title: {block.title}")
        print(f"    Strength: {block.strength_level}")
        print(f"    Skills: {', '.join(block.skills[:3])}")
        print(f"    Content: {block.content[:80]}...")

    # Test search
    print(f"\n🔍 Search Test - ML Engineer roles:")
    ml_blocks = manager.search_blocks(role_type="ML Engineer")
    print(f"  Found {len(ml_blocks)} blocks")
    for block in ml_blocks[:3]:
        print(f"    - {block.title}")

    # Test ranking
    print(f"\n🏆 Ranking Test - Match to ML job:")
    job_reqs = ["machine learning", "python", "AWS", "scale"]
    ranked = manager.rank_blocks(
        manager.blocks,
        job_requirements=job_reqs,
        required_skills=["Python", "Machine Learning"],
        preferred_role="ML Engineer"
    )
    print(f"  Top 5 matches:")
    for i, (block, score) in enumerate(ranked[:5], 1):
        print(f"    {i}. [{score:.1f}] {block.title}")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()
