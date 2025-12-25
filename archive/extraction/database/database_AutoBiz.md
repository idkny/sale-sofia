---
id: 20251201_database_autobiz
type: extraction
subject: database
source_repo: Auto-Biz
description: "SQLite database patterns, CRUD operations, URL classification from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [database, sqlite, crud, classification, auto-biz]
---

# SUBJECT: database/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `data/data_store_main.py`

---

## 1. EXTRACTED CODE

### 1.1 Connection Management

```python
# data/data_store_main.py

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from paths import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        raise
```

### 1.2 Insert-or-Get Pattern

```python
def _insert_or_get_id(cursor: sqlite3.Cursor, table: str, field: str, value: Any) -> int:
    """Helper to get the ID of a value, inserting it if it doesn't exist."""
    cursor.execute(f"SELECT id FROM {table} WHERE {field} = ?", (value,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(f"INSERT INTO {table} ({field}) VALUES (?)", (value,))
    return cursor.lastrowid
```

### 1.3 URL and Domain Management

```python
def add_urls(urls_to_add: List[str], source_visit_type: str = "manual_input") -> Tuple[int, int]:
    """
    Adds a list of URLs to the database, creating domain and classification entries.
    Returns a tuple of (added_count, skipped_count).
    """
    added_count = 0
    skipped_count = 0
    conn = get_db_connection()
    try:
        with conn:
            for url in urls_to_add:
                url = url.strip()
                if not url:
                    skipped_count += 1
                    continue

                # Basic validation
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if not (parsed.scheme in ["http", "https"] and parsed.netloc):
                    skipped_count += 1
                    continue

                # Check for existence first
                cur = conn.cursor()
                cur.execute("SELECT id FROM urls WHERE url = ?", (url,))
                if cur.fetchone():
                    skipped_count += 1
                    continue

                # Add new URL
                from search_engine.search_engines import extract_root_domain
                domain_name = extract_root_domain(url)
                domain_id = _insert_or_get_id(conn, "domains", "root", domain_name)

                cur.execute("INSERT INTO urls (domain_id, url) VALUES (?, ?)", (domain_id, url))
                url_id = cur.lastrowid

                # Create associated pending classification and visit records
                cur.execute(
                    "INSERT INTO url_classifications (url_id, status) VALUES (?, ?)",
                    (url_id, "pending")
                )
                cur.execute(
                    "INSERT INTO page_visits (url_id, visit_type, visited_at) VALUES (?, ?, ?)",
                    (url_id, source_visit_type, datetime.utcnow().isoformat())
                )
                added_count += 1
    except sqlite3.Error as e:
        logger.error(f"Database error while adding URLs: {e}", exc_info=True)
    finally:
        conn.close()
    return added_count, skipped_count
```

### 1.4 Search Result Management

```python
def save_search_results(
    results: List[Dict[str, Any]],
    source: str,
    keyword_text: str,
    region: str,
    language: str
):
    """Saves a list of search engine results to the database."""
    conn = get_db_connection()
    try:
        with conn:
            keyword_id = _insert_or_get_id(
                conn, "keywords", "keyword, region, language", (keyword_text, region, language)
            )

            for result in results:
                url = result.get("href") or result.get("url")
                if not url:
                    continue

                from search_engine.search_engines import extract_root_domain
                domain_id = _insert_or_get_id(conn, "domains", "root", extract_root_domain(url))
                url_id = _insert_or_get_id(conn, "urls", "url", url)
                conn.execute("UPDATE urls SET domain_id = ? WHERE id = ?", (domain_id, url_id))

                # Record the search result
                conn.execute(
                    """
                    INSERT INTO results (keyword_id, url_id, rank, search_type, source, retrieved_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        keyword_id,
                        url_id,
                        result.get("rank"),
                        result.get("search_type"),
                        source,
                        datetime.utcnow().isoformat(),
                    ),
                )

                # Ensure a page visit is logged
                conn.execute(
                    "INSERT OR IGNORE INTO page_visits (url_id, visit_type) VALUES (?, 'search')",
                    (url_id,)
                )
    except sqlite3.Error as e:
        logger.error(f"Database error saving search results: {e}", exc_info=True)
    finally:
        conn.close()
```

### 1.5 Classification Management

```python
def get_pending_classification_urls(
    limit: int,
    region: Optional[str],
    language: Optional[str],
    process_gui_retries_only: bool
) -> List[sqlite3.Row]:
    """Fetches URLs that are pending classification from the database."""
    conn = get_db_connection()
    try:
        query_parts = [
            "SELECT u.id, u.url FROM urls u",
            "LEFT JOIN url_classifications c ON u.id = c.url_id",
            "LEFT JOIN results r ON u.id = r.url_id",
            "LEFT JOIN keywords k ON r.keyword_id = k.id",
        ]
        params = []
        where_clauses = []

        if process_gui_retries_only:
            where_clauses.append("c.status = 'pending_gui_retry'")
        else:
            where_clauses.append("(c.id IS NULL OR c.status = 'pending')")

        if region:
            where_clauses.append("k.region = ?")
            params.append(region)
        if language:
            where_clauses.append("k.language = ?")
            params.append(language)

        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))

        query_parts.append("LIMIT ?")
        params.append(limit)

        cursor = conn.cursor()
        cursor.execute(" ".join(query_parts), params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Database error fetching pending URLs: {e}")
        return []
    finally:
        conn.close()


def save_classification_result(
    url_id: int,
    decision: str,
    details: Dict[str, Any],
    browser_use_json: Optional[str]
):
    """Saves the result of a URL classification to the database."""
    conn = get_db_connection()
    try:
        with conn:
            # Insert or update the classification (UPSERT pattern)
            conn.execute(
                """
                INSERT INTO url_classifications (
                    url_id, status, final_decision, rule_label, format_label,
                    format_confidence, browser_use_json, last_checked
                )
                VALUES (?, 'classified', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(url_id) DO UPDATE SET
                    status = 'classified',
                    final_decision = excluded.final_decision,
                    rule_label = excluded.rule_label,
                    format_label = excluded.format_label,
                    format_confidence = excluded.format_confidence,
                    browser_use_json = excluded.browser_use_json,
                    last_checked = CURRENT_TIMESTAMP;
                """,
                (
                    url_id,
                    decision,
                    details.get("rule_label"),
                    details.get("format_label"),
                    details.get("format_confidence"),
                    browser_use_json,
                ),
            )

            # Log the classification history
            conn.execute(
                """
                INSERT INTO classification_history (url_id, decision, details_json)
                VALUES (?, ?, ?)
                """,
                (url_id, decision, json.dumps(details)),
            )
    except sqlite3.Error as e:
        logger.error(f"Database error saving classification: {e}")
    finally:
        conn.close()


def mark_url_as_failed(url_id: int, is_headless_failure: bool):
    """Marks a URL as failed, incrementing the failure count."""
    new_status = "pending_gui_retry" if is_headless_failure else "failed"
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO url_classifications (url_id, status, failed_attempts, last_checked)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(url_id) DO UPDATE SET
                    status = excluded.status,
                    failed_attempts = failed_attempts + 1,
                    last_checked = CURRENT_TIMESTAMP;
                """,
                (url_id, new_status),
            )
    except sqlite3.Error as e:
        logger.error(f"Database error marking url_id {url_id} as failed: {e}")
    finally:
        conn.close()
```

---

## 2. INFERRED SCHEMA (from code)

```sql
-- Inferred from code patterns

CREATE TABLE domains (
    id INTEGER PRIMARY KEY,
    root TEXT UNIQUE NOT NULL
);

CREATE TABLE urls (
    id INTEGER PRIMARY KEY,
    domain_id INTEGER REFERENCES domains(id),
    url TEXT UNIQUE NOT NULL
);

CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL,
    region TEXT,
    language TEXT,
    UNIQUE(keyword, region, language)
);

CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(id),
    url_id INTEGER REFERENCES urls(id),
    rank INTEGER,
    search_type TEXT,
    source TEXT,  -- 'ddg', 'serpapi'
    retrieved_at TEXT
);

CREATE TABLE page_visits (
    id INTEGER PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id),
    visit_type TEXT,  -- 'search', 'manual_input'
    visited_at TEXT
);

CREATE TABLE url_classifications (
    id INTEGER PRIMARY KEY,
    url_id INTEGER UNIQUE REFERENCES urls(id),
    status TEXT,  -- 'pending', 'classified', 'pending_gui_retry', 'failed'
    final_decision TEXT,
    rule_label TEXT,
    format_label TEXT,
    format_confidence REAL,
    enriched_label TEXT,
    browser_use_json TEXT,
    failed_attempts INTEGER DEFAULT 0,
    last_checked TEXT
);

CREATE TABLE classification_history (
    id INTEGER PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id),
    decision TEXT,
    details_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. CONCLUSIONS

### What is Good / Usable

1. **row_factory = sqlite3.Row**: Name-based column access
2. **_insert_or_get_id**: Efficient get-or-insert pattern
3. **Context manager**: `with conn:` for auto-commit
4. **UPSERT pattern**: `ON CONFLICT DO UPDATE` for classifications
5. **Dynamic query building**: Flexible WHERE clause construction
6. **History tracking**: Classification history table
7. **Status workflow**: pending -> classified/failed/pending_gui_retry

### What is Outdated

1. **No explicit schema**: Schema must be inferred from code
2. **Inline imports**: `from search_engine.search_engines import...`

### What Must Be Rewritten

1. **Connection per function**: Should use connection pool or context manager
2. **SQL injection risk**: Dynamic table/field in `_insert_or_get_id`
3. **Missing indexes**: No explicit index creation

### How it Fits into AutoBiz

- **ADAPT**: Schema needs explicit definition
- **KEEP**: _insert_or_get_id pattern, UPSERT pattern
- **IMPROVE**: Add connection pooling, proper schema management

### Conflicts or Duplicates with Previous Repos

| Pattern | Auto-Biz | MarketIntel | SerpApi | Best |
|---------|----------|-------------|---------|------|
| Tables | 7 (inferred) | 5 | 10 (spec) | **SerpApi** (more complete) |
| _execute_query | No | Yes | Yes | **MarketIntel** |
| get_or_insert | Yes | Yes | Yes (spec) | **Same pattern** |
| UPSERT | Yes | No | No | **Auto-Biz** |
| History table | Yes | No | No | **Auto-Biz** |
| Status workflow | Yes | Partial | Yes (spec) | **Auto-Biz** (GUI retry) |
| row_factory | Yes | Yes | N/A | **Same** |

### Best Version Recommendation

**MERGE Auto-Biz + MarketIntel + SerpApi**:
- Auto-Biz: UPSERT pattern, status workflow, history tracking
- MarketIntel: _execute_query helper, caching pattern
- SerpApi: Comprehensive schema design, keyword workflow
