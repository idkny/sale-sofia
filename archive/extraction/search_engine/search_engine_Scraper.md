---
id: 20251201_search_engine_scraper
type: extraction
subject: search_engine
source_repo: Scraper
description: "DuckDuckGo multi-search client - free alternative to SerpAPI"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, search_engine, duckduckgo, ddg, free]
---

# SUBJECT: search_engine/

**Source**: `idkny/Scraper`
**Files Extracted**: 1 file
**Quality**: GOOD - Complete DuckDuckGo client (SerpAPI placeholder empty)

---

## 1. DuckDuckGo Multi-Search Client (ddg.py)

Free search engine client with multi-keyword, multi-region, multi-type support.

```python
import json
import csv
from pathlib import Path
from typing import List, Optional, Union
from duckduckgo_search import DDGS
import re

class DuckDuckGoMultiSearch:
    """
    Multi-keyword, multi-region search client using DuckDuckGo.
    FREE alternative to paid APIs like SerpAPI.

    Features:
    - Multiple keywords in single call
    - Multiple search types (text, images, videos, news)
    - Multiple regions (localized results)
    - Export to JSONL, CSV, TXT, Markdown
    """

    def __init__(self):
        pass

    def search(
        self,
        keywords: Union[str, List[str]],
        types: List[str] = ["text"],
        regions: Optional[List[str]] = None,
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: int = 50,
    ) -> dict[str, List[dict]]:
        """
        Run searches across keywords/types/regions and return results grouped by keyword.
        Includes search operators like: filetype:pdf, site:..., inurl:..., etc.

        Args:
            keywords: Single keyword or list of keywords
            types: Search types - ["text", "images", "videos", "news", "maps"]
            regions: Region codes - ["wt-wt" (global), "us-en", "uk-en", "bg-bg", etc.]
            safesearch: "on", "moderate", "off"
            timelimit: "d" (day), "w" (week), "m" (month), "y" (year)
            max_results: Maximum results per search (up to ~100 for DDG)

        Returns:
            Dict mapping keywords to lists of result dicts
        """
        if isinstance(keywords, str):
            keywords = [keywords]

        results_by_keyword = {}

        with DDGS(timeout=20) as ddgs:
            for keyword in keywords:
                all_results = []
                for region in regions or ["wt-wt"]:
                    for t in types:
                        print(f"Searching [{t}] for '{keyword}' in {region}")
                        search_func = getattr(ddgs, t)
                        try:
                            results = search_func(
                                keywords=keyword,
                                region=region,
                                safesearch=safesearch,
                                timelimit=timelimit,
                                max_results=max_results,
                            )
                            for rank, item in enumerate(results, start=1):
                                item["rank"] = rank
                                item["search_type"] = t
                                item["region"] = region
                                item["keyword"] = keyword
                                all_results.append(item)
                        except Exception as e:
                            print(f"Error with {t} search in {region}: {e}")
                results_by_keyword[keyword] = all_results

        return results_by_keyword

    def save_results(
        self,
        results_by_keyword: dict[str, List[dict]],
        output_dir: str = "results",
        format: str = "jsonl"
    ):
        """
        Save search results to files.

        Args:
            results_by_keyword: Results dict from search()
            output_dir: Output directory path
            format: "jsonl", "csv", "txt", or "md"
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for keyword, results in results_by_keyword.items():
            # Sanitize keyword for filename
            safe_keyword = re.sub(r'\W+', '_', keyword.strip().lower())[:50]
            path = Path(output_dir) / f"results_{safe_keyword}.{format}"

            if format == "jsonl":
                with open(path, "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                print(f"Saved {len(results)} results to {path} (JSONL)")

            elif format == "csv":
                keys = sorted({k for r in results for k in r})
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(results)
                print(f"Saved {len(results)} results to {path} (CSV)")

            elif format == "txt":
                with open(path, "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(f"{r['rank']}. {r.get('title', '')} - {r.get('href', r.get('url', ''))}\n")
                print(f"Saved {len(results)} results to {path} (TXT)")

            elif format == "md":
                with open(path, "w", encoding="utf-8") as f:
                    f.write("| Rank | Title | URL | Type | Region | Keyword |\n")
                    f.write("|------|-------|-----|------|--------|---------|\n")
                    for r in results:
                        title = r.get("title", "").replace("|", "-")
                        url = r.get("href") or r.get("url", "")
                        stype = r.get("search_type", "")
                        region = r.get("region", "")
                        keyword_col = r.get("keyword", "")
                        rank = r.get("rank", "")
                        f.write(f"| {rank} | [{title}]({url}) | {url} | {stype} | {region} | {keyword_col} |\n")
                print(f"Saved {len(results)} results to {path} (Markdown)")

            else:
                raise ValueError(f"Unsupported export format: {format}")
```

---

## CONCLUSIONS

### What is GOOD / Usable (Direct Port)

1. **Free Alternative to SerpAPI**
   - No API key required
   - No rate limits (within reason)
   - Good for testing and low-budget projects

2. **Multi-Dimensional Search**
   - Multiple keywords
   - Multiple search types (text, images, videos, news)
   - Multiple regions

3. **Export Formats**
   - JSONL (best for processing)
   - CSV (spreadsheet compatible)
   - TXT (simple list)
   - Markdown (documentation)

4. **Result Enrichment**
   - Adds rank, search_type, region, keyword to each result
   - Easy to trace origin of results

### What is OUTDATED

- Print statements instead of logging
- No retry/error handling for rate limits
- `serpapi.py` and `search-engine.py` are empty placeholders

### What Must Be REWRITTEN

1. **Add logging** - Replace print statements
2. **Add retry decorator** - Handle DDG rate limits
3. **Add caching** - Cache results to avoid repeat searches
4. **Async version** - DDG library supports async

### Cross-Repo Comparison

| Feature | Scraper | MarketIntel | SerpApi | Best |
|---------|---------|-------------|---------|------|
| SerpAPI client | Empty | Full | Full | MarketIntel |
| DuckDuckGo | Complete | None | None | **SCRAPER** |
| Free option | Yes | Paid only | Paid only | **SCRAPER** |
| Caching | None | SHA256 | None | MarketIntel |

**MERGE RECOMMENDATION**:
- Use MarketIntel's SerpAPI client for paid searches
- Use Scraper's DuckDuckGo for free/testing
- Apply MarketIntel's caching pattern to both

### How It Fits Into AutoBiz

**Location**: `autobiz/tools/search/`
- `serpapi_client.py` - SerpAPI (from MarketIntel)
- `ddg_client.py` - DuckDuckGo (from Scraper)
- `search_manager.py` - Unified interface with fallback

**Integration Points**:
- Market research pipeline uses search
- Competitor discovery uses search
- Keyword research uses search

---

## Usage Examples

```python
# Basic search
client = DuckDuckGoMultiSearch()
results = client.search(
    keywords=["python automation", "web scraping best practices"],
    types=["text", "news"],
    max_results=20
)

# Regional search
results = client.search(
    keywords="local restaurants",
    regions=["us-en", "uk-en", "bg-bg"],
    timelimit="m"  # Last month
)

# Save results
client.save_results(results, output_dir="search_output", format="jsonl")

# Search operators (supported by DDG)
results = client.search(
    keywords=[
        "site:github.com python scraper",
        "filetype:pdf web automation",
        "inurl:api documentation"
    ]
)
```

---

## Dependencies

```txt
duckduckgo_search>=8.0.2
```

**Note**: DDG library may have rate limits. For production, use SerpAPI from MarketIntel.
