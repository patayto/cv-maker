from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import re
from collections import defaultdict


@dataclass
class LegoBlock:
    """Represents a single achievement block from the CV library"""
    category: str
    subcategory: Optional[str]
    title: str
    content: str
    skills: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    strength_level: str = "good"  # essential, strong, good
    role_types: List[str] = field(default_factory=list)  # ML Engineer, Backend, Full-Stack, etc.
    company_types: List[str] = field(default_factory=list)  # Big Tech, Startup, etc.

    def __repr__(self):
        return f"LegoBlock(category='{self.category}', title='{self.title[:50]}...')"


class LegoBlockManager:
    """Manager class for parsing, searching, and ranking Lego Blocks"""

    # Category-based skill inference
    CATEGORY_SKILLS = {
        "SYSTEM ARCHITECTURE & DESIGN": ["System Design", "Architecture", "Microservices", "API Design", "Distributed Systems"],
        "MACHINE LEARNING & DATA SCIENCE": ["Machine Learning", "ML", "Data Science", "Model Training", "Python", "TensorFlow", "Spark"],
        "SCALE & PERFORMANCE": ["Scalability", "Performance", "High Traffic", "Optimization", "Distributed Systems"],
        "COST OPTIMIZATION & BUSINESS IMPACT": ["Cost Optimization", "Business Impact", "ROI", "Resource Planning"],
        "TECHNICAL LEADERSHIP & MENTORING": ["Leadership", "Mentoring", "Team Building", "Coaching", "Management"],
        "CROSS-FUNCTIONAL COLLABORATION": ["Collaboration", "Communication", "Cross-team", "Stakeholder Management"],
        "INTERNATIONAL EXPANSION & REGULATORY COMPLIANCE": ["International", "Compliance", "GDPR", "Regulatory", "Localization"],
        "DEVOPS & OPERATIONAL EXCELLENCE": ["DevOps", "CI/CD", "CloudFormation", "Infrastructure", "On-Call", "Monitoring"],
        "INNOVATION & EXPERIMENTATION": ["Innovation", "Experimentation", "A/B Testing", "Research"],
        "FULL-STACK DEVELOPMENT": ["Full-Stack", "Frontend", "Backend", "JavaScript", "Java", "React", "UI/UX"],
        "EARLY CAREER & FOUNDATION": ["Internship", "Early Career", "Algorithm", "Research"],
        "LEADERSHIP & PROFESSIONAL SKILLS": ["Leadership", "Training", "Documentation", "Communication"],
        "EDUCATION & ACADEMIC EXCELLENCE": ["Education", "Computer Science", "Academic"],
        "TECHNICAL SKILLS EVIDENCE": ["Programming", "Languages", "Frameworks", "Tools"],
    }

    # Category-based role type inference
    CATEGORY_ROLE_TYPES = {
        "SYSTEM ARCHITECTURE & DESIGN": ["Backend Engineer", "Software Engineer", "Systems Engineer", "Staff Engineer"],
        "MACHINE LEARNING & DATA SCIENCE": ["ML Engineer", "Data Scientist", "ML/AI Engineer", "Research Engineer"],
        "SCALE & PERFORMANCE": ["Backend Engineer", "Performance Engineer", "Infrastructure Engineer", "Staff Engineer"],
        "COST OPTIMIZATION & BUSINESS IMPACT": ["Senior Engineer", "Staff Engineer", "Tech Lead", "Product Engineer"],
        "TECHNICAL LEADERSHIP & MENTORING": ["Senior Engineer", "Staff Engineer", "Tech Lead", "Engineering Manager"],
        "CROSS-FUNCTIONAL COLLABORATION": ["Product Engineer", "Tech Lead", "Senior Engineer"],
        "INTERNATIONAL EXPANSION & REGULATORY COMPLIANCE": ["Senior Engineer", "Staff Engineer", "Compliance Engineer"],
        "DEVOPS & OPERATIONAL EXCELLENCE": ["DevOps Engineer", "SRE", "Platform Engineer", "Infrastructure Engineer"],
        "INNOVATION & EXPERIMENTATION": ["Research Engineer", "Senior Engineer", "Product Engineer"],
        "FULL-STACK DEVELOPMENT": ["Full-Stack Engineer", "Product Engineer", "Software Engineer"],
        "EARLY CAREER & FOUNDATION": ["Software Engineer", "Junior Engineer"],
        "LEADERSHIP & PROFESSIONAL SKILLS": ["Senior Engineer", "Staff Engineer", "Tech Lead"],
        "EDUCATION & ACADEMIC EXCELLENCE": ["Software Engineer", "ML Engineer", "Research Engineer"],
        "TECHNICAL SKILLS EVIDENCE": ["Software Engineer", "Backend Engineer", "ML Engineer", "Full-Stack Engineer"],
    }

    def __init__(self, db_session=None):
        self.db = db_session
        self.blocks: List[LegoBlock] = []

    def import_from_markdown(self, filepath: str) -> List[LegoBlock]:
        """
        Parse markdown file and return list of LegoBlocks.

        Format expected:
        - ## 🏗️ CATEGORY NAME or ## CATEGORY NAME = category header
        - ### Title = achievement title
        - **bold text** = the actual achievement content
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        blocks = []
        current_category = None
        current_subcategory = None

        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and metadata
            if not line or line.startswith('*Note:') or line == '---':
                i += 1
                continue

            # Category header (## with optional emoji)
            if line.startswith('## '):
                # Remove markdown, emoji, and clean up
                category = re.sub(r'^##\s+[🏗️🤖📊💰👥🤝🌍⚙️🚀💻📚💼🎓🔧📝🎯]*\s*', '', line)
                category = category.strip()

                # Skip special sections
                if category.startswith('NOTES ON') or category.startswith('ACHIEVEMENT THEMES'):
                    break

                current_category = category
                current_subcategory = None
                i += 1
                continue

            # Achievement title (###)
            if line.startswith('### ') and current_category:
                title = line.replace('### ', '').strip()
                i += 1

                # Next line should have the bold content
                if i < len(lines):
                    content_line = lines[i].strip()

                    # Extract bold text
                    bold_match = re.search(r'\*\*(.*?)\*\*', content_line)
                    if bold_match:
                        content = bold_match.group(1)

                        # Extract keywords and skills from content
                        keywords = self._extract_keywords(content)
                        skills = self._extract_skills(content, current_category)

                        # Determine role types and company types
                        role_types = self._infer_role_types(current_category, title, content)
                        company_types = self._infer_company_types(current_category, title, content)

                        # Determine strength level based on metrics and keywords
                        strength_level = self._determine_strength_level(content)

                        block = LegoBlock(
                            category=current_category,
                            subcategory=current_subcategory,
                            title=title,
                            content=content,
                            skills=skills,
                            keywords=keywords,
                            strength_level=strength_level,
                            role_types=role_types,
                            company_types=company_types
                        )
                        blocks.append(block)

                i += 1
                continue

            i += 1

        self.blocks = blocks
        return blocks

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract technology terms, metrics, and important keywords from content"""
        keywords = []

        # Technology patterns
        tech_patterns = [
            r'\b(Java|Python|Scala|Kotlin|JavaScript|TypeScript|SQL|React|TensorFlow|Spark|AWS|EMR|DynamoDB|S3|ElasticSearch|SageMaker|Lambda|Amber|CloudFormation|CDK|Docker|Kubernetes|SpringMVC|Bootstrap)\b',
            r'\b(ML|AI|API|ETL|CI/CD|DevOps|SRE|GDPR|CCPA|DMA|A/B|UI/UX)\b',
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.extend([m for m in matches if m not in keywords])

        # Extract metrics (numbers with context)
        metric_patterns = [
            r'(\d+[M|B|K|TB|PB|GB]?\+?\s*(?:users|customers|countries|engineers|scientists|services|models|requests|TPS|years|months|weeks|days))',
            r'(\$\d+[M|B|K]?\+?)',
            r'(\d+%\+?)',
        ]

        for pattern in metric_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.extend([m for m in matches if m not in keywords])

        return keywords[:15]  # Limit to top 15 keywords

    def _extract_skills(self, content: str, category: str) -> List[str]:
        """Extract skills based on content and category"""
        skills = []

        # Add category-based skills
        if category in self.CATEGORY_SKILLS:
            skills.extend(self.CATEGORY_SKILLS[category][:3])  # Top 3 category skills

        # Add explicit technology mentions
        tech_keywords = [
            "Java", "Python", "Scala", "Kotlin", "JavaScript", "TypeScript", "SQL",
            "Spark", "TensorFlow", "AWS", "React", "Machine Learning", "System Design",
            "Architecture", "API", "DevOps", "Leadership", "Mentoring"
        ]

        for tech in tech_keywords:
            if tech.lower() in content.lower() and tech not in skills:
                skills.append(tech)

        return skills[:8]  # Limit to 8 skills

    def _infer_role_types(self, category: str, title: str, content: str) -> List[str]:
        """Infer suitable role types based on category and content"""
        role_types = []

        # Category-based role types
        if category in self.CATEGORY_ROLE_TYPES:
            role_types.extend(self.CATEGORY_ROLE_TYPES[category][:3])

        # Content-based additions
        if "ML" in content or "Machine Learning" in content or "model" in content.lower():
            if "ML Engineer" not in role_types:
                role_types.append("ML Engineer")

        if "full-stack" in content.lower() or ("frontend" in content.lower() and "backend" in content.lower()):
            if "Full-Stack Engineer" not in role_types:
                role_types.append("Full-Stack Engineer")

        if "team" in title.lower() or "mentor" in content.lower() or "led" in content.lower():
            if "Tech Lead" not in role_types and "Senior Engineer" not in role_types:
                role_types.append("Senior Engineer")

        return role_types[:4]  # Limit to 4 role types

    def _infer_company_types(self, category: str, title: str, content: str) -> List[str]:
        """Infer suitable company types"""
        company_types = []

        # Scale indicators
        if any(keyword in content for keyword in ["1B+", "billion", "PB", "petabyte", "international", "17 countries"]):
            company_types.append("Big Tech")

        # Innovation indicators
        if any(keyword in content for keyword in ["0-to-1", "MVP", "sole engineer", "ground up", "pioneered"]):
            company_types.append("Startup")
            company_types.append("Scale-up")

        # Business impact
        if "$" in content or "revenue" in content.lower() or "cost savings" in content.lower():
            company_types.append("Product-focused")

        # ML/AI focus
        if category == "MACHINE LEARNING & DATA SCIENCE":
            company_types.append("ML/AI Company")

        # Default to general if no specific match
        if not company_types:
            company_types = ["Big Tech", "Startup", "Scale-up"]

        return company_types[:3]

    def _determine_strength_level(self, content: str) -> str:
        """Determine strength level based on content metrics and impact"""
        score = 0

        # High impact metrics
        if any(keyword in content for keyword in ["$10M", "1B+", "PB+", "17 countries", "500M"]):
            score += 3
        elif any(keyword in content for keyword in ["$", "M+", "TB+", "international"]):
            score += 2
        elif re.search(r'\d+', content):  # Has any numbers
            score += 1

        # Leadership and scope
        if any(keyword in content for keyword in ["led", "architected", "built", "designed", "sole engineer"]):
            score += 2
        elif any(keyword in content for keyword in ["developed", "implemented", "created"]):
            score += 1

        # Impact words
        if any(keyword in content.lower() for keyword in ["zero", "100%", "complete", "comprehensive"]):
            score += 1

        if score >= 5:
            return "essential"
        elif score >= 3:
            return "strong"
        else:
            return "good"

    def search_blocks(
        self,
        skills: List[str] = None,
        role_type: str = None,
        category: str = None,
        keywords: List[str] = None,
        strength_level: str = None
    ) -> List[LegoBlock]:
        """
        Search blocks by various criteria.

        Args:
            skills: List of skills to match
            role_type: Role type to filter by
            category: Category to filter by
            keywords: Keywords to search for in content
            strength_level: Minimum strength level (good, strong, essential)

        Returns:
            List of matching LegoBlocks
        """
        results = self.blocks.copy()

        # Filter by category
        if category:
            results = [b for b in results if category.lower() in b.category.lower()]

        # Filter by role type
        if role_type:
            results = [b for b in results if role_type in b.role_types]

        # Filter by skills
        if skills:
            results = [
                b for b in results
                if any(skill.lower() in [s.lower() for s in b.skills] for skill in skills)
            ]

        # Filter by keywords
        if keywords:
            results = [
                b for b in results
                if any(kw.lower() in b.content.lower() or kw.lower() in ' '.join(b.keywords).lower()
                       for kw in keywords)
            ]

        # Filter by strength level
        if strength_level:
            level_order = {"good": 0, "strong": 1, "essential": 2}
            min_level = level_order.get(strength_level, 0)
            results = [b for b in results if level_order.get(b.strength_level, 0) >= min_level]

        return results

    def rank_blocks(
        self,
        blocks: List[LegoBlock],
        job_requirements: List[str],
        required_skills: List[str] = None,
        preferred_role: str = None
    ) -> List[Tuple[LegoBlock, float]]:
        """
        Rank blocks by relevance to job requirements.

        Args:
            blocks: List of LegoBlocks to rank
            job_requirements: List of requirement keywords/phrases from job description
            required_skills: List of required skills from job posting
            preferred_role: Preferred role type

        Returns:
            List of (LegoBlock, score) tuples, sorted by score descending
        """
        scored_blocks = []

        for block in blocks:
            score = 0.0

            # Match job requirements in content
            for req in job_requirements:
                req_lower = req.lower()
                if req_lower in block.content.lower():
                    score += 3.0
                elif req_lower in block.title.lower():
                    score += 2.0
                elif any(req_lower in kw.lower() for kw in block.keywords):
                    score += 1.5

            # Match required skills
            if required_skills:
                for skill in required_skills:
                    if any(skill.lower() in s.lower() for s in block.skills):
                        score += 2.5
                    elif skill.lower() in block.content.lower():
                        score += 1.5

            # Match role type
            if preferred_role and preferred_role in block.role_types:
                score += 2.0

            # Boost by strength level
            strength_boost = {
                "essential": 2.0,
                "strong": 1.0,
                "good": 0.5
            }
            score += strength_boost.get(block.strength_level, 0)

            # Keyword density bonus
            total_keywords_matched = sum(
                1 for req in job_requirements
                if req.lower() in block.content.lower()
            )
            if total_keywords_matched > 0:
                score += total_keywords_matched * 0.5

            scored_blocks.append((block, score))

        # Sort by score descending
        scored_blocks.sort(key=lambda x: x[1], reverse=True)

        return scored_blocks

    def get_blocks_by_category(self) -> Dict[str, List[LegoBlock]]:
        """Group blocks by category for easy browsing"""
        grouped = defaultdict(list)
        for block in self.blocks:
            grouped[block.category].append(block)
        return dict(grouped)

    def get_summary_stats(self) -> Dict[str, any]:
        """Get summary statistics about the blocks"""
        stats = {
            "total_blocks": len(self.blocks),
            "categories": len(set(b.category for b in self.blocks)),
            "category_breakdown": {},
            "strength_breakdown": {
                "essential": 0,
                "strong": 0,
                "good": 0
            },
            "top_skills": {},
            "top_role_types": {},
        }

        # Category breakdown
        for block in self.blocks:
            stats["category_breakdown"][block.category] = \
                stats["category_breakdown"].get(block.category, 0) + 1
            stats["strength_breakdown"][block.strength_level] += 1

        # Top skills
        skill_counts = defaultdict(int)
        for block in self.blocks:
            for skill in block.skills:
                skill_counts[skill] += 1
        stats["top_skills"] = dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        # Top role types
        role_counts = defaultdict(int)
        for block in self.blocks:
            for role in block.role_types:
                role_counts[role] += 1
        stats["top_role_types"] = dict(sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        return stats
