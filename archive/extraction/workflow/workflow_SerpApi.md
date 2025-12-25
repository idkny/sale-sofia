---
id: 20251201_workflow_serpapi
type: extraction
subject: workflows
source_repo: idkny/SerpApi
source_file: Note.md
description: "Orchestration and pipeline patterns from SerpApi planning document"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, workflow, orchestration, pipeline, serpapi]
---

# WORKFLOWS / ORCHESTRATION - SerpApi

**Source**: `idkny/SerpApi/Note.md`
**Type**: Specification (orchestration logic and discovery pipelines)

---

## EXTRACTED WORKFLOW CODE

### 1. Main Research Cycle Orchestrator

```python
# src/main.py

import logging
from datetime import datetime

import api_client
import db_interface
import data_extractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_market_research_cycle():
    """
    Main orchestration function for market research.

    Flow:
        1. Initialize database
        2. Loop through locations
        3. Loop through keywords
        4. For each (keyword, location) pair:
            - Call multiple SerpAPI engines
            - Extract data from responses
            - Insert into database
        5. Run keyword discovery
        6. Log completion

    Error handling:
        - Continue on individual failures
        - Log errors but don't halt cycle
    """
    # Initialize database
    db_interface.init_db()
    logger.info("Database initialized")

    # Process each location
    for loc in TARGET_CITIES:
        location_id = db_interface.get_or_insert_location(
            city=loc['city'],
            state=loc['state'],
            country=loc['country']
        )
        logger.info(f"Processing location: {loc['city']}, {loc['state']}")

        # Process core + indirect keywords
        all_keywords = CORE_KEYWORDS + INDIRECT_KEYWORDS

        for keyword_text in all_keywords:
            try:
                process_keyword_location_pair(keyword_text, location_id, loc)
            except Exception as e:
                logger.error(f"Error processing {keyword_text} in {loc['city']}: {e}")
                continue  # Continue with next keyword

    # Run keyword discovery after main cycle
    run_keyword_discovery()

    logger.info("Market research cycle completed")
```

---

### 2. Keyword-Location Pair Processor

```python
def process_keyword_location_pair(keyword_text: str, location_id: int, location_dict: dict):
    """
    Process a single keyword-location combination across all SerpAPI engines.

    Args:
        keyword_text: Keyword string
        location_id: Database ID for location
        location_dict: Location data for API calls

    Flow for each engine:
        1. Get/insert keyword
        2. Call SerpAPI engine
        3. Create search session
        4. Extract data
        5. Insert results linked to session
    """
    # Get or insert keyword (idempotent)
    keyword_id = db_interface.get_or_insert_keyword(
        keyword_text=keyword_text,
        initial_category='core' if keyword_text in CORE_KEYWORDS else 'indirect'
    )

    location_str = f"{location_dict['city']}, {location_dict['state']}, {location_dict['country']}"

    # --- Google Search (organic + ads + PAA) ---
    try:
        response = api_client.call_google_search_api(
            query=keyword_text,
            location=location_str,
            device='desktop',
            num=20
        )

        session_id = db_interface.create_search_session(
            keyword_id=keyword_id,
            location_id=location_id,
            engine_used='google',
            device_type='desktop',
            serpapi_id=response.get('search_metadata', {}).get('id')
        )

        # Extract and insert organic results
        organic_results = data_extractor.extract_organic_results(response)
        for result in organic_results:
            db_interface.insert_organic_result(session_id=session_id, **result)

        # Extract and insert paid ads
        paid_ads = data_extractor.extract_paid_ads(response)
        for ad in paid_ads:
            db_interface.insert_paid_ad(session_id=session_id, **ad)

        # Extract and insert related questions (PAA)
        questions = data_extractor.extract_related_questions(response)
        for question in questions:
            db_interface.insert_related_question(session_id=session_id, **question)

        logger.info(f"Google Search: {len(organic_results)} organic, {len(paid_ads)} ads, {len(questions)} PAA")

    except Exception as e:
        logger.error(f"Google Search failed for {keyword_text}: {e}")

    # --- Google Local (business listings) ---
    try:
        response = api_client.call_google_local_api(
            query=keyword_text,
            location=location_str
        )

        session_id = db_interface.create_search_session(
            keyword_id=keyword_id,
            location_id=location_id,
            engine_used='google_local',
            device_type='desktop',
            serpapi_id=response.get('search_metadata', {}).get('id')
        )

        local_results = data_extractor.extract_local_business_results(response)
        for business in local_results:
            db_interface.insert_local_business_result(session_id=session_id, **business)

            # Optionally fetch reviews for each business
            place_id = business.get('place_id')
            if place_id:
                try:
                    reviews_response = api_client.call_google_maps_reviews_api(place_id)
                    # Process reviews (store in separate table or JSON field)
                except Exception as review_error:
                    logger.warning(f"Reviews fetch failed for {place_id}: {review_error}")

        logger.info(f"Google Local: {len(local_results)} businesses")

    except Exception as e:
        logger.error(f"Google Local failed for {keyword_text}: {e}")

    # --- Google Trends ---
    try:
        geo_code = "US-TX"  # Texas
        for data_type in ['TIMESERIES', 'RELATED_QUERIES', 'RELATED_TOPICS']:
            response = api_client.call_google_trends_api(
                query=keyword_text,
                geo=geo_code,
                date='today 12-m',
                data_type=data_type
            )

            trends_data = data_extractor.extract_trends_data(response)

            # Insert interest over time
            for point in trends_data.get('interest_over_time', []):
                db_interface.insert_google_trends_data(
                    keyword_id=keyword_id,
                    location_id=location_id,
                    date_range_query='today 12-m',
                    data_type='TIMESERIES',
                    interest_value=point['interest_value']
                )

            # Insert related queries as new keywords
            for query in trends_data.get('related_queries', []):
                db_interface.get_or_insert_keyword(
                    keyword_text=query['query_text'],
                    initial_category='trend-discovered',
                    source_endpoint='google_trends',
                    base_query=keyword_text
                )

        logger.info(f"Google Trends: processed for {keyword_text}")

    except Exception as e:
        logger.error(f"Google Trends failed for {keyword_text}: {e}")

    # --- Google News ---
    try:
        response = api_client.call_google_news_api(
            query=keyword_text,
            location=location_str
        )

        session_id = db_interface.create_search_session(
            keyword_id=keyword_id,
            location_id=location_id,
            engine_used='google_news',
            device_type='desktop',
            serpapi_id=response.get('search_metadata', {}).get('id')
        )

        news_articles = data_extractor.extract_news_articles(response)
        for article in news_articles:
            db_interface.insert_news_article(session_id=session_id, **article)

        logger.info(f"Google News: {len(news_articles)} articles")

    except Exception as e:
        logger.error(f"Google News failed for {keyword_text}: {e}")
```

---

### 3. Keyword Discovery Pipeline

```python
def run_keyword_discovery():
    """
    Automated keyword discovery from multiple sources.

    Sources:
        1. Google Autocomplete - query suggestions
        2. Google Trends - related queries and topics
        3. SERP PAA - related questions as keywords
        4. News articles - extract keywords from headlines

    All discovered keywords inserted with status='pending_review'
    """
    logger.info("Starting keyword discovery pipeline")

    # Discover from autocomplete
    for seed_keyword in CORE_KEYWORDS:
        discover_from_autocomplete(seed_keyword)

    # Discover from trends (already done in main loop, but can be expanded)
    for seed_keyword in CORE_KEYWORDS:
        discover_from_google_trends(seed_keyword)

    # Discover from PAA questions
    for seed_keyword in CORE_KEYWORDS:
        discover_from_serp_related_questions(seed_keyword)

    logger.info("Keyword discovery pipeline completed")


def discover_from_autocomplete(seed_query: str):
    """
    Discover keywords via Google Autocomplete.

    Args:
        seed_query: Base query to expand

    Inserts: Suggestions with category='query_suggestion'
    """
    try:
        response = api_client.call_google_autocomplete_api(seed_query)
        suggestions = data_extractor.extract_autocomplete_suggestions(response)

        for suggestion in suggestions:
            db_interface.get_or_insert_keyword(
                keyword_text=suggestion,
                initial_category='query_suggestion',
                source_endpoint='google_autocomplete',
                base_query=seed_query
            )

        logger.info(f"Autocomplete: {len(suggestions)} suggestions for '{seed_query}'")

    except Exception as e:
        logger.error(f"Autocomplete discovery failed for {seed_query}: {e}")


def discover_from_google_trends(seed_query: str, geo: str = 'US-TX'):
    """
    Discover keywords via Google Trends related queries/topics.

    Args:
        seed_query: Base query to analyze
        geo: Geographic code

    Inserts: Related queries/topics with category='trend-based'
    """
    try:
        for data_type in ['RELATED_QUERIES', 'RELATED_TOPICS']:
            response = api_client.call_google_trends_api(
                query=seed_query,
                geo=geo,
                date='today 12-m',
                data_type=data_type
            )

            trends_data = data_extractor.extract_trends_data(response)

            for query in trends_data.get('related_queries', []):
                db_interface.get_or_insert_keyword(
                    keyword_text=query['query_text'],
                    initial_category='trend-based',
                    source_endpoint='google_trends',
                    base_query=seed_query
                )

            for topic in trends_data.get('related_topics', []):
                if topic['topic_text']:
                    db_interface.get_or_insert_keyword(
                        keyword_text=topic['topic_text'],
                        initial_category='trend-based',
                        source_endpoint='google_trends',
                        base_query=seed_query
                    )

        logger.info(f"Trends discovery completed for '{seed_query}'")

    except Exception as e:
        logger.error(f"Trends discovery failed for {seed_query}: {e}")


def discover_from_serp_related_questions(seed_query: str, location: str = 'Texas, United States'):
    """
    Discover keywords via People Also Ask questions.

    Args:
        seed_query: Base query
        location: Location string

    Inserts: Questions with category='user_pain_point'
    """
    try:
        response = api_client.call_google_related_questions_api(
            query=seed_query,
            location=location
        )

        questions = data_extractor.extract_related_questions(response)

        for question in questions:
            db_interface.get_or_insert_keyword(
                keyword_text=question['question_text'],
                initial_category='user_pain_point',
                source_endpoint='google_search_related_questions',
                base_query=seed_query
            )

        logger.info(f"PAA discovery: {len(questions)} questions for '{seed_query}'")

    except Exception as e:
        logger.error(f"PAA discovery failed for {seed_query}: {e}")
```

---

### 4. Keyword Review CLI Workflow

```python
# src/keyword_manager.py

import db_interface
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def list_pending_keywords():
    """Display all keywords awaiting review."""
    pending = db_interface.get_pending_keywords()

    if not pending:
        print("No pending keywords to review.")
        return []

    print(f"\n{'ID':<6} {'Keyword':<50} {'Category':<20} {'Source':<30}")
    print("-" * 106)

    for row in pending:
        keyword_id, keyword_text, category, source = row
        print(f"{keyword_id:<6} {keyword_text:<50} {category or 'N/A':<20} {source or 'N/A':<30}")

    return pending


def review_keyword_cli():
    """
    Interactive CLI for keyword review workflow.

    Actions:
        - List pending keywords
        - Select by ID
        - Approve or reject
        - Optionally update category
        - Bulk operations
    """
    db_interface.init_db()

    while True:
        print("\n=== Keyword Review ===")
        print("1. List pending keywords")
        print("2. Approve keyword")
        print("3. Reject keyword")
        print("4. Bulk approve all")
        print("5. Exit")

        choice = input("\nChoice: ").strip()

        if choice == '1':
            list_pending_keywords()

        elif choice == '2':
            keyword_id = input("Keyword ID to approve: ").strip()
            category = input("Category (or Enter to keep): ").strip() or None
            try:
                db_interface.update_keyword_status(
                    keyword_id=int(keyword_id),
                    status='approved',
                    initial_category=category
                )
                print(f"Keyword {keyword_id} approved.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '3':
            keyword_id = input("Keyword ID to reject: ").strip()
            try:
                db_interface.update_keyword_status(
                    keyword_id=int(keyword_id),
                    status='rejected'
                )
                print(f"Keyword {keyword_id} rejected.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '4':
            pending = db_interface.get_pending_keywords()
            for row in pending:
                db_interface.update_keyword_status(keyword_id=row[0], status='approved')
            print(f"Approved {len(pending)} keywords.")

        elif choice == '5':
            print("Exiting keyword review.")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    review_keyword_cli()
```

---

### 5. Entry Point (main.py)

```python
# src/main.py

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Market Research System")
    parser.add_argument('--run', action='store_true', help='Run full research cycle')
    parser.add_argument('--discover', action='store_true', help='Run keyword discovery only')
    parser.add_argument('--init', action='store_true', help='Initialize database only')

    args = parser.parse_args()

    if args.init:
        db_interface.init_db()
        print("Database initialized.")

    elif args.discover:
        db_interface.init_db()
        run_keyword_discovery()

    elif args.run:
        run_market_research_cycle()

    else:
        parser.print_help()
```

---

## WORKFLOW PATTERNS SUMMARY

### Pattern 1: Nested Loop Orchestration

```
for location in locations:
    for keyword in keywords:
        for engine in engines:
            try:
                response = call_api(engine, keyword, location)
                data = extract(response)
                insert(data)
            except:
                log_error()
                continue  # Don't halt on individual failures
```

### Pattern 2: Continue-on-Error

```python
try:
    process_item(item)
except Exception as e:
    logger.error(f"Failed for {item}: {e}")
    continue  # Process next item
```

### Pattern 3: Session-Based Result Linking

```python
session_id = create_session(keyword_id, location_id, engine)
results = extract_results(response)
for result in results:
    insert_result(session_id=session_id, **result)
```

### Pattern 4: Multi-Source Discovery

```python
# Discover from multiple sources, insert all with pending status
for source in [autocomplete, trends, paa, news]:
    keywords = discover_from(source, seed_query)
    for kw in keywords:
        get_or_insert_keyword(kw, status='pending_review', source=source)
```

### Pattern 5: CLI Review Workflow

```python
while True:
    show_menu()
    choice = get_input()
    if choice == 'list': list_pending()
    elif choice == 'approve': update_status(id, 'approved')
    elif choice == 'reject': update_status(id, 'rejected')
    elif choice == 'exit': break
```

---

## CONCLUSIONS

### What is Good / Usable

1. **Nested loop orchestration** - Clean iteration over locations × keywords × engines
2. **Continue-on-error** - Robust to individual failures
3. **Session-based linking** - Audit trail for all results
4. **Multi-source discovery** - Comprehensive keyword expansion
5. **CLI review workflow** - Human-in-the-loop approval
6. **Entry point CLI** - Flexible run modes

### What is Outdated

1. **Synchronous execution** - Should be async for parallel API calls
2. **No rate limiting** - Risk of API quota exhaustion
3. **No progress tracking** - No resume capability
4. **Hardcoded parameters** - geo, date ranges in code

### What Must Be Rewritten

1. **Add async execution** - Concurrent API calls
2. **Add rate limiting** - Token bucket or semaphore
3. **Add checkpoint/resume** - Track progress for long runs
4. **Externalize parameters** - Config file for geo, dates
5. **Add batch size control** - Limit concurrent operations

### How It Fits Into AutoBiz

- **Port orchestration pattern** for pipeline execution
- **Port discovery pipeline** for keyword/entity expansion
- **Adapt CLI workflow** for human review steps
- **Add async + rate limiting** before use

### Conflicts with Previous Repos

| Feature | SerpApi (This) | MarketIntel | Best |
|---------|----------------|-------------|------|
| Orchestration | Comprehensive | Similar | Same pattern |
| Error handling | Continue-on-error | Continue-on-error | Same |
| Discovery | Multi-source | Limited | SerpApi |
| CLI review | Full | None | SerpApi |
| Async | None | None | Need to add |

### Best Version

**SerpApi's orchestration is more complete** (discovery pipeline, CLI review). Port to AutoBiz with async enhancement.
