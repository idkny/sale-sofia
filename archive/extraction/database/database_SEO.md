---
id: database_seo
type: extraction
subject: database
source_repo: SEO
description: "7-table SEO schema: cache, negatives, entities, harvest_log, discovered_keywords, task_runs"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [database, sqlite, seo, keywords, cache]
---

# Database Extraction: SEO

**Source**: `idkny/SEO`
**Files**: `src/scripts/db.py`, `migrations.py`

---

## Schema Overview

7 tables for SEO keyword research and API tracking:

| Table | Purpose |
|-------|---------|
| `cache` | API response cache with TTL |
| `negatives` | Negative keywords to filter |
| `brand_terms` | Brand terms to filter |
| `stop_domains` | Domains to exclude |
| `entities` | Business/competitor entities |
| `harvest_log` | API request audit log |
| `discovered_keywords` | Keyword discovery workflow |
| `task_runs` | Task execution tracking |

---

## Full DDL

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    engine TEXT,
    params_json TEXT,
    response_json TEXT,
    fetched_at REAL,
    ttl_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS negatives (term TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS brand_terms (term TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS stop_domains (domain TEXT PRIMARY KEY);

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    domain TEXT,
    place_id TEXT,
    data_cid TEXT,
    category TEXT,
    nap TEXT,
    is_ours BOOLEAN,
    confidence REAL
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

CREATE TABLE IF NOT EXISTS discovered_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    source_endpoint TEXT NOT NULL,
    base_query TEXT NOT NULL,
    keyword TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending_review',
    last_run_at DATETIME,
    attempts INTEGER DEFAULT 0,
    run_status TEXT
);

CREATE TABLE IF NOT EXISTS task_runs (
    task_name TEXT PRIMARY KEY,
    last_run_at TEXT NOT NULL,
    status TEXT NOT NULL
);
```

---

## Keyword Workflow

```
pending_review → approved → (run)
               ↘ rejected → (added to negatives)
```

---

## What's Good / Usable

1. **Cache table** - TTL-based API caching
2. **Audit log** - Request/response logging
3. **Keyword workflow** - Discovery → Review → Approve/Reject
4. **Entity tracking** - Our business vs competitors

---

## Cross-Repo Comparison

| Feature | SEO | MarketIntel | Competitor-Intel |
|---------|-----|-------------|------------------|
| Cache | Yes | Yes | No |
| Audit log | Yes | No | No |
| Keyword workflow | Yes | No | phrases table |

**Recommendation**: SEO has best keyword workflow. Merge with Competitor-Intel.
