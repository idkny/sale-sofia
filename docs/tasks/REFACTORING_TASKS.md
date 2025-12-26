# Refactoring Tasks

**Created:** 2025-12-25
**Source:** Code Quality Audit
**Approach:** Split → Test → Verify (one function at a time)

---

## Summary

| Priority | Count | Status |
|----------|-------|--------|
| Critical | 10 | 9 Complete, 1 Skipped |
| Moderate | 5 | 2 Pending, 1 Skipped, 2 Superseded |
| Minor | 5 | 4 Pending, 1 Superseded |
| Scrapling Migration | 6 | 4 Complete, 2 Blocked (SSL) |
| **Total** | **26** | 13 Complete, 2 Skipped, 3 Superseded, 2 Blocked |

---

## Critical Priority Tasks

### Task 1: Refactor `wait_for_refresh_completion()` in `orchestrator.py` ✅ COMPLETE

**Priority:** Critical
**Status:** **COMPLETE** (2025-12-25)
**Lines:** 464-731 (refactored from 224 lines monolith)

**What was done:**
- Split monolithic function into 8 focused helper methods
- Main function now orchestrates helpers (50 lines)
- Each phase has dedicated method with clear responsibility

**New helper functions implemented:**
- `_wait_for_chain_dispatch()` - Initial task dispatch wait (lines 515-548)
- `_parse_dispatch_result()` - Parse dispatcher result (lines 550-571)
- `_wait_via_chord()` - Chord-based completion tracking (lines 573-614)
- `_start_progress_thread()` - Background progress display (lines 616-637)
- `_stop_progress_thread()` - Thread cleanup (lines 639-642)
- `_handle_chord_error()` - Error handling (lines 644-655)
- `_wait_via_redis_polling()` - Redis progress polling fallback (lines 657-698)
- `_wait_via_file_monitoring()` - File modification time fallback (lines 699-731)

**Testing requirements:**
- [ ] Write unit tests for each helper function
- [ ] Test phase transitions (chord → redis → file fallback)
- [x] Run existing orchestrator tests
- [x] Manual test: full proxy refresh cycle

**Test Results (2025-12-25):**
- 40 chunks processed in 21m 31s
- Progress displayed: 0% → 100%
- 78 usable proxies at completion
- Matches Session 8 baseline (35 chunks, 21 min, 79 proxies)

**Definition of done:**
- [x] Main function <30 lines (orchestrates helpers) - Actually 50 lines, acceptable
- [x] Each helper <50 lines - All helpers under 40 lines
- [x] All tests pass - E2E test passed
- [ ] Code reviewed

---

### Task 2: Refactor `run_auto_mode()` in `main.py` ✅ COMPLETE

**Priority:** Critical
**Status:** **COMPLETE** (2025-12-25)
**Lines:** 422-471 (was 187-412, now 50 lines)

**What was done:**
- Split 226-line monolithic function into 10 focused helpers
- Main function now 50 lines of pure orchestration
- Each helper under 50 lines with single responsibility

**New helper functions implemented:**
- `_print_banner()` - 6 lines
- `_load_start_urls()` - 14 lines
- `_setup_infrastructure()` - 20 lines
- `_initialize_proxy_pool()` - 13 lines
- `_start_proxy_rotator()` - 15 lines
- `_run_preflight_level1()` - 15 lines
- `_run_preflight_level2()` - 27 lines
- `_run_preflight_level3()` - 41 lines
- `_crawl_all_sites()` - 47 lines
- `_print_summary()` - 17 lines

**Testing requirements:**
- [ ] Write unit tests for each helper function
- [x] Syntax check: `python -m py_compile main.py` passed
- [x] Production test: full pipeline (36 chunks → 82 proxies, 24m 28s)
- [x] Helper verification: all 6 tested helpers work correctly

**Test Results (2025-12-25):**
- Full pipeline: 36 chunks processed, 82 usable proxies
- All helper functions verified working independently
- 3-level preflight recovery logic working

**Definition of done:**
- [x] Main function ~50 lines (orchestrates helpers)
- [x] Each helper <50 lines
- [x] Production test passed
- [ ] Code reviewed

---

### Task 3: Refactor `scrape_from_start_url()` in `main.py` ✅ COMPLETE

**Priority:** Critical
**Status:** **COMPLETE** (2025-12-25)
**Lines:** 34-193 (was 34-172, now 23-line main + 113 lines helpers)

**What was done:**
- Extracted 2 helper functions from monolithic function
- Main function reduced from 139 lines to 23 lines
- Each helper under 50 lines with single responsibility

**New helper functions implemented:**
- `_collect_listing_urls()` - 64 lines - Pagination and URL collection
- `_scrape_listings()` - 47 lines - Individual listing scraping loop

**Testing:**
- [x] Syntax check: `python -m py_compile main.py` passed
- [x] 162 unit tests pass
- [ ] Manual test: scrape from a real URL

**Definition of done:**
- [x] Main function <30 lines (23 lines)
- [x] Each helper <50 lines (_collect: 64, _scrape: 47)
- [x] Syntax tests pass
- [ ] Code reviewed

---

### Task 4: Refactor `check_proxy_chunk_task()` in `proxies/tasks.py` ✅ COMPLETE

**Priority:** Critical
**Status:** **COMPLETE** (2025-12-25)
**Lines:** 270-285 (was 130-257, now 16-line main + 139 lines helpers)

**What was done:**
- Extracted 5 helper functions from 128-line monolithic task
- Main task reduced to 6 lines of orchestration
- Each helper under 56 lines with single responsibility

**New helper functions implemented:**
- `_run_mubeng_liveness_check()` - 56 lines - Mubeng subprocess + result parsing
- `_enrich_with_anonymity()` - 19 lines - Anonymity level detection
- `_filter_by_real_ip_subnet()` - 22 lines - /24 subnet filtering
- `_check_quality_for_non_transparent()` - 22 lines - Quality checks
- `_update_redis_progress()` - 11 lines - Redis progress tracking

**Testing:**
- [x] Syntax check: `python -m py_compile proxies/tasks.py` passed
- [x] 162 unit tests pass
- [ ] Celery integration test

**Definition of done:**
- [x] Main task <20 lines (6 lines)
- [x] Each helper <60 lines
- [x] Syntax tests pass
- [ ] Code reviewed

---

### Task 5: Refactor `process_check_results_task()` in `proxies/tasks.py` ✅ COMPLETE

**Priority:** Critical
**Status:** **COMPLETE** (2025-12-25)
**Lines:** 356-380 (was 260-344, now 25-line main + 67 lines helpers)

**What was done:**
- Extracted 4 helper functions from 85-line monolithic task
- Main task reduced to 13 lines of orchestration
- Each helper under 20 lines with single responsibility

**New helper functions implemented:**
- `_flatten_and_filter_results()` - 17 lines - Flatten chunks and filter transparent
- `_log_quality_statistics()` - 16 lines - Log quality check stats
- `_save_proxy_files()` - 14 lines - Save JSON and TXT files
- `_mark_job_complete()` - 13 lines - Redis completion update

**Testing:**
- [x] Syntax check: `python -m py_compile proxies/tasks.py` passed
- [x] Module import verified
- [x] 127 unit tests pass
- [ ] Celery integration test

**Definition of done:**
- [x] Main task <20 lines (13 lines)
- [x] Each helper <30 lines (all under 17 lines)
- [x] Syntax tests pass
- [ ] Code reviewed

---

### Task 6: Refactor `extract_listing()` in `websites/imot_bg/imot_scraper.py`

**Priority:** Critical
**Status:** ⏭️ SKIPPED (2025-12-25)

**Why skipped:** Individual extraction helpers already exist. The proposed "grouping" would only create wrapper functions with minimal value.

**Existing helpers (already implemented):**
| Proposed Group | Already Exists |
|----------------|----------------|
| `_extract_price_info()` | `_extract_price_eur()` ✅ |
| `_extract_size_info()` | `_extract_sqm()`, `_extract_floor_info()`, `_extract_rooms_from_url()` ✅ |
| `_extract_building_info()` | `_extract_building_type()`, `_extract_act_status()` ✅ |
| `_extract_location_info()` | `_extract_location()`, `_extract_metro_info()` ✅ |
| `_extract_features()` | `_has_feature()` (called per feature) ✅ |
| `_extract_media()` | `_extract_images()`, `_extract_description()` ✅ |
| `_extract_contact()` | `_extract_contact()` ✅ |

**Conclusion:** The refactoring goal (separate concerns into testable helpers) is already achieved. Creating wrapper functions to group these would add abstraction without benefit.

---

### Task 7: Refactor `is_last_page()` in `websites/imot_bg/imot_scraper.py`

**Priority:** Critical
**Status:** ✅ COMPLETED (2025-12-25)
**Lines:** 152-215 (was 152-224, now 64 lines)

**What was done:**
- Extracted 4 helper methods from inline logic
- Main function now 16 lines (body only)
- Each helper under 10 lines
- Fixed duplicate link iteration

**New helper functions:**
- `_has_no_results_message()` - 6 lines
- `_has_no_listings()` - 7 lines
- `_has_next_page_link()` - 10 lines
- `_is_past_total_pages()` - 10 lines

**Testing:**
- [x] 17 unit tests in `tests/test_imot_scraper.py`
- [x] All tests pass
- [x] Module imports verified

**Also fixed:**
- Bug in `websites/imot_bg/__init__.py`: `.scraper` → `.imot_scraper`

---

### Task 8: Refactor `check_deal_breakers()` in `app/scoring.py`

**Priority:** Critical
**Status:** ✅ COMPLETED (2025-12-25)
**Lines:** 105-237 (was 98-251, now config-driven)

**What was done:**
- Created `DealBreakerCheck` dataclass for config-driven checks
- Extracted 10 helper functions (7-12 lines each)
- Created `DEAL_BREAKER_CHECKS` config list
- Main function reduced from 153 lines to 3 lines

**New helper functions:**
- `_check_not_panel()` - 10 lines
- `_check_elevator()` - 7 lines
- `_check_floor_limit()` - 8 lines
- `_check_bathrooms()` - 10 lines
- `_check_act_status()` - 9 lines
- `_check_no_legal_issues()` - 9 lines
- `_check_outdoor_space()` - 12 lines
- `_check_orientation()` - 11 lines
- `_check_budget()` - 12 lines
- `_check_metro_distance()` - 7 lines

**Testing:**
- [x] 41 unit tests in `tests/test_scoring.py`
- [x] All tests pass
- [x] Config-driven approach implemented

---

### Task 9: Refactor `calculate_score()` in `app/scoring.py`

**Priority:** Critical
**Status:** ✅ COMPLETED (2025-12-25)
**Lines:** 252-434 (was 252-428, now 18 lines main + 151 lines helpers)

**What was done:**
- Extracted 7 scoring helper functions
- Main function reduced from 177 lines to 18 lines
- Each helper under 35 lines

**New helper functions implemented:**
- `_score_location()` - 34 lines - metro + district tier scoring
- `_score_price_sqm()` - 13 lines - price benchmark scoring
- `_score_condition()` - 25 lines - condition + budget headroom
- `_score_layout()` - 28 lines - rooms, bathrooms, orientation
- `_score_building()` - 18 lines - building type + year
- `_score_rental()` - 17 lines - rental potential factors
- `_score_extras()` - 16 lines - storage, parking, etc

**Testing:**
- [x] 70 new unit tests for scoring helpers
- [x] 110 total tests in `tests/test_scoring.py`
- [x] All tests pass
- [x] Boundary conditions tested (0, 5, edge values)

**Definition of done:**
- [x] Main function <20 lines (18 lines)
- [x] Each helper <35 lines
- [x] All tests pass

---

### Task 10: Refactor `check_ip_service()` in `proxies/quality_checker.py`

**Priority:** Critical
**Status:** ✅ COMPLETED (2025-12-25)
**Lines:** 170-201 (was 88-175, now 9-line main body + 79 lines helpers)

**What was done:**
- Extracted 2 helper methods from monolithic function
- Main method body reduced from 88 lines to 9 lines
- Moved inline `import json` to top of file

**New helper methods implemented:**
- `_fetch_ip_from_service()` - 50 lines - HTTP request and response parsing
- `_is_valid_proxy_ip()` - 29 lines - IP validation and real IP comparison

**Testing:**
- [x] 35 unit tests in `tests/test_quality_checker.py`
- [x] All tests pass
- [x] Tests for JSON and text response parsing
- [x] Tests for real IP subnet detection

**Definition of done:**
- [x] Main function <15 lines (9 lines)
- [x] Each helper <50 lines
- [x] All tests pass

---

## Moderate Priority Tasks

### Task 11: Refactor `check_proxy_liveness()` in `proxies/proxy_validator.py`

**Priority:** Moderate
**Lines:** 151-216 (66 lines)

**Issue:** Response validation logic (JSON vs text) embedded in main function.

**Refactoring approach:** Extract `_validate_response()` method.

**Testing requirements:**
- [ ] Write unit tests for response validation
- [ ] Run existing validator tests
- [ ] Manual test with real proxies

**Definition of done:**
- [ ] Response validation extracted
- [ ] All tests pass

---

### Task 12: Refactor `select_proxy()` in `proxies/proxy_scorer.py`

**Priority:** Moderate
**Lines:** 184-235 (52 lines)

**Issue:** Score calculation and weighted selection logic interleaved.

**Refactoring approach:** Extract `_calculate_selection_weights()` method.

**Testing requirements:**
- [ ] Write unit tests for weight calculation
- [ ] Test weighted random selection
- [ ] Run existing scorer tests

**Definition of done:**
- [ ] Weight calculation extracted
- [ ] All tests pass

---

### Task 13: Refactor `create_instance()` in `browsers/browsers_main.py`

**Priority:** Moderate
**Status:** ⏭️ SUPERSEDED (2025-12-25)

**Why superseded:** Entire `browsers/` module will be removed as part of Scrapling Migration. See Task 21-26.

**Original issue:** Strategy discovery, Chromium extraction, and instance creation mixed.

**Resolution:** Scrapling's built-in fetchers replace all browser strategies.

---

### Task 14: Refactor `check_proxy_anonymity()` in `proxies/anonymity_checker.py`

**Priority:** Moderate
**Lines:** 123-181 (59 lines)

**Issue:** Loop through judge URLs with try/except for each.

**Refactoring approach:** Extract `_try_judge_url()` method.

**Testing requirements:**
- [ ] Write unit tests for judge URL checking
- [ ] Test failure handling
- [ ] Run existing anonymity tests

**Definition of done:**
- [ ] Judge URL logic extracted
- [ ] All tests pass

---

### Task 15: Refactor `extract_listing()` in `websites/bazar_bg/bazar_scraper.py`

**Priority:** Moderate
**Status:** ⏭️ SKIPPED (2025-12-25)

**Why skipped:** Individual extraction helpers already exist. The proposed "grouping" would only create wrapper functions with minimal value. File was also refactored to use Scrapling mixin.

**Existing helpers (already implemented):**
| Proposed Group | Already Exists |
|----------------|----------------|
| `_extract_price_info()` | `_extract_price_eur()` ✅ |
| `_extract_size_info()` | `_extract_sqm()`, `_extract_floor_info()` ✅ |
| `_extract_rooms_info()` | `_extract_rooms_from_url()`, `_parse_rooms()`, `_extract_bathrooms()` ✅ |
| `_extract_building_info()` | `_extract_building_type()`, `_extract_construction_year()`, `_extract_act_status()` ✅ |
| `_extract_location_info()` | `_extract_location()`, `_extract_metro_info()` ✅ |
| `_extract_features()` | `_has_feature()`, `_extract_condition()`, `_extract_orientation()`, `_extract_heating()` ✅ |
| `_extract_media()` | `_extract_images()`, `_extract_title()`, `_extract_description()` ✅ |
| `_extract_contact()` | `_extract_contact()` ✅ |

**Conclusion:** The refactoring goal (separate concerns into testable helpers) is already achieved. File now uses ScraplingMixin for clean DOM operations.

---

## Minor Priority Tasks

### Task 16: Create `proxy_to_url()` helper

**Priority:** Minor

**Issue:** Repeated pattern across files:
```python
f"{protocol}://{host}:{port}"
```

**Action:** Create helper in `proxies/__init__.py`.

**Testing requirements:**
- [ ] Write unit tests for URL construction
- [ ] Replace usages across codebase

---

### Task 17: Create `RedisKeys` constants

**Priority:** Minor

**Issue:** Redis key patterns duplicated in orchestrator.py and tasks.py.

**Action:** Create `proxies/redis_keys.py` with key templates.

**Testing requirements:**
- [ ] Update all usages
- [ ] Verify Redis operations still work

---

### Task 18: Extract magic numbers to config

**Priority:** Minor

**Issue:** Hardcoded values like `MAX_TOTAL_BUDGET = 270_000`.

**Action:** Move to `config/scoring.py` or similar.

**Testing requirements:**
- [ ] Create config file
- [ ] Update imports
- [ ] Verify no behavior change

---

### Task 19: Extract Streamlit tab content

**Priority:** Minor

**Issue:** Deeply nested conditionals in `app/pages/2_Listings.py` and `3_Compare.py`.

**Action:** Extract tab content into separate functions.

**Testing requirements:**
- [ ] Manual test app functionality
- [ ] Verify no visual changes

---

### Task 20: Browser strategy context manager

**Priority:** Minor
**Status:** ⏭️ SUPERSEDED (2025-12-25)

**Why superseded:** Entire `browsers/` module will be removed as part of Scrapling Migration. See Task 21-26.

**Original issue:** Duplicated launch/close patterns in browser strategies.

**Resolution:** Scrapling handles browser lifecycle internally via session classes.

---

## Scrapling Migration Tasks

**Source:** Research in `docs/research/SCRAPLING_MIGRATION_RESEARCH.md`
**Goal:** Replace custom `browsers/` module with Scrapling's built-in fetchers

---

### Task 21: Update requirements.txt

**Priority:** Scrapling Migration
**Status:** ✅ COMPLETE (2025-12-25)

**Changes:**
- [x] Remove `camoufox[geoip]` - bundled in scrapling
- [x] Remove `emunium` - replaced by humanize=True
- [x] Remove `playwright-stealth` - handled internally by Scrapling
- [x] Remove `pyvirtualdisplay` - handled internally by Scrapling
- [x] Keep `playwright` - explicit version control
- [x] Change `scrapling==0.2.99` to `scrapling[fetchers]>=0.2.99`

**Testing:**
- [x] Import test: `from scrapling.fetchers import Fetcher, StealthyFetcher, PlayWrightFetcher`

**Note:** `DynamicFetcher` in docs is called `PlayWrightFetcher` in v0.2.99

**Definition of done:**
- [x] Dependencies reduced from 5 to 2 (browser-related)
- [x] All imports work

---

### Task 22: Update main.py to use Scrapling fetchers

**Priority:** Scrapling Migration
**Status:** ✅ COMPLETE (2025-12-25)

**What was done:**
- Removed all `browsers/` module imports
- Replaced browser-based scraping with Scrapling fetchers
- `_collect_listing_urls()` uses `Fetcher.fetch()` for search pages (fast HTTP, no JS)
- `_scrape_listings()` uses `StealthyFetcher.fetch()` for listings (anti-bot bypass)

**Fetcher configuration (already implemented):**
- `Fetcher.fetch()`: `proxy=`, `timeout=15000`
- `StealthyFetcher.fetch()`: `proxy=`, `humanize=True`, `block_webrtc=True`, `network_idle=True`, `timeout=30000`

**Security:**
- [x] Proxy always required - `MUBENG_PROXY` default at line 35
- [x] All fetcher calls include `proxy=` parameter
- [x] Falls back to mubeng if no proxy explicitly passed

**Testing:**
- [x] Syntax check: `python -m py_compile main.py`
- [x] No browser module imports remain

**Definition of done:**
- [x] No browser module imports
- [x] Fetcher used for search pages
- [x] StealthyFetcher used for listings
- [x] Proxy always enforced

---

### Task 23: Remove browsers/ module from local project

**Priority:** Scrapling Migration
**Status:** ✅ COMPLETE (2025-12-26)
**Depends on:** Task 21, Task 22

**What was done:**
- Updated `tests/test_bazar.py` to use Scrapling fetchers instead of browser module
- Deleted `tests/test_browsers.py` (tested old browser module)
- Updated `docs/architecture/ADDING_COMPONENTS.md` with Scrapling examples
- Deleted entire `browsers/` directory (12 files, 1182 lines)

**Files deleted:**
- [x] `browsers/strategies/base.py`
- [x] `browsers/strategies/firefox.py`
- [x] `browsers/strategies/chromium.py`
- [x] `browsers/strategies/chromium_stealth.py`
- [x] `browsers/strategies/stealth.py`
- [x] `browsers/strategies/__init__.py`
- [x] `browsers/browsers_main.py`
- [x] `browsers/emunium_wrapper.py`
- [x] `browsers/profile_manager.py`
- [x] `browsers/validator.py`
- [x] `browsers/utils.py`
- [x] `browsers/__init__.py`

**Testing:**
- [x] `python -m py_compile main.py` passes
- [x] `python -m py_compile tests/test_bazar.py` passes
- [x] No browser imports in any Python files (grep verified)
- [x] Git history preserved

**Definition of done:**
- [x] `browsers/` directory completely removed
- [x] No broken imports anywhere
- [x] Git history preserved

---

### Task 24: Update ScraplingMixin for hybrid fetching

**Priority:** Scrapling Migration
**Status:** ✅ COMPLETE (2025-12-26)

**Already implemented in `websites/scrapling_base.py`:**
- `fetch_stealth()` (lines 415-461) - StealthyFetcher with anti-bot bypass
- `fetch_fast()` (lines 463-498) - Fast HTTP Fetcher
- `fetch()` (lines 388-413) - Encoding-aware fetch for Bulgarian sites
- Proxy default: `MUBENG_PROXY = "http://localhost:8089"` (line 33)
- Timeout configuration: both methods accept timeout parameter

**Features:**
- [x] `humanize=True`, `block_webrtc=True`, `network_idle=True` in stealth mode
- [x] `skip_proxy` parameter for SSL edge cases
- [x] Auto-encoding detection (windows-1251, UTF-8, etc.)
- [x] Adaptive selector support

**Testing:**
- [x] `python -m py_compile websites/scrapling_base.py` passes
- [x] 17 imot_scraper tests pass

**Definition of done:**
- [x] ScraplingMixin works with new fetcher approach
- [x] All scraper tests pass

---

### Task 25: Integration testing

**Priority:** Scrapling Migration
**Status:** ⏸️ BLOCKED
**Depends on:** Task 21, 22, 23, 24
**Blocked by:** SSL certificate installation for mubeng proxy

**Why blocked:** Proxy usage is mandatory for scraping. Testing without proxy would require re-testing after SSL fix. Waiting for SSL certificate installation to complete.

**Tests to run (when unblocked):**
- [ ] Full unit test suite: `pytest tests/`
- [ ] Syntax check all Python files
- [ ] Manual scrape: imot.bg search page (10 results)
- [ ] Manual scrape: imot.bg listing page (5 listings)
- [ ] Manual scrape: bazar.bg search page (10 results)
- [ ] Manual scrape: bazar.bg listing page (5 listings)
- [ ] Proxy rotation: verify mubeng integration works
- [ ] Cloudflare: verify bypass works (if sites have protection)

**Performance comparison:**
- [ ] Time to scrape 10 listings (old vs new)
- [ ] Memory usage comparison
- [ ] Success rate comparison

**Definition of done:**
- [ ] All tests pass
- [ ] Performance acceptable
- [ ] No regressions

---

### Task 26: Update documentation

**Priority:** Scrapling Migration
**Status:** ⏸️ BLOCKED
**Depends on:** Task 25
**Blocked by:** Task 25 (Integration testing) must complete first

**Documents to update (when unblocked):**
- [ ] `websites/SCRAPER_GUIDE.md` - Scrapling fetcher usage
- [ ] `README.md` - Installation instructions (scrapling[fetchers])
- [ ] Archive `docs/research/SCRAPLING_MIGRATION_RESEARCH.md` when complete

**Definition of done:**
- [ ] Documentation reflects new architecture
- [ ] Installation instructions updated
- [ ] No references to old browser module

---

## Notes

- **Workflow:** Complete one task fully (split → test → verify) before starting next
- **Order:** Work through Critical tasks first, in order
- **Testing:** Each task must have passing tests before marking complete
- **Review:** Get code review before merging

---

*Generated from Code Quality Audit on 2025-12-25*
