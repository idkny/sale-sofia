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
