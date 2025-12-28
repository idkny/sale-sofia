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
| Pre-Production Hardening (Phases 1-3) | 10 | Completed (563 tests) |
| Historical Completed Work | 35+ | Completed |

---

## Instance Coordination

| Instance | Current Task |
|----------|--------------|
| 1 | Available |
| 2 | Available |
| 3 | Available |

**Session 40 (2025-12-28)**: Instance 2 - Phase 4.3 Spec + Pre-requisites. Created Spec 115 (Celery Site Tasks) from validation research. Completed 4.3.0.1 (timeout fix) and 4.3.0.2 (DB init race condition fix). 77 tests verified.

**Session 39 (2025-12-28)**: Instance 2 - Orchestration Validation. Launched 6 architect-review agents to validate all modules for Celery correctness. Found 3 critical issues, 3 modules need Redis backing. Created 7 validation docs. Added BLOCKING task for next session.

**Session 39 (2025-12-28)**: Instance 1 - Pre-Production Hardening COMPLETE. Phase 1: Added field allowlist to update_listing_evaluation(). Phase 2: Deployed 2 agents for impact analysis (3 cancelled, 3 implemented). Phase 3: Consolidated extract_domain() to resilience/, removed update_listing_features(), documented agency_store.py. 563 tests passing.

**Session 38 (2025-12-28)**: Instance 1 - Pre-Production Audit. Deployed 10 agents total. Found 4 potential issues, 3 cancelled after impact analysis. Added Pre-Production Hardening tasks to TASKS.md.

**Session 37 (2025-12-27)**: Instance 2 - Phase 4.2 Async Implementation COMPLETE. Created `scraping/async_fetcher.py` with httpx.AsyncClient, added `acquire_async()` to rate_limiter, made scrapers/main.py sync. 11 new tests, 563 total passing.

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

### Orchestration Research Review (P0) - COMPLETE

> **UNBLOCKED** - Spec 115 written, Phase 4.3 tasks updated

**Completed** (Session 40):
- [x] Review 7 validation documents
- [x] Write spec for Phase 4.3 based on validation findings → [115_CELERY_SITE_TASKS.md](../specs/115_CELERY_SITE_TASKS.md)
- [x] Update Phase 4.3 tasks (added pre-requisites)

**Research archived**: `docs/research/orchestration_*.md`, `docs/research/validation_*.md`

---

### Crawler Validation & Enhancement (P1)

**Spec**: [106_CRAWLER_VALIDATION_PLAN.md](../specs/106_CRAWLER_VALIDATION_PLAN.md)

> **Phase 0**: COMPLETE (Scrapling migration)
> **Phase 2**: SUPERSEDED by LLM extraction (Specs 107/108/110 achieved 100% accuracy)

#### Phase 1: Scraper Validation (COMPLETE)
- [x] Create test harness (`tests/scrapers/`) - 46 tests, 46 passing
- [x] Validate imot.bg scraper (pagination, extraction, save) - 23/23 tests passing
- [x] Validate bazar.bg scraper (pagination, extraction, save) - 23/23 tests passing
- [x] Create validation matrix - [106A_CRAWLER_VALIDATION_MATRIX.md](../../archive/specs/106A_CRAWLER_VALIDATION_MATRIX.md)
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
> **Spec**: [106B_CROSS_SITE_DEDUPLICATION.md](../../archive/specs/106B_CROSS_SITE_DEDUPLICATION.md)
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
> **Spec**: [115_CELERY_SITE_TASKS.md](../specs/115_CELERY_SITE_TASKS.md)
> Parallel site scraping via Celery with shared resilience state.
> **Research**: `docs/research/validation_synthesis.md`, `docs/research/orchestration_synthesis.md`

**BEFORE EACH TASK** (mandatory):
1. **Impact Analysis**: Review how the change affects the project (callers, dependencies, side effects)
2. **Test Identification**: Identify which tests to run before/after to verify no regressions
3. **Implementation**: Make the change
4. **Verification**: Run identified tests, confirm no new bugs introduced

###### Phase 4.3.0: Pre-requisites (Critical Fixes)
> Must complete before any Celery work. Found by validation agents.

- [x] 4.3.0.1 Fix timeout forwarding in `orchestrator.py:521`
  - Impact: `wait_for_proxies()` callers, `main.py:508`
  - Tests: `tests/unit/test_orchestrator_helpers.py` (30 passed)
- [x] 4.3.0.2 Move DB init out of module-level in `data_store_main.py`
  - Impact: All imports of `data_store_main`, worker startup
  - Tests: `tests/test_db_concurrency.py`, `tests/test_change_detection.py` (47 passed)
- [ ] 4.3.0.3 Add `@retry_on_busy()` to read functions in `data_store_main.py`
  - Impact: All `get_*` function callers
  - Tests: `tests/test_db_concurrency.py`, `tests/data/`
- [ ] 4.3.0.4 Increase `SQLITE_BUSY_RETRIES` from 3 to 5
  - Impact: All `@retry_on_busy()` decorated functions
  - Tests: `tests/test_db_concurrency.py`

###### Phase 4.3.1: Redis-Backed Circuit Breaker
- [ ] 4.3.1.1 Create `resilience/redis_circuit_breaker.py`
  - Impact: New file, no existing code affected
  - Tests: New tests to create
- [ ] 4.3.1.2 Add `REDIS_CIRCUIT_BREAKER_ENABLED` feature flag
  - Impact: `config/settings.py` only
  - Tests: None (config only)
- [ ] 4.3.1.3 Update `resilience/__init__.py` factory function
  - Impact: All `get_circuit_breaker()` callers
  - Tests: `tests/resilience/`
- [ ] 4.3.1.4 Write unit tests for Redis circuit breaker
  - Impact: None (test only)
  - Tests: Self-verifying

###### Phase 4.3.2: Redis-Backed Rate Limiter
- [ ] 4.3.2.1 Create `resilience/redis_rate_limiter.py` (Lua script for atomicity)
  - Impact: New file, no existing code affected
  - Tests: New tests to create
- [ ] 4.3.2.2 Add `REDIS_RATE_LIMITER_ENABLED` feature flag
  - Impact: `config/settings.py` only
  - Tests: None (config only)
- [ ] 4.3.2.3 Update factory function in `resilience/__init__.py`
  - Impact: All `get_rate_limiter()` callers
  - Tests: `tests/resilience/`
- [ ] 4.3.2.4 Write unit tests for Redis rate limiter
  - Impact: None (test only)
  - Tests: Self-verifying

###### Phase 4.3.3: Scraping Celery Tasks
- [ ] 4.3.3.1 Create `scraping/redis_keys.py` (key patterns)
  - Impact: New file, no existing code affected
  - Tests: New tests to create
- [ ] 4.3.3.2 Create `scraping/tasks.py` with dispatcher/worker/callback
  - Impact: New file, no existing code affected
  - Tests: New tests to create
- [ ] 4.3.3.3 Update `celery_app.py` to include `scraping.tasks`
  - Impact: Celery task registration
  - Tests: `tests/proxies/test_celery_tasks.py`
- [ ] 4.3.3.4 Write unit tests for Celery tasks
  - Impact: None (test only)
  - Tests: Self-verifying

###### Phase 4.3.4: Integration
- [ ] 4.3.4.1 Add scraping orchestration methods to `orchestrator.py`
  - Impact: Orchestrator API
  - Tests: `tests/unit/test_orchestrator_helpers.py`
- [ ] 4.3.4.2 Update `main.py` with `PARALLEL_SCRAPING` mode
  - Impact: Main entry point, scraping flow
  - Tests: Manual E2E test
- [ ] 4.3.4.3 Add new settings to `config/settings.py`
  - Impact: Config only
  - Tests: None (config only)
- [ ] 4.3.4.4 Integration tests (chord workflow, progress tracking)
  - Impact: None (test only)
  - Tests: Self-verifying
- [ ] 4.3.4.5 **Run Phase Completion Checklist** (consistency + alignment)

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
- [x] 1.1 Create `scraping/metrics.py` with MetricsCollector class
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

## Related Documents

- [docs/specs/](../specs/) - Active specifications
- [docs/research/](../research/) - Active research
- [archive/](../../archive/) - Completed work archives

---

**Last Updated**: 2025-12-28 (Pre-Production Hardening complete, archived)
