---
id: 20251201_database_market_ai
type: extraction
subject: database
source_repo: Market_AI
description: "10-table SQLite schema with CRUD operations, _execute_query helper, get_or_insert pattern"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [database, sqlite, schema, crud, serpapi, market-research]
---

# SUBJECT: database/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `SerpApi/src/db_interface.py`, `SerpApi/src/scripts/db.py`

---

## 1. EXTRACTED CODE

### 1.1 Complete SQLite Schema (10 Tables)

```sql
-- Keywords table
CREATE TABLE IF NOT EXISTS Keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_text TEXT NOT NULL UNIQUE,
    initial_category TEXT,
    source_endpoint TEXT,
    base_query TEXT,
    status TEXT DEFAULT 'pending_review',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table
CREATE TABLE IF NOT EXISTS Locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    state TEXT,
    country TEXT,
    uule_code TEXT,
    population INTEGER,
    UNIQUE(city, state, country)
);

-- SearchSessions table (links keywords to locations)
CREATE TABLE IF NOT EXISTS SearchSessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    engine_used TEXT,
    device_type TEXT,
    serpapi_id TEXT,
    session_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords (keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations (location_id)
);

-- OrganicResults table
CREATE TABLE IF NOT EXISTS OrganicResults (
    organic_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    url TEXT,
    domain TEXT,
    snippet TEXT,
    date_published TIMESTAMP,
    content_type TEXT,
    search_intent_classified TEXT,
    site_category_classified TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

-- PaidAds table
CREATE TABLE IF NOT EXISTS PaidAds (
    paid_ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    link TEXT,
    displayed_link TEXT,
    snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

-- LocalBusinessResults table
CREATE TABLE IF NOT EXISTS LocalBusinessResults (
    local_business_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    business_name TEXT,
    address TEXT,
    phone TEXT,
    website TEXT,
    google_maps_link TEXT,
    rating REAL,
    total_reviews INTEGER,
    category TEXT,
    place_id TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

-- RelatedQuestions table (People Also Ask)
CREATE TABLE IF NOT EXISTS RelatedQuestions (
    related_question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_text TEXT,
    answer_snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

-- GoogleTrendsData table
CREATE TABLE IF NOT EXISTS GoogleTrendsData (
    google_trends_data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    date_range_query TEXT,
    data_type TEXT,
    interest_value INTEGER,
    trending_topic_or_query_text TEXT,
    extracted_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords (keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations (location_id)
);

-- NewsArticles table
CREATE TABLE IF NOT EXISTS NewsArticles (
    news_article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    title TEXT,
    url TEXT,
    source TEXT,
    published_date TIMESTAMP,
    snippet TEXT,
    relevance_score REAL,
    FOREIGN KEY (session_id) REFERENCES SearchSessions (session_id)
);

-- Entities table (polymorphic FK via source_table)
CREATE TABLE IF NOT EXISTS Entities (
    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id INTEGER,
    source_table TEXT,
    entity_text TEXT,
    salience REAL,
    sentiment_score REAL,
    sentiment_magnitude REAL,
    num_mentions INTEGER,
    entity_type TEXT
);
```

### 1.2 Database Interface Functions

```python
import sqlite3
import os
import logging
from datetime import datetime

DATABASE_FILE = 'data/market_intelligence.db'

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    try:
        os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        for statement in CREATE_TABLE_STATEMENTS:
            cursor.execute(statement)
        conn.commit()
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
    finally:
        if conn:
            conn.close()

def _execute_query(query, params=(), fetch=None):
    """
    Internal helper for executing SQL queries.
    Args:
        query (str): The SQL query to execute.
        params (tuple): The parameters to pass to the query.
        fetch (str): 'one', 'all', or None for lastrowid.
    Returns:
        Result of fetch operation or last inserted row id.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        if fetch == 'one':
            return cursor.fetchone()
        elif fetch == 'all':
            return cursor.fetchall()
        else:
            return cursor.lastrowid
    except sqlite3.Error as e:
        logging.error(f"Database query failed: {e}\nQuery: {query}\nParams: {params}")
        return None
    finally:
        if conn:
            conn.close()
```

### 1.3 Get-or-Insert Pattern (Deduplication)

```python
def get_or_insert_keyword(keyword_text, initial_category=None, source_endpoint=None, base_query=None):
    """Inserts a new keyword if it doesn't exist, otherwise returns the existing keyword_id."""
    try:
        # Check if keyword exists
        query = "SELECT keyword_id FROM Keywords WHERE keyword_text = ?"
        result = _execute_query(query, (keyword_text,), fetch='one')
        if result:
            keyword_id = result[0]
            # Update last_updated timestamp
            update_query = "UPDATE Keywords SET last_updated = ? WHERE keyword_id = ?"
            _execute_query(update_query, (datetime.now(), keyword_id))
            return keyword_id
        else:
            # Insert new keyword
            insert_query = """
            INSERT INTO Keywords (keyword_text, initial_category, source_endpoint, base_query, status)
            VALUES (?, ?, ?, ?, 'pending_review')
            """
            return _execute_query(insert_query, (keyword_text, initial_category, source_endpoint, base_query))
    except Exception as e:
        logging.error(f"Error in get_or_insert_keyword: {e}")
        return None

def get_or_insert_location(city, state, country, uule_code=None, population=None):
    """Inserts a new location if it doesn't exist, otherwise returns the existing location_id."""
    try:
        query = "SELECT location_id FROM Locations WHERE city = ? AND state = ? AND country = ?"
        result = _execute_query(query, (city, state, country), fetch='one')
        if result:
            return result[0]
        else:
            insert_query = """
            INSERT INTO Locations (city, state, country, uule_code, population)
            VALUES (?, ?, ?, ?, ?)
            """
            return _execute_query(insert_query, (city, state, country, uule_code, population))
    except Exception as e:
        logging.error(f"Error in get_or_insert_location: {e}")
        return None
```

### 1.4 Insert Functions with Deduplication

```python
def create_search_session(keyword_id, location_id, engine_used, device_type, serpapi_id):
    """Creates a new search session record and returns the session_id."""
    query = """
    INSERT INTO SearchSessions (keyword_id, location_id, engine_used, device_type, serpapi_id)
    VALUES (?, ?, ?, ?, ?)
    """
    return _execute_query(query, (keyword_id, location_id, engine_used, device_type, serpapi_id))

def insert_organic_result(session_id, position, title, url, domain, snippet,
                          date_published=None, content_type=None,
                          search_intent_classified=None, site_category_classified=None):
    # Check if result already exists (deduplication)
    query = "SELECT organic_result_id FROM OrganicResults WHERE url = ? AND session_id = ?"
    result = _execute_query(query, (url, session_id), fetch='one')
    if result:
        logging.info(f"Organic result with URL '{url}' already exists. Skipping.")
        return

    query = """
    INSERT INTO OrganicResults (session_id, position, title, url, domain, snippet,
                                date_published, content_type, search_intent_classified,
                                site_category_classified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (session_id, position, title, url, domain, snippet, date_published,
              content_type, search_intent_classified, site_category_classified)
    return _execute_query(query, params)

def insert_local_business_result(session_id, business_name, address, phone=None,
                                  website=None, google_maps_link=None, rating=None,
                                  total_reviews=None, category=None, place_id=None):
    # Deduplication by business_name + address + session
    query = "SELECT local_business_result_id FROM LocalBusinessResults WHERE business_name = ? AND address = ? AND session_id = ?"
    result = _execute_query(query, (business_name, address, session_id), fetch='one')
    if result:
        logging.info(f"Local business '{business_name}' already exists. Skipping.")
        return

    query = """
    INSERT INTO LocalBusinessResults (session_id, business_name, address, phone, website,
                                      google_maps_link, rating, total_reviews, category, place_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (session_id, business_name, address, phone, website, google_maps_link,
              rating, total_reviews, category, place_id)
    return _execute_query(query, params)
```

### 1.5 Keyword Status Workflow

```python
def get_pending_keywords():
    """Retrieves all keywords with the status 'pending_review'."""
    query = "SELECT * FROM Keywords WHERE status = 'pending_review'"
    return _execute_query(query, fetch='all')

def update_keyword_status(keyword_id, status, initial_category=None):
    """Updates the status and optionally the category of a keyword."""
    if initial_category:
        query = "UPDATE Keywords SET status = ?, initial_category = ? WHERE keyword_id = ?"
        params = (status, initial_category, keyword_id)
    else:
        query = "UPDATE Keywords SET status = ? WHERE keyword_id = ?"
        params = (status, keyword_id)
    _execute_query(query, params)
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **10-table schema** | HIGH | Comprehensive market research structure |
| **_execute_query helper** | HIGH | Reusable query executor |
| **get_or_insert pattern** | HIGH | Deduplication + timestamp update |
| **Session linking** | HIGH | Keywords linked to locations via sessions |
| **Status workflow** | HIGH | pending_review -> approved/rejected |
| **Polymorphic Entities** | MEDIUM | source_table + source_item_id pattern |
| **Deduplication on insert** | HIGH | URL/business checks before insert |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| No caching | Every query opens new connection | Add connection pooling or caching |
| No UPSERT | Separate check + insert | Use `ON CONFLICT DO UPDATE` |
| No row_factory | Returns tuples | Add `sqlite3.Row` for dict access |
| No indexes | May be slow on large datasets | Add indexes on frequently queried columns |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. Schema design (10 tables) for market research
2. _execute_query helper pattern
3. get_or_insert for keywords/locations
4. Session linking pattern
5. Status workflow for human review

**Integration Points:**
- `autobiz/tools/data/` - Database layer
- `autobiz/tools/data/_queries.py` - Query functions
- `autobiz/tools/data/_models.py` - Pydantic models for schema

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| Schema | 10 tables (actual SQL) | SerpApi (spec - same schema) | **USE Market_AI** - actual code |
| _execute_query | Same pattern | MarketIntel (with caching) | **USE MarketIntel** - has caching |
| get_or_insert | Updates timestamp | MarketIntel (same) | **SAME** |
| UPSERT | Not used | Auto-Biz (ON CONFLICT) | **USE Auto-Biz** - cleaner |
| Status workflow | pending_review | Auto-Biz (classification history) | **MERGE** - both patterns |

---

## 6. BEST VERSION RECOMMENDATION

**MERGE approach:**
1. **Schema** from Market_AI (10 tables, comprehensive)
2. **_execute_query with caching** from MarketIntel
3. **UPSERT pattern** from Auto-Biz
4. **Status workflow** from Market_AI
5. **Classification history** from Auto-Biz

**Recommended final schema:**
- Market_AI's 10 tables as base
- Add MarketIntel's cache table
- Add Auto-Biz's history tracking columns
- Add indexes on frequently queried columns

---

## 7. SCHEMA DIAGRAM

```
Keywords (1) ──┬── (M) SearchSessions (M) ──┬── (1) Locations
               │                            │
               ├── (M) GoogleTrendsData ────┘
               │
SearchSessions (1) ──┬── (M) OrganicResults
                     ├── (M) PaidAds
                     ├── (M) LocalBusinessResults
                     ├── (M) RelatedQuestions
                     └── (M) NewsArticles

Entities: Polymorphic (source_table + source_item_id)
```
