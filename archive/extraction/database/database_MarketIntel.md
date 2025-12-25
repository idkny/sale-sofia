---
id: 20251201_database_marketintel
type: extraction
subject: database
description: "Database schema and patterns extracted from MarketIntel repository"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [database, sqlite, schema, patterns, marketintel, extraction]
source_repo: idkny/MarketIntel
---

# Database Extraction: MarketIntel

**Source**: `idkny/MarketIntel`
**Files**: `src/db_interface.py`, `src/scripts/db.py`
**Production Data**: 1346 keywords, 1997 businesses, 427 sessions

---

## Conclusions

### What's Good (USE FOR AUTOBIZ)

| Pattern | Description | Priority |
|---------|-------------|----------|
| `_execute_query()` | Generic query helper with fetch modes | HIGH |
| `get_or_insert_*` | Deduplication pattern | HIGH |
| `cache` table | API response caching with TTL | HIGH |
| `harvest_log` table | API call audit trail | HIGH |
| Status workflow | pending_review → approved/rejected | MEDIUM |
| Session linking | Links multiple entities to one event | MEDIUM |

### What to Skip

- SERP-specific tables (OrganicResults, PaidAds, etc.)
- Location/geo targeting (not needed for Zoho)
- Google Trends integration

---

## Schema (12 tables)

```sql
-- =============================================================================
-- CORE TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS Keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_text TEXT NOT NULL UNIQUE,
    initial_category TEXT,
    source_endpoint TEXT,
    base_query TEXT,
    predicted_category TEXT,
    confidence_score REAL,
    status TEXT DEFAULT 'pending_review',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    state TEXT,
    country TEXT,
    uule_code TEXT,
    population INTEGER,
    UNIQUE(city, state, country)
);

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

-- =============================================================================
-- RESULT TABLES (linked via session_id)
-- =============================================================================

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

-- =============================================================================
-- CACHING & LOGGING (HIGH VALUE)
-- =============================================================================

CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    engine TEXT,
    params_json TEXT,
    response_json TEXT,
    fetched_at REAL,
    ttl_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS harvest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    params_json TEXT NOT NULL,
    response_json TEXT,
    saved_to TEXT,
    status TEXT NOT NULL,
    http_status INTEGER,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Pattern 1: Generic Query Executor

```python
def _execute_query(conn, query, params=(), fetch=None):
    """
    Generic SQL query executor with fetch modes.

    Args:
        conn: SQLite connection
        query: SQL query string
        params: Query parameters tuple
        fetch: 'one' | 'all' | None (returns lastrowid)

    Returns:
        fetchone result | fetchall result | lastrowid
    """
    try:
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
```

**AutoBiz Use**: Adapt for `tools/data/_queries.py`

---

## Pattern 2: Get or Insert (Deduplication)

```python
def get_or_insert_keyword(conn, keyword_text, initial_category=None,
                           source_endpoint=None, base_query=None,
                           predicted_category=None, confidence_score=None,
                           status_override=None):
    """
    Insert new keyword OR return existing ID (deduplication).
    Also updates last_updated timestamp on existing records.
    """
    try:
        # Check if exists
        query = "SELECT keyword_id FROM Keywords WHERE keyword_text = ?"
        result = _execute_query(conn, query, (keyword_text,), fetch='one')

        if result:
            # Exists - update timestamp, return ID
            keyword_id = result[0]
            update_query = "UPDATE Keywords SET last_updated = ? WHERE keyword_id = ?"
            _execute_query(conn, update_query, (datetime.now(), keyword_id))
            return keyword_id
        else:
            # New - insert with all fields
            status = status_override or 'pending_review'
            insert_query = """
                INSERT INTO Keywords (keyword_text, initial_category, source_endpoint,
                                       base_query, predicted_category, confidence_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            params = (keyword_text, initial_category, source_endpoint, base_query,
                      predicted_category, confidence_score, status)
            return _execute_query(conn, insert_query, params)
    except Exception as e:
        logging.error(f"Error in get_or_insert_keyword: {e}")
        return None
```

**AutoBiz Use**: For Zoho entity sync (avoid duplicates)

---

## Pattern 3: Status Workflow

```python
# Status values: pending_review | approved | rejected

def get_pending_keywords(conn):
    """Get all keywords pending review."""
    query = "SELECT * FROM Keywords WHERE status = 'pending_review'"
    return _execute_query(conn, query, fetch='all')

def get_keywords_by_status(conn, status):
    """Get keywords by status."""
    query = "SELECT * FROM Keywords WHERE status = ?"
    return _execute_query(conn, query, (status,), fetch='all')

def update_keyword_status(conn, keyword_id, status, initial_category=None):
    """Update keyword status (state transition)."""
    if initial_category:
        query = "UPDATE Keywords SET status = ?, initial_category = ? WHERE keyword_id = ?"
        params = (status, initial_category, keyword_id)
    else:
        query = "UPDATE Keywords SET status = ? WHERE keyword_id = ?"
        params = (status, keyword_id)
    _execute_query(conn, query, params)
```

**AutoBiz Use**: For pipeline step tracking

---

## Pattern 4: API Call Logging

```python
def save_response(
    conn,
    endpoint: str,
    params: dict,
    data: dict | None,
    saved_to: str | None,
    status: str,
    http_status: int | None,
    error_message: str | None,
):
    """
    Log API call with request/response for audit trail.
    Useful for debugging, replay, and analytics.
    """
    with conn:
        conn.execute(
            """
            INSERT INTO harvest_log (
                endpoint, params_json, response_json, saved_to, status,
                http_status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                endpoint,
                json.dumps(params),
                json.dumps(data) if data else None,
                saved_to,
                status,
                http_status,
                error_message,
            ),
        )
```

**AutoBiz Use**: For Zoho API call logging

---

## AutoBiz Mapping

| MarketIntel | AutoBiz Equivalent |
|-------------|-------------------|
| Keywords | `sync_items` or `pipeline_inputs` |
| SearchSessions | `sync_sessions` |
| cache | `api_cache` |
| harvest_log | `api_log` |
| OrganicResults | `zoho_records` (adapted) |
