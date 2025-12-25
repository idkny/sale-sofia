---
id: 20251201_data_extractors_serpapi
type: extraction
subject: data_extractors
source_repo: idkny/SerpApi
source_file: Note.md
description: "JSON response parsing and data extraction patterns from SerpApi planning"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, data_extractors, parsing, serpapi, json]
---

# DATA EXTRACTORS - SerpApi

**Source**: `idkny/SerpApi/Note.md`
**Type**: Specification (function signatures and logic)
**Purpose**: Parse SerpAPI JSON responses into clean, structured data for database insertion

---

## EXTRACTED DATA EXTRACTOR CODE

### 1. Text Cleaning Helper

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    """
    Basic text cleaning for extracted content.

    Args:
        text: Raw text string from API response

    Returns:
        str: Cleaned text with normalized whitespace

    Operations:
        - Strip leading/trailing whitespace
        - Normalize internal whitespace
        - Handle None gracefully
    """
    if not text:
        return ""
    return " ".join(text.split()).strip()
```

---

### 2. Organic Results Extractor

```python
def extract_organic_results(serpapi_response: dict) -> list[dict]:
    """
    Extract organic SERP results from Google Search response.

    Args:
        serpapi_response: Full JSON response from google engine

    Returns:
        list[dict]: List of organic results with standardized fields:
            - position: int
            - title: str
            - url: str
            - domain: str
            - snippet: str
            - date_published: str (if available)

    Response path: serpapi_response['organic_results']
    """
    results = []
    organic = serpapi_response.get('organic_results', [])

    for item in organic:
        result = {
            'position': item.get('position'),
            'title': _clean_text(item.get('title')),
            'url': item.get('link'),
            'domain': item.get('displayed_link', '').split('/')[0] if item.get('displayed_link') else None,
            'snippet': _clean_text(item.get('snippet')),
            'date_published': item.get('date')
        }
        results.append(result)
        logger.info(f"Extracted organic result: position={result['position']}, url={result['url']}")

    return results
```

---

### 3. Paid Ads Extractor

```python
def extract_paid_ads(serpapi_response: dict) -> list[dict]:
    """
    Extract paid advertisement results.

    Args:
        serpapi_response: Full JSON response

    Returns:
        list[dict]: List of ad results with:
            - position: int
            - title: str
            - link: str
            - displayed_link: str
            - snippet: str

    Response paths:
        - serpapi_response['ads'] (top ads)
        - serpapi_response['bottom_ads'] (bottom ads)
    """
    results = []

    # Top ads
    for item in serpapi_response.get('ads', []):
        results.append({
            'position': item.get('position'),
            'title': _clean_text(item.get('title')),
            'link': item.get('link'),
            'displayed_link': item.get('displayed_link'),
            'snippet': _clean_text(item.get('description'))
        })

    # Bottom ads (append after top)
    for item in serpapi_response.get('bottom_ads', []):
        results.append({
            'position': item.get('position'),
            'title': _clean_text(item.get('title')),
            'link': item.get('link'),
            'displayed_link': item.get('displayed_link'),
            'snippet': _clean_text(item.get('description'))
        })

    logger.info(f"Extracted {len(results)} paid ads")
    return results
```

---

### 4. Local Business Results Extractor

```python
def extract_local_business_results(serpapi_response: dict) -> list[dict]:
    """
    Extract Google Maps/Local Pack business results.

    Args:
        serpapi_response: Response from google_local engine

    Returns:
        list[dict]: List of businesses with:
            - business_name: str
            - address: str
            - phone: str
            - website: str
            - google_maps_link: str
            - rating: float
            - total_reviews: int
            - category: str
            - place_id: str (for review fetching)

    Response path: serpapi_response['local_results']
    """
    results = []
    local = serpapi_response.get('local_results', [])

    for item in local:
        result = {
            'business_name': _clean_text(item.get('title')),
            'address': _clean_text(item.get('address')),
            'phone': item.get('phone'),
            'website': item.get('website'),
            'google_maps_link': item.get('link'),
            'rating': item.get('rating'),
            'total_reviews': item.get('reviews'),
            'category': item.get('type'),
            'place_id': item.get('place_id')
        }
        results.append(result)
        logger.info(f"Extracted local business: {result['business_name']}")

    return results
```

---

### 5. Google Trends Extractor

```python
def extract_trends_data(serpapi_response: dict) -> dict:
    """
    Extract Google Trends data (interest over time + related).

    Args:
        serpapi_response: Response from google_trends engine

    Returns:
        dict with keys:
            - interest_over_time: list[dict] with:
                - date: str
                - interest_value: int
            - related_topics: list[dict] with:
                - topic_text: str
                - extracted_value: str
                - data_type: str ('rising' or 'top')
            - related_queries: list[dict] with:
                - query_text: str
                - extracted_value: str
                - data_type: str ('rising' or 'top')

    Response paths:
        - serpapi_response['interest_over_time']['timeline_data']
        - serpapi_response['related_topics']['rising']
        - serpapi_response['related_topics']['top']
        - serpapi_response['related_queries']['rising']
        - serpapi_response['related_queries']['top']
    """
    result = {
        'interest_over_time': [],
        'related_topics': [],
        'related_queries': []
    }

    # Interest over time
    timeline = serpapi_response.get('interest_over_time', {}).get('timeline_data', [])
    for point in timeline:
        result['interest_over_time'].append({
            'date': point.get('date'),
            'interest_value': point.get('values', [{}])[0].get('value', 0)
        })

    # Related topics
    topics = serpapi_response.get('related_topics', {})
    for topic in topics.get('rising', []):
        result['related_topics'].append({
            'topic_text': topic.get('topic', {}).get('title'),
            'extracted_value': topic.get('value'),
            'data_type': 'rising'
        })
    for topic in topics.get('top', []):
        result['related_topics'].append({
            'topic_text': topic.get('topic', {}).get('title'),
            'extracted_value': topic.get('value'),
            'data_type': 'top'
        })

    # Related queries
    queries = serpapi_response.get('related_queries', {})
    for query in queries.get('rising', []):
        result['related_queries'].append({
            'query_text': query.get('query'),
            'extracted_value': query.get('value'),
            'data_type': 'rising'
        })
    for query in queries.get('top', []):
        result['related_queries'].append({
            'query_text': query.get('query'),
            'extracted_value': query.get('value'),
            'data_type': 'top'
        })

    logger.info(f"Extracted trends: {len(result['interest_over_time'])} timeline points, "
                f"{len(result['related_topics'])} topics, {len(result['related_queries'])} queries")

    return result
```

---

### 6. News Articles Extractor

```python
def extract_news_articles(serpapi_response: dict) -> list[dict]:
    """
    Extract Google News article results.

    Args:
        serpapi_response: Response from google_news engine

    Returns:
        list[dict]: News articles with:
            - title: str
            - url: str
            - source: str
            - published_date: str
            - snippet: str

    Response path: serpapi_response['news_results']
    """
    results = []
    news = serpapi_response.get('news_results', [])

    for item in news:
        result = {
            'title': _clean_text(item.get('title')),
            'url': item.get('link'),
            'source': item.get('source'),
            'published_date': item.get('date'),
            'snippet': _clean_text(item.get('snippet'))
        }
        results.append(result)

    logger.info(f"Extracted {len(results)} news articles")
    return results
```

---

### 7. Related Questions (PAA) Extractor

```python
def extract_related_questions(serpapi_response: dict) -> list[dict]:
    """
    Extract People Also Ask questions.

    Args:
        serpapi_response: Response from google engine (with or without json_restrictor)

    Returns:
        list[dict]: PAA items with:
            - question_text: str
            - answer_snippet: str

    Response path: serpapi_response['related_questions']
    """
    results = []
    questions = serpapi_response.get('related_questions', [])

    for item in questions:
        result = {
            'question_text': _clean_text(item.get('question')),
            'answer_snippet': _clean_text(item.get('snippet'))
        }
        results.append(result)

    logger.info(f"Extracted {len(results)} related questions (PAA)")
    return results
```

---

### 8. Autocomplete Suggestions Extractor

```python
def extract_autocomplete_suggestions(serpapi_response: dict) -> list[str]:
    """
    Extract Google Autocomplete suggestions.

    Args:
        serpapi_response: Response from google_autocomplete engine

    Returns:
        list[str]: List of suggestion strings

    Response path: serpapi_response['suggestions']
    """
    suggestions = []
    for item in serpapi_response.get('suggestions', []):
        query = item.get('value')
        if query:
            suggestions.append(_clean_text(query))

    logger.info(f"Extracted {len(suggestions)} autocomplete suggestions")
    return suggestions
```

---

### 9. AI Post-Processing Placeholders

```python
def classify_organic_result_ai(organic_result_id: int, title: str, snippet: str) -> dict:
    """
    PLACEHOLDER: AI classification of organic result.

    Would later call external AI APIs (GPT, Google NLP) to:
        - Classify content_type (blog, product, forum, etc.)
        - Classify search_intent (informational, transactional, navigational)
        - Classify site_category (competitor, review site, news, etc.)

    Args:
        organic_result_id: Database ID for updating
        title: Result title
        snippet: Result snippet

    Returns:
        dict: Classification results (currently empty)
    """
    logger.info(f"AI classification placeholder for organic_result_id={organic_result_id}")
    return {}


def extract_entities_ai(source_item_id: int, source_table: str, text: str) -> list[dict]:
    """
    PLACEHOLDER: AI entity extraction.

    Would later call external AI APIs to extract:
        - Named entities (people, places, organizations)
        - Entity salience/importance
        - Sentiment per entity

    Args:
        source_item_id: ID of source record
        source_table: Table name for polymorphic FK
        text: Text to analyze

    Returns:
        list[dict]: Extracted entities (currently empty)
    """
    logger.info(f"AI entity extraction placeholder for {source_table}:{source_item_id}")
    return []
```

---

## RESPONSE PATH REFERENCE

| Extractor | Response Path | Note |
|-----------|---------------|------|
| Organic | `response['organic_results']` | List of dicts |
| Paid Ads | `response['ads']` + `response['bottom_ads']` | Separate top/bottom |
| Local | `response['local_results']` | List of businesses |
| Trends | `response['interest_over_time']['timeline_data']` | Nested |
| Trends | `response['related_topics']['rising'/'top']` | Two sublists |
| Trends | `response['related_queries']['rising'/'top']` | Two sublists |
| News | `response['news_results']` | List of articles |
| PAA | `response['related_questions']` | List of Q&A |
| Autocomplete | `response['suggestions']` | List with 'value' key |

---

## CONCLUSIONS

### What is Good / Usable

1. **Standardized output format** - Consistent dict structure for DB insertion
2. **Defensive .get()** - Handles missing fields gracefully
3. **_clean_text helper** - Centralizes text normalization
4. **Logging throughout** - Traceable extraction process
5. **Response path documentation** - Clear mapping to API structure

### What is Outdated

1. **No Pydantic models** - Using raw dicts instead of validated models
2. **No type hints** - Limited typing (should use TypedDict or dataclass)
3. **Minimal error handling** - Should catch specific exceptions
4. **No extraction metrics** - Should track success/failure rates

### What Must Be Rewritten

1. **Add Pydantic models** for input validation and output structure
2. **Add TypedDict** or **dataclass** for extracted data
3. **Add error handling** for malformed responses
4. **Add extraction stats** (items extracted, fields missing, etc.)

### How It Fits Into AutoBiz

- **Port extractors** with Pydantic model wrappers
- **Add to data pipeline** between API call and DB insert
- **Use for SerpAPI integration** (if/when added to AutoBiz)
- **Pattern reusable** for other JSON APIs

### Conflicts with Previous Repos

| Feature | SerpApi (This) | MarketIntel | Best |
|---------|----------------|-------------|------|
| Response parsing | Comprehensive | Similar | Same patterns |
| Validation | None | None | Need Pydantic |
| Text cleaning | Basic | Similar | Same |
| AI placeholders | Yes | OllamaClient | MarketIntel |

### Best Version

**SerpApi's extractors are more comprehensive** (more endpoints covered), but need Pydantic wrapping for production use.

---

## REUSABLE PATTERNS SUMMARY

```python
# Pattern 1: Defensive extraction with .get()
def extract_X(response: dict) -> list[dict]:
    results = []
    for item in response.get('X_results', []):
        results.append({
            'field1': _clean_text(item.get('field1')),
            'field2': item.get('field2'),  # numeric, no clean
        })
    return results

# Pattern 2: Nested path extraction
value = response.get('level1', {}).get('level2', {}).get('field')

# Pattern 3: Multi-list extraction (rising + top)
for category in ['rising', 'top']:
    for item in data.get(category, []):
        item['data_type'] = category
        results.append(item)

# Pattern 4: AI placeholder pattern
def process_ai(id: int, text: str) -> dict:
    logger.info(f"AI placeholder for {id}")
    return {}  # Replace with actual AI call later
```
