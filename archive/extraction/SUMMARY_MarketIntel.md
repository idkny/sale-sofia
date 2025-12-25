---
id: 20251201_summary_marketintel
type: extraction_summary
subject: repository
description: "Complete extraction summary for MarketIntel repository"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [summary, marketintel, extraction, repository]
source_repo: idkny/MarketIntel
---

# MarketIntel Repository Summary

**Repository**: `idkny/MarketIntel`
**Analyzed**: 2025-12-01
**Status**: Production-ready (real data present)
**Quality Score**: 7/10

---

## What This Repo Does

Market research automation system that:
- Collects SERP data via SerpAPI
- Tracks competitors (1,997 local businesses)
- Auto-classifies keywords using Ollama (1,346 keywords)
- Caches API responses with TTL
- Stores everything in SQLite (3.5MB production DB)

---

## Extracted Files

| File | Subject | Priority |
|------|---------|----------|
| `database_MarketIntel.md` | Database schema + patterns | HIGH |
| `api_client_MarketIntel.md` | Caching, retry, deduplication | HIGH |
| `ai_llm_MarketIntel.md` | Ollama client, classification | HIGH |
| `config_MarketIntel.md` | Pydantic + YAML config | HIGH |
| `workflow_MarketIntel.md` | Registry, pipelines | MEDIUM |
| `database_MarketIntel_schema.sql` | Raw SQL schema | REF |

---

## Key Patterns for AutoBiz

### HIGH Priority (Port Directly)

1. **OllamaClient** - Local LLM with JSON mode
   - File: `ai_llm_MarketIntel.md`
   - Target: `autobiz/tools/llm/`

2. **API Cache with TTL** - SHA256 keys, thread-safe
   - File: `api_client_MarketIntel.md`
   - Target: `autobiz/tools/api/`

3. **get_or_insert Pattern** - Deduplication
   - File: `database_MarketIntel.md`
   - Target: `autobiz/tools/data/`

4. **Pydantic Settings** - .env + YAML hybrid
   - File: `config_MarketIntel.md`
   - Target: `autobiz/core/config.py`

### MEDIUM Priority (Learn From)

5. **Endpoint Registry** - Name to function mapping
   - File: `workflow_MarketIntel.md`
   - Target: `autobiz/pipelines/`

6. **Confidence Automation** - Auto-approve/reject
   - File: `ai_llm_MarketIntel.md`
   - Target: Pipeline decision logic

7. **Resilient Iteration** - Continue on error
   - File: `workflow_MarketIntel.md`
   - Target: Batch processing

### LOW Priority (Reference Only)

8. **SERP extractors** - Too API-specific
9. **Geo/location handling** - Not needed

---

## What is NOT in This Repo

- No browser automation (API-only approach)
- No proxy handling
- No raw HTML scraping
- No Selenium/Playwright

---

## Database Tables (12 total)

| Table | Records | AutoBiz Use |
|-------|---------|-------------|
| Keywords | 1,346 | Adapt for sync_items |
| SearchSessions | 427 | Adapt for sync_sessions |
| LocalBusinessResults | 1,997 | Reference only |
| OrganicResults | 1,501 | Reference only |
| **cache** | N/A | **PORT DIRECTLY** |
| **harvest_log** | N/A | **PORT DIRECTLY** |

---

## Dependencies

```
google-search-results  # SerpAPI SDK
python-dotenv          # .env loading
requests               # HTTP client
beautifulsoup4         # HTML parsing (not used)
python-dateutil        # Date handling
pydantic-settings      # Config management
pyyaml                 # YAML config
```

**Relevant for AutoBiz**: requests, pydantic-settings, pyyaml

---

## Next Steps

1. Wait for more repos to compare
2. After all repos analyzed:
   - Merge similar patterns
   - Choose best implementation per subject
   - Port to AutoBiz structure
