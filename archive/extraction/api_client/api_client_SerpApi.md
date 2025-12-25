---
id: 20251201_api_client_serpapi
type: extraction
subject: api_clients
source_repo: idkny/SerpApi
source_file: Note.md
description: "SerpAPI client specifications from planning document"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, api_client, serpapi, http]
---

# API CLIENTS - SerpApi

**Source**: `idkny/SerpApi/Note.md`
**Type**: Specification (function signatures and endpoint mappings)
**API**: SerpAPI (google-search-results library)

---

## EXTRACTED API CLIENT CODE

### 1. Configuration & Setup

```python
import os
import serpapi
import logging
import time

# Load API key from environment
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise EnvironmentError("SERPAPI_API_KEY not found in environment variables")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

---

### 2. Core API Caller (Internal Helper)

```python
def _call_serpapi(engine: str, params: dict) -> dict:
    """
    Internal helper to make SerpApi calls.

    Args:
        engine: SerpAPI engine name ('google', 'google_local', 'google_trends', etc.)
        params: Dictionary of API parameters

    Returns:
        dict: JSON response from SerpAPI

    Handles:
        - Network errors
        - SerpAPI-specific errors
        - Logging of requests

    Note: Should add retry logic with exponential backoff
    """
    try:
        params['api_key'] = SERPAPI_API_KEY
        params['engine'] = engine

        logger.info(f"Calling SerpAPI engine={engine} with params={params}")

        # Using serpapi library
        search = serpapi.search(params)
        return search

    except Exception as e:
        logger.error(f"SerpAPI error for engine={engine}: {e}")
        raise
```

---

### 3. Google Search API

```python
def call_google_search_api(query: str, location: str, device: str = 'desktop',
                           num: int = 20, start: int = 0, no_cache: bool = False,
                           json_restrictor: str = None) -> dict:
    """
    General Google SERP search.

    Args:
        query: Search query string
        location: Location string (e.g., "Austin, Texas, United States")
        device: 'desktop' or 'mobile'
        num: Number of results (max 100)
        start: Pagination offset
        no_cache: Force fresh results (costs more credits)
        json_restrictor: Limit response to specific section
            Options: 'organic_results', 'related_questions', 'local_results', etc.

    Returns:
        dict: Full SERP response including:
            - organic_results
            - ads (paid results)
            - related_questions (PAA)
            - local_results
            - knowledge_graph
            - etc.

    Use cases:
        - Competitor organic rankings
        - Paid ad monitoring
        - PAA/FAQ discovery
        - Content gap analysis
    """
    params = {
        'q': query,
        'location': location,
        'device': device,
        'num': num,
        'start': start,
        'no_cache': no_cache
    }
    if json_restrictor:
        params['json_restrictor'] = json_restrictor

    return _call_serpapi('google', params)
```

---

### 4. Google Local API

```python
def call_google_local_api(query: str, location: str) -> dict:
    """
    Google Maps local business search.

    Args:
        query: Business type query (e.g., "air duct cleaning")
        location: Location string

    Returns:
        dict: Local results including:
            - local_results: List of businesses with:
                - title (business name)
                - address
                - phone
                - website
                - rating
                - reviews
                - place_id (for fetching reviews)
                - gps_coordinates

    Use cases:
        - Competitor discovery
        - Local market analysis
        - Review monitoring
    """
    params = {
        'q': query,
        'location': location
    }
    return _call_serpapi('google_local', params)
```

---

### 5. Google Maps Reviews API

```python
def call_google_maps_reviews_api(place_id: str) -> dict:
    """
    Fetch reviews for a specific business.

    Args:
        place_id: Google Place ID from local search results

    Returns:
        dict: Reviews data including:
            - reviews: List of review objects with:
                - rating
                - date
                - text
                - user (reviewer info)
            - rating_breakdown: Distribution by stars

    Use cases:
        - Competitor reputation analysis
        - Customer sentiment mining
        - Service improvement insights
    """
    params = {
        'place_id': place_id
    }
    return _call_serpapi('google_maps_reviews', params)
```

---

### 6. Google Trends API

```python
def call_google_trends_api(query: str, geo: str, date: str,
                           data_type: str, include_low_search_volume: bool = True) -> dict:
    """
    Google Trends interest and related queries.

    Args:
        query: Keyword to analyze
        geo: Geographic code (e.g., 'US-TX' for Texas)
        date: Date range string:
            - 'today 12-m' (last 12 months)
            - 'today 3-m' (last 3 months)
            - '2023-01-01 2023-12-31' (custom range)
        data_type: Type of trends data:
            - 'TIMESERIES': Interest over time
            - 'RELATED_TOPICS': Related topics
            - 'RELATED_QUERIES': Related search queries
            - 'GEO_MAP': Interest by region
        include_low_search_volume: Include low-volume terms

    Returns:
        dict: Trends data based on data_type:
            - interest_over_time: Time series of interest values
            - related_topics: Rising/top topics
            - related_queries: Rising/top queries

    Use cases:
        - Seasonality analysis
        - Trend discovery
        - Keyword expansion
        - Market demand tracking
    """
    params = {
        'q': query,
        'geo': geo,
        'date': date,
        'data_type': data_type,
        'include_low_search_volume': include_low_search_volume
    }
    return _call_serpapi('google_trends', params)
```

---

### 7. Google News API

```python
def call_google_news_api(query: str, location: str) -> dict:
    """
    Google News search results.

    Args:
        query: News search query
        location: Location string

    Returns:
        dict: News results including:
            - news_results: List of articles with:
                - title
                - link
                - source
                - date
                - snippet
                - thumbnail

    Use cases:
        - Industry news monitoring
        - PR/brand monitoring
        - Competitor news tracking
    """
    params = {
        'q': query,
        'location': location
    }
    return _call_serpapi('google_news', params)
```

---

### 8. Google Autocomplete API

```python
def call_google_autocomplete_api(query: str) -> dict:
    """
    Google search autocomplete suggestions.

    Args:
        query: Partial query string

    Returns:
        dict: Suggestions including:
            - suggestions: List of autocomplete strings

    Use cases:
        - Keyword discovery
        - User intent research
        - Long-tail keyword mining
    """
    params = {
        'q': query
    }
    return _call_serpapi('google_autocomplete', params)
```

---

### 9. Google Related Questions API

```python
def call_google_related_questions_api(query: str, location: str) -> dict:
    """
    Specifically targets People Also Ask box.

    Args:
        query: Search query
        location: Location string

    Returns:
        dict: Related questions with:
            - related_questions: List of PAA items with:
                - question
                - snippet
                - link

    Note: Uses json_restrictor='related_questions' with google engine
    """
    params = {
        'q': query,
        'location': location,
        'json_restrictor': 'related_questions'
    }
    return _call_serpapi('google', params)
```

---

### 10. Additional Endpoint Placeholders

```python
def call_google_about_this_result_api(url: str) -> dict:
    """Get information about a specific URL's search presence."""
    params = {'url': url}
    return _call_serpapi('google_about_this_result', params)

def call_google_discussions_and_forums_api(query: str, location: str) -> dict:
    """Search discussions and forums."""
    params = {'q': query, 'location': location}
    return _call_serpapi('google_discussions', params)

def call_google_images_api(query: str, location: str) -> dict:
    """Image search results."""
    params = {'q': query, 'location': location}
    return _call_serpapi('google_images', params)

def call_google_videos_api(query: str, location: str) -> dict:
    """Video search results."""
    params = {'q': query, 'location': location}
    return _call_serpapi('google_videos', params)

def call_youtube_search_api(query: str, location: str) -> dict:
    """YouTube search results."""
    params = {'search_query': query, 'location': location}
    return _call_serpapi('youtube', params)

def call_google_shopping_api(query: str, location: str) -> dict:
    """Shopping/product search results."""
    params = {'q': query, 'location': location}
    return _call_serpapi('google_shopping', params)

def call_locations_api(query: str) -> dict:
    """Get canonical SerpAPI location IDs."""
    params = {'q': query}
    return _call_serpapi('google_locations', params)

def call_search_archive_api(serpapi_id: str) -> dict:
    """Retrieve archived search results by SerpAPI ID."""
    params = {'search_archive_id': serpapi_id}
    return _call_serpapi('search_archive', params)
```

---

## SERPAPI ENDPOINT REGISTRY

| Endpoint | Engine Name | Key Params | Primary Use |
|----------|-------------|------------|-------------|
| Google Search | `google` | q, location, num, device | Organic + PAA |
| Google Local | `google_local` | q, location | Local businesses |
| Maps Reviews | `google_maps_reviews` | place_id | Business reviews |
| Trends | `google_trends` | q, geo, date, data_type | Market demand |
| News | `google_news` | q, location | News monitoring |
| Autocomplete | `google_autocomplete` | q | Keyword discovery |
| Images | `google_images` | q, location | Image SERP |
| Videos | `google_videos` | q, location | Video SERP |
| YouTube | `youtube` | search_query | YouTube search |
| Shopping | `google_shopping` | q, location | Product search |
| Locations | `google_locations` | q | Location ID lookup |
| Archive | `search_archive` | search_archive_id | Retrieve past searches |

---

## CONCLUSIONS

### What is Good / Usable

1. **Comprehensive endpoint coverage** - 12+ SerpAPI engines mapped
2. **Function-per-endpoint pattern** - Clean separation of concerns
3. **Parameter documentation** - Clear args and use cases
4. **json_restrictor** - Efficient response filtering
5. **place_id chaining** - Local → Reviews workflow

### What is Outdated

1. **No retry logic** - Missing exponential backoff
2. **No caching** - Every call hits API
3. **No rate limiting** - Risk of API quota exhaustion
4. **No async support** - Blocking calls only

### What Must Be Rewritten

1. **Add retry with backoff** - Handle transient failures
2. **Add response caching** - SQLite or Redis cache
3. **Add rate limiting** - Token bucket or similar
4. **Add async variants** - For concurrent requests
5. **Add response validation** - Pydantic models

### How It Fits Into AutoBiz

- **Port endpoint registry** directly
- **Add caching layer** from MarketIntel
- **Add retry logic** from MarketIntel
- **Use for market research pipelines**

### Conflicts with Previous Repos

| Feature | SerpApi (This) | MarketIntel | Best |
|---------|----------------|-------------|------|
| Endpoints | 12+ | ~5 | SerpApi (more complete) |
| Caching | None | SQLite + TTL | MarketIntel |
| Retry | None | Exp backoff + jitter | MarketIntel |
| Rate limiting | None | None | Need to add |
| Async | None | None | Need to add |

### Best Version

**Merge**: SerpApi's comprehensive endpoint registry + MarketIntel's caching/retry infrastructure.

---

## REUSABLE PATTERNS SUMMARY

```python
# Pattern 1: Function-per-endpoint
def call_{engine}_api(required_params, **optional_params) -> dict:
    params = {required_params, **optional_params}
    return _call_serpapi('{engine}', params)

# Pattern 2: Endpoint registry
SERPAPI_ENDPOINTS = {
    'google': {'required': ['q'], 'optional': ['location', 'num', 'device']},
    'google_local': {'required': ['q', 'location']},
    'google_trends': {'required': ['q', 'geo', 'date', 'data_type']},
    # ...
}

# Pattern 3: Response chaining
# Local search → get place_id → Reviews lookup
local_results = call_google_local_api(query, location)
for business in local_results.get('local_results', []):
    place_id = business.get('place_id')
    if place_id:
        reviews = call_google_maps_reviews_api(place_id)
```
