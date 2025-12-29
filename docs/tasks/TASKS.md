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

**Total Tests**: 1042 passed, 8 skipped

---

## Instance Coordination

| Instance | Current Task |
|----------|--------------|
| 1 | Available |
| 2 | Available |
| 3 | Available |

**Session 49 (2025-12-28)**: Instance 2 - Debug scraper not saving data. Found proxy system issues. See instance_002.md for details.

**Claim**: Add `[Instance N]` next to task before starting
**Complete**: Add `[x]` and remove `[Instance N]` when done

---

## Pending Tasks

### P0: Fix Proxy System (Scraper Not Working)

> **Problem**: Scraper runs but no data saved. Pre-flight check blocks everything.
> **Details**: See `docs/tasks/instance_002.md` Session 49 for full analysis.

- [x] Fix KeyError in `proxy_scorer.py` (Session 49)
- [ ] Remove mubeng server from scraping flow (use proxies directly)
- [ ] Remove blocking pre-flight gate (3-level system)
- [ ] Add per-request liveness check (test proxy before browser use)
- [ ] Add background refresh trigger (when count < MIN_PROXIES)
- [ ] Test full pipeline end-to-end

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
- [ ] 2.1 Create field type parsers (currency, number, floor_pattern)
- [ ] 2.2 Support Bulgarian patterns (BGN/EUR, кв.м, етаж X от Y)
- [ ] 2.3 Write unit tests for all parsers

#### Phase 3: Pagination Support
- [ ] 3.1 Implement numbered pagination
- [ ] 3.2 Implement next_link pagination
- [ ] 3.3 Implement load_more pagination
- [ ] 3.4 Implement infinite_scroll pagination
- [ ] 3.5 Write pagination tests

#### Phase 4: OLX.bg Pilot
- [ ] 4.1 Research OLX.bg HTML structure
- [ ] 4.2 Create `config/sites/olx_bg.yaml`
- [ ] 4.3 Test extraction with sample pages
- [ ] 4.4 Verify pagination works
- [ ] 4.5 Integration test: full scrape

#### Phase 5: Homes.bg
- [ ] 5.1 Research homes.bg HTML structure
- [ ] 5.2 Create `config/sites/homes_bg.yaml`
- [ ] 5.3 Test and verify

#### Phase 6: Migration (Optional)
- [ ] 6.1 Create YAML configs for imot.bg/bazar.bg
- [ ] 6.2 Validate against existing scraper output
- [ ] 6.3 Deprecate old scraper code

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

**Last Updated**: 2025-12-28 (Spec 116 Generic Scraper Template added)
