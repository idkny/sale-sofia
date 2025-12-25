---
id: database_competitor_intel
type: extraction
subject: database
source_repo: Competitor-Intel
description: "9-table SQLite schema for SEO competitor analysis with content change detection"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [database, sqlite, seo, competitor-intel, schema, change-detection]
---

# Database Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/storage/db.py`, `competitor_intel/storage/models.py`, `db.md`

---

## Schema Overview

9 tables designed for SEO competitor analysis with content change tracking:

| Table | Purpose |
|-------|---------|
| `pages` | Central URL registry with SEO metadata |
| `links` | Hyperlink graph (internal/external) |
| `media` | Images with alt text |
| `structured` | JSON-LD, microdata, RDFa |
| `texts` | Extracted body content |
| `phrases` | NLP-mined keywords |
| `phrase_usage` | Keyword presence mapping |
| `page_history` | Content version archive |
| `domain_metadata` | Anti-bot and rate limit config |

---

## Full DDL

```sql
-- Connection setup
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- Core page tracking
CREATE TABLE IF NOT EXISTS pages (
    url TEXT PRIMARY KEY,
    domain TEXT,
    discovered_at TEXT,
    fetched_at TEXT,
    last_scrape_time TEXT,
    status INTEGER,
    content_type TEXT,
    charset TEXT,
    html_path TEXT,
    content_hash TEXT,           -- SHA256 for change detection
    retry_count INTEGER DEFAULT 0,
    needs_investigation INTEGER DEFAULT 0,
    canonical TEXT,
    title TEXT,
    meta_desc TEXT,
    h1 TEXT,
    h2 TEXT,
    h3 TEXT,
    robots TEXT,
    rel_canonical TEXT,
    lang TEXT
);

-- Link graph
CREATE TABLE IF NOT EXISTS links (
    src_url TEXT,
    dst_url TEXT,
    anchor TEXT,
    rel TEXT,
    nofollow INTEGER,
    is_internal INTEGER
);

-- Media assets
CREATE TABLE IF NOT EXISTS media (
    url TEXT,
    page_url TEXT,
    alt_text TEXT,
    type TEXT
);

-- Structured data (JSON-LD, microdata, etc.)
CREATE TABLE IF NOT EXISTS structured (
    page_url TEXT,
    syntax TEXT,      -- json-ld, microdata, rdfa, opengraph, microformat
    type TEXT,        -- @type field value
    json TEXT
);

-- Extracted body text
CREATE TABLE IF NOT EXISTS texts (
    page_url TEXT PRIMARY KEY,
    text TEXT,
    tokens INTEGER,
    word_count INTEGER
);

-- NLP-mined phrases
CREATE TABLE IF NOT EXISTS phrases (
    page_url TEXT,
    phrase TEXT,
    n INTEGER,         -- n-gram size
    method TEXT,       -- gensim, yake, rake, keybert
    score REAL,
    freq INTEGER
);

-- Phrase presence mapping
CREATE TABLE IF NOT EXISTS phrase_usage (
    page_url TEXT,
    phrase TEXT,
    in_title INTEGER,
    in_h1 INTEGER,
    in_h2 INTEGER,
    in_anchor INTEGER,
    in_alt INTEGER,
    in_body INTEGER
);

-- Content version history
CREATE TABLE IF NOT EXISTS page_history (
    url TEXT,
    scraped_at TEXT,
    html_path TEXT,
    content_hash TEXT,
    PRIMARY KEY (url, content_hash)
);

-- Domain-level crawl config
CREATE TABLE IF NOT EXISTS domain_metadata (
    domain TEXT PRIMARY KEY,
    anti_bot INTEGER DEFAULT 0,
    last_success_at TEXT,
    delay_seconds REAL DEFAULT 5.0
);
```

---

## Data Models

```python
from typing import List, Optional

class Page:
    url: str
    domain: str
    discovered_at: str
    fetched_at: Optional[str]
    status: Optional[int]
    content_type: Optional[str]
    charset: Optional[str]
    html_path: Optional[str]
    canonical: Optional[str]
    title: Optional[str]
    meta_desc: Optional[str]
    h1: Optional[str]
    h2: Optional[str]
    h3: Optional[str]
    robots: Optional[str]
    rel_canonical: Optional[str]
    lang: Optional[str]

class Link:
    src_url: str
    dst_url: str
    anchor: Optional[str]
    rel: Optional[str]
    nofollow: int
    is_internal: int

class Media:
    url: str
    page_url: str
    alt_text: Optional[str]
    type: str

class Structured:
    page_url: str
    syntax: str
    type: Optional[str]
    json: str

class Text:
    page_url: str
    text: str
    tokens: int
    word_count: int

class Phrase:
    page_url: str
    phrase: str
    n: int
    method: str
    score: Optional[float]
    freq: Optional[int]

class PhraseUsage:
    page_url: str
    phrase: str
    in_title: int
    in_h1: int
    in_h2: int
    in_anchor: int
    in_alt: int
    in_body: int
```

---

## Connection Pattern

```python
import sqlite3
from pathlib import Path

def db_connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row  # Dict-like access
    return conn

DDL = {
    "pages": "...",
    "links": "...",
    # ... dictionary of DDL statements
}

def init_db(conn: sqlite3.Connection) -> None:
    for ddl in DDL.values():
        conn.execute(ddl)
    conn.commit()
```

---

## Key Patterns

### 1. Content Change Detection
```python
from hashlib import sha256

def content_hash(data: bytes) -> str:
    return sha256(data).hexdigest()

# Compare hashes
if new_hash == existing_content_hash:
    # Content unchanged, skip update
    conn.execute("UPDATE pages SET last_scrape_time = ? WHERE url = ?", (ts, url))
else:
    # Archive old version
    conn.execute(
        "INSERT OR IGNORE INTO page_history (url, scraped_at, html_path, content_hash) VALUES (?, ?, ?, ?)",
        (url, ts, html_path, existing_content_hash)
    )
    # Update with new content
```

### 2. Retry Tracking with Investigation Flag
```python
def _handle_fetch_failure(conn, url, status=-2):
    cur = conn.execute("SELECT retry_count FROM pages WHERE url = ?", (url,))
    row = cur.fetchone()
    retry_count = row[0] if row else 0

    new_retry_count = retry_count + 1
    needs_investigation = 1 if new_retry_count >= 3 else 0

    conn.execute(
        "UPDATE pages SET status=?, retry_count=?, needs_investigation=? WHERE url=?",
        (status, new_retry_count, needs_investigation, url)
    )
```

### 3. Anti-bot Detection via Domain Metadata
```python
# Detect anti-bot: 404 after recent success
if status == 404:
    cur = conn.execute("SELECT last_success_at FROM domain_metadata WHERE domain = ?", (domain,))
    row = cur.fetchone()
    if row and row["last_success_at"]:
        last_success = datetime.fromisoformat(row["last_success_at"])
        if (datetime.now(UTC) - last_success).total_seconds() < 3600:  # 1 hour
            conn.execute("UPDATE domain_metadata SET anti_bot = 1 WHERE domain = ?", (domain,))

# On success, reset anti-bot flag
if 200 <= status < 300:
    conn.execute(
        """
        INSERT INTO domain_metadata (domain, last_success_at, anti_bot)
        VALUES (?, ?, 0)
        ON CONFLICT(domain) DO UPDATE SET
            last_success_at=excluded.last_success_at,
            anti_bot=0;
        """,
        (domain, datetime.now(UTC).isoformat())
    )
```

---

## What's Good / Usable

1. **Content hash comparison** - Efficient change detection, avoids redundant processing
2. **Page history archiving** - Full version control for competitor tracking
3. **Anti-bot detection** - Adaptive crawling based on response patterns
4. **Retry tracking** - `needs_investigation` flag for manual review
5. **SEO-focused schema** - title, meta_desc, h1-h3, canonical, robots
6. **Phrase usage mapping** - Keyword presence in title/h1/h2/anchor/alt/body
7. **PRAGMA optimizations** - WAL mode + NORMAL sync for better write performance

---

## What's Outdated

1. **Plain dataclasses vs ORM** - No validation, no relationships defined
2. **No indexes** - Large tables would benefit from indexes on domain, status
3. **No foreign keys** - Referential integrity not enforced

---

## What Must Be Rewritten

1. Add **Pydantic models** for validation
2. Add **indexes** for frequently queried columns:
   ```sql
   CREATE INDEX idx_pages_domain ON pages(domain);
   CREATE INDEX idx_pages_status ON pages(status);
   CREATE INDEX idx_links_src ON links(src_url);
   CREATE INDEX idx_phrases_page ON phrases(page_url);
   ```
3. Consider **composite index** for phrase_usage queries

---

## How It Fits AutoBiz

- **Merge with Market_AI schema** for comprehensive data layer
- **Use content_hash pattern** for all scraped/cached content
- **Adapt anti-bot detection** for business data collection
- **phrase_usage table** useful for SEO/content analysis features

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Market_AI | MarketIntel |
|---------|------------------|-----------|-------------|
| Tables | 9 | 10 | 3+ cache |
| Change detection | SHA256 hash | None | None |
| Version history | page_history | None | None |
| NLP storage | phrases + phrase_usage | None | None |
| Anti-bot tracking | domain_metadata | None | None |
| ORM | None | None | None |

**Recommendation**: Competitor-Intel has the most comprehensive schema for web scraping. Merge with Market_AI's 10-table schema for AutoBiz.
