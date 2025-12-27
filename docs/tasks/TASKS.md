# Tasks - Single Source of Truth

**RULES:**
1. Claim tasks with `[Instance N]` before starting
2. Mark complete with `[x]` when done
3. Unclaim if not finishing this session

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
| Ollama Integration (Phases 1-5) | 45+ | Completed |
| Crawler Validation (Phase 0) | 7 | Completed |
| Historical Completed Work | 35+ | Completed |

---

## Instance Coordination

| Instance | Current Task |
|----------|--------------|
| 1 | Available |
| 2 | Available |
| 3 | Available |

**Session 28 (2025-12-27)**: Instance 1 - Scraper Resilience Research. Analyzed current error handling gaps, researched best practices, explored AutoBiz codebase for production-grade patterns. Created research doc, spec 112, and 18 implementation tasks. Found 5 modules to port: circuit breaker, error system, rate limiter, bulkhead, timeout budget.

**Session 27 (2025-12-27)**: Instance 2 - Consolidated scoring constants. Fixed min_count=5 bug. Added scoring constants to config/settings.py.

**Session 26 (2025-12-27)**: Instance 1 - TASKS.md cleanup + Centralized proxy settings.

**Session 25 (2025-12-27)**: Instance 2 - Dashboard Integration (Spec 111 Phase 3) + Unified Proxy Timeout.

**Claim**: Add `[Instance N]` next to task before starting
**Complete**: Add `[x]` and remove `[Instance N]` when done

---

## Pending Tasks

### Testing (P1)

- [ ] Test 3.2: Concurrent task handling
- [ ] Test full proxy refresh + quality detection flow
- [ ] Test imot.bg scraper with real listings
- [ ] Debug/refine extraction logic

---

### Crawler Validation & Enhancement (P1)

**Spec**: [106_CRAWLER_VALIDATION_PLAN.md](../specs/106_CRAWLER_VALIDATION_PLAN.md)

#### Phase 1: Scraper Validation
- [ ] Create test harness (`tests/scrapers/`)
- [ ] Validate imot.bg scraper (pagination, extraction, save)
- [ ] Validate bazar.bg scraper (pagination, extraction, save)
- [ ] Create validation matrix (document what works)

#### Phase 3: Change Detection & History (Remaining)
- [ ] Create `scrape_history` table
- [ ] Create `listing_changes` table (track ALL field changes)

#### Phase 3.5: Cross-Site Duplicate Detection & Merging
- [ ] Create `listing_sources` table (track which sites list property)
- [ ] Build `PropertyFingerprinter` class (identify duplicates)
- [ ] Build `PropertyMerger` class (smart data merging)
- [ ] Track price discrepancies across sites
- [ ] Add cross-site comparison view to dashboard

#### Phase 4: Rate Limiting & Orchestration
- [ ] Define rate limit config per site
- [ ] Build Redis-backed `SiteRateLimiter`
- [ ] Build async orchestrator (parallel sites)
- [ ] Integrate with Celery

#### Phase 5: Full Pipeline
- [ ] E2E testing (full pipeline)
- [ ] Add monitoring/alerting

---

### Ollama Integration - Remaining Tasks

**Spec**: [107_OLLAMA_INTEGRATION.md](../specs/107_OLLAMA_INTEGRATION.md)

#### Phase 3.6: Achieve 95%+ Accuracy (Remaining)
- [ ] Phase 4: Hybrid CSS/LLM (If < 95%) - Extract structured fields with CSS, LLM for free-text
- [ ] Phase 5: Field-Specific Prompts (If < 98%) - Focused prompts for problematic fields
- [ ] No field below 80% accuracy - has_elevator at 0% (1 sample)

#### Future: Scrapling + LLM Synergy
- [ ] Research element-aware prompts vs raw text prompts
- [ ] Implement hybrid extraction: Scrapling CSS -> LLM fallback

---

### Scraper Resilience & Error Handling (P1)

**Spec**: [112_SCRAPER_RESILIENCE.md](../specs/112_SCRAPER_RESILIENCE.md)
**Research**: [SCRAPER_RESILIENCE_RESEARCH.md](../research/SCRAPER_RESILIENCE_RESEARCH.md)

#### Phase 1: Foundation
- [ ] Create `resilience/` module structure
- [ ] Implement `resilience/exceptions.py` (exception hierarchy)
- [ ] Implement `resilience/error_classifier.py`
- [ ] Implement `resilience/retry.py` (sync + async with backoff + jitter)
- [ ] Add resilience settings to `config/settings.py`
- [ ] Integrate retry decorator into `main.py`
- [ ] Write unit tests for Phase 1

#### Phase 2: Domain Protection
- [ ] Implement `resilience/circuit_breaker.py`
- [ ] Implement `resilience/rate_limiter.py` (token bucket)
- [ ] Integrate circuit breaker into scraper
- [ ] Integrate rate limiter into scraper
- [ ] Write unit tests for Phase 2

#### Phase 3: Session Recovery
- [ ] Implement `resilience/checkpoint.py`
- [ ] Add checkpoint save/restore to main.py
- [ ] Add SIGTERM/SIGINT graceful shutdown handlers
- [ ] Write unit tests for Phase 3

#### Phase 4: Detection (P3)
- [ ] Implement `resilience/response_validator.py` (CAPTCHA/soft block detection)
- [ ] Add 429/Retry-After header handling
- [ ] Write unit tests for Phase 4

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

**Last Updated**: 2025-12-27 (Archived completed sections)
