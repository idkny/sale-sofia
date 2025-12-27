"""Bulgarian dictionary scanner for dynamic prompt building.

Scans input text for Bulgarian keywords and returns relevant hints
for LLM prompt injection.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import yaml

logger = logging.getLogger(__name__)

DICT_PATH = Path(__file__).parent.parent / "config" / "bulgarian_dictionary.yaml"


class BulgarianDictionary:
    """Bulgarian->English dictionary with text scanning."""

    def __init__(self, dict_path: Path = DICT_PATH):
        self.dict_path = dict_path
        self._data = self._load()
        self._build_lookup()

    def _load(self) -> dict:
        """Load dictionary from YAML."""
        with open(self.dict_path, encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _build_lookup(self):
        """Build reverse lookup: bulgarian_word -> (field, english_value)."""
        self._lookup: Dict[str, Tuple[str, str]] = {}
        self._boolean_lookup: Dict[str, str] = {}
        self._patterns: Dict[str, dict] = {}

        # Enum fields
        for field in ['construction', 'heating_type', 'orientation', 'furnishing',
                      'condition', 'parking_type', 'view_type']:
            if field not in self._data:
                continue
            for english_val, bg_words in self._data[field].items():
                for bg_word in bg_words:
                    self._lookup[bg_word.lower()] = (field, english_val)

        # Boolean fields
        for field in ['has_elevator', 'has_parking', 'has_security',
                      'has_balcony', 'has_storage', 'has_view']:
            if field not in self._data:
                continue
            for bg_word in self._data[field]:
                self._boolean_lookup[bg_word.lower()] = field

        # Numeric patterns
        for field in ['rooms', 'bedrooms', 'bathrooms']:
            if field in self._data and 'pattern' in self._data[field]:
                self._patterns[field] = self._data[field]

    def scan(self, text: str) -> dict:
        """Scan text and return found mappings.

        Returns:
            {
                'enum_hints': {'construction': [('tuhla', 'brick')], ...},
                'boolean_hints': {'has_elevator': ['asansor'], ...},
                'numeric_extractions': {'rooms': 3, 'bathrooms': 1},
                'unknown_words': ['nepoznata_duma', ...]
            }
        """
        text_lower = text.lower()
        result = {
            'enum_hints': {},
            'boolean_hints': {},
            'numeric_extractions': {},
            'unknown_words': []
        }

        # Scan for enum matches
        for bg_word, (field, eng_val) in self._lookup.items():
            if bg_word in text_lower:
                if field not in result['enum_hints']:
                    result['enum_hints'][field] = []
                result['enum_hints'][field].append((bg_word, eng_val))

        # Scan for boolean matches
        for bg_word, field in self._boolean_lookup.items():
            if bg_word in text_lower:
                if field not in result['boolean_hints']:
                    result['boolean_hints'][field] = []
                result['boolean_hints'][field].append(bg_word)

        # Extract numeric values
        for field, config in self._patterns.items():
            pattern = config.get('pattern')
            if pattern:
                match = re.search(pattern, text_lower)
                if match:
                    if 'mapping' in config:
                        # Word to number mapping (rooms)
                        word = match.group(1)
                        result['numeric_extractions'][field] = config['mapping'].get(word)
                    else:
                        # Direct number extraction (bedrooms, bathrooms)
                        result['numeric_extractions'][field] = int(match.group(1))

        return result

    def build_hints_text(self, scan_result: dict) -> str:
        """Build hint text for prompt injection."""
        lines = []

        # Enum hints
        if scan_result['enum_hints']:
            lines.append("DETECTED BULGARIAN WORDS (use these mappings):")
            for field, matches in scan_result['enum_hints'].items():
                for bg_word, eng_val in matches:
                    lines.append(f"  {bg_word} -> {eng_val} (field: {field})")

        # Boolean hints
        if scan_result['boolean_hints']:
            lines.append("\nDETECTED FEATURES (set to true):")
            for field, keywords in scan_result['boolean_hints'].items():
                lines.append(f"  {', '.join(keywords)} -> {field} = true")

        # Pre-extracted numbers
        if scan_result['numeric_extractions']:
            lines.append("\nEXTRACTED NUMBERS (use these values):")
            for field, value in scan_result['numeric_extractions'].items():
                lines.append(f"  {field} = {value}")

        return '\n'.join(lines)


# Module-level singleton
_dictionary: Optional[BulgarianDictionary] = None


def get_dictionary() -> BulgarianDictionary:
    """Get or create singleton dictionary instance."""
    global _dictionary
    if _dictionary is None:
        _dictionary = BulgarianDictionary()
    return _dictionary


def scan_and_build_hints(text: str) -> Tuple[str, dict, dict, dict]:
    """Convenience function: scan text and return hints + extractions.

    Returns:
        (hints_text, numeric_extractions, boolean_extractions, enum_extractions)

    Dictionary-First Approach:
    - Numeric: regex extraction (100% reliable for patterns)
    - Boolean: keyword matching (100% reliable)
    - Enum: keyword matching (100% reliable for known words)
    - LLM only handles fields dictionary didn't find
    """
    dictionary = get_dictionary()
    result = dictionary.scan(text)
    hints = dictionary.build_hints_text(result)

    # Convert boolean_hints to actual boolean values
    # If dictionary found keywords for a boolean field, set it to True
    boolean_extractions = {}
    for field, keywords in result.get('boolean_hints', {}).items():
        if keywords:  # If any keywords were found for this field
            boolean_extractions[field] = True

    # Convert enum_hints to actual enum values
    # Use the longest matching keyword (most specific match)
    enum_extractions = {}
    for field, matches in result.get('enum_hints', {}).items():
        if matches:
            # Sort by keyword length (longest first) for most specific match
            sorted_matches = sorted(matches, key=lambda x: len(x[0]), reverse=True)
            # Use the English value from the longest match
            enum_extractions[field] = sorted_matches[0][1]

    return hints, result['numeric_extractions'], boolean_extractions, enum_extractions
