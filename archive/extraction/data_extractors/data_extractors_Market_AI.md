---
id: 20251201_data_extractors_market_ai
type: extraction
subject: data_extractors
source_repo: Market_AI
description: "7 extractor functions for SerpAPI response parsing with _clean_text helper"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [data, extraction, parsing, serpapi, json, cleaning]
---

# SUBJECT: data_extractors/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `SerpApi/src/data_extractor.py` (173 lines)

---

## 1. EXTRACTED CODE

### 1.1 Text Cleaning Helper

```python
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _clean_text(text):
    """A helper for basic text cleaning (whitespace, stripping)."""
    return text.strip() if isinstance(text, str) else text
```

### 1.2 Extract Organic Results

```python
def extract_organic_results(serpapi_response):
    """Extracts and cleans organic results from a SerpApi response."""
    extracted_data = []
    if not serpapi_response or 'organic_results' not in serpapi_response:
        return extracted_data

    for result in serpapi_response['organic_results']:
        extracted_data.append({
            'position': result.get('position'),
            'title': _clean_text(result.get('title')),
            'url': result.get('link'),
            'domain': result.get('source'),
            'snippet': _clean_text(result.get('snippet')),
            'date_published': result.get('date'),
        })
    logging.info(f"Extracted {len(extracted_data)} organic results.")
    return extracted_data
```

### 1.3 Extract Paid Ads

```python
def extract_paid_ads(serpapi_response):
    """Extracts and cleans paid ads from a SerpApi response."""
    extracted_data = []
    if not serpapi_response or 'ads' not in serpapi_response:
        return extracted_data

    for ad in serpapi_response['ads']:
        extracted_data.append({
            'position': ad.get('position'),
            'title': _clean_text(ad.get('title')),
            'link': ad.get('link'),
            'displayed_link': ad.get('displayed_link'),
            'snippet': _clean_text(ad.get('snippet')),
        })
    logging.info(f"Extracted {len(extracted_data)} paid ads.")
    return extracted_data
```

### 1.4 Extract Local Business Results

```python
def extract_local_business_results(serpapi_response):
    """Extracts and cleans local business results from a SerpApi response."""
    extracted_data = []
    if not serpapi_response or 'local_results' not in serpapi_response:
        return extracted_data

    for result in serpapi_response['local_results']:
        extracted_data.append({
            'business_name': _clean_text(result.get('title')),
            'address': _clean_text(result.get('address')),
            'phone': result.get('phone'),
            'website': result.get('website'),
            'google_maps_link': result.get('link'),
            'rating': result.get('rating'),
            'total_reviews': result.get('reviews'),
            'category': _clean_text(result.get('type')),
            'place_id': result.get('place_id'),
        })
    logging.info(f"Extracted {len(extracted_data)} local business results.")
    return extracted_data
```

### 1.5 Extract Google Trends Data

```python
def extract_trends_data(serpapi_response):
    """Extracts and cleans trends data from a SerpApi response."""
    extracted_data = []
    if not serpapi_response:
        return extracted_data

    # For interest over time
    if 'interest_over_time' in serpapi_response:
        for item in serpapi_response['interest_over_time'].get('timeline_data', []):
            extracted_data.append({
                'data_type': 'interest_over_time',
                'date': item.get('date'),
                'interest_value': item.get('values', [{}])[0].get('value'),
                'trending_topic_or_query_text': None,
                'extracted_value': None
            })

    # For related queries
    if 'related_queries' in serpapi_response:
        for query_type, queries in serpapi_response['related_queries'].items():
            for query in queries:
                extracted_data.append({
                    'data_type': f'related_queries_{query_type}',
                    'date': None,
                    'interest_value': None,
                    'trending_topic_or_query_text': _clean_text(query.get('query')),
                    'extracted_value': query.get('value')
                })

    # For related topics
    if 'related_topics' in serpapi_response:
        for topic_type, topics in serpapi_response['related_topics'].items():
            for topic in topics:
                extracted_data.append({
                    'data_type': f'related_topics_{topic_type}',
                    'date': None,
                    'interest_value': None,
                    'trending_topic_or_query_text': _clean_text(topic.get('topic', {}).get('title')),
                    'extracted_value': topic.get('value')
                })

    logging.info(f"Extracted {len(extracted_data)} trends data points.")
    return extracted_data
```

### 1.6 Extract News Articles

```python
def extract_news_articles(serpapi_response):
    """Extracts and cleans news articles from a SerpApi response."""
    extracted_data = []
    if not serpapi_response or 'news_results' not in serpapi_response:
        return extracted_data

    for article in serpapi_response['news_results']:
        extracted_data.append({
            'title': _clean_text(article.get('title')),
            'url': article.get('link'),
            'source': _clean_text(article.get('source', {}).get('name')),
            'published_date': article.get('date'),
            'snippet': _clean_text(article.get('snippet')),
        })
    logging.info(f"Extracted {len(extracted_data)} news articles.")
    return extracted_data
```

### 1.7 Extract Related Questions (People Also Ask)

```python
def extract_related_questions(serpapi_response):
    """Extracts and cleans related questions from a SerpApi response."""
    extracted_data = []
    if not serpapi_response or 'related_questions' not in serpapi_response:
        return extracted_data

    for question in serpapi_response['related_questions']:
        extracted_data.append({
            'question_text': _clean_text(question.get('question')),
            'answer_snippet': _clean_text(question.get('snippet')),
        })
    logging.info(f"Extracted {len(extracted_data)} related questions.")
    return extracted_data
```

### 1.8 Extract Autocomplete Suggestions

```python
def extract_autocomplete_suggestions(serpapi_response):
    """Extracts and cleans autocomplete suggestions from a SerpApi response."""
    extracted_data = []
    if not serpapi_response or 'suggestions' not in serpapi_response:
        return extracted_data

    for suggestion in serpapi_response['suggestions']:
        extracted_data.append({
            'query': _clean_text(suggestion.get('value')),
        })
    logging.info(f"Extracted {len(extracted_data)} autocomplete suggestions.")
    return extracted_data
```

### 1.9 AI Classification Placeholders

```python
def classify_organic_result_ai(organic_result_id, title, snippet):
    """Placeholder for classifying an organic result using an AI model."""
    logging.info(f"Placeholder: AI-classifying organic result ID {organic_result_id}")
    # Future: Call external AI API (GPT, Google NLP)
    return {
        'content_type': 'Unknown',
        'search_intent_classified': 'Informational',
        'site_category_classified': 'General'
    }

def extract_entities_ai(source_item_id, source_table, text):
    """Placeholder for extracting entities from text using an AI model."""
    logging.info(f"Placeholder: AI-extracting entities from {source_table} ID {source_item_id}")
    # Future: Call NLP API for entity extraction
    return []
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **7 extractor functions** | HIGH | Complete SerpAPI response parsing |
| **_clean_text helper** | HIGH | Reusable text sanitization |
| **Structured output** | HIGH | Consistent dict format for DB insertion |
| **Nested data handling** | HIGH | Handles complex response structures |
| **Logging** | MEDIUM | Extraction counts logged |
| **Null safety** | HIGH | Safe .get() with defaults |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| No Pydantic models | Returns raw dicts | Add Pydantic validation |
| AI placeholders | Not implemented | Connect to Ollama |
| Basic text cleaning | Only strip() | Add more sanitization |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. All 7 extractor functions
2. _clean_text helper
3. Extraction logging pattern

**Integration Points:**
- `autobiz/tools/api/extractors.py` - Response parsers
- `autobiz/tools/data/` - Feed into database layer

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| Extractors | 7 functions (actual code) | SerpApi (spec - same) | **USE Market_AI** - actual implementation |
| AI classification | Placeholders | MarketIntel (confidence-based) | **USE MarketIntel** - implemented |
| Entity extraction | Placeholder | None | Implement later |

---

## 6. BEST VERSION RECOMMENDATION

**Market_AI is the ONLY repo with actual extractor implementations.**

**Recommended enhancements:**
1. Add Pydantic models for validation
2. Connect AI placeholders to Ollama (use MarketIntel's classification)
3. Add more robust text cleaning
4. Add error handling for malformed responses

---

## 7. EXTRACTOR COVERAGE

| Response Type | Function | Fields Extracted |
|---------------|----------|------------------|
| Organic Results | `extract_organic_results` | position, title, url, domain, snippet, date |
| Paid Ads | `extract_paid_ads` | position, title, link, displayed_link, snippet |
| Local Business | `extract_local_business_results` | name, address, phone, website, rating, reviews, category, place_id |
| Trends | `extract_trends_data` | data_type, date, interest_value, topic/query, value |
| News | `extract_news_articles` | title, url, source, date, snippet |
| Related Questions | `extract_related_questions` | question_text, answer_snippet |
| Autocomplete | `extract_autocomplete_suggestions` | query |
