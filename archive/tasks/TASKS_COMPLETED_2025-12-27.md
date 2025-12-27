# Tasks - Completed Archive (2025-12-27)

**Archived from**: [TASKS.md](../../docs/tasks/TASKS.md)

---

## Summary

| Section | Tasks | Status |
|---------|-------|--------|
| Bugs (P0) | 3 | Completed |
| Proxy Scoring Bug (Solution F) | 31 | Completed |
| Chunk Processing Timing Bug | 12 | Completed |
| Page Change Detection Phases 1-3 | 8 | Completed |
| Ollama Integration Phases 1-5 | 45+ | Completed |
| Crawler Validation Phase 0 | 7 | Completed |
| Scraper Resilience Phases 1-4 | 33 | Completed (153 tests) |
| Historical Completed Work | 35+ | Completed |

---

## Bugs (P0) - COMPLETE

- [x] Run stress tests - Test 5 PASSED: no orphan mubeng processes

- [x] Proxy-level real IP protection (verified implemented)
  - quality_checker.py:143-155 - rejects if exit_ip matches /24 subnet
  - tasks.py:160-173 - filters /24 subnet matches
  - tasks.py:223-226 - removes Transparent proxies
  - anonymity_checker.py - detects Elite/Anonymous/Transparent

- [x] Browser-level proxy enforcement (implemented)
  - browsers_main.py:147-152 - rejects if validated_proxy=None
  - firefox.py:17-19 - rejects if proxy=None
  - chromium.py:19-21 - rejects if proxy=None

---

## CRITICAL BUG: Proxy Scoring System Broken (P0) - FIXED

**Found by**: Instance 3 (Session 1, 2025-12-26)
**Status**: Complete (Solution F - Sessions 14-23)
**Unblocks**: Automatic threshold-based proxy refresh

### Root Cause Analysis

**Finding 1: Wrong Proxy Being Tracked**
- Location: `main.py:148-160`
- Problem: `main.py` uses mubeng as an auto-rotating proxy (`http://localhost:8089`). When recording success/failure, it passes this mubeng URL to `proxy_pool.record_result()` instead of the actual underlying proxy.

**Finding 2: Proxy Removal Doesn't Persist**
- Location: `proxies/proxy_scorer.py:306-344`
- Problem: When `remove_proxy()` is called, it removes from in-memory but does NOT update `live_proxies.json`.

### Chosen Solution: Solution F - Mubeng with --watch + X-Proxy-Offset

**Decision Date**: 2025-12-26 (Session 14)
**Key Discovery**: Mubeng supports `--watch` flag (live-reload) and `X-Proxy-Offset: N` header (select specific proxy)

### Implementation Phases - ALL COMPLETE

#### Phase 0: Pre-Implementation Verification
- [x] **0.1** Create test script `tests/debug/test_mubeng_features.py`
- [x] **0.2** Test `--watch` flag: Start mubeng, modify proxy file, verify reload
- [x] **0.3** Test `X-Proxy-Offset` header: Send requests with specific offsets
- [x] **0.4** Test behavior without `--rotate-on-error`

#### Phase 1: Mubeng Configuration
- [x] **1.1** Edit `proxies/mubeng_manager.py` - Added `-w` flag, removed `--rotate-on-error` and `--max-errors`
- [x] **1.2** Test: Mubeng starts correctly with new flags

#### Phase 2: Proxy Order Tracking
- [x] **2.1** Edit `proxies/proxies_main.py` - `get_and_filter_proxies()` now returns `Tuple[Path, List[str]]`
- [x] **2.2** Edit `proxies/proxies_main.py` - `setup_mubeng_rotator()` returns 4-tuple with ordered keys
- [x] **2.3** Edit `proxies/proxy_scorer.py` - Added `set_proxy_order()` and `get_proxy_index()` methods
- [x] **2.4** Test: Index mapping works correctly (verified with unit test)

#### Phase 3: Persistence on Removal
- [x] **3.1** Edit `proxies/proxy_scorer.py` - Added `_mubeng_proxy_file` attr + `set_mubeng_proxy_file()` method
- [x] **3.2** Edit `proxies/proxy_scorer.py` - Added `_save_proxy_file()` method
- [x] **3.3** Edit `proxies/proxy_scorer.py` - Updated `remove_proxy()` to persist + rebuild index
- [x] **3.4** Test: Removal persists to file (verified - indexes shift correctly)
- [x] **3.5** Test: Mubeng stays running after file modification (--watch reload verified)

#### Phase 4: X-Proxy-Offset Header in Requests
- [x] **4.1** Verify Scrapling supports `extra_headers`
- [x] **4.2** Edit `main.py` - Update `_scrape_listings()` function
- [x] **4.3** Edit `main.py` - Update `_collect_listing_urls()` function
- [x] **4.4** Test: Verify correct proxy is tracked (4 tests pass)

#### Phase 5: Retry Logic
- [x] **5.1** Edit `main.py` - Add retry loop to `_scrape_listings()` (MAX_PROXY_RETRIES = 3)
- [x] **5.2** Edit `main.py` - Add retry to `_collect_listing_urls()`
- [x] **5.3** Test: Verify retry logic (5 tests pass)

#### Phase 6: Integration Testing
- [x] **6.1** Create integration test: `tests/debug/test_solution_f_integration.py`
- [x] **6.2** Test scenario: Mixed proxy pool (6 tests, all pass)
- [x] **6.3** Test scenario: Persistence across sessions
- [x] **6.4** Test scenario: Index synchronization
- **Bug Fixed**: `threading.Lock()` -> `threading.RLock()` in proxy_scorer.py (deadlock fix)

#### Phase 7: Edge Cases & Hardening
- [x] **7.1** Add MIN_PROXIES check before scraping (`MIN_PROXIES = 5` constant)
- [x] **7.2** Add file locking for concurrent access (`fcntl.flock`)
- [x] **7.3** Add delay after file write (0.2s for mubeng reload)
- [x] **7.4** Add hook for proxy refresh (`reload_proxies()` rebuilds index map)

---

## CRITICAL BUG: Chunk Processing Timing (P1) - COMPLETE

**Spec**: [105_CHUNK_PROCESSING_TIMING_BUG.md](../../archive/specs/105_CHUNK_PROCESSING_TIMING_BUG.md) *(archived - all tasks complete)*

### Tasks Completed

- [x] Review `orchestrator.py` for hardcoded timeouts (wait_for_refresh_completion:445-461 only waits 30s)
- [x] Review `tasks.py` for dispatcher wait patterns (dispatcher returns immediately)
- [x] Implement Redis progress tracking
  - `proxies/tasks.py`: Redis keys for progress tracking
  - `orchestrator.py`: `get_refresh_progress()` method
- [x] Switch to event-based completion (CRITICAL)
  - Dispatcher returns chord_id: `proxies/tasks.py:124-127`
  - Orchestrator uses `AsyncResult(chord_id).get()`: `orchestrator.py:533-597`
  - Background thread shows progress during wait
- [x] Test full pipeline end-to-end with event-based completion
  - test_orchestrator_event_based.py: 35 chunks, 21min, chord_id verified
- [x] Fix chord.get() infinite block bug (Session 9)
  - Bug: `chord_result.get(timeout=None)` blocked forever if any chunk failed
  - Fix: Dynamic timeout calculation + fallback to Redis polling
  - `orchestrator.py:504-514` - fallback logic
  - `orchestrator.py:594-600` - dynamic timeout: `max((chunks/8)*400*1.5, 600)`
- [x] Verify chord timeout fix with full live test (Session 10)
- [x] Fix false positive fallback message (Session 11, commit 5b71300)
- [x] Fix proxy file overwrite bug (Session 11, commit 9d5d3ad)
- [x] Fix `wait_for_proxies` blind polling bug (Session 12)

---

## Debugging: Celery + Mubeng + PSC Integration (P1) - COMPLETE

**Spec**: [101_DEBUG_CELERY_MUBENG_PROXIES.md](../../docs/specs/101_DEBUG_CELERY_MUBENG_PROXIES.md)

### Phase 1: Isolated Component Tests (2025-12-25 - ALL PASSED)
- [x] Test 1.1: Redis connectivity - v7.0.15, standalone mode
- [x] Test 1.2: Celery worker start/stop - 5 tasks registered, ping OK
- [x] Test 1.3: Mubeng SERVER mode - loads 123 proxies, auto-rotates, routes requests
- [x] Test 1.4: Mubeng CHECKER mode - 16/20 alive, filters dead proxies correctly
- [x] Test 1.5: PSC binary - scraped 2,847 proxies, valid JSON output

### Phase 2: Integration Tests
- [x] Test 2.1: Celery + Redis integration - ALL PASSED
- [x] Test 2.2: Celery + Mubeng - PASSED (task executed 0.037s, warm shutdown, no orphans)
- [x] Test 2.2.5: Celery + PSC - PASSED (scraped 2,897 proxies in 180s)
- [x] Test 2.2.6: PSC -> Dispatcher -> Mubeng - PASSED (2897->48 proxies, 29 chunks)
- [x] Test 2.3: Full pipeline end-to-end - PASSED (5000 proxies -> 79 live, 16min)

### Phase 3: Stress Tests
- [x] Test 3.1: Run `bash tests/stress/run_all_stress_tests.sh` - PASSED

---

## Page Change Detection (P2) - Phases 1-3 COMPLETE

**Spec**: [111_PAGE_CHANGE_DETECTION.md](../../docs/specs/111_PAGE_CHANGE_DETECTION.md)

### Phase 1: Basic Hash Detection
- [x] Add DB columns via migration (content_hash, last_change_at, change_count, price_history, consecutive_unchanged)
- [x] Create `data/change_detector.py` (compute_hash, has_changed, track_price_change)
- [x] Integrate into `main.py` scraping loop (`_check_and_save_listing()`)
- [x] Test: 24 unit tests pass (`tests/test_change_detector.py`)

### Phase 2: Price Tracking
- [x] Implement `track_price_change()` with history (JSON array, 10 entries max)
- [x] Log price changes (logger.info for drops/increases)
- [x] Price history stored in `price_history` column

### Phase 3: Dashboard Integration
- [x] Show price history chart in Streamlit
- [x] Filter by "recently changed"

---

## Ollama Integration (P1) - Phases 1-5 COMPLETE

**Spec**: [107_OLLAMA_INTEGRATION.md](../../docs/specs/107_OLLAMA_INTEGRATION.md)

### Phase 1: Foundation + Health Check
- [x] Update manifest.json and FILE_STRUCTURE.md for `llm/` folder
- [x] Create `llm/` with 4 files (__init__.py, llm_main.py, prompts.py, schemas.py)
- [x] Create `config/ollama.yaml`
- [x] Implement OllamaClient in llm_main.py (check_health, kill_port, start_server, ensure_ready)
- [x] Test: Ollama start/stop/restart
- [x] Pull model: `ollama pull qwen2.5:1.5b` (already installed)

### Phase 2: API + Field Mapping
- [x] Implement `_call_ollama()` REST API
- [x] Implement `_parse_response()` JSON extraction
- [x] Add FIELD_MAPPING_PROMPT to prompts.py
- [x] Add MappedFields to schemas.py
- [x] Implement `map_fields()` public function
- [x] Test: Map 5 imot.bg pages - **100% extraction** (price, area, floor, construction)

### Phase 3: Description Extraction
- [x] Add EXTRACTION_PROMPT to prompts.py
- [x] Add ExtractedDescription to schemas.py
- [x] Implement `extract_description()` public function
- [x] Test: Extract from 5 descriptions - **78% extraction** (7/9 fields avg)

### Phase 3.5: Prompt Accuracy Improvements
**Spec**: [108_OLLAMA_PROMPT_IMPROVEMENTS.md](../../docs/specs/108_OLLAMA_PROMPT_IMPROVEMENTS.md)

#### Research (Complete)
- [x] Investigate why model returns Bulgarian despite English prompt constraints
- [x] Research Ollama's `format: json` behavior
- [x] Test prompt language impact (English prompts = 5/5, Bulgarian = 2/5)
- [x] Create test script: `tests/llm/test_ollama_prompts.py`

#### Implementation Tasks (Complete - Session 7)
- [x] Phase 1: Switch prompts to English with "RESPOND IN ENGLISH ONLY"
- [x] Phase 2: Add JSON schema enforcement
- [x] Phase 3: Configure OLLAMA_KEEP_ALIVE for batch processing
- [x] Run test suite: **100% accuracy** on enum fields (V4 pattern)
- [x] Keep `_translate_values()` as safety fallback

### Phase 3.6: Achieve 95%+ Extraction Accuracy (P1)
**Spec**: [110_DYNAMIC_BULGARIAN_DICTIONARY.md](../../docs/specs/110_DYNAMIC_BULGARIAN_DICTIONARY.md)
**Result**: 97.4% accuracy achieved (Session 9, 2025-12-26)

#### Research (Complete - 2025-12-26)
- [x] Analyze extraction failures - which fields fail most?
- [x] Test with larger model (qwen2.5:3b vs 1.5b) - 1.5b better
- [x] Identify root cause: Missing Bulgarian hints for low-accuracy fields
- [x] Design solution: Dynamic dictionary with regex pre-scan

#### Phase 1: Dynamic Dictionary (Complete)
- [x] Create `config/bulgarian_dictionary.yaml` (600+ lines, 400+ terms)
- [x] Create `llm/dictionary.py` (scanner + hint builder)
- [x] Update `llm/prompts.py` with base templates + `{hints}` placeholder
- [x] Update `llm/llm_main.py` to use dictionary via `scan_and_build_hints()`
- [x] Create `tests/llm/test_extraction_accuracy.py`
- [x] Run accuracy test - **97.4% achieved** (exceeds 95% target)

#### Phase 2: Few-Shot Examples - SKIPPED
- [x] Tested few-shot examples for boolean fields
- **Result**: Caused regressions (heating_type, orientation dropped)
- **Decision**: Skip - 97.4% already exceeds 95% target

#### Phase 3: Temperature = 0 - NO EFFECT
- [x] Change description_extraction temperature: 0.1 -> 0.0
- [x] Re-run accuracy test
- **Result**: No change (97.4% -> 97.4%)

### Phase 4: Scrapling Integration - COMPLETE (Session 17)
- [x] Add `use_llm` flag to ScraplingMixin (`websites/scrapling_base.py:216`)
- [x] Add LLM calls in extraction flow (`websites/imot_bg/imot_scraper.py:92-118`)
- [x] CSS primary, LLM fills gaps when confidence >= 0.7
- [x] Test: End-to-end extraction verified (orientation filled by LLM)

### Phase 5: Production Hardening
- [x] Add extraction cache (`llm/llm_main.py:340-382`, Redis-based, 7-day TTL)
- [x] Add confidence threshold to config (`config/ollama.yaml:11`)
- [x] Add metrics logging (`llm/llm_main.py:36-45, 413-441`)
- [x] Performance test (`tests/llm/test_performance.py` - 100% success, 0.95 confidence)

---

## Crawler Validation & Enhancement (P1) - Phase 0 COMPLETE

**Spec**: [106_CRAWLER_VALIDATION_PLAN.md](../../docs/specs/106_CRAWLER_VALIDATION_PLAN.md)

### Phase 0: Scrapling Integration (Complete)
- [x] Install Scrapling and verify setup (v0.2.99)
- [x] Create `websites/scrapling_base.py` adapter
- [x] Test with imot.bg (price: 170400 EUR, area: 71 sqm, floor: 4/6)
- [x] Migrate imot_scraper.py to Scrapling (2025-12-25, 17 tests pass)
- [x] Migrate bazar_scraper.py to Scrapling (2025-12-25)
- [x] Enable adaptive mode with baseline selectors (2025-12-25)
- [x] Test StealthyFetcher with mubeng proxy (2025-12-25)

### Phase 2: Description Extraction (Complete via LLM)
- [x] Build `DescriptionExtractor` class - Implemented via LLM instead of regex
- [x] Test extraction accuracy - 97.4% accuracy achieved via LLM
- [x] Optional: Add LLM fallback - LLM is now PRIMARY method

### Phase 3: Change Detection & History (Partial)
- [x] Build `ChangeDetector` class - Implemented as `data/change_detector.py`
- [x] Integrate into scraper flow - Done in `main.py:_check_and_save_listing()`
- [x] Add dashboard timeline view - Price history chart + "recently changed" filter

---

## Scraper Resilience & Error Handling (P1) - PHASES 1-4 COMPLETE

**Implementation File**: [112_RESILIENCE_IMPLEMENTATION.md](../specs/112_RESILIENCE_IMPLEMENTATION.md) (archived)
> 153 tests passing. Code is source of truth.

### Phase 1: Foundation (COMPLETE)
- [x] Create `resilience/` module structure
- [x] Implement `resilience/exceptions.py` (exception hierarchy)
- [x] Implement `resilience/error_classifier.py`
- [x] Implement `resilience/retry.py` (sync + async with backoff + jitter)
- [x] Add resilience settings to `config/settings.py`
- [x] Integrate retry decorator into `main.py`
- [x] Write unit tests for Phase 1 (45 tests, 100% pass)

### Phase 2: Domain Protection (COMPLETE)
- [x] Implement `resilience/circuit_breaker.py`
- [x] Implement `resilience/rate_limiter.py` (token bucket)
- [x] Integrate circuit breaker into main.py
- [x] Integrate rate limiter into main.py
- [x] Write unit tests for Phase 2 (42 tests, 100% pass)

### Phase 3: Session Recovery (COMPLETE)
- [x] Implement `resilience/checkpoint.py`
- [x] Add checkpoint save/restore to main.py
- [x] Add SIGTERM/SIGINT graceful shutdown handlers
- [x] Write unit tests for Phase 3 (18 tests, 100% pass)
- [x] **Run Phase Completion Checklist** (consistency + alignment)

### Phase 4: Detection (COMPLETE)
- [x] Implement `resilience/response_validator.py` (CAPTCHA/soft block detection)
- [x] Add 429/Retry-After header handling
- [x] Write unit tests for Phase 4 (48 tests, 100% pass)
- [x] **Run Phase Completion Checklist** (consistency + alignment)

---

## Historical Completed Work

### Scraper Development
- [x] Set up scraper project structure
- [x] Simplify architecture (EUR only, BG only, no filtering)
- [x] Create database schema for listings
- [x] Build scoring system (7 weighted criteria + deal breakers)
- [x] Build Streamlit dashboard
- [x] Implement imot.bg scraper (extraction + pagination)
- [x] Implement bazar.bg scraper (tested with live data)
- [x] Create orchestrator.py - Redis/Celery/proxy lifecycle
- [x] Create proxy_validator.py - pre-flight check
- [x] Create anonymity_checker.py
- [x] Create runtime proxy scorer
- [x] Create quality checker
- [x] Integrate quality check into Celery pipeline

### Research
- [x] Map Sofia districts and neighborhoods
- [x] Understand public transport (metro lines)
- [x] Identify "up and coming" areas
- [x] Learn typical price ranges per neighborhood
- [x] Track metro expansion plans
- [x] List top real estate agencies (6 in DB)

### Project Setup (2025-12-24)
- [x] Clean root directory, organize files
- [x] Create README.md and .gitignore
- [x] Create multi-instance coordination system
- [x] Create research -> specs -> code workflow
- [x] Create /lss and /ess commands

### Session 3 (2025-12-24)
- [x] Run stress tests - Test 5 PASSED (no orphan mubeng)
- [x] Verify proxy-level real IP protection
- [x] Implement browser-level proxy enforcement
- [x] Create debugging workflow for Celery/Mubeng/PSC
- [x] Organize docs into workflow structure (specs/, archive/docs/)

### Architecture Documentation (2025-12-24)
- [x] Document project architecture (docs/architecture/ARCHITECTURE.md)
  - Layered Architecture with Pipeline Processing pattern
  - 8 design patterns documented
  - Project structure with 769-line comprehensive guide

### File Structure Rules (2025-12-25)
- [x] Create file placement rules (docs/architecture/FILE_STRUCTURE.md)
- [x] Update CLAUDE.md with FILE PLACEMENT RULES section
- [x] Clean up misplaced files

### Automated File Placement Enforcement (2025-12-25)
- [x] Implement manifest.json with file rules
- [x] Create validation script
- [x] Create hook wrapper
- [x] Configure Claude Code hooks
- [x] Add max_depth (3) and block_root_files rules
- [x] Split ARCHITECTURE.md into focused documents
- [x] Initialize git repository (253 files, branch: main)

---

**Archived**: 2025-12-27
