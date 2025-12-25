# Coding Conventions

> Naming, file organization, and code patterns. Read when writing new code.

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | `snake_case.py` | `imot_scraper.py` |
| Classes | `PascalCase` | `ImotBgScraper` |
| Functions | `snake_case` | `extract_listing` |
| Constants | `UPPER_SNAKE` | `MAX_TOTAL_BUDGET` |
| Private | `_prefix` | `_extract_price` |

---

## File Organization

1. **One class per file** for major classes (scrapers, strategies)
2. **Selectors separate** from logic (`selectors.py`)
3. **Constants at top** of module
4. **Imports grouped**: stdlib → third-party → local

### Import Order Example

```python
# Standard library
import json
from pathlib import Path
from typing import Optional, List

# Third-party
import httpx
from bs4 import BeautifulSoup
from loguru import logger

# Local
from .base_scraper import BaseSiteScraper, ListingData
from .selectors import PRICE_SELECTOR
```

---

## Code Patterns

### Abstract Methods

```python
from abc import ABC, abstractmethod

class BaseClass(ABC):
    @abstractmethod
    async def method(self) -> ReturnType:
        pass
```

### Optional Returns (extraction)

```python
def extract_field(self) -> Optional[Type]:
    """Return None if not found, don't raise."""
    try:
        return parsed_value
    except Exception:
        return None
```

### Dataclasses for DTOs

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class MyData:
    required_field: str
    optional_field: Optional[int] = None
```

### Context Managers

```python
async with browser_handle as handle:
    page = await handle.new_tab()
    # ... use page ...
# Automatic cleanup
```

---

## Code Quality Standards

### Function Length

| Metric | Limit | Purpose |
|--------|-------|---------|
| **Hard limit** | 50 lines | Maximum allowed - exceeding requires refactoring |
| **Soft target** | 30 lines | Ideal target - review for splitting opportunities if exceeded |

**Enforcement**: Functions over 30 lines should be reviewed during code review. Functions over 50 lines must be split before merging.

### Single Responsibility Principle

**Rules**:
- Each function does ONE thing
- If you can describe a function with "and", it should be split
- Helper functions should be prefixed with `_`

**Examples**:

```python
# BAD: Multiple responsibilities
def process_listing(html):
    # Parse HTML AND validate AND save AND notify
    soup = BeautifulSoup(html)
    data = extract_data(soup)
    if not is_valid(data):
        return None
    save_to_db(data)
    send_notification(data)
    return data

# GOOD: Single responsibility
def process_listing(html):
    """Parse and return listing data."""
    soup = BeautifulSoup(html)
    return _extract_data(soup)

def _extract_data(soup) -> ListingData:
    """Extract structured data from parsed HTML."""
    # ... extraction only ...
```

### Nesting Depth

**Limit**: Maximum 3 levels of nesting

**Solution**: Extract deeply nested logic into helper functions

```python
# BAD: 4+ levels of nesting
def process_batch(items):
    for item in items:
        if item.is_valid:
            for field in item.fields:
                if field.needs_update:
                    for validator in validators:
                        if validator.check(field):
                            # Too deep!
                            pass

# GOOD: Extracted nested logic
def process_batch(items):
    for item in items:
        if item.is_valid:
            _process_item_fields(item)

def _process_item_fields(item):
    for field in item.fields:
        if field.needs_update:
            _validate_field(field)

def _validate_field(field):
    for validator in validators:
        if validator.check(field):
            # Now only 2 levels deep
            pass
```

### Complexity Indicators

**Signs a function needs splitting**:

1. **Multiple phases/stages** - If your function has distinct "phases" (parse → validate → transform → save)
2. **More than 5 local variables** - Too many concerns in one place
3. **Try/except inside loops** - Extract the exception-prone logic
4. **Mixed responsibilities** - IO, validation, and transformation together

**Example**:

```python
# BAD: Mixed responsibilities
def fetch_and_process_listing(url):
    # IO
    response = httpx.get(url)
    html = response.text

    # Parsing
    soup = BeautifulSoup(html)
    title = soup.select_one('.title').text

    # Validation
    if not title or len(title) < 5:
        return None

    # Transformation
    data = ListingData(title=title.strip().upper())

    # More IO
    save_to_db(data)
    return data

# GOOD: Separated responsibilities
async def fetch_listing_html(url: str) -> str:
    """Fetch raw HTML from URL."""
    response = await httpx.get(url)
    return response.text

def parse_listing(html: str) -> Optional[dict]:
    """Extract raw fields from HTML."""
    soup = BeautifulSoup(html)
    title = soup.select_one('.title')
    return {'title': title.text if title else None}

def validate_listing_data(data: dict) -> bool:
    """Check if listing data is valid."""
    title = data.get('title')
    return title and len(title) >= 5

def transform_listing(data: dict) -> ListingData:
    """Convert raw data to domain model."""
    return ListingData(title=data['title'].strip().upper())
```

### Testing Requirements

**Rules**:
- Each helper function must be independently testable
- Split functions **before** adding features, not after
- If you can't easily write a unit test, the function is too complex

**Example**:

```python
# Each function can be tested independently
def test_parse_listing():
    html = "<div class='title'>Test</div>"
    result = parse_listing(html)
    assert result['title'] == 'Test'

def test_validate_listing_data():
    assert validate_listing_data({'title': 'Valid Title'}) is True
    assert validate_listing_data({'title': 'Bad'}) is False

def test_transform_listing():
    data = {'title': 'test listing'}
    result = transform_listing(data)
    assert result.title == 'TEST LISTING'
```

### Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Long sequential extraction** | `field1 = ...; field2 = ...; field3 = ...` (20+ lines) | Group related fields, use config-driven approach |
| **Repeated patterns inline** | Same extraction logic duplicated | Extract to helper with parameters |
| **Magic numbers** | `if price > 200000:` | Use constants: `if price > MAX_BUDGET:` |
| **Catch-all try/except** | `try: ... except: pass` | Catch specific exceptions, log failures |
| **Boolean parameters** | `def process(data, full=True, skip=False)` | Use separate functions or enums |

**Config-driven example**:

```python
# BAD: Hardcoded extraction
def extract_fields(soup):
    title = soup.select_one('.title').text
    price = soup.select_one('.price').text
    area = soup.select_one('.area').text
    # ... 20 more fields ...

# GOOD: Config-driven
FIELD_SELECTORS = {
    'title': '.title',
    'price': '.price',
    'area': '.area',
    # ... centralized config ...
}

def extract_fields(soup):
    return {
        field: _extract_text(soup, selector)
        for field, selector in FIELD_SELECTORS.items()
    }

def _extract_text(soup, selector):
    element = soup.select_one(selector)
    return element.text.strip() if element else None
```

---

## Testing Patterns

| Test Type | Location | Naming |
|-----------|----------|--------|
| Unit tests | `tests/test_<module>.py` | `test_<function>` |
| Integration | `tests/debug/` | Descriptive name |
| Stress tests | `tests/stress/` | `test_<scenario>.py` |

### Pytest Example

```python
import pytest
from websites.imot_bg.imot_scraper import ImotBgScraper

@pytest.fixture
def scraper():
    return ImotBgScraper()

def test_extract_price(scraper):
    result = scraper._parse_price("50 000 EUR")
    assert result == 50000.0
```

---

## Known Gaps (to fix later)

| Gap | Description |
|-----|-------------|
| `*_main.py` suffix | Unclear naming - consider renaming |
| Scoring in app/ | Domain logic in presentation layer |
| Magic numbers | Hardcoded values should be in config |
| No custom exceptions | Should have `ScrapingError`, `ProxyError` |
