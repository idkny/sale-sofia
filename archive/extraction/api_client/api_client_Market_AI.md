---
id: 20251201_api_client_market_ai
type: extraction
subject: api_client
source_repo: Market_AI
description: "SerpAPI client with 12+ endpoints, _call_serpapi helper, tool contract pattern"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [api, serpapi, google, search, trends, news, local]
---

# SUBJECT: api_client/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `SerpApi/src/api_client.py`, `tools.py`

---

## 1. EXTRACTED CODE

### 1.1 SerpAPI Base Client

```python
import os
import logging
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY not found in environment variables.")

def _call_serpapi(params):
    """
    Internal helper to make SerpApi calls.
    Args:
        params (dict): The parameters for the SerpApi call.
    Returns:
        The dictionary response from SerpApi, or None on error.
    """
    try:
        params['api_key'] = SERPAPI_API_KEY
        search = GoogleSearch(params)
        response = search.get_dict()
        if "error" in response:
            logging.error(f"SerpApi Error: {response['error']}")
            return None
        return response
    except Exception as e:
        logging.error(f"An error occurred during the SerpApi call: {e}")
        return None
```

### 1.2 Google Search API (Organic, Ads, PAA)

```python
def call_google_search_api(query, location, device='desktop', num=20, start=0, no_cache=False):
    """For general SERP data, organic results, ads, PAA, etc."""
    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
        "device": device,
        "num": num,
        "start": start,
        "no_cache": no_cache,
    }
    logging.info(f"Calling Google Search API with query: {query} for location: {location}")
    return _call_serpapi(params)
```

### 1.3 Google Local API (Business Results)

```python
def call_google_local_api(query, location):
    """For local business results."""
    params = {
        "engine": "google_local",
        "q": query,
        "location": location,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
    }
    logging.info(f"Calling Google Local API with query: {query} for location: {location}")
    return _call_serpapi(params)
```

### 1.4 Google Maps Reviews API

```python
def call_google_maps_reviews_api(place_id):
    """For business reviews."""
    params = {
        "engine": "google_maps_reviews",
        "place_id": place_id,
        "hl": "en",
    }
    logging.info(f"Calling Google Maps Reviews API for place_id: {place_id}")
    return _call_serpapi(params)
```

### 1.5 Google Trends API

```python
def call_google_trends_api(query, geo='US', date="today 12-m", data_type="TIMESERIES", include_low_search_volume=True):
    """For market demand, seasonality, related topics/queries."""
    params = {
        "engine": "google_trends",
        "q": query,
        "geo": geo,
        "date": date,
        "data_type": data_type,
        "tz": "420",  # US Central Time
        "low_search_volume": include_low_search_volume,
    }
    logging.info(f"Calling Google Trends API for query: {query}, data_type: {data_type}")
    return _call_serpapi(params)
```

### 1.6 Google News API

```python
def call_google_news_api(query, location):
    """For industry news and developments."""
    params = {
        "engine": "google_news",
        "q": query,
        "location": location,
        "gl": "us",
        "hl": "en",
    }
    logging.info(f"Calling Google News API with query: {query}")
    return _call_serpapi(params)
```

### 1.7 Google Autocomplete API

```python
def call_google_autocomplete_api(query):
    """For search suggestions."""
    params = {
        "engine": "google_autocomplete",
        "q": query,
        "hl": "en",
    }
    logging.info(f"Calling Google Autocomplete API with query: {query}")
    return _call_serpapi(params)
```

### 1.8 Related Questions (People Also Ask)

```python
def call_google_related_questions_api(query, location):
    """Specifically targets the 'People Also Ask' box from Google Search results."""
    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
    }
    # Note: related_questions are part of standard Google Search response
    logging.info(f"Calling Google Related Questions (via Search API) with query: {query}")
    return _call_serpapi(params)
```

### 1.9 Tool Contract Pattern (from tools.py)

```python
import time
import uuid
import logging
import serpapi
from tenacity import retry, stop_after_attempt, wait_exponential

def web_search_tool(query: str, location: str = "Austin, Texas, United States") -> dict:
    """
    Performs a web search using the SerpAPI client.
    Returns a standardized tool contract response.
    """
    start_time = time.time()
    trace_id = str(uuid.uuid4())

    if not SERPAPI_KEY:
        return {
            "ok": False,
            "data": "SERPAPI_KEY is not configured.",
            "cost": 0.0,
            "latency_ms": int((time.time() - start_time) * 1000),
            "trace_id": trace_id,
            "retries": 0,
        }

    try:
        search_results = _serpapi_search_with_retry(query, location)
        latency = int((time.time() - start_time) * 1000)
        logging.info(f"Web search successful for query '{query}'. Duration: {latency}ms.")

        return {
            "ok": True,
            "data": search_results.get("organic_results", []),
            "cost": 0.01,  # Estimated cost per API call
            "latency_ms": latency,
            "trace_id": trace_id,
            "retries": _serpapi_search_with_retry.retry.statistics.get("attempt_number", 1) - 1,
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        logging.error(f"Web search failed for query '{query}'. Duration: {latency}ms.", exc_info=True)
        return {
            "ok": False,
            "data": f"An error occurred during web search: {e}",
            "cost": 0.0,
            "latency_ms": latency,
            "trace_id": trace_id,
            "retries": _serpapi_search_with_retry.retry.statistics.get("attempt_number", 1) - 1,
        }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
def _serpapi_search_with_retry(query: str, location: str) -> dict:
    """Private function with retry logic."""
    logging.info(f"Performing SerpAPI search for query: {query}")
    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    search_results = serpapi.search(params)
    return search_results
```

### 1.10 Placeholder Endpoints (Not Implemented)

```python
def call_google_about_this_result_api(url):
    """Placeholder for Google About This Result API."""
    logging.info(f"Placeholder: Calling Google About This Result API for url: {url}")
    return None

def call_google_discussions_and_forums_api(query, location):
    """Placeholder for Google Discussions and Forums API."""
    return None

def call_google_images_api(query, location):
    """Placeholder for Google Images API."""
    return None

def call_google_videos_api(query, location):
    """Placeholder for Google Videos API."""
    return None

def call_youtube_search_api(query, location):
    """Placeholder for YouTube Search API."""
    return None

def call_google_shopping_api(query, location):
    """Placeholder for Google Shopping API."""
    return None
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **_call_serpapi helper** | HIGH | Central API caller with error handling |
| **12+ endpoint functions** | HIGH | Comprehensive SerpAPI coverage |
| **Tool contract pattern** | HIGH | {ok, data, cost, latency_ms, trace_id, retries} |
| **Tenacity retry** | HIGH | 3 attempts with exponential backoff |
| **Trace ID generation** | MEDIUM | UUID for request tracking |
| **Cost tracking** | MEDIUM | Per-call cost estimation |
| **Location parameter** | HIGH | All endpoints support geo-targeting |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| No response caching | Every call hits API | Add SQLite caching (like MarketIntel) |
| No rate limiting | Could hit API limits | Add rate limiter |
| Placeholder endpoints | Not implemented | Implement if needed |
| Hardcoded google_domain | Not configurable | Move to config |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. _call_serpapi helper pattern
2. All implemented endpoint functions
3. Tool contract return format
4. Retry decorator with statistics

**Integration Points:**
- `autobiz/tools/api/serpapi_client.py` - Core client
- `autobiz/tools/search/` - Search tool implementations
- `autobiz/core/` - Tool contract base class

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| API client | _call_serpapi | MarketIntel (with cache) | **USE MarketIntel** - has caching |
| Endpoints | 12+ functions | SerpApi (spec - same) | **USE Market_AI** - actual code |
| Retry | Tenacity (3 attempts) | MarketIntel (+ jitter) | **USE MarketIntel** - more robust |
| Tool contract | {ok, data, cost, ...} | None | **USE Market_AI** - unique |
| DuckDuckGo | None | Scraper (full impl) | **USE Scraper** - free alternative |

---

## 6. BEST VERSION RECOMMENDATION

**MERGE approach:**
1. **Endpoint functions** from Market_AI (comprehensive)
2. **Caching** from MarketIntel (SQLite response cache)
3. **Retry with jitter** from MarketIntel
4. **Tool contract** from Market_AI
5. **DuckDuckGo** from Scraper (free fallback)

---

## 7. SUPPORTED ENDPOINTS

| Endpoint | Status | Description |
|----------|--------|-------------|
| `call_google_search_api` | **Implemented** | Organic, ads, PAA |
| `call_google_local_api` | **Implemented** | Local business results |
| `call_google_maps_reviews_api` | **Implemented** | Business reviews |
| `call_google_trends_api` | **Implemented** | Trends, related queries |
| `call_google_news_api` | **Implemented** | News articles |
| `call_google_autocomplete_api` | **Implemented** | Search suggestions |
| `call_google_related_questions_api` | **Implemented** | People Also Ask |
| `call_google_about_this_result_api` | Placeholder | About This Result |
| `call_google_discussions_and_forums_api` | Placeholder | Discussions |
| `call_google_images_api` | Placeholder | Images |
| `call_google_videos_api` | Placeholder | Videos |
| `call_youtube_search_api` | Placeholder | YouTube |
| `call_google_shopping_api` | Placeholder | Shopping |
