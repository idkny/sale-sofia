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

**Session 27 (2025-12-27)**: Instance 2 - Consolidated scoring constants. Fixed min_count=5 bug (should use MIN_PROXIES_FOR_SCRAPING=10). Added `SCORE_SUCCESS_MULTIPLIER`, `SCORE_FAILURE_MULTIPLIER`, `MAX_PROXY_FAILURES`, `MIN_PROXY_SCORE` to config/settings.py. Updated proxy_scorer.py and proxy_validator.py to import from settings (were duplicate definitions). Fixed orchestrator.py defaults.

**Session 26 (2025-12-27)**: Instance 1 - TASKS.md cleanup + Centralized proxy settings. Removed duplicate JIT Proxy Validation (already in Solution F), removed homes.bg task, removed P3 research tasks. Added `MUBENG_PROXY`, `MIN_PROXIES_TO_START=1`, `MIN_PROXIES_FOR_SCRAPING=10`, `MAX_PROXY_RETRIES=3` to config/settings.py. Fixed inconsistent min_proxies values (was 1/5/10 in different places).

**Session 25 (2025-12-27)**: Instance 2 - Dashboard Integration (Spec 111 Phase 3) + Unified Proxy Timeout. Added price history chart tab and "recently changed" filter to Listings page. Created `config/settings.py` with `PROXY_TIMEOUT_SECONDS=45`.

**Session 24 (2025-12-27)**: Instance 2 - Implemented Page Change Detection (Spec 111) Phases 1-2. Created `data/change_detector.py`. 24 unit tests pass.

**Session 23 (2025-12-26)**: Instance 3 - Completed Solution F Phase 7 (Edge Cases & Hardening). All 15 Solution F tests pass.

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
