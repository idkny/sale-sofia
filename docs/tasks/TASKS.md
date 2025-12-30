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

> **Archives**:
> - [TASKS_COMPLETED_2025-12-28.md](../../archive/tasks/TASKS_COMPLETED_2025-12-28.md) - Latest
> - [TASKS_COMPLETED_2025-12-27.md](../../archive/tasks/TASKS_COMPLETED_2025-12-27.md)

| Section | Tasks | Status |
|---------|-------|--------|
| Bugs (P0) | 3 | Completed |
| Proxy Scoring Bug (Solution F, Phases 0-7) | 31 | Completed |
| Chunk Processing Timing Bug | 12 | Completed |
| Celery + Mubeng + PSC Integration (Phases 1-2) | 14 | Completed |
| Page Change Detection (Phases 1-3) | 8 | Completed |
| Ollama Integration (Phases 1-5, 3.6) | 45+ | Completed |
| Crawler Validation (Phases 0-5) | 71 | Completed (894 tests) |
| Scraper Resilience (Phases 1-4) | 33 | Completed (153 tests) |
| Scraper Monitoring (Phases 1-4) | 12 | Completed |
| Pre-Production Hardening (Phases 1-3) | 10 | Completed |
| Historical Completed Work | 35+ | Completed |

**Total Tests**: 1036 passed, 8 skipped

---

## Instance Coordination

| Instance | Current Task |
|----------|--------------|
| 1 | Available |
| 2 | Available |
| 3 | Available |

**Session 54 (2025-12-30)**: Instance 2 - Dead code cleanup (~483 lines). Deleted `proxy_validator.py` (408 lines, never imported), removed PREFLIGHT_* settings, fixed stale docstrings.

**Session 53 (2025-12-30)**: Instance 2 - Proxy cleanup x2: (1) Simplified proxy scoring - removed weighted selection, score multipliers, persistence. (2) Removed PROXY_WAIT_TIMEOUT dead code.

**Session 52 (2025-12-30)**: Instance 1 - Proxy settings cleanup. Renamed MAX_PROXY_RETRIES → MAX_URL_RETRIES. Added 3 new tasks: Failed URL Tracking, Simplify Proxy Scoring, Cleanup PROXY_WAIT_TIMEOUT.

**Session 51 (2025-12-30)**: Instance 1 - OLX.bg live test + enhanced parsers. Added `:contains()` selector, `label_value/number/floor` parsers.

**Session 50 (2025-12-29)**: Instance 2 - Fixed proxy system. Removed mubeng/preflight, implemented direct proxy with liveness check.

**Claim**: Add `[Instance N]` next to task before starting
**Complete**: Add `[x]` and remove `[Instance N]` when done

---

## Pending Tasks

### P0: Fix Proxy System (Scraper Not Working) - COMPLETE

> **Fixed in Session 50 (2025-12-29)**

- [x] Fix KeyError in `proxy_scorer.py` (Session 49)
- [x] Remove mubeng server from scraping flow (use proxies directly)
- [x] Remove blocking pre-flight gate (3-level system)
- [x] Add per-request liveness check (test proxy before browser use)
- [x] Add background refresh trigger (when count < MIN_PROXIES)
- [x] Consolidated timeout settings (removed PROXY_VALIDATION_TIMEOUT, use PROXY_TIMEOUT_SECONDS everywhere)
- [ ] Test full pipeline end-to-end (needs fresh proxies)

---

## Future Enhancements (Backlog)

> **Note**: These are ideas for future development. Not prioritized, no timeline.

### Operations
- [x] Auto-start dashboard after scraping (launch Streamlit when main.py completes)
- [ ] Backup strategy (scheduled DB backups, retention policy)
- [ ] Systemd services (auto-start on server wake/boot)

### Notifications & Alerts
- [ ] Failure alerts (Telegram/email when scraping fails)
- [ ] New listing alerts (notify when listings match user criteria)
- [ ] Circuit breaker alerts (alert when sites become unavailable)
- [ ] Daily digest (summary of new/changed listings)

### Generic Scraper Template & Additional Sites

**Spec**: [116_GENERIC_SCRAPER_TEMPLATE.md](../specs/116_GENERIC_SCRAPER_TEMPLATE.md)

> **Goal**: Config-driven scraper - add new sites with YAML only, no code changes.
> **Pattern**: User provides filtered URL → scraper extracts using selector fallback chains.

#### Phase 1: Core Framework
- [x] 1.1 Create `websites/generic/__init__.py`
- [x] 1.2 Create `config_loader.py` (YAML loading + validation)
- [x] 1.3 Create `selector_chain.py` (fallback extraction engine)
- [x] 1.4 Create `config_scraper.py` (generic ConfigScraper class)
- [x] 1.5 Write unit tests for config loading and selector chains

#### Phase 2: Field Parsers
- [x] 2.1 Create field type parsers (currency, number, floor_pattern) - Session 50
- [x] 2.2 Support Bulgarian patterns (BGN/EUR, кв.м, етаж X от Y) - Session 50
- [x] 2.3 Write unit tests for all parsers - Session 50

> **Session 51 Addition**: Added `:contains()` selector, `label_value`, `label_number`, `label_floor` parsers

#### Phase 3: Pagination Support
- [ ] 3.1 Implement numbered pagination
- [ ] 3.2 Implement next_link pagination
- [ ] 3.3 Implement load_more pagination
- [ ] 3.4 Implement infinite_scroll pagination
- [ ] 3.5 Write pagination tests

#### Phase 4: OLX.bg Pilot
- [x] 4.1 Research OLX.bg HTML structure - Session 51
- [x] 4.2 Create `config/sites/olx_bg.yaml` - Session 51
- [x] 4.3 Test extraction with sample pages - Session 51 (offline test passed)
- [ ] 4.4 Verify pagination works
- [ ] 4.5 Integration test: full scrape (needs proxy rotation - mubeng)

#### Phase 5: Homes.bg
- [ ] 5.1 Research homes.bg HTML structure
- [ ] 5.2 Create `config/sites/homes_bg.yaml`
- [ ] 5.3 Test and verify

#### Phase 6: Migration (Optional)
- [ ] 6.1 Create YAML configs for imot.bg/bazar.bg
- [ ] 6.2 Validate against existing scraper output
- [ ] 6.3 Deprecate old scraper code

### Simplify Proxy Scoring System - COMPLETE (Session 53)

> **Completed 2025-12-30**: Removed complex scoring, now uses simple consecutive failure tracking.

#### Completed Tasks
- [x] 1. Remove `SCORE_SUCCESS_MULTIPLIER`, `SCORE_FAILURE_MULTIPLIER`, `MIN_PROXY_SCORE` from settings
- [x] 2. Rename `MAX_PROXY_FAILURES` → `MAX_CONSECUTIVE_PROXY_FAILURES`
- [x] 3. Simplify `proxy_scorer.py` - remove score math, keep failure counter only
- [x] 4. Remove weighted selection - use random.choice()
- [x] 5. Remove `proxy_scores.json` persistence
- [x] 6. ~~Update `proxy_validator.py`~~ (DELETED in Session 54 - was dead code)
- [x] 7. Update/remove related tests (deleted 6, modified 4)
- [x] 8. Delete unused code (~120 lines removed)

**Files Modified**: config/settings.py, proxies/proxy_scorer.py, main.py, tests/test_proxy_scorer.py
**Tests**: 1036 passed, 8 skipped

### Cleanup PROXY_WAIT_TIMEOUT (Dead Code) - COMPLETE (Session 53)

> **Completed 2025-12-30**: Removed misleading timeout setting.

#### Completed Tasks
- [x] 1. Remove `PROXY_WAIT_TIMEOUT` from `config/settings.py`
- [x] 2. Remove `PROXY_WAIT_TIMEOUT` import from `main.py`
- [x] 3. Update `main.py:650` to not pass timeout (use orchestrator default)
- [x] 4. Add comment in `orchestrator.py` explaining timeout is safety net only

**Files Modified**: config/settings.py, main.py, orchestrator.py
**Tests**: 1036 passed, 8 skipped

### Failed URL Tracking & Retry System

> **Goal**: Persist failed URLs to database for retry with different strategies (captcha solving, different proxy, etc.)
> **Problem**: Currently failed URLs are only logged - no way to retry later or analyze failure patterns.

#### Phase 1: Database Schema
- [ ] 1.1 Create `failed_urls` table (url, site, failure_count, error_type, error_message, status)
- [ ] 1.2 Add status enum: `pending`, `captcha_needed`, `permanent`, `resolved`
- [ ] 1.3 Add `retry_after` timestamp for rate-limited retries

#### Phase 2: Integration
- [ ] 2.1 Update `main.py` `_scrape_listings()` to save failed URLs on `MAX_URL_RETRIES` exhausted
- [ ] 2.2 Classify errors: timeout → pending, blocked → captcha_needed, 404 → permanent
- [ ] 2.3 Skip URLs already marked as `permanent` in future runs

#### Phase 3: Retry Logic
- [ ] 3.1 Add CLI command to retry `pending` URLs
- [ ] 3.2 Add CLI command to retry `captcha_needed` URLs (with captcha solver)
- [ ] 3.3 Auto-resolve URLs that succeed on retry

#### Phase 4: Dashboard Integration
- [ ] 4.1 Show failed URL stats in dashboard
- [ ] 4.2 Allow manual status changes (mark as permanent, reset to pending)
- [ ] 4.3 Export failed URLs list

### Analytics & Insights
- [ ] Price trends (historical price analysis per neighborhood)
- [ ] Market heatmaps (visualization of pricing by area)
- [ ] Deal scoring (identify underpriced listings)
- [ ] Time-on-market tracking (how long listings stay active)

### Code Quality
- [ ] Code coverage (increase to 90%+)
- [ ] Type hints (full mypy compliance)
- [ ] Documentation (README, architecture docs, API docs)
- [ ] Dependency audit (security scan, update packages)

---

## Related Documents

- [docs/specs/](../specs/) - Active specifications
- [docs/research/](../research/) - Active research
- [archive/](../../archive/) - Completed work archives

---

**Last Updated**: 2025-12-30 (Session 54 - Dead code cleanup)
