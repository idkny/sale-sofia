# Orchestration Research: Data Module

## Executive Summary

The data module uses **SQLite with WAL mode**. Write operations have retry logic for lock contention. **Critical concerns**: SQLite doesn't support true parallel writes; with 10+ concurrent agents, expect bottlenecks. Consider connection pooling and batch operations for Phase 4.3.

---

## 1. Database Technology

### SQLite with WAL Mode
- Location: `data/bg-estate.db`
- Mode: Write-Ahead Logging (WAL) enabled
- Concurrency: Unlimited readers, single writer

### Settings (config/settings.py)
```python
SQLITE_TIMEOUT = 30.0        # Connection wait timeout
SQLITE_WAL_MODE = True       # Enables concurrent readers
SQLITE_BUSY_RETRIES = 3      # Retry attempts
SQLITE_BUSY_DELAY = 0.5      # Base delay seconds
SQLITE_BUSY_MAX_DELAY = 5.0  # Max delay cap
```

---

## 2. Core Data Store Functions

### Main Module: `data_store_main.py` (1332 lines)

### Tables
| Table | Purpose |
|-------|---------|
| listings | Main property data (100+ columns) |
| listing_viewings | Viewing records |
| scrape_history | Content hashes, scrape metadata |
| listing_changes | Field-level change history |
| listing_sources | Cross-site deduplication |
| agencies | Real estate agency metadata |

### Key Functions
| Function | Purpose |
|----------|---------|
| `save_listing()` | Upsert with change detection (@retry_on_busy) |
| `update_listing_evaluation()` | User evaluation data |
| `init_db()`, `migrate_listings_schema()` | Schema management |
| `add_listing_source()` | Cross-site deduplication |
| `record_field_change()` | Change tracking |
| `get_listings()`, `get_listings_stats()` | Query functions |

---

## 3. Retry Logic (db_retry.py)

### Algorithm: Exponential Backoff with Jitter
```python
delay = min(base * 2^attempt, max_delay) + jitter(0-50%)
```

### Behavior
- Attempt 0: Initial try, fails
- Attempt 1: 0.5s + jitter = ~0.25-0.75s wait
- Attempt 2: 1.0s + jitter = ~0.5-1.5s wait
- Attempt 3: 2.0s → capped at 5.0s
- All exhausted: raises sqlite3.OperationalError

### Important
Only retries "database is locked" errors. Other errors fail immediately.

---

## 4. Deduplication System

### Cross-Site Deduplication (Spec 106B)

#### A. Property Fingerprinting (`property_fingerprinter.py`)
- Hash input: `neighborhood | sqm_total | rooms_count | floor_number | building_type`
- Normalizes neighborhood names (removes prefixes)
- Returns 16-char SHA256 hex

#### B. listing_sources Table
- UNIQUE constraint on (property_fingerprint, source_site)
- Tracks: fingerprint, listing_id, source_site, source_url, price, timestamps

#### C. Price Discrepancy Detection (`property_merger.py`)
- Compares prices across sources for same fingerprint
- Thresholds: 5% (highlight), 10% (high alert)

### Save Flow
```
scraper → save_listing() → listings table (upsert on URL)
        → compute_hash() → store in content_hash column
        → link_listing_to_sources() → listing_sources table
        → detect duplicate → log if cross-site match
```

---

## 5. Concurrency Concerns

### SQLite Lock Contention
| Issue | Impact |
|-------|--------|
| Single writer at a time | Even with WAL mode |
| 10+ concurrent agents | Write lock bottleneck |
| Retry delays | 5s + 5s + 5s = 15s per blocked operation |

### Connection Management Issues
- Each function opens new connection
- No connection pooling
- 30s timeout may be too generous

### Undecorated Reads
- Read functions NOT decorated with @retry_on_busy()
- Can get "database is locked" without retry
- Examples: `get_listing_by_url()`, `get_listings_stats()`

### Timeout Cascade Risk
- Hard 5.0s max delay
- Under load, multiple operations hit max
- Could cause cascading timeouts upstream

### No Metrics
- No logging of lock wait times
- Difficult to detect contention until timeouts occur

---

## 6. What Orchestrator Needs to Know

### Capacity & Rate Limits
- SQLite max write throughput: ~1 write/sec per core (conservative)
- Recommend: max 3-5 concurrent agents writing simultaneously
- Batching is critical for high-throughput

### Operation Latencies
| Scenario | Latency |
|----------|---------|
| Read (no lock) | <10ms |
| Write (low contention) | 10-50ms |
| Write (high contention) | 5-15 seconds |

### Bottleneck Points
- `save_listing()` with duplicate detection (3 DB operations)
- `record_field_change()` on every update (scales poorly)
- `get_properties_with_multiple_sources()` with join/group

### Health Signals
- "database is locked" error rate
- Average retry count per operation
- Failed operations after 3 retries

### Initialization Order
```
init_db() → migrate_listings_schema() → init_viewings_table()
         → init_change_detection_tables() → init_listing_sources_table()
```

---

## 7. Gaps for Production Parallel Scraping

| Gap | Impact | Mitigation |
|-----|--------|-----------|
| No connection pooling | Overhead under 10+ agents | Implement pooling |
| Undecorated reads | Silent failures | Add @retry_on_busy() to reads |
| No write batching | N listings = N transactions | Implement batch insert |
| Missing metrics | Blind to degradation | Log to Redis |
| Hard 5.0s delay cap | Cascading timeouts | Make dynamic |
| Agency linking separate | Race conditions | Include in save_listing() |

---

## 8. Recommendations for Phase 4.3

### Immediate (before 10+ agents)
1. Add @retry_on_busy() to read functions
2. Implement `save_listings_batch()` for bulk inserts
3. Add logging: track retry counts, lock wait times
4. Document expected throughput: "max 5 concurrent saves"

### Short-term (production readiness)
1. Implement connection pooling
2. Create `orchestrator_data` module with rate limiting
3. Add health check: `check_db_health()`
4. Implement exponential backoff at orchestrator level

### Long-term (post Phase 4.3)
1. Consider PostgreSQL migration (eliminates write lock contention)
2. Implement async/await for DB operations
3. Add replication for read scaling

---

## Architecture Notes for Orchestrator

### Data Module Interface for Orchestration
The orchestrator should NOT call data functions directly in parallel:

- Implement **task queue** in front of data writes (Celery with rate limiting)
- Use **batch operations** for bulk inserts
- Monitor **lock contention metrics** via Redis
- Implement **adaptive concurrency**: reduce agents if retry rate exceeds threshold

### Key Integration Points
| Function | When Called | Can Batch? |
|----------|-------------|------------|
| `save_listing()` | After scraping each page | Yes |
| `record_field_change()` | On updates | Yes |
| `upsert_scrape_history()` | Per URL scraped | Yes |
| `add_listing_source()` | For deduplication | Part of save flow |

All should flow through Celery tasks with explicit rate limiting.
