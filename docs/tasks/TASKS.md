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
| Historical Completed Work | 35+ | Completed |

---

## Instance Coordination

| Instance | Current Task |
|----------|--------------|
| 1 | Available |
| 2 | Available |
| 3 | Available |

**Session 30 (2025-12-27)**: Instance 2 - Crawler Validation Phase 1 complete. All 46 scraper tests passing. Fixed floor extraction, price JS patterns, sqm patterns, and test fixtures for both scrapers.

**Session 30 (2025-12-27)**: Instance 1 - Spec 112 Phase 2 Implementation + Cleanup. Created circuit_breaker.py and rate_limiter.py. Integrated into main.py. 87 tests passing.

**Session 29 (2025-12-27)**: Instance 1 - Spec 112 Phase 1 Implementation. Created resilience/ module. 45 tests passing.

**Session 28 (2025-12-27)**: Instance 2 - Ollama Phase 3.6 complete. 100% accuracy via dictionary-first extraction.

**Claim**: Add `[Instance N]` next to task before starting
**Complete**: Add `[x]` and remove `[Instance N]` when done

---

## Pending Tasks

### Testing (P1)

- [ ] Test 3.2: Concurrent task handling
- [ ] Test full proxy refresh + quality detection flow
- [ ] Test imot.bg scraper with real listings

---

### Crawler Validation & Enhancement (P1)

**Spec**: [106_CRAWLER_VALIDATION_PLAN.md](../specs/106_CRAWLER_VALIDATION_PLAN.md)

> **Phase 0**: COMPLETE (Scrapling migration)
> **Phase 2**: SUPERSEDED by LLM extraction (Specs 107/108/110 achieved 100% accuracy)

#### Phase 1: Scraper Validation
- [x] Create test harness (`tests/scrapers/`) - 46 tests, 46 passing
- [x] Validate imot.bg scraper (pagination, extraction, save) - 23/23 tests passing
- [x] Validate bazar.bg scraper (pagination, extraction, save) - 23/23 tests passing
- [ ] Create validation matrix (document what works)
- [ ] **Run Phase Completion Checklist** (consistency + alignment)

#### Phase 3: Change Detection & History (Remaining)
> Basic change detection exists (`data/change_detector.py`). Tables below still needed.
- [ ] Create `scrape_history` table
- [ ] Create `listing_changes` table (track ALL field changes)
- [ ] **Run Phase Completion Checklist** (consistency + alignment)

#### Phase 3.5: Cross-Site Duplicate Detection & Merging
- [ ] Create `listing_sources` table (track which sites list property)
- [ ] Build `PropertyFingerprinter` class (identify duplicates)
- [ ] Build `PropertyMerger` class (smart data merging)
- [ ] Track price discrepancies across sites
- [ ] Add cross-site comparison view to dashboard
- [ ] **Run Phase Completion Checklist** (consistency + alignment)

#### Phase 4: Orchestration
> **Rate limiter**: Use `resilience/rate_limiter.py` (DomainRateLimiter, Spec 112 Phase 2)
- [x] Rate limiter - use `resilience/rate_limiter.py` (token bucket per domain)
- [ ] Build async orchestrator (parallel sites)
- [ ] Integrate with Celery
- [ ] **Run Phase Completion Checklist** (consistency + alignment)

#### Phase 5: Full Pipeline
- [ ] E2E testing (full pipeline)
- [ ] Add monitoring/alerting
- [ ] **Run Phase Completion Checklist** (consistency + alignment)

---

### Ollama Integration - Future Enhancements

**Spec**: [107_OLLAMA_INTEGRATION.md](../specs/107_OLLAMA_INTEGRATION.md)

> **Phase 3.6 Complete**: Achieved 100% accuracy. Dictionary extracts booleans directly (has_elevator fix). Phases 4-5 skipped (thresholds already exceeded).

#### Future: Scrapling + LLM Synergy
- [ ] Research element-aware prompts vs raw text prompts
- [ ] Implement hybrid extraction: Scrapling CSS -> LLM fallback

---

### Scraper Resilience & Error Handling (P1)

**Spec**: [112_SCRAPER_RESILIENCE.md](../specs/112_SCRAPER_RESILIENCE.md)
**Tasks**: [112_RESILIENCE_IMPLEMENTATION.md](112_RESILIENCE_IMPLEMENTATION.md) (detailed breakdown with AutoBiz refs)
**Research**: [SCRAPER_RESILIENCE_RESEARCH.md](../research/SCRAPER_RESILIENCE_RESEARCH.md)

#### Phase 1: Foundation (COMPLETE)
- [x] Create `resilience/` module structure
- [x] Implement `resilience/exceptions.py` (exception hierarchy)
- [x] Implement `resilience/error_classifier.py`
- [x] Implement `resilience/retry.py` (sync + async with backoff + jitter)
- [x] Add resilience settings to `config/settings.py`
- [x] Integrate retry decorator into `main.py`
- [x] Write unit tests for Phase 1 (45 tests, 100% pass)

#### Phase 2: Domain Protection (COMPLETE)
- [x] Implement `resilience/circuit_breaker.py`
- [x] Implement `resilience/rate_limiter.py` (token bucket)
- [x] Integrate circuit breaker into main.py
- [x] Integrate rate limiter into main.py
- [x] Write unit tests for Phase 2 (42 tests, 100% pass)

#### Phase 3: Session Recovery (COMPLETE)
- [x] Implement `resilience/checkpoint.py`
- [x] Add checkpoint save/restore to main.py
- [x] Add SIGTERM/SIGINT graceful shutdown handlers
- [x] Write unit tests for Phase 3 (18 tests, 100% pass)
- [x] **Run Phase Completion Checklist** (consistency + alignment)

#### Phase 4: Detection (P3)
- [ ] Implement `resilience/response_validator.py` (CAPTCHA/soft block detection)
- [ ] Add 429/Retry-After header handling
- [ ] Write unit tests for Phase 4
- [ ] **Run Phase Completion Checklist** (consistency + alignment)

---

### Features (P2)

- [ ] Improve floor extraction in bazar.bg scraper
- [ ] Populate dashboard with scraped data

---

### Future: Automatic Threshold Refresh

**Dependency**: Proxy Scoring Bug (Solution F) - COMPLETE

- [ ] Automatic threshold-based proxy refresh (check count every N minutes, refresh if < X)

---

## Related Documents

- [REFACTORING_TASKS.md](REFACTORING_TASKS.md) - Code quality refactoring tasks
- [docs/specs/](../specs/) - Active specifications
- [docs/research/](../research/) - Active research
- [archive/](../../archive/) - Completed work archives

---

**Last Updated**: 2025-12-27 (Crawler Validation Phase 1 - scrapers 46/46 tests passing)
