---
id: extraction_ollamarag_db_schemas
type: extraction
subject: database
source_repo: Ollama-Rag
description: "Database schema extracted from Ollama-Rag - GitHub repository indexing"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, database, schema, ollamarag, github, repositories]
---

# Database Schemas - Ollama-Rag

**Source**: `save_to_md.py` (SQL query reveals schema)
**Purpose**: GitHub repository metadata storage for RAG indexing
**Status**: PARTIAL - Schema inferred from query, no actual SQL file exists

---

## Schema Overview

This is a **GitHub repository analysis** database schema. Different use case from:
- MarketIntel (market research, businesses, keywords)
- SerpApi (keyword discovery, entities)

---

## Inferred Tables

### Table: `repositories`

```sql
-- Inferred from save_to_md.py query
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,          -- e.g., "owner/repo-name"
    description TEXT,
    language TEXT,                     -- Primary programming language
    readme_content TEXT                -- Full README.md content
);
```

### Table: `repository_stats`

```sql
CREATE TABLE repository_stats (
    id INTEGER PRIMARY KEY,
    repository_id INTEGER NOT NULL,
    forks INTEGER DEFAULT 0,
    stars INTEGER DEFAULT 0,
    date_last_push TEXT,               -- ISO date string
    FOREIGN KEY (repository_id) REFERENCES repositories(id)
);
```

### Table: `topics`

```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE          -- Topic name (e.g., "python", "machine-learning")
);
```

### Table: `repository_topics` (Junction)

```sql
CREATE TABLE repository_topics (
    id INTEGER PRIMARY KEY,
    repository_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    FOREIGN KEY (repository_id) REFERENCES repositories(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    UNIQUE(repository_id, topic_id)
);
```

---

## Query Pattern: Join All Tables

```sql
-- From save_to_md.py:fetch_data_and_save_to_markdown()
SELECT
    r.full_name,
    r.description,
    r.language,
    r.readme_content,
    rs.forks,
    rs.stars,
    rs.date_last_push,
    GROUP_CONCAT(t.name, ', ') AS topics
FROM
    repositories r
LEFT JOIN
    repository_stats rs ON r.id = rs.repository_id
LEFT JOIN
    repository_topics rt ON r.id = rt.repository_id
LEFT JOIN
    topics t ON rt.topic_id = t.id
GROUP BY
    r.id
```

---

## Data Flow

```
GitHub API → repositories table → repository_stats
                              → repository_topics ← topics
                              ↓
                         save_to_md.py
                              ↓
                         ./data/*.md files
                              ↓
                         RAG VectorStoreIndex
```

---

## Conclusions

### ✅ Good / Usable

1. **Clean normalization** - Stats and topics in separate tables
2. **Junction table pattern** - Many-to-many for topics (same as SerpApi's entity linking)
3. **GROUP_CONCAT** - Efficient way to flatten topics

### ⚠️ Outdated / Missing

1. **No actual schema file** - Only inferred from query
2. **Missing database.py** - `save_to_md.py` imports `from src.database import database_connection` but `src/` folder doesn't exist
3. **No connection pool** - Unknown how connections are managed
4. **No created_at/updated_at** - Missing audit timestamps

### 🔧 Must Rewrite

1. **Complete the schema** - Create actual migration/schema file
2. **Add database connection context manager** - Missing `database_connection()` function
3. **Add indexes** - No index definitions visible

### 📊 Comparison with Previous Repos

| Feature | MarketIntel | SerpApi | Ollama-Rag |
|---------|-------------|---------|------------|
| Purpose | Market research | Keyword discovery | GitHub repo indexing |
| Tables | businesses, keywords, search_results, api_cache | keywords, entities, serp_results, discovery_batch | repositories, repository_stats, topics |
| Junction Tables | keyword_business_links | repository_topics | repository_topics |
| Stats Tracking | No | No | Yes (forks, stars) |
| Timestamps | Yes (created_at, updated_at) | Yes | No (missing) |
| Caching | Yes (api_cache with TTL) | No | No |

### 🎯 Fit for AutoBiz

- **Not directly usable** - GitHub-specific schema
- **Pattern reusable** - Junction table for many-to-many, stats separation
- **Missing too much** - Incomplete implementation

---

## Files

- Source: `/tmp/Ollama-Rag/save_to_md.py` (query only)
- No schema.sql file exists
- No database.py exists (import fails)
