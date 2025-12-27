# Tasks - Single Source of Truth

**RULES:**
1. Claim tasks with `[Instance N]` before starting
2. Mark complete with `[x]` when done
3. Unclaim if not finishing this session
4. **Before marking phase complete**, run the Phase Completion Checklist (see below)

---

## Phase Completion Checklist

**Run these checks before marking ANY phase as complete:**

### 1. Consistency Check
- [ ] No hardcoded values (timeouts, limits, thresholds) - use `config/settings.py`
- [ ] Check for duplicate constants across files
- [ ] If new setting needed → add to `config/settings.py` with clear name
- [ ] Reference: `MIN_PROXIES_FOR_SCRAPING`, `PROXY_TIMEOUT`, `DOMAIN_RATE_LIMITS`

### 2. Alignment Check
- [ ] Is this task still relevant? (LLM, resilience, etc. may have changed things)
- [ ] Does the spec reflect current code? (code is source of truth)
- [ ] Are there overlaps with other specs/features?
- [ ] Update spec status annotations if needed

---

## Completed Work Summary

> **Archive**: [TASKS_COMPLETED_2025-12-27.md](../../archive/tasks/TASKS_COMPLETED_2025-12-27.md)

| Section | Tasks | Status |
|---------|-------|--------|
| Bugs (P0) | 3 | Completed |
| Proxy Scoring Bug (Solution F, Phases 0-7) | 31 | Completed |
| Chunk Processing Timing Bug | 12 | Completed |
| Celery + Mubeng + PSC Integration (Phases 1-2) | 14 | Completed |
| Page Change Detection (Phases 1-3) | 8 | Completed |
| Ollama Integration (Phases 1-5, 3.6) | 45+ | Completed |
| Crawler Validation (Phase 0) | 7 | Completed |
| Scraper Resilience (Phases 1-4) | 33 | Completed (153 tests) |
| Historical Completed Work | 35+ | Completed |

---

## Instance Coordination

| Instance | Current Task |
|----------|--------------|
| 1 | Available |
| 2 | Available |
| 3 | Available |

**Session 34 (2025-12-27)**: Instance 2 - Phase 4.1 Scraping Configuration COMPLETE. Created 2-level config system (scraping_defaults.yaml + sites/*.yaml), ScrapingConfig loader with 8 dataclasses, 7 tests passing (99% coverage).

**Session 33 (2025-12-27)**: Instance 2 - Phase 3.5 Cross-Site Duplicate Detection COMPLETE. Created listing_sources table, PropertyFingerprinter, PropertyMerger, price discrepancy tracking, dashboard page. 527 tests passing.

**Session 33 (2025-12-27)**: Instance 1 - Phase 4 Task Consolidation. Analyzed async/parallel patterns, researched Celery best practices, consolidated "async orchestrator" + "Celery integration" into unified Phase 4 with 4 sub-phases (22 tasks).

**Session 32 (2025-12-27)**: Instance 1 - Spec 112 Phase 4 (Detection) COMPLETE. Created response_validator.py, added Retry-After handling. 153 resilience tests passing. Spec archived.

**Session 31 (2025-12-27)**: Instance 2 - Phase 3 Change Detection COMPLETE. Added scrape_history + listing_changes tables, 7 CRUD functions, detect_all_changes(), 30 tests passing.

**Session 30 (2025-12-27)**: Instance 2 - Crawler Validation Phase 1 complete. All 46 scraper tests passing. Fixed floor extraction, price JS patterns, sqm patterns, and test fixtures for both scrapers.

**Session 30 (2025-12-27)**: Instance 1 - Spec 112 Phase 2 Implementation + Cleanup. Created circuit_breaker.py and rate_limiter.py. Integrated into main.py. 87 tests passing.

**Session 29 (2025-12-27)**: Instance 1 - Spec 112 Phase 1 Implementation. Created resilience/ module. 45 tests passing.

**Session 28 (2025-12-27)**: Instance 2 - Ollama Phase 3.6 complete. 100% accuracy via dictionary-first extraction.

**Claim**: Add `[Instance N]` next to task before starting
**Complete**: Add `[x]` and remove `[Instance N]` when done

---

## Pending Tasks

### Crawler Validation & Enhancement (P1)

**Spec**: [106_CRAWLER_VALIDATION_PLAN.md](../specs/106_CRAWLER_VALIDATION_PLAN.md)

> **Phase 0**: COMPLETE (Scrapling migration)
> **Phase 2**: SUPERSEDED by LLM extraction (Specs 107/108/110 achieved 100% accuracy)

#### Phase 1: Scraper Validation (COMPLETE)
- [x] Create test harness (`tests/scrapers/`) - 46 tests, 46 passing
- [x] Validate imot.bg scraper (pagination, extraction, save) - 23/23 tests passing
- [x] Validate bazar.bg scraper (pagination, extraction, save) - 23/23 tests passing
- [x] Create validation matrix - [106A_CRAWLER_VALIDATION_MATRIX.md](../specs/106A_CRAWLER_VALIDATION_MATRIX.md)
- [x] **Phase Completion Checklist** - Passed (no hardcoded values, spec aligned)

#### Phase 3: Change Detection & History (COMPLETE)
> Tables and functions added to `data/data_store_main.py` and `data/change_detector.py`.
- [x] Create `scrape_history` table - tracks URL scrape metadata
- [x] Create `listing_changes` table - tracks ALL field changes over time
- [x] Add 7 CRUD functions (upsert_scrape_history, record_field_change, etc.)
- [x] Add `detect_all_changes()` function with SKIP_FIELDS
- [x] Write 30 tests (`tests/test_change_detection.py`) - 100% pass
- [x] **Phase Completion Checklist** - Passed (no hardcoded values, spec aligned)

#### Phase 3.5: Cross-Site Duplicate Detection & Merging (COMPLETE)
> **Spec**: [106B_CROSS_SITE_DEDUPLICATION.md](../specs/106B_CROSS_SITE_DEDUPLICATION.md)
> Files: `data/property_fingerprinter.py`, `data/property_merger.py`, `app/pages/4_Cross_Site.py`

- [x] Create `listing_sources` table (track which sites list property)
- [x] Build `PropertyFingerprinter` class (identify duplicates)
- [x] Build `PropertyMerger` class (smart data merging)
- [x] Track price discrepancies across sites
- [x] Add cross-site comparison view to dashboard
- [x] **Phase Completion Checklist** - Passed (added settings to config/settings.py)

#### Phase 4: Celery Site Orchestration (CONSOLIDATED)
> **Goal**: Parallel site scraping via Celery with proper async and per-site configuration.
> **Consolidates**: "Build async orchestrator" + "Integrate with Celery" (same goal).
> **Dependencies**: Resilience module (complete), Rate limiter (complete).

##### Phase 4.0: Database Concurrency (BLOCKER)
> **Why first**: SQLite has single-writer limitation. Without fixes, parallel Celery workers
> calling `save_listing()` simultaneously WILL cause `database is locked` errors and data loss.
> **Risk**: HIGH - Phase 4.1+ will fail without this.
>
> **Current issues in `data/data_store_main.py`**:
> - No WAL mode (single-writer lock)
> - No timeout on `sqlite3.connect()` (5s default too short)
> - No retry on `SQLITE_BUSY` errors
> - No database settings in `config/settings.py`

- [ ] 4.0.1 Add database settings to `config/settings.py`
  - `SQLITE_TIMEOUT = 30.0` (seconds to wait for lock)
  - `SQLITE_BUSY_RETRIES = 3` (retry attempts on busy)
  - `SQLITE_BUSY_DELAY = 0.5` (delay between retries)
  - `SQLITE_WAL_MODE = True` (enable Write-Ahead Logging)
- [ ] 4.0.2 Update `get_db_connection()` in `data/data_store_main.py`
  - Add `timeout=SQLITE_TIMEOUT` to `sqlite3.connect()`
  - Add `PRAGMA journal_mode = WAL` when `SQLITE_WAL_MODE` is True
  - Add `PRAGMA busy_timeout` as fallback
- [ ] 4.0.3 Create `data/db_retry.py` with retry decorator
  - Follow `resilience/retry.py` pattern (exponential backoff)
  - Catch `sqlite3.OperationalError` with "database is locked"
  - `@retry_on_busy(max_attempts=SQLITE_BUSY_RETRIES)`
  - Log warnings on retry, error after exhausted
- [ ] 4.0.4 Apply `@retry_on_busy` to write functions in `data_store_main.py`
  - `save_listing()`, `update_listing_evaluation()`, `add_viewing()`
  - `upsert_scrape_history()`, `record_field_change()`
  - `add_listing_source()`, `update_source_price()`
- [ ] 4.0.5 Write concurrent write tests (`tests/test_db_concurrency.py`)
  - Test: 10 parallel threads calling `save_listing()`
  - Test: Mixed reads/writes under load
  - Verify: All writes succeed, no data loss
- [ ] 4.0.6 **Run Phase Completion Checklist** (settings centralized, no hardcoded values)

##### Phase 4.1: Scraping Settings Configuration
> **Spec**: [113_SCRAPING_CONFIGURATION.md](../specs/113_SCRAPING_CONFIGURATION.md)
> **Why**: Settings define the contract for how Celery tasks behave.
> Create 2-level config: general defaults + per-site overrides.
> Based on Scrapy, Colly, Crawlee best practices.
>
> **Cleanup Done**: Removed dead `SCRAPER_CONFIG` from `config/__init__.py`

- [x] 4.1.1 Create `config/scraping_defaults.yaml` (general settings)
- [x] 4.1.2 Create `config/sites/` with `imot_bg.yaml` and `bazar_bg.yaml`
- [x] 4.1.3 Create `config/scraping_config.py` loader (8 dataclasses, deep merge)
- [x] 4.1.4 Write unit tests (7 tests, 99% coverage)
- [x] 4.1.5 **Phase Completion Checklist** - Passed
  - Legacy `DEFAULT_SCRAPE_DELAY` + `SiteConfig` remain until main.py updated (Phase 4.2)

##### Phase 4.2: Async Implementation (Fix Fake Async)
> **Why second**: Clean foundation before Celery integration.
> Current code has `async def` with blocking `time.sleep()` - needs real async.

- [ ] 4.2.1 Add async rate limiter method to `resilience/rate_limiter.py`
  - `async def acquire_async(domain)` using `asyncio.sleep()`
  - Keep sync `acquire()` for backward compatibility
- [ ] 4.2.2 Update scrapers to use sync methods (remove fake async)
  - `websites/base_scraper.py`: `async def` → `def` for extract methods
  - `websites/imot_bg/imot_scraper.py`: Remove `async` (CPU-bound parsing)
  - `websites/bazar_bg/bazar_scraper.py`: Remove `async` (CPU-bound parsing)
- [ ] 4.2.3 Create async fetch functions using `httpx.AsyncClient`
  - New file: `scraping/async_fetcher.py`
  - `async def fetch_page(url, config)` with async rate limiting
  - Uses `asyncio.Semaphore` for concurrency control per domain
- [ ] 4.2.4 Update `main.py` to use real async or sync consistently
  - Remove `asyncio.run()` wrappers (will move to Celery)
  - Make scrape functions sync (Celery tasks handle async internally)
- [ ] 4.2.5 Write unit tests for async fetcher
- [ ] 4.2.6 **Run Phase Completion Checklist** (consistency + alignment)

##### Phase 4.3: Celery Site Tasks
> **Why third**: Uses settings from 4.1 and async from 4.2.
> One Celery task per site, internal async for concurrent URL fetching.

- [ ] 4.3.1 Create `scraping/tasks.py` with site scraping task
  - `@celery_app.task def scrape_site_task(site, start_urls)`
  - Loads config via `load_scraping_config(site)`
  - Uses `asyncio.run()` internally for concurrent fetching
  - Checkpoint integration for crash recovery
- [ ] 4.3.2 Update `celery_app.py` to include scraping tasks
  - Add `scraping.tasks` to `include` list
  - Configure task timeouts based on site config
- [ ] 4.3.3 Update `main.py` to submit Celery group
  - Replace sequential `for site in start_urls` loop
  - Use `group([scrape_site_task.s(site, urls) for site, urls in ...])`
  - Wait for group completion with progress display
- [ ] 4.3.4 Add task retry logic with exponential backoff
  - `@celery_app.task(bind=True, max_retries=3)`
  - Use existing `resilience/` patterns
- [ ] 4.3.5 Write unit tests for Celery tasks (mock async)
- [ ] 4.3.6 **Run Phase Completion Checklist** (consistency + alignment)

##### Phase 4.4: Integration Testing
> **Why last**: Validates end-to-end with real Celery workers.

- [ ] 4.4.1 Test parallel scraping with 2+ sites
  - Verify sites run concurrently (check timestamps)
  - Verify rate limiting per domain works
- [ ] 4.4.2 Test site-specific config overrides
  - Fast site (imot.bg) vs slow site (bazar.bg)
  - Verify different delays applied
- [ ] 4.4.3 Test crash recovery with checkpoints
  - Kill worker mid-scrape, restart, verify resume
- [ ] 4.4.4 Test circuit breaker + Celery interaction
  - Trigger failures, verify circuit opens, task retries
- [ ] 4.4.5 **Run Phase Completion Checklist** (full E2E validation)

---

#### Phase 5: Full Pipeline & Monitoring
> **Depends on**: Phase 4 complete (Celery orchestration working).

- [ ] 5.1 E2E testing (scrape → store → dashboard)
- [ ] 5.2 Add Celery Flower for task monitoring
- [ ] 5.3 Add alerting for scrape failures (email/Slack)
- [ ] 5.4 Performance benchmarking (parallel vs sequential)
- [ ] 5.5 **Run Phase Completion Checklist** (consistency + alignment)

---

## Related Documents

- [docs/specs/](../specs/) - Active specifications
- [docs/research/](../research/) - Active research
- [archive/](../../archive/) - Completed work archives

---

**Last Updated**: 2025-12-27 (Added Phase 4.0 Database Concurrency - BLOCKER for parallel scraping)
