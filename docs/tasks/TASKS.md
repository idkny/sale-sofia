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

**Session 37 (2025-12-27)**: Instance 2 - Phase 4.2 Async Implementation COMPLETE. Created `scraping/async_fetcher.py` with httpx.AsyncClient, added `acquire_async()` to rate_limiter, made scrapers/main.py sync. 11 new tests, 563 total passing.

**Session 36 (2025-12-27)**: Instance 3 - Created Spec 114: Scraper Monitoring & Observability. Researched codebase monitoring gaps, industry best practices, and designed 4-phase implementation plan (12 tasks). Spec ready for implementation.

**Session 35 (2025-12-27)**: Instance 1 - Phase 4.0 Database Concurrency COMPLETE. Created db_retry.py with @retry_on_busy decorator, enabled WAL mode + timeout in get_db_connection(), applied to 7 write functions. 17 concurrency tests passing.

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

##### Phase 4.0: Database Concurrency (COMPLETE)
> Files: `data/db_retry.py`, `data/data_store_main.py`, `tests/test_db_concurrency.py`
> Settings: `config/settings.py` - SQLITE_TIMEOUT, SQLITE_WAL_MODE, SQLITE_BUSY_*

- [x] 4.0.1 Add database settings to `config/settings.py`
- [x] 4.0.2 Update `get_db_connection()` with WAL mode + timeout
- [x] 4.0.3 Create `data/db_retry.py` with `@retry_on_busy()` decorator
- [x] 4.0.4 Apply `@retry_on_busy()` to 7 write functions
- [x] 4.0.5 Write concurrent write tests (17 tests passing)
- [x] 4.0.6 **Phase Completion Checklist** - Passed (200 tests total)

##### Phase 4.1: Scraping Settings Configuration (COMPLETE)
> **Spec archived**: `archive/specs/113_SCRAPING_CONFIGURATION.md`
> Created 2-level config: `scraping_defaults.yaml` + `config/sites/*.yaml`
> Integrated into main.py. Old `DEFAULT_SCRAPE_DELAY` removed.

- [x] 4.1.1 Create `config/scraping_defaults.yaml`
- [x] 4.1.2 Create `config/sites/` with per-site overrides
- [x] 4.1.3 Create `config/scraping_config.py` loader
- [x] 4.1.4 Write unit tests (7 tests, 99% coverage)
- [x] 4.1.5 Phase Completion Checklist + Integration

##### Phase 4.2: Async Implementation (COMPLETE)
> Fixed fake async patterns. Created true async fetcher for Celery integration.
> Files: `scraping/async_fetcher.py`, `resilience/rate_limiter.py` (acquire_async)

- [x] 4.2.1 Add async rate limiter method to `resilience/rate_limiter.py`
- [x] 4.2.2 Update scrapers to use sync methods (remove fake async)
- [x] 4.2.3 Create async fetch functions using `httpx.AsyncClient`
- [x] 4.2.4 Update `main.py` to use real async or sync consistently
- [x] 4.2.5 Write unit tests for async fetcher (11 tests, 100% coverage)
- [x] 4.2.6 **Phase Completion Checklist** - Passed (563 tests passing)

##### Phase 4.3: Celery Site Tasks
> **Why third**: Uses settings from 4.1 and async from 4.2.
> One Celery task per site, internal async for concurrent URL fetching.
>
> **Recommended**: Do Spec 114 Phase 1-2 (Core Metrics + Integration) BEFORE Phase 4.3.
> Reason: Having metrics/visibility helps debug Celery issues. Without monitoring, you're debugging blind.
> See: `docs/research/orchestration_research_prompt.md` for deep-dive research context.

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

### Scraper Monitoring & Observability (P1)

**Spec**: [114_SCRAPER_MONITORING.md](../specs/114_SCRAPER_MONITORING.md)

> **Goal**: Track scraper health, persist session reports, visualize performance.
> **Independent**: Can run in parallel with Phase 4 work.

#### Phase 1: Core Metrics
- [ ] 1.1 Create `scraping/metrics.py` with MetricsCollector class
- [ ] 1.2 Create `scraping/session_report.py` with SessionReportGenerator
- [ ] 1.3 Add health thresholds to `config/settings.py`
- [ ] 1.4 Write unit tests for metrics and reports

#### Phase 2: Integration
- [ ] 2.1 Add `get_all_states()` to `resilience/circuit_breaker.py`
- [ ] 2.2 Add `get_stats()` to `proxies/proxy_scorer.py`
- [ ] 2.3 Integrate MetricsCollector into `main.py` scraping flow

#### Phase 3: Dashboard
- [ ] 3.1 Create `app/pages/5_Scraper_Health.py` with basic layout
- [ ] 3.2 Add trend charts (success rate over time)
- [ ] 3.3 Add health indicators and run history table

#### Phase 4: Testing
- [ ] 4.1 Integration test: full scrape with metrics collection
- [ ] 4.2 Dashboard test: verify report loading and display

---

### Pre-Production Hardening (P0)

**Research**: [pre_production_audit_2025-12-28.md](../research/pre_production_audit_2025-12-28.md)

> **Context**: 6 AI agents audited codebase. 4 issues identified, 3 cancelled after impact analysis.
> Only 1 change confirmed safe. Other recommendations need impact analysis before implementing.

#### Phase 1: Confirmed Safe Change
- [ ] 1.1 Read research file `docs/research/pre_production_audit_2025-12-28.md`
- [ ] 1.2 Implement field allowlist in `update_listing_evaluation()`
  - Add `ALLOWED_UPDATE_FIELDS` set (37 fields)
  - Add validation loop before SQL building
  - Location: `data/data_store_main.py` around line 460
- [ ] 1.3 Run tests: `PYTHONPATH=. pytest tests/test_db_concurrency.py -v`
  - Expected: 17 passed (no regression)

#### Phase 2: Impact Analysis for Other Recommendations
> Before implementing any of these, run agents to check if they're actually needed.

- [ ] 2.1 **Impact analysis**: Consolidate `_calculate_delay()` duplicates
  - Files: `resilience/retry.py:29` vs `data/db_retry.py:24`
  - Question: Will importing from resilience break db_retry's independence?
- [ ] 2.2 **Impact analysis**: Consolidate `detect_encoding()` duplicates
  - Files: `websites/scrapling_base.py:51` vs `tests/scrapers/fetch_fixtures.py:42`
  - Question: Will test imports production code correctly?
- [ ] 2.3 **Impact analysis**: Consolidate `_extract_domain()` duplicates
  - Files: `main.py:78` vs `scraping/async_fetcher.py:40`
  - Question: Where should shared utility live?
- [ ] 2.4 **Impact analysis**: Fix `get_db_connection()` in agency_store.py
  - Files: `data/agency_store.py:20` missing WAL mode
  - Question: Is agency_store even used? Check for callers.
- [ ] 2.5 **Impact analysis**: Remove dead `archive/browsers/` directory
  - Question: Any hidden dependencies? Check all imports.
- [ ] 2.6 **Impact analysis**: Remove dead `update_listing_features()` function
  - Question: Any callers we missed?

#### Phase 3: Post-Analysis Implementation
> Only implement after Phase 2 confirms changes are safe.

- [ ] 3.1 Implement confirmed-safe consolidations
- [ ] 3.2 Remove confirmed-safe dead code
- [ ] 3.3 Run full test suite: `PYTHONPATH=. pytest tests/ -v`

---

## Related Documents

- [docs/specs/](../specs/) - Active specifications
- [docs/research/](../research/) - Active research
- [archive/](../../archive/) - Completed work archives

---

**Last Updated**: 2025-12-28 (Added Pre-Production Hardening tasks from audit)
