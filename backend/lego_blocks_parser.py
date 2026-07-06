"""
Lego Blocks Parser - Extracts CV experience blocks from the master HTML file
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LegoBlock:
    """Represents a single CV experience block"""

    def __init__(
        self,
        id: str,
        strength: str,
        company: str,
        location: str,
        text: str,
        reasoning: str,
        questions: List[str]
    ):
        self.id = id
        self.strength = strength
        self.company = company
        self.location = location
        self.text = text
        self.reasoning = reasoning
        self.questions = questions

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'strength': self.strength,
            'company': self.company,
            'location': self.location,
            'text': self.text,
            'reasoning': self.reasoning,
            'questions': self.questions
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'LegoBlock':
        """Create LegoBlock from dictionary"""
        return cls(
            id=data['id'],
            strength=data['strength'],
            company=data['company'],
            location=data['location'],
            text=data['text'],
            reasoning=data['reasoning'],
            questions=data['questions']
        )


class LegoBlocksParser:
    """Parser for extracting CV blocks from master HTML file"""

    def __init__(self, html_path: Optional[str] = None):
        """
        Initialize parser with path to master HTML file

        Args:
            html_path: Path to cv_complete_ranked_all_bullets_react_FULL.html
                      Defaults to expected location in project structure
        """
        if html_path is None:
            # Default path relative to backend directory
            backend_dir = Path(__file__).parent
            html_path = backend_dir.parent.parent / "my-cv-app" / "masters" / "cv_complete_ranked_all_bullets_react_FULL.html"

        self.html_path = Path(html_path)
        self._blocks: Optional[List[LegoBlock]] = None
        self._cache_path = Path(__file__).parent / "lego_blocks_cache.json"

    def parse(self, force_refresh: bool = False) -> List[LegoBlock]:
        """
        Parse all lego blocks from HTML file

        Args:
            force_refresh: If True, re-parse HTML even if cache exists

        Returns:
            List of LegoBlock objects
        """
        # Return cached blocks if available
        if self._blocks is not None and not force_refresh:
            return self._blocks

        # Try loading from cache file
        if not force_refresh and self._cache_path.exists():
            logger.info(f"Loading blocks from cache: {self._cache_path}")
            try:
                with open(self._cache_path, 'r') as f:
                    cached_data = json.load(f)
                self._blocks = [LegoBlock.from_dict(block) for block in cached_data]
                logger.info(f"Loaded {len(self._blocks)} blocks from cache")
                return self._blocks
            except Exception as e:
                logger.warning(f"Failed to load cache, re-parsing: {e}")

        # Parse from HTML file
        logger.info(f"Parsing blocks from HTML: {self.html_path}")

        if not self.html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {self.html_path}")

        with open(self.html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Extract the bulletPointsData array from the JavaScript
        blocks = self._extract_blocks_from_js(html_content)

        # Cache the results
        self._save_cache(blocks)

        self._blocks = blocks
        logger.info(f"Parsed {len(blocks)} blocks from HTML")
        return blocks

    def _extract_blocks_from_js(self, html_content: str) -> List[LegoBlock]:
        """
        Extract bullet point data from the JavaScript array in HTML

        Args:
            html_content: Full HTML file content

        Returns:
            List of LegoBlock objects
        """
        # Find the bulletPointsData array definition
        # Pattern: const bulletPointsData = [ ... ];
        pattern = r'const bulletPointsData\s*=\s*\[(.*?)\];'
        match = re.search(pattern, html_content, re.DOTALL)

        if not match:
            raise ValueError("Could not find bulletPointsData array in HTML")

        array_content = match.group(1)

        # Parse individual objects using regex
        # Pattern: { id: '...', strength: '...', ... }
        object_pattern = r'\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'

        blocks = []
        for obj_match in re.finditer(object_pattern, array_content):
            obj_str = obj_match.group(1)

            try:
                # Extract fields
                id_match = re.search(r"id:\s*['\"]([^'\"]+)['\"]", obj_str)
                strength_match = re.search(r"strength:\s*['\"]([^'\"]+)['\"]", obj_str)
                company_match = re.search(r"company:\s*['\"]([^'\"]+)['\"]", obj_str)
                location_match = re.search(r"location:\s*['\"]([^'\"]+)['\"]", obj_str)
                text_match = re.search(r"text:\s*['\"]([^'\"]+)['\"]", obj_str)
                reasoning_match = re.search(r"reasoning:\s*['\"]([^'\"]+)['\"]", obj_str)

                # Extract questions array
                questions_match = re.search(r"questions:\s*\[(.*?)\]", obj_str, re.DOTALL)
                questions = []
                if questions_match:
                    questions_str = questions_match.group(1)
                    # Extract individual question strings
                    for q_match in re.finditer(r"['\"]([^'\"]+)['\"]", questions_str):
                        questions.append(q_match.group(1))

                if all([id_match, strength_match, company_match, location_match, text_match, reasoning_match]):
                    block = LegoBlock(
                        id=id_match.group(1),
                        strength=strength_match.group(1),
                        company=company_match.group(1),
                        location=location_match.group(1),
                        text=text_match.group(1),
                        reasoning=reasoning_match.group(1),
                        questions=questions
                    )
                    blocks.append(block)
            except Exception as e:
                logger.warning(f"Failed to parse block: {e}")
                continue

        return blocks

    def _save_cache(self, blocks: List[LegoBlock]):
        """Save parsed blocks to cache file"""
        try:
            cache_data = [block.to_dict() for block in blocks]
            with open(self._cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Cached {len(blocks)} blocks to {self._cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def get_blocks_by_strength(self, strength: str) -> List[LegoBlock]:
        """
        Get all blocks of a specific strength level

        Args:
            strength: One of 'essential', 'strong', 'good', 'weak', 'omit'

        Returns:
            List of matching LegoBlock objects
        """
        if self._blocks is None:
            self.parse()

        return [block for block in self._blocks if block.strength == strength]

    def get_block_by_id(self, block_id: str) -> Optional[LegoBlock]:
        """
        Get a specific block by ID

        Args:
            block_id: Block ID (e.g., 'ads-essential-1')

        Returns:
            LegoBlock if found, None otherwise
        """
        if self._blocks is None:
            self.parse()

        for block in self._blocks:
            if block.id == block_id:
                return block
        return None

    def get_essential_blocks(self) -> List[LegoBlock]:
        """Get all essential blocks (always include in CV)"""
        return self.get_blocks_by_strength('essential')

    def get_strong_blocks(self) -> List[LegoBlock]:
        """Get all strong blocks (include in most CVs)"""
        return self.get_blocks_by_strength('strong')

    def get_good_blocks(self) -> List[LegoBlock]:
        """Get all good blocks (include if space allows)"""
        return self.get_blocks_by_strength('good')

    def get_recommended_blocks(self) -> List[LegoBlock]:
        """Get recommended blocks (essential + strong)"""
        if self._blocks is None:
            self.parse()

        return [
            block for block in self._blocks
            if block.strength in ['essential', 'strong']
        ]

    def get_all_blocks(self) -> List[LegoBlock]:
        """Get all blocks (including weak and omit)"""
        if self._blocks is None:
            self.parse()

        return self._blocks.copy()


# Global singleton instance
_parser_instance: Optional[LegoBlocksParser] = None


def get_parser() -> LegoBlocksParser:
    """Get or create the global parser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = LegoBlocksParser()
    return _parser_instance


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(level=logging.INFO)

    parser = LegoBlocksParser()
    blocks = parser.parse()

    print(f"\n✅ Successfully parsed {len(blocks)} lego blocks\n")

    # Count by strength
    strengths = {}
    for block in blocks:
        strengths[block.strength] = strengths.get(block.strength, 0) + 1

    print("Blocks by strength:")
    for strength, count in sorted(strengths.items()):
        print(f"  {strength}: {count}")

    # Show sample block
    print("\nSample block (first essential):")
    essential = parser.get_essential_blocks()
    if essential:
        sample = essential[0]
        print(f"  ID: {sample.id}")
        print(f"  Company: {sample.company}")
        print(f"  Text: {sample.text[:100]}...")
        print(f"  Questions: {len(sample.questions)}")
