# Code Quality Audit Report

**Date:** 2025-12-25
**Scope:** Python codebase analysis for Sofia Apartment Search project
**Focus:** Function length, complexity, and maintainability

---

## Executive Summary

The codebase has several significant maintainability concerns, primarily around **long functions** that handle multiple responsibilities. The most critical issues are concentrated in:

1. **orchestrator.py** - Process management with monolithic wait/refresh logic
2. **main.py** - Automation pipeline with deeply nested pre-flight checks
3. **proxies/tasks.py** - Celery tasks doing too many things
4. **app/scoring.py** - Large scoring/deal-breaker functions with repeated patterns
5. **websites/*_scraper.py** - Extraction methods with many sequential operations

**Overall Code Health:** Moderate concern - The code is functional but would benefit from refactoring for better testability and debugging. Approximately 12 functions exceed 50 lines, and several exceed 100 lines.

---

## Critical Issues (Functions >50 lines or major complexity)

### 1. `orchestrator.py` - `wait_for_refresh_completion()`

| Attribute | Value |
|-----------|-------|
| **File** | `orchestrator.py` |
| **Lines** | 451-674 (224 lines) |
| **Function** | `wait_for_refresh_completion()` |

**What it does:**
- Phase 1: Waits for Celery chain task to complete
- Phase 2: Event-based wait using chord_id with progress thread
- Phase 3: Fallback to Redis progress polling
- Phase 4: File-based fallback monitoring

**Problems:**
- Four distinct "phases" in one function
- Mixed concerns: threading, Celery integration, Redis polling, file monitoring
- Deep nesting with while loops and try/except blocks
- Hard to debug which phase is failing

**Suggested split:**
- `_wait_for_chain_dispatch()` - Initial task dispatch wait
- `_wait_via_chord()` - Chord-based completion tracking
- `_wait_via_redis_polling()` - Redis progress polling fallback
- `_wait_via_file_monitoring()` - File modification time fallback

---

### 2. `main.py` - `run_auto_mode()`

| Attribute | Value |
|-----------|-------|
| **File** | `main.py` |
| **Lines** | 187-412 (226 lines) |
| **Function** | `run_auto_mode()` |

**What it does:**
- Loads configuration, starts Redis/Celery, waits for proxies
- Initializes proxy scoring, sets up mubeng rotator
- Runs 3-level pre-flight check with recovery
- Crawls all sites, saves final proxy scores

**Problems:**
- Single function handling entire automation pipeline
- Three-level pre-flight retry logic is deeply nested
- Mix of setup, validation, execution, and cleanup
- Hard to test individual stages

**Suggested split:**
- `_load_and_validate_config()`
- `_setup_infrastructure()`
- `_initialize_proxy_pool()`
- `_setup_proxy_rotator()`
- `_run_preflight_checks()`
- `_crawl_all_sites()`

---

### 3. `main.py` - `scrape_from_start_url()`

| Attribute | Value |
|-----------|-------|
| **File** | `main.py` |
| **Lines** | 34-172 (139 lines) |

**What it does:**
- Collects listing URLs from search pages with pagination
- Scrapes each listing and saves to database

**Suggested split:**
- `_collect_listing_urls()` - Pagination and URL collection
- `_scrape_listings()` - Individual listing scraping

---

### 4. `proxies/tasks.py` - `check_proxy_chunk_task()`

| Attribute | Value |
|-----------|-------|
| **File** | `proxies/tasks.py` |
| **Lines** | 130-257 (128 lines) |

**What it does:**
- Runs mubeng liveness check
- Enriches with anonymity, filters by real IP
- Runs quality checks, updates Redis

**Suggested split:**
- `_run_mubeng_liveness_check()`
- `_enrich_with_anonymity()`
- `_filter_by_real_ip_subnet()`
- `_check_quality_for_anonymous()`

---

### 5. `proxies/tasks.py` - `process_check_results_task()`

| Attribute | Value |
|-----------|-------|
| **File** | `proxies/tasks.py` |
| **Lines** | 260-344 (85 lines) |

**Suggested split:**
- `_flatten_and_filter_results()`
- `_log_quality_statistics()`
- `_save_proxy_files()`
- `_mark_job_complete()`

---

### 6. `websites/imot_bg/imot_scraper.py` - `extract_listing()`

| Attribute | Value |
|-----------|-------|
| **File** | `websites/imot_bg/imot_scraper.py` |
| **Lines** | 33-119 (87 lines) |

**Suggested split:** Group related field extractions:
- `_extract_price_info()`
- `_extract_size_info()`
- `_extract_location_info()`
- `_extract_building_info()`
- `_extract_features()`
- `_extract_media()`
- `_extract_contact()`

---

### 7. `websites/imot_bg/imot_scraper.py` - `is_last_page()`

| Attribute | Value |
|-----------|-------|
| **File** | `websites/imot_bg/imot_scraper.py` |
| **Lines** | 152-224 (73 lines) |

**Suggested split:**
- `_has_no_results_message()`
- `_has_no_listings()`
- `_has_next_page_link()`
- `_is_past_total_pages()`

---

### 8. `app/scoring.py` - `check_deal_breakers()`

| Attribute | Value |
|-----------|-------|
| **File** | `app/scoring.py` |
| **Lines** | 98-251 (154 lines) |

**Suggested refactor:** Use config-driven approach with individual check functions:
- `_check_not_panel()`
- `_check_elevator()`
- `_check_floor_limit()`
- etc.

---

### 9. `app/scoring.py` - `calculate_score()`

| Attribute | Value |
|-----------|-------|
| **File** | `app/scoring.py` |
| **Lines** | 265-442 (178 lines) |

**Suggested split:**
- `_score_location()`
- `_score_price_sqm()`
- `_score_condition()`
- `_score_layout()`
- `_score_building()`
- `_score_rental()`
- `_score_extras()`

---

### 10. `proxies/quality_checker.py` - `check_ip_service()`

| Attribute | Value |
|-----------|-------|
| **File** | `proxies/quality_checker.py` |
| **Lines** | 88-175 (88 lines) |

**Suggested split:**
- `_fetch_ip_from_service()`
- `_is_valid_proxy_ip()`

---

## Moderate Issues (30-50 lines)

| File | Function | Lines | Issue |
|------|----------|-------|-------|
| proxies/proxy_validator.py | check_proxy_liveness() | 66 | Response validation embedded |
| proxies/proxy_scorer.py | select_proxy() | 52 | Score/weight calculation mixed |
| browsers/browsers_main.py | create_instance() | 61 | Discovery/extraction/creation mixed |
| proxies/anonymity_checker.py | check_proxy_anonymity() | 59 | Loop with embedded try/except |
| websites/bazar_bg/bazar_scraper.py | extract_listing() | 89 | Same as imot_bg pattern |

---

## Minor Issues

1. **Repeated proxy URL construction** - Create `proxy_to_url()` helper
2. **Redis key patterns** - Create `RedisKeys` constants
3. **Magic numbers** - Move to config files
4. **Nested Streamlit conditionals** - Extract tab content functions
5. **Duplicated browser launch logic** - Use decorator/context manager

---

## Metrics Summary

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 10 | Functions >50 lines requiring split |
| Moderate | 5 | Functions 30-50 lines worth improving |
| Minor | 5 | Small improvements and patterns to extract |

**Estimated refactoring effort:** 3-5 days for critical issues

---

*Report generated by code quality audit on 2025-12-25*
