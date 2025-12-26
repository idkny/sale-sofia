# Spec 110: Dynamic Bulgarian Dictionary for LLM Extraction

**Created**: 2025-12-26
**Status**: Ready for Implementation
**Priority**: P1 - Core extraction improvement
**Supersedes**: Spec 109 (static prompt hints)

---

## 1. Problem Statement

### Current Approach (Static Hints)
Prompt contains ALL Bulgarian hints, regardless of input text:
```python
EXTRACTION_PROMPT = """...
- orientation: "north" | "south" | "east" | "west" | null
  (север=north, юг=south, изток=east, запад=west)
- heating_type: ...
  (ТЕЦ=district, газ=gas, ток=electric...)
# 50+ hint lines, most not relevant to current text
"""
```

**Problems**:
- Long prompts (token waste)
- LLM must parse irrelevant hints
- Hard to maintain - hints buried in code
- No learning from new words

### Proposed Approach (Dynamic Dictionary)
1. Maintain Bulgarian→English dictionary in separate file
2. Scan input text for matches BEFORE calling LLM
3. Inject ONLY relevant hints into prompt
4. Log unknown words for future dictionary updates

---

## 2. Architecture

### 2.1 Flow Diagram

```
┌─────────────────┐
│ Website Text    │
│ "тухла, 2 бани" │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────────┐
│ Dictionary Scan │◄────│ bulgarian_dict.yaml  │
│ (regex match)   │     │ (source of truth)    │
└────────┬────────┘     └──────────────────────┘
         │
         │ Found: тухла, бани
         ▼
┌─────────────────┐
│ Build Prompt    │
│ + relevant hints│
│ "тухла=brick,   │
│  бани=bathrooms"│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Extraction  │
│ (focused task)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Result + Log    │
│ unknown words   │
└─────────────────┘
```

### 2.2 Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Dictionary | `config/bulgarian_dictionary.yaml` | Bulgarian→English mappings |
| Scanner | `llm/dictionary.py` | Scan text, find matches |
| Prompt Builder | `llm/prompts.py` | Build dynamic prompts |
| Unknown Logger | `llm/dictionary.py` | Log unmatched Bulgarian words |

---

## 3. Dictionary Structure

### 3.1 File: `config/bulgarian_dictionary.yaml`

```yaml
# Bulgarian Real Estate Dictionary
# Structure: field_name -> english_value -> [bulgarian_variants]
# Add new words as discovered from real listings

version: 1
updated: 2025-12-26

# =============================================================================
# ENUM FIELDS - Map Bulgarian words to exact English enum values
# =============================================================================

construction:
  brick:
    - тухла
    - тухлена
    - тухлен
    - масивна
    - масивно
  panel:
    - панел
    - панелен
    - панелна
    - едропанелен
    - ЕПЖС
  epk:
    - ЕПК
    - епк
    - едроплощен кофраж

heating:
  district:
    - ТЕЦ
    - централно
    - парно
    - централно топлоснабдяване
    - топлофикация
  gas:
    - газ
    - газово
    - газов котел
    - газова
    - газов
  electric:
    - ток
    - електричество
    - електрическо
    - електрически
    - ел. отопление
  air_conditioner:
    - климатик
    - климатици
    - климатична система
    - климатизация

orientation:
  north:
    - север
    - северно
    - северна
    - С
  south:
    - юг
    - южно
    - южна
    - Ю
  east:
    - изток
    - източно
    - източна
    - И
  west:
    - запад
    - западно
    - западна
    - З

furnishing:
  furnished:
    - обзаведен
    - обзаведена
    - напълно обзаведен
    - с мебели
    - меблиран
    - оборудван
  partially:
    - частично обзаведен
    - частично
    - полуобзаведен
  unfurnished:
    - необзаведен
    - необзаведена
    - без обзавеждане
    - празен
    - празна
    - без мебели

condition:
  new:
    - нов
    - нова
    - ново
    - ново строителство
    - новопостроен
    - новопостроена
    - в строеж
  renovated:
    - ремонтиран
    - ремонтирана
    - ремонт
    - обновен
    - обновена
    - реновиран
    - след ремонт
  needs_renovation:
    - за ремонт
    - нуждае се от ремонт
    - стар ремонт
    - без ремонт

parking_type:
  underground:
    - подземен
    - подземен паркинг
    - подземно паркомясто
    - подземен гараж
  outdoor:
    - двор
    - открит
    - на двора
    - паркомясто в двора
    - открито паркомясто
    - пред блока
  garage:
    - гараж
    - гаражна клетка
    - гаражно място

view_type:
  city:
    - град
    - градска гледка
    - към града
    - панорама към града
  mountain:
    - планина
    - Витоша
    - Рила
    - Пирин
    - Стара планина
    - планинска гледка
    - към Витоша
    - към планината
  park:
    - парк
    - градина
    - зелена площ
    - към парка
    - паркова гледка

# =============================================================================
# BOOLEAN FIELDS - Keywords that indicate true
# =============================================================================

has_elevator:
  - асансьор
  - лифт
  - с асансьор

has_parking:
  - паркомясто
  - паркинг
  - гараж
  - място за паркиране

has_security:
  - охрана
  - СОТ
  - 24-часова охрана
  - видеонаблюдение
  - жива охрана
  - портиер

has_balcony:
  - тераса
  - балкон
  - лоджия
  - с тераса
  - с балкон

has_storage:
  - мазе
  - склад
  - таван
  - складово помещение
  - избено помещение

has_view:
  - гледка
  - изглед
  - панорама
  - панорамна гледка

# =============================================================================
# NUMERIC PATTERNS - Regex patterns for number extraction
# =============================================================================

rooms:
  pattern: "(едностаен|двустаен|тристаен|четиристаен|петстаен|многостаен)"
  mapping:
    едностаен: 1
    двустаен: 2
    тристаен: 3
    четиристаен: 4
    петстаен: 5
    многостаен: 6

bedrooms:
  keywords:
    - спалня
    - спални
  pattern: "(\d+)\s*спалн[яи]"

bathrooms:
  keywords:
    - баня
    - бани
    - санитарен възел
    - санитарни възли
    - тоалетна
  pattern: "(\d+)\s*бан[яи]"

# =============================================================================
# COMMON ABBREVIATIONS
# =============================================================================

abbreviations:
  кв.м: квадратни метри
  кв.м.: квадратни метри
  ет.: етаж
  бр.: брой
  лв.: лева
  EUR: евро
  BGN: лева
```

---

## 4. Implementation

### 4.1 New File: `llm/dictionary.py`

```python
"""Bulgarian dictionary scanner for dynamic prompt building.

Scans input text for Bulgarian keywords and returns relevant hints
for LLM prompt injection.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import yaml

logger = logging.getLogger(__name__)

DICT_PATH = Path(__file__).parent.parent / "config" / "bulgarian_dictionary.yaml"
UNKNOWN_LOG_PATH = Path(__file__).parent.parent / "data" / "logs" / "unknown_bulgarian_words.log"


class BulgarianDictionary:
    """Bulgarian→English dictionary with text scanning."""

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
        for field in ['construction', 'heating', 'orientation', 'furnishing',
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
                'enum_hints': {'construction': [('тухла', 'brick')], ...},
                'boolean_hints': {'has_elevator': ['асансьор'], ...},
                'numeric_extractions': {'rooms': 3, 'bathrooms': 1},
                'unknown_words': ['непозната_дума', ...]
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
                    lines.append(f"  {bg_word} → {eng_val} (field: {field})")

        # Boolean hints
        if scan_result['boolean_hints']:
            lines.append("\nDETECTED FEATURES (set to true):")
            for field, keywords in scan_result['boolean_hints'].items():
                lines.append(f"  {', '.join(keywords)} → {field} = true")

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
```

### 4.2 Updated `llm/prompts.py`

```python
"""Prompt templates for Ollama LLM extraction tasks.

Uses dynamic hint injection from bulgarian_dictionary.yaml.
"""

# Base prompt - hints injected dynamically
EXTRACTION_PROMPT_BASE = """You are a Bulgarian real estate data extraction expert.

CRITICAL RULES:
1. Extract information from the BULGARIAN DESCRIPTION below
2. RESPOND IN ENGLISH ONLY - use ONLY English enum values
3. Use the DETECTED WORDS section - these are pre-matched for you
4. Return valid JSON matching the schema
5. Use null for missing information

BULGARIAN DESCRIPTION:
{description}

{hints}

REQUIRED JSON FIELDS:
- rooms: number or null
- bedrooms: number or null
- bathrooms: number or null
- furnishing: "furnished" | "partially" | "unfurnished" | null
- condition: "new" | "renovated" | "needs_renovation" | null
- has_parking: boolean or null
- parking_type: "underground" | "outdoor" | "garage" | null
- has_elevator: boolean or null
- has_security: boolean or null
- has_balcony: boolean or null
- has_storage: boolean or null
- orientation: "north" | "south" | "east" | "west" | null
- has_view: boolean or null
- view_type: "city" | "mountain" | "park" | null
- heating_type: "district" | "gas" | "electric" | "air_conditioner" | null
- payment_options: "cash" | "installments" | "mortgage" | null
- confidence: number (0.0-1.0)

Return ONLY valid JSON.
"""

# Similar update for FIELD_MAPPING_PROMPT_BASE...
```

### 4.3 Updated `llm/llm_main.py`

```python
def extract_description(description: str) -> ExtractedDescription:
    """Extract structured data from free-text description."""
    from llm.dictionary import scan_and_build_hints

    client = _get_client()

    if not client.ensure_ready():
        logger.error("Ollama not available for description extraction")
        return ExtractedDescription(confidence=0.0)

    # Scan text and build dynamic hints
    hints, pre_extracted = scan_and_build_hints(description)

    # Build prompt with injected hints
    prompt = EXTRACTION_PROMPT_BASE.format(
        description=description,
        hints=hints if hints else "No specific Bulgarian keywords detected."
    )

    response = client._call_ollama(
        prompt, "description_extraction", schema_class=ExtractedDescription
    )
    result = client._parse_response(response, ExtractedDescription)

    # Override with pre-extracted numeric values (more reliable than LLM)
    for field, value in pre_extracted.items():
        if value is not None:
            setattr(result, field, value)

    return result
```

---

## 5. Benefits

| Aspect | Before (Static) | After (Dynamic) |
|--------|-----------------|-----------------|
| Prompt length | ~80 lines | ~30 lines + relevant hints |
| Maintainability | Hints in code | Dictionary file (YAML) |
| Learning | Manual updates | Unknown word logging |
| Accuracy | 69% | Target 95%+ |
| Token usage | High (all hints) | Low (only matches) |

---

## 6. Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `config/bulgarian_dictionary.yaml` | CREATE | Dictionary source of truth |
| `llm/dictionary.py` | CREATE | Scanner and hint builder |
| `llm/prompts.py` | MODIFY | Base prompts with {hints} placeholder |
| `llm/llm_main.py` | MODIFY | Integrate dictionary scanning |
| `data/logs/unknown_bulgarian_words.log` | AUTO-CREATE | Unknown word log |

---

## 7. Testing Plan

### 7.1 Unit Tests

```python
# tests/llm/test_dictionary.py

def test_scan_finds_construction():
    from llm.dictionary import get_dictionary
    d = get_dictionary()
    result = d.scan("Тухлена конструкция, южно изложение")
    assert ('тухлена', 'brick') in result['enum_hints']['construction']
    assert ('южно', 'south') in result['enum_hints']['orientation']

def test_scan_finds_boolean():
    from llm.dictionary import get_dictionary
    d = get_dictionary()
    result = d.scan("С асансьор и охрана")
    assert 'has_elevator' in result['boolean_hints']
    assert 'has_security' in result['boolean_hints']

def test_numeric_extraction():
    from llm.dictionary import get_dictionary
    d = get_dictionary()
    result = d.scan("Тристаен апартамент, 2 бани")
    assert result['numeric_extractions']['rooms'] == 3
    assert result['numeric_extractions']['bathrooms'] == 2
```

### 7.2 Integration Tests

Run existing `tests/llm/test_extraction_accuracy.py` - target 95%+.

---

## 8. Implementation Checklist

- [ ] Create `config/bulgarian_dictionary.yaml`
- [ ] Create `llm/dictionary.py`
- [ ] Update `llm/prompts.py` with base templates
- [ ] Update `llm/llm_main.py` to use dictionary
- [ ] Create `tests/llm/test_dictionary.py`
- [ ] Run accuracy test - verify 95%+
- [ ] Run existing tests - no regression

---

## 9. Additional Accuracy Improvements (If < 95%)

If dictionary approach alone doesn't achieve 95%+, implement these in order:

### 9.1 Few-Shot Examples in Prompt

Add concrete input/output examples to guide the model:

```python
EXTRACTION_PROMPT_BASE = """...

EXAMPLES:
Input: "Двустаен, 1 баня, обзаведен"
Output: {"rooms": 2, "bathrooms": 1, "furnishing": "furnished"}

Input: "Тристаен с тераса, южно изложение, ТЕЦ"
Output: {"rooms": 3, "has_balcony": true, "orientation": "south", "heating_type": "district"}

Input: "Четиристаен, 2 спални, асансьор, охрана"
Output: {"rooms": 4, "bedrooms": 2, "has_elevator": true, "has_security": true}

Now extract from this text:
{description}
...
"""
```

**Why it helps**: Models learn patterns from examples better than instructions alone.

### 9.2 Temperature = 0 (Verify)

Ensure deterministic output:

```yaml
# config/ollama.yaml
tasks:
  description_extraction:
    temperature: 0.0  # NOT 0.1 - must be exactly 0 for consistency
```

**Current setting**: 0.1 (slight variation) - should be 0.0 for enum fields.

### 9.3 Field-Specific Prompts

For problematic fields, use dedicated focused prompts:

```python
# Instead of one big prompt, split into focused extractions
ROOM_COUNT_PROMPT = """Count rooms in Bulgarian text.
едностаен=1, двустаен=2, тристаен=3, четиристаен=4, петстаен=5
Text: {text}
Return ONLY a number or null."""

BOOLEAN_FEATURES_PROMPT = """Find features in Bulgarian text.
Return JSON with true/false for each:
- has_elevator (асансьор/лифт)
- has_parking (паркомясто/гараж)
- has_balcony (тераса/балкон)
Text: {text}"""
```

**Trade-off**: More LLM calls but higher accuracy per field.

### 9.4 Hybrid: Scrapling CSS + LLM Fallback

Best of both worlds:

```python
def extract_listing(html):
    # Phase 1: Try CSS selectors first (fast, reliable)
    result = scrapling_extract(html)

    # Phase 2: LLM only for missing fields or free-text
    if result.rooms is None:
        result.rooms = llm_extract_rooms(html.text)

    if result.description:
        # Only use LLM for unstructured description text
        desc_data = llm_extract_description(result.description)
        result.merge(desc_data)

    return result
```

**Why it helps**:
- Structured fields (price, area) → CSS selectors (100% reliable)
- Free-text fields (features, condition) → LLM (smart extraction)

### 9.5 Confidence-Based Retry

If LLM returns low confidence, retry with different prompt:

```python
def extract_with_retry(text):
    result = extract_description(text)

    if result.confidence < 0.7:
        # Retry with few-shot examples
        result = extract_with_examples(text)

    if result.confidence < 0.7:
        # Retry with field-specific prompts
        result = extract_field_by_field(text)

    return result
```

---

## 10. Implementation Priority

| Phase | Approach | Expected Accuracy | Effort |
|-------|----------|-------------------|--------|
| **Phase 1** | Dynamic dictionary | 85-95% | Medium |
| **Phase 2** | + Few-shot examples | 90-97% | Low |
| **Phase 3** | + Temperature = 0 | +2-3% | Trivial |
| **Phase 4** | + Hybrid CSS/LLM | 95-99% | Medium |
| **Phase 5** | + Field-specific prompts | 98-99% | Medium |

**Recommendation**: Implement Phase 1-3 first, measure, then add Phase 4-5 if needed.

---

## 11. Future Enhancements

1. **Auto-learn from corrections** - If user corrects extraction, add word to dictionary
2. **Frequency tracking** - Track which words appear most often
3. **Synonym detection** - Group similar words automatically
4. **Multi-language support** - Extend pattern for other languages if needed
