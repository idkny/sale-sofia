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
UNKNOWN_LOG_PATH = Path(__file__).parent.parent / "data" / "logs" / "unknown_bulgarian_words.log"


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

    def log_unknown(self, words: List[str]):
        """Log unknown Bulgarian words for future dictionary updates."""
        if not words:
            return
        UNKNOWN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(UNKNOWN_LOG_PATH, 'a', encoding='utf-8') as f:
            for word in words:
                f.write(f"{word}\n")
        logger.info(f"Logged {len(words)} unknown Bulgarian words")


# Module-level singleton
_dictionary: Optional[BulgarianDictionary] = None


def get_dictionary() -> BulgarianDictionary:
    """Get or create singleton dictionary instance."""
    global _dictionary
    if _dictionary is None:
        _dictionary = BulgarianDictionary()
    return _dictionary


def scan_and_build_hints(text: str) -> Tuple[str, dict]:
    """Convenience function: scan text and return hints + extractions.

    Returns:
        (hints_text, numeric_extractions)
    """
    dictionary = get_dictionary()
    result = dictionary.scan(text)
    hints = dictionary.build_hints_text(result)
    return hints, result['numeric_extractions']
