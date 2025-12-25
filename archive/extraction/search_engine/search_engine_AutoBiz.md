---
id: 20251201_search_engine_autobiz
type: extraction
subject: search_engine
source_repo: Auto-Biz
description: "DuckDuckGo and SerpAPI integration from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [search-engine, ddg, serpapi, auto-biz]
---

# SUBJECT: search_engine/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `search_engine/ddg.py`, `search_engine/serpapi.py`, `search_engine/search_engines.py`

---

## 1. EXTRACTED CODE

### 1.1 DuckDuckGo Multi-Search

```python
"""DuckDuckGo search engine integration."""

import time
from typing import Optional, Union

from duckduckgo_search import DDGS


class DuckDuckGoMultiSearch:
    """Performs searches using DuckDuckGo and returns results."""

    def __init__(self) -> None:
        pass

    def search(
        self,
        keywords: Union[str, list[str]],
        types: list[str] | None = None,
        regions: Optional[list[str]] = None,
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: int = 50,
    ) -> dict[str, list[dict]]:
        """Performs a DuckDuckGo search."""
        if types is None:
            types = ["text"]
        results = {}
        with DDGS() as ddgs:
            for t in types:
                if t == "text":
                    ddgs_output = ddgs.text(
                        keywords=keywords,
                        region=regions[0] if regions else "wt-wt",
                        safesearch=safesearch,
                        timelimit=timelimit,
                        max_results=max_results,
                    )
                    results["text_results"] = list(ddgs_output)
        time.sleep(1)  # Rate limiting
        return results
```

### 1.2 SerpAPI Integration

```python
"""SerpAPI search engine integration."""

import os
from typing import Any

from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()
SERP_API_KEY = os.getenv("SERPAPI_API_KEY")


def search_single(keyword: str, region: str, **kwargs: Any) -> list[dict]:
    """Performs a single search using SerpAPI."""
    if not SERP_API_KEY:
        raise ValueError("Missing SERPAPI_API_KEY in .env file")

    params = {
        "api_key": SERP_API_KEY,
        "engine": "google",
        "q": keyword,
        "gl": region,
        "hl": region,
        **kwargs,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return results.get("organic_results", [])
```

### 1.3 Search Orchestration

```python
# search_engines.py
from urllib.parse import urlparse

import tldextract
from loguru import logger

from config import SEARCH_QUERIES, SEARCH_SETTINGS
from data import data_store_main
from search_engine import ddg, serpapi


def extract_root_domain(url: str) -> str:
    """Extract the registered domain from a URL."""
    try:
        extracted = tldextract.extract(url)
        if extracted.registered_domain:
            return extracted.registered_domain
        return extracted.domain
    except Exception as e:
        logger.warning(f"Could not extract domain from URL '{url}': {e}")
        return ""


def search_ddg() -> None:
    """Perform a search on DuckDuckGo for all configured queries."""
    engine = ddg.DuckDuckGoMultiSearch()
    for entry in SEARCH_QUERIES:
        region = entry["region"]
        language = entry["language"]
        for keyword in entry["keywords"]:
            results = engine.search(
                keywords=[keyword],
                types=SEARCH_SETTINGS["types"],
                regions=[region],
                safesearch=SEARCH_SETTINGS["safesearch"],
                timelimit=SEARCH_SETTINGS["timelimit"],
                max_results=SEARCH_SETTINGS["max_results"],
            )
            data_store_main.save_search_results(
                results.get(keyword, []),
                source="ddg",
                keyword_text=keyword,
                region=region,
                language=language
            )


def search_serp() -> None:
    """Perform a search on SerpAPI for all configured queries."""
    for entry in SEARCH_QUERIES:
        region = entry["region"]
        language = entry["language"]
        for keyword in entry["keywords"]:
            results = serpapi.search_single(keyword, region)
            data_store_main.save_search_results(
                results,
                source="serpapi",
                keyword_text=keyword,
                region=region,
                language=language
            )


def search_all() -> None:
    """Perform a search on all available search engines."""
    search_ddg()
    search_serp()


def add_urls_to_database(urls_to_add: list[str], source_visit_type: str = "manual_input") -> tuple[int, int]:
    """Add a list of URLs to the database."""
    return data_store_main.add_urls(urls_to_add, source_visit_type)
```

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **DuckDuckGoMultiSearch**: Clean wrapper with rate limiting
2. **extract_root_domain**: tldextract for proper domain parsing
3. **Config-driven**: SEARCH_QUERIES and SEARCH_SETTINGS
4. **Database integration**: Results saved automatically

### What is Outdated

1. **Single search type**: Only "text" implemented for DDG

### What Must Be Rewritten

1. **DDG types**: Add images, news, videos support
2. **Error handling**: No retry on failures

### Conflicts with Previous Repos

| Pattern | Auto-Biz | Scraper | Best |
|---------|----------|---------|------|
| DDG | Basic | Multi-type + multi-region | **Scraper** |
| SerpAPI | Single search | N/A | **Auto-Biz** |
| Domain extract | tldextract | N/A | **Auto-Biz** |

### Best Version Recommendation

**Scraper DDG + Auto-Biz SerpAPI**:
- Scraper has more complete DDG implementation (multi-type, multi-region)
- Auto-Biz has proper SerpAPI and domain extraction
