---
id: 20251201_database_serpapi_schemas
type: extraction
subject: database/schemas
source_repo: idkny/SerpApi
source_file: Note.md
description: "Database schema specifications from SerpApi planning document"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, database, schemas, serpapi, sqlite]
---

# DATABASE SCHEMAS - SerpApi

**Source**: `idkny/SerpApi/Note.md`
**Type**: Specification (not implemented code)
**Database**: SQLite
**Tables**: 10

---

## EXTRACTED SCHEMAS

### Table 1: Keywords

```sql
CREATE TABLE IF NOT EXISTS Keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_text TEXT NOT NULL UNIQUE,
    initial_category TEXT,
    status TEXT DEFAULT 'pending_review',  -- pending_review, approved, rejected
    source_endpoint TEXT,
    base_query TEXT,
    attempts INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Keyword tracking with approval workflow
**Key Pattern**: Status workflow (pending_review → approved/rejected)

---

### Table 2: Locations

```sql
CREATE TABLE IF NOT EXISTS Locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    state TEXT,
    country TEXT NOT NULL,
    uule_code TEXT,
    population INTEGER,
    UNIQUE(city, state, country)
);
```

**Purpose**: Geographic targeting for searches
**Key Pattern**: UULE code for Google location targeting

---

### Table 3: SearchSessions

```sql
CREATE TABLE IF NOT EXISTS SearchSessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    engine_used TEXT NOT NULL,
    device_type TEXT DEFAULT 'desktop',
    serpapi_id TEXT,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords(keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
);
```

**Purpose**: Links keywords + locations to search executions
**Key Pattern**: Session as central FK hub for all results

---

### Table 4: OrganicResults

```sql
CREATE TABLE IF NOT EXISTS OrganicResults (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    url TEXT,
    domain TEXT,
    snippet TEXT,
    date_published TEXT,
    content_type TEXT,
    search_intent_classified TEXT,
    site_category_classified TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);
```

**Purpose**: Store SERP organic results
**Key Pattern**: AI classification fields (content_type, search_intent, site_category)

---

### Table 5: PaidAds

```sql
CREATE TABLE IF NOT EXISTS PaidAds (
    ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    link TEXT,
    displayed_link TEXT,
    snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);
```

**Purpose**: Google Ads competitor tracking

---

### Table 6: LocalBusinessResults

```sql
CREATE TABLE IF NOT EXISTS LocalBusinessResults (
    local_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);
```

**Purpose**: Google Maps/Local pack results
**Key Pattern**: place_id for review fetching

---

### Table 7: RelatedQuestions

```sql
CREATE TABLE IF NOT EXISTS RelatedQuestions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_text TEXT,
    answer_snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);
```

**Purpose**: People Also Ask data

---

### Table 8: GoogleTrendsData

```sql
CREATE TABLE IF NOT EXISTS GoogleTrendsData (
    trend_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    date_range_query TEXT,
    data_type TEXT,  -- TIMESERIES, RELATED_TOPICS, RELATED_QUERIES
    interest_value INTEGER,
    trending_topic_or_query_text TEXT,
    extracted_value TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords(keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
);
```

**Purpose**: Google Trends interest over time + related queries
**Key Pattern**: data_type enum for different trend types

---

### Table 9: NewsArticles

```sql
CREATE TABLE IF NOT EXISTS NewsArticles (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    title TEXT,
    url TEXT,
    source TEXT,
    published_date TEXT,
    snippet TEXT,
    relevance_score REAL,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);
```

**Purpose**: Google News results

---

### Table 10: Entities

```sql
CREATE TABLE IF NOT EXISTS Entities (
    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id INTEGER NOT NULL,
    source_table TEXT NOT NULL,  -- 'OrganicResults', 'NewsArticles', etc.
    entity_text TEXT,
    salience REAL,
    sentiment_score REAL,
    sentiment_magnitude REAL,
    num_mentions INTEGER,
    entity_type TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Generic entity extraction from any source
**Key Pattern**: Polymorphic FK (source_item_id + source_table)

---

## CONCLUSIONS

### What is Good / Usable

1. **Session-based architecture** - SearchSessions as central hub is clean
2. **Keyword workflow** - Status field with pending/approved/rejected is practical
3. **UULE codes** - Google location targeting built-in
4. **Polymorphic FK pattern** - Entities table can link to any source
5. **AI classification fields** - OrganicResults ready for post-processing
6. **place_id** - Enables Google Maps review fetching

### What is Outdated

1. **10 tables is over-engineered** for initial AutoBiz needs
2. **No indexes defined** - Would need performance optimization
3. **No updated_at triggers** - Manual timestamp management

### What Must Be Rewritten

1. **Combine some tables** - OrganicResults + PaidAds could be unified with type field
2. **Add indexes** - On keyword_id, session_id, domain
3. **Simplify Entities** - Polymorphic FK is complex, might use JSONB instead

### How It Fits Into AutoBiz

- **Use SearchSessions pattern** for any API call tracking
- **Use keyword workflow** for discovery pipelines
- **Adapt Locations** for multi-business support
- **Skip** NewsArticles, RelatedQuestions (not needed initially)

### Conflicts with Previous Repos

| Aspect | SerpApi (This) | MarketIntel | Best |
|--------|----------------|-------------|------|
| Tables | 10 | 5 | MarketIntel (simpler) |
| Session hub | Yes | Yes | Same pattern |
| Keyword workflow | Full | Partial | SerpApi (more complete) |
| Entity extraction | Polymorphic FK | None | Consider for v2 |
| Indexes | None | Basic | Need to add |

### Best Version

**MarketIntel's actual schema** is better for production, but **SerpApi's keyword workflow** is more complete. Merge the keyword status fields into MarketIntel's simpler structure.

---

## REUSABLE ARTIFACTS

### Full Schema SQL (All 10 Tables)

```sql
-- Keywords table with status workflow
CREATE TABLE IF NOT EXISTS Keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_text TEXT NOT NULL UNIQUE,
    initial_category TEXT,
    status TEXT DEFAULT 'pending_review',
    source_endpoint TEXT,
    base_query TEXT,
    attempts INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations with UULE support
CREATE TABLE IF NOT EXISTS Locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    state TEXT,
    country TEXT NOT NULL,
    uule_code TEXT,
    population INTEGER,
    UNIQUE(city, state, country)
);

-- Search sessions as FK hub
CREATE TABLE IF NOT EXISTS SearchSessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    engine_used TEXT NOT NULL,
    device_type TEXT DEFAULT 'desktop',
    serpapi_id TEXT,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords(keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
);

-- Organic SERP results
CREATE TABLE IF NOT EXISTS OrganicResults (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    url TEXT,
    domain TEXT,
    snippet TEXT,
    date_published TEXT,
    content_type TEXT,
    search_intent_classified TEXT,
    site_category_classified TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);

-- Paid ads
CREATE TABLE IF NOT EXISTS PaidAds (
    ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    position INTEGER,
    title TEXT,
    link TEXT,
    displayed_link TEXT,
    snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);

-- Local business results
CREATE TABLE IF NOT EXISTS LocalBusinessResults (
    local_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);

-- People Also Ask
CREATE TABLE IF NOT EXISTS RelatedQuestions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_text TEXT,
    answer_snippet TEXT,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);

-- Google Trends data
CREATE TABLE IF NOT EXISTS GoogleTrendsData (
    trend_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    date_range_query TEXT,
    data_type TEXT,
    interest_value INTEGER,
    trending_topic_or_query_text TEXT,
    extracted_value TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES Keywords(keyword_id),
    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
);

-- News articles
CREATE TABLE IF NOT EXISTS NewsArticles (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    title TEXT,
    url TEXT,
    source TEXT,
    published_date TEXT,
    snippet TEXT,
    relevance_score REAL,
    FOREIGN KEY (session_id) REFERENCES SearchSessions(session_id)
);

-- Generic entity extraction
CREATE TABLE IF NOT EXISTS Entities (
    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id INTEGER NOT NULL,
    source_table TEXT NOT NULL,
    entity_text TEXT,
    salience REAL,
    sentiment_score REAL,
    sentiment_magnitude REAL,
    num_mentions INTEGER,
    entity_type TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
