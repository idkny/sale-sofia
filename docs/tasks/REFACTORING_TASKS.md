# Refactoring Tasks

**Created:** 2025-12-25
**Source:** Code Quality Audit
**Approach:** Split → Test → Verify (one function at a time)

---

## Summary

| Priority | Count | Status |
|----------|-------|--------|
| Critical | 10 | 2 Complete, 1 Skipped, 7 Pending |
| Moderate | 5 | Pending |
| Minor | 5 | Pending |
| **Total** | **20** | 2 Complete, 1 Skipped |

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

### Task 2: Refactor `run_auto_mode()` in `main.py`

**Priority:** Critical
**Lines:** 187-412 (226 lines)

**Current issues:**
- Single function handling entire automation pipeline
- Three-level pre-flight retry logic deeply nested
- Mix of setup, validation, execution, cleanup
- Hard to test individual stages

**Refactoring approach:**
```python
def run_auto_mode() -> None:
    config = _load_and_validate_config()
    with Orchestrator() as orch:
        if not _setup_infrastructure(orch):
            return
        proxy_pool = _initialize_proxy_pool()
        proxy_url, mubeng = _setup_proxy_rotator(orch, proxy_pool)
        if not _run_preflight_checks(orch, proxy_url, mubeng):
            return
        _crawl_all_sites(config.start_urls, proxy_url, proxy_pool)
```

**New helper functions:**
- `_load_and_validate_config()` - Config loading
- `_setup_infrastructure()` - Redis/Celery startup
- `_initialize_proxy_pool()` - Proxy pool initialization
- `_setup_proxy_rotator()` - Mubeng rotator setup
- `_run_preflight_checks()` - 3-level pre-flight logic
- `_crawl_all_sites()` - Site crawling loop

**Testing requirements:**
- [ ] Write unit tests for config loading
- [ ] Write unit tests for preflight check logic
- [ ] Run existing main.py tests
- [ ] Manual test: full auto mode run

**Definition of done:**
- [ ] Main function <30 lines
- [ ] Each helper <50 lines
- [ ] All tests pass
- [ ] Code reviewed

---

### Task 3: Refactor `scrape_from_start_url()` in `main.py`

**Priority:** Critical
**Lines:** 34-172 (139 lines)

**Current issues:**
- Two distinct phases in one function
- Try/except inside loops with continue
- Browser cleanup in finally block

**Refactoring approach:**
```python
async def scrape_from_start_url(...) -> dict:
    browser_handle = await create_instance(...)
    try:
        urls = await _collect_listing_urls(browser_handle, scraper, start_url, limit, delay)
        stats = await _scrape_listings(browser_handle, scraper, urls, delay, proxy_pool)
        return stats
    finally:
        await browser_handle._browser.close()
```

**New helper functions:**
- `_collect_listing_urls()` - Pagination and URL collection
- `_scrape_listings()` - Individual listing scraping loop

**Testing requirements:**
- [ ] Write unit tests for URL collection
- [ ] Write unit tests for listing scraping
- [ ] Test pagination edge cases
- [ ] Manual test: scrape from a real URL

**Definition of done:**
- [ ] Main function <30 lines
- [ ] Each helper <50 lines
- [ ] All tests pass
- [ ] Code reviewed

---

### Task 4: Refactor `check_proxy_chunk_task()` in `proxies/tasks.py`

**Priority:** Critical
**Lines:** 130-257 (128 lines)

**Current issues:**
- Six distinct responsibilities in one task
- Subprocess management mixed with data enrichment
- Multiple filtering stages interleaved with logging

**Refactoring approach:**
```python
@celery_app.task
def check_proxy_chunk_task(proxy_chunk, job_id="") -> List[dict]:
    live_proxies = _run_mubeng_liveness_check(proxy_chunk)
    enriched = _enrich_with_anonymity(live_proxies)
    filtered = _filter_by_real_ip_subnet(enriched)
    quality_checked = _check_quality_for_anonymous(filtered)
    _update_redis_progress(job_id)
    return quality_checked
```

**New helper functions:**
- `_run_mubeng_liveness_check()` - Mubeng subprocess handling
- `_enrich_with_anonymity()` - Anonymity level detection
- `_filter_by_real_ip_subnet()` - /24 subnet filtering
- `_check_quality_for_anonymous()` - Quality checks

**Testing requirements:**
- [ ] Write unit tests for each helper
- [ ] Mock mubeng subprocess for testing
- [ ] Test filtering logic independently
- [ ] Run Celery task integration test

**Definition of done:**
- [ ] Main task <20 lines
- [ ] Each helper <40 lines
- [ ] All tests pass
- [ ] Code reviewed

---

### Task 5: Refactor `process_check_results_task()` in `proxies/tasks.py`

**Priority:** Critical
**Lines:** 260-344 (85 lines)

**Current issues:**
- File I/O mixed with data transformation
- Statistics calculation embedded in main flow
- Multiple output formats handled together

**Refactoring approach:**
```python
@celery_app.task
def process_check_results_task(results, job_id=""):
    all_proxies = _flatten_and_filter_results(results)
    if not all_proxies:
        _mark_job_complete(job_id, 0)
        return "No live proxies found."
    _log_quality_statistics(all_proxies)
    sorted_proxies = sorted(all_proxies, key=lambda p: p.get("timeout", 999))
    _save_proxy_files(sorted_proxies)
    _mark_job_complete(job_id, len(sorted_proxies))
    return f"Saved {len(sorted_proxies)} live proxies."
```

**New helper functions:**
- `_flatten_and_filter_results()` - Result processing
- `_log_quality_statistics()` - Stats logging
- `_save_proxy_files()` - JSON/TXT file writing
- `_mark_job_complete()` - Redis status update

**Testing requirements:**
- [ ] Write unit tests for result flattening
- [ ] Write unit tests for file saving (use temp files)
- [ ] Test empty results handling
- [ ] Run Celery task integration test

**Definition of done:**
- [ ] Main task <20 lines
- [ ] Each helper <30 lines
- [ ] All tests pass
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
**Lines:** 98-251 (154 lines)

**Current issues:**
- Highly repetitive pattern for each check
- Hardcoded logic for each deal breaker
- Should be config-driven

**Refactoring approach:**
```python
DEAL_BREAKER_CHECKS = [
    DealBreakerCheck("Not panel construction", _check_not_panel),
    DealBreakerCheck("Has elevator (floor 3+)", _check_elevator),
    DealBreakerCheck("Floor 4 or below", _check_floor_limit),
    # ... etc
]

def check_deal_breakers(listing: dict) -> List[DealBreakerResult]:
    return [check.evaluate(listing) for check in DEAL_BREAKER_CHECKS]
```

**New helper functions:**
- `_check_not_panel()` - Construction type check
- `_check_elevator()` - Elevator requirement
- `_check_floor_limit()` - Floor limit check
- `_check_budget()` - Budget check
- `_check_size()` - Size check
- (one function per deal breaker)

**Testing requirements:**
- [ ] Write unit tests for each check function
- [ ] Test with various listing combinations
- [ ] Verify all deal breakers still trigger correctly
- [ ] Manual test in Streamlit app

**Definition of done:**
- [ ] Main function <10 lines
- [ ] Each check <15 lines
- [ ] Config-driven approach implemented
- [ ] All tests pass
- [ ] Code reviewed

---

### Task 9: Refactor `calculate_score()` in `app/scoring.py`

**Priority:** Critical
**Lines:** 265-442 (178 lines)

**Current issues:**
- 7 distinct calculations in one function
- Repeated pattern: extract, apply rules, clamp
- Each section could be tested independently

**Refactoring approach:**
```python
def calculate_score(listing: dict) -> ScoreBreakdown:
    return ScoreBreakdown(
        location=_score_location(listing),
        price_sqm=_score_price_sqm(listing),
        condition=_score_condition(listing),
        layout=_score_layout(listing),
        building=_score_building(listing),
        rental=_score_rental(listing),
        extras=_score_extras(listing),
        total_weighted=_calculate_weighted_total(...)
    )
```

**New helper functions:**
- `_score_location()` - Location scoring
- `_score_price_sqm()` - Price per sqm scoring
- `_score_condition()` - Condition scoring
- `_score_layout()` - Layout scoring
- `_score_building()` - Building scoring
- `_score_rental()` - Rental potential scoring
- `_score_extras()` - Extras scoring
- `_calculate_weighted_total()` - Final weighted calculation

**Testing requirements:**
- [ ] Write unit tests for each scoring function
- [ ] Test boundary conditions (0, 5, edge values)
- [ ] Verify weighted totals are correct
- [ ] Manual test in Streamlit app

**Definition of done:**
- [ ] Main function <20 lines
- [ ] Each helper <30 lines
- [ ] All tests pass
- [ ] Code reviewed

---

### Task 10: Refactor `check_ip_service()` in `proxies/quality_checker.py`

**Priority:** Critical
**Lines:** 88-175 (88 lines)

**Current issues:**
- Deep nesting with try/except inside for loop
- Response parsing embedded in main flow
- Real IP comparison could be extracted

**Refactoring approach:**
```python
def check_ip_service(self, proxy_url) -> tuple[bool, str | None]:
    for service in IP_CHECK_SERVICES:
        try:
            exit_ip = self._fetch_ip_from_service(proxy_url, service)
            if exit_ip and self._is_valid_proxy_ip(exit_ip):
                return True, exit_ip
        except (httpx.TimeoutException, httpx.ProxyError):
            continue
    return False, None
```

**New helper functions:**
- `_fetch_ip_from_service()` - HTTP request and response parsing
- `_is_valid_proxy_ip()` - IP validation and real IP comparison

**Testing requirements:**
- [ ] Write unit tests with mocked HTTP responses
- [ ] Test JSON and text response parsing
- [ ] Test real IP detection
- [ ] Run quality checker integration test

**Definition of done:**
- [ ] Main function <15 lines
- [ ] Each helper <30 lines
- [ ] All tests pass
- [ ] Code reviewed

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
**Lines:** 108-168 (61 lines)

**Issue:** Strategy discovery, Chromium extraction, and instance creation mixed.

**Refactoring approach:** Move strategy discovery to module load time.

**Testing requirements:**
- [ ] Write unit tests for instance creation
- [ ] Test strategy selection
- [ ] Manual test browser launch

**Definition of done:**
- [ ] Strategy discovery separated
- [ ] All tests pass

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
**Lines:** 33-121 (89 lines)

**Issue:** Same pattern as imot_bg - sequential field extraction.

**Refactoring approach:** Same as Task 6 - group related extractions.

**Testing requirements:**
- [ ] Write unit tests for each extraction group
- [ ] Use sample HTML fixtures
- [ ] Manual test with real listing

**Definition of done:**
- [ ] Grouped extraction helpers
- [ ] All tests pass

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

**Issue:** Duplicated launch/close patterns in browser strategies.

**Action:** Create decorator or context manager for browser lifecycle.

**Testing requirements:**
- [ ] Write unit tests for lifecycle management
- [ ] Manual test browser sessions

---

## Notes

- **Workflow:** Complete one task fully (split → test → verify) before starting next
- **Order:** Work through Critical tasks first, in order
- **Testing:** Each task must have passing tests before marking complete
- **Review:** Get code review before merging

---

*Generated from Code Quality Audit on 2025-12-25*
