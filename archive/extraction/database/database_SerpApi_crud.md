---
id: 20251201_database_serpapi_crud
type: extraction
subject: database/crud
source_repo: idkny/SerpApi
source_file: Note.md
description: "Database CRUD operation patterns from SerpApi planning document"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, database, crud, serpapi, sqlite]
---

# DATABASE CRUD PATTERNS - SerpApi

**Source**: `idkny/SerpApi/Note.md`
**Type**: Specification (function signatures and logic)
**Database**: SQLite via Python sqlite3

---

## EXTRACTED CRUD FUNCTIONS

### 1. Database Initialization

```python
def init_db():
    """
    Initializes the database and creates tables using CREATE_TABLE_STATEMENTS.
    Includes error handling for table creation.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    for statement in CREATE_TABLE_STATEMENTS:
        try:
            cursor.execute(statement)
        except Exception as e:
            logging.error(f"Error creating table: {e}")
    conn.commit()
    conn.close()
```

---

### 2. Query Executor (Internal Helper)

```python
def _execute_query(query, params=None, fetch_mode=None):
    """
    Internal helper to execute SQL queries.

    Args:
        query: SQL query string
        params: Tuple of parameters for parameterized query
        fetch_mode: None (execute only), 'one', 'all', 'lastrowid'

    Returns:
        Based on fetch_mode: lastrowid, single row, all rows, or None

    Handles:
        - Connection management
        - Transaction commit
        - Error logging
        - Connection cleanup
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()

        if fetch_mode == 'lastrowid':
            return cursor.lastrowid
        elif fetch_mode == 'one':
            return cursor.fetchone()
        elif fetch_mode == 'all':
            return cursor.fetchall()
        return None
    except Exception as e:
        logging.error(f"Query error: {e}")
        raise
    finally:
        conn.close()
```

---

### 3. Get-or-Insert Pattern (Keywords)

```python
def get_or_insert_keyword(keyword_text, initial_category=None, source_endpoint=None, base_query=None):
    """
    Inserts keyword if new, updates if existing.

    Logic:
        1. Check if keyword_text exists
        2. If exists: increment attempts, update last_updated, return existing ID
        3. If new: insert with category/source, return new ID

    Args:
        keyword_text: The keyword string (unique)
        initial_category: Classification category
        source_endpoint: Which API discovered this keyword
        base_query: Parent query that generated this keyword

    Returns:
        keyword_id: Integer ID of existing or new keyword
    """
    # Check existing
    existing = _execute_query(
        "SELECT keyword_id FROM Keywords WHERE keyword_text = ?",
        (keyword_text,),
        fetch_mode='one'
    )

    if existing:
        # Update existing
        _execute_query(
            """UPDATE Keywords
               SET attempts = attempts + 1,
                   last_updated = CURRENT_TIMESTAMP
               WHERE keyword_id = ?""",
            (existing[0],)
        )
        return existing[0]
    else:
        # Insert new
        return _execute_query(
            """INSERT INTO Keywords (keyword_text, initial_category, source_endpoint, base_query)
               VALUES (?, ?, ?, ?)""",
            (keyword_text, initial_category, source_endpoint, base_query),
            fetch_mode='lastrowid'
        )
```

---

### 4. Get-or-Insert Pattern (Locations)

```python
def get_or_insert_location(city, state, country, uule_code=None, population=None):
    """
    Inserts location if new, returns existing ID if found.

    Args:
        city: City name
        state: State/province (nullable)
        country: Country name
        uule_code: Google UULE location code (optional)
        population: City population (optional)

    Returns:
        location_id: Integer ID
    """
    existing = _execute_query(
        "SELECT location_id FROM Locations WHERE city = ? AND state = ? AND country = ?",
        (city, state, country),
        fetch_mode='one'
    )

    if existing:
        return existing[0]
    else:
        return _execute_query(
            """INSERT INTO Locations (city, state, country, uule_code, population)
               VALUES (?, ?, ?, ?, ?)""",
            (city, state, country, uule_code, population),
            fetch_mode='lastrowid'
        )
```

---

### 5. Keyword Workflow Functions

```python
def get_pending_keywords():
    """Retrieves keywords with status='pending_review'."""
    return _execute_query(
        "SELECT keyword_id, keyword_text, initial_category, source_endpoint FROM Keywords WHERE status = 'pending_review'",
        fetch_mode='all'
    )

def update_keyword_status(keyword_id, status, initial_category=None):
    """
    Updates keyword status and optionally category.

    Args:
        keyword_id: Integer ID
        status: 'approved' or 'rejected'
        initial_category: Optional category update
    """
    if initial_category:
        _execute_query(
            "UPDATE Keywords SET status = ?, initial_category = ?, last_updated = CURRENT_TIMESTAMP WHERE keyword_id = ?",
            (status, initial_category, keyword_id)
        )
    else:
        _execute_query(
            "UPDATE Keywords SET status = ?, last_updated = CURRENT_TIMESTAMP WHERE keyword_id = ?",
            (status, keyword_id)
        )
```

---

### 6. Session Creation

```python
def create_search_session(keyword_id, location_id, engine_used, device_type, serpapi_id):
    """
    Creates a search session record.

    Args:
        keyword_id: FK to Keywords
        location_id: FK to Locations
        engine_used: 'google', 'google_local', 'google_trends', etc.
        device_type: 'desktop' or 'mobile'
        serpapi_id: SerpAPI response ID for archive retrieval

    Returns:
        session_id: Integer ID for linking results
    """
    return _execute_query(
        """INSERT INTO SearchSessions (keyword_id, location_id, engine_used, device_type, serpapi_id)
           VALUES (?, ?, ?, ?, ?)""",
        (keyword_id, location_id, engine_used, device_type, serpapi_id),
        fetch_mode='lastrowid'
    )
```

---

### 7. Result Insertion Functions

```python
def insert_organic_result(session_id, position, title, url, domain, snippet,
                          date_published=None, content_type=None,
                          search_intent_classified=None, site_category_classified=None):
    """Insert organic SERP result linked to session."""
    return _execute_query(
        """INSERT INTO OrganicResults
           (session_id, position, title, url, domain, snippet, date_published,
            content_type, search_intent_classified, site_category_classified)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, position, title, url, domain, snippet, date_published,
         content_type, search_intent_classified, site_category_classified),
        fetch_mode='lastrowid'
    )

def insert_paid_ad(session_id, position, title, link, displayed_link, snippet):
    """Insert paid ad result linked to session."""
    return _execute_query(
        """INSERT INTO PaidAds (session_id, position, title, link, displayed_link, snippet)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session_id, position, title, link, displayed_link, snippet),
        fetch_mode='lastrowid'
    )

def insert_local_business_result(session_id, business_name, address, phone=None,
                                  website=None, google_maps_link=None, rating=None,
                                  total_reviews=None, category=None, place_id=None):
    """Insert local business result linked to session."""
    return _execute_query(
        """INSERT INTO LocalBusinessResults
           (session_id, business_name, address, phone, website, google_maps_link,
            rating, total_reviews, category, place_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, business_name, address, phone, website, google_maps_link,
         rating, total_reviews, category, place_id),
        fetch_mode='lastrowid'
    )

def insert_related_question(session_id, question_text, answer_snippet=None):
    """Insert People Also Ask question linked to session."""
    return _execute_query(
        """INSERT INTO RelatedQuestions (session_id, question_text, answer_snippet)
           VALUES (?, ?, ?)""",
        (session_id, question_text, answer_snippet),
        fetch_mode='lastrowid'
    )

def insert_google_trends_data(keyword_id, location_id, date_range_query, data_type,
                               interest_value=None, trending_topic_or_query_text=None,
                               extracted_value=None):
    """Insert Google Trends data (directly linked to keyword + location, not session)."""
    return _execute_query(
        """INSERT INTO GoogleTrendsData
           (keyword_id, location_id, date_range_query, data_type, interest_value,
            trending_topic_or_query_text, extracted_value)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (keyword_id, location_id, date_range_query, data_type, interest_value,
         trending_topic_or_query_text, extracted_value),
        fetch_mode='lastrowid'
    )

def insert_news_article(session_id, title, url, source, published_date=None,
                        snippet=None, relevance_score=None):
    """Insert news article linked to session."""
    return _execute_query(
        """INSERT INTO NewsArticles
           (session_id, title, url, source, published_date, snippet, relevance_score)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (session_id, title, url, source, published_date, snippet, relevance_score),
        fetch_mode='lastrowid'
    )

def insert_entity(source_item_id, source_table, entity_text, salience=None,
                  sentiment_score=None, sentiment_magnitude=None, num_mentions=None,
                  entity_type=None):
    """Insert entity with polymorphic FK to any source table."""
    return _execute_query(
        """INSERT INTO Entities
           (source_item_id, source_table, entity_text, salience, sentiment_score,
            sentiment_magnitude, num_mentions, entity_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (source_item_id, source_table, entity_text, salience, sentiment_score,
         sentiment_magnitude, num_mentions, entity_type),
        fetch_mode='lastrowid'
    )
```

---

## CONCLUSIONS

### What is Good / Usable

1. **get_or_insert pattern** - Clean idempotent insert/update logic
2. **_execute_query helper** - Centralized query execution with error handling
3. **Session-based FK linking** - All results tied to sessions
4. **Keyword workflow** - Status management with timestamps
5. **Polymorphic entity insertion** - Flexible FK pattern

### What is Outdated

1. **No connection pooling** - Opens/closes connection per query
2. **No context manager** - Should use `with` statement
3. **No async support** - Blocking database calls
4. **No batch insert** - One row at a time

### What Must Be Rewritten

1. **Add connection pooling** or use SQLAlchemy
2. **Use context manager** for connections
3. **Add batch insert** with executemany()
4. **Add transaction support** for multi-table inserts

### How It Fits Into AutoBiz

- **Use get_or_insert pattern** for all lookup tables
- **Use _execute_query pattern** as base, add pooling
- **Use session linking** for audit trails
- **Adapt keyword workflow** for pipeline states

### Conflicts with Previous Repos

| Pattern | SerpApi (This) | MarketIntel | Best |
|---------|----------------|-------------|------|
| Query executor | Basic | With caching | MarketIntel |
| Get-or-insert | Full with update | Similar | Same |
| Connection mgmt | Per-query | Per-query | Need pooling |
| Batch insert | No | No | Need to add |

### Best Version

**Hybrid**: Use MarketIntel's caching-aware executor + SerpApi's keyword workflow pattern.

---

## REUSABLE PATTERNS SUMMARY

```python
# Pattern 1: Get-or-Insert (idempotent upsert)
def get_or_insert_X(unique_field, **kwargs):
    existing = query("SELECT id FROM X WHERE unique_field = ?", (unique_field,))
    if existing:
        update_timestamps(existing[0])
        return existing[0]
    return insert(unique_field, **kwargs)

# Pattern 2: Session-based result linking
session_id = create_session(keyword_id, location_id, engine)
insert_result(session_id, **result_data)  # All results link to session

# Pattern 3: Keyword status workflow
# Status: pending_review → approved | rejected
# Fields: status, last_updated, attempts
```
