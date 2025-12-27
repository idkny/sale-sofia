---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-27
---

# Instance 2 Session

**You are Instance 2.** Work independently.

---

## Workflow: Research → Specs → Code

**Single source of truth at each stage:**

```
docs/research/  →  docs/specs/  →  TASKS.md  →  code
(discovery)        (blueprint)     (tracking)    (truth)
      ↓                 ↓                           ↓
archive/research/  archive/specs/          (code supersedes)
```

**Rules:**
1. Research done → create spec + task → archive research
2. Spec done → implement code → archive spec
3. Code is source of truth (specs become historical)
4. New features = new specs (don't update archived)

---

## How to Work

1. Read [TASKS.md](TASKS.md) coordination table
2. Claim task with `[Instance 2]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 2] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 2] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 2] Implement proxy rotation
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# After complete (spec archived, link removed)
- [x] Implement proxy rotation
```

---

## CRITICAL RULES

1. **NEVER WRITE "NEXT STEPS" IN THIS FILE**
2. **TASKS.md IS THE SINGLE SOURCE OF TRUTH FOR TASKS**
3. **THIS FILE IS FOR SESSION HISTORY ONLY**
4. **KEEP ONLY LAST 3 SESSIONS**
5. **CODE IS SOURCE OF TRUTH, NOT SPECS**

---

## Instance Rules

1. **One task at a time** - Finish before claiming another
2. **Check coordination table FIRST** - Re-read TASKS.md before claiming
3. **Claim in TASKS.md** - Add `[Instance 2]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_001.md** - Other instance file is off-limits

---

## Session History

### 2025-12-27 (Session 37 - Phase 4.2 Async Implementation)

| Task | Status |
|------|--------|
| Add `acquire_async()` to rate_limiter.py | Complete |
| Update scrapers to sync (remove fake async) | Complete |
| Create `scraping/async_fetcher.py` | Complete |
| Update main.py for sync consistency | Complete |
| Write 11 async fetcher tests (100% coverage) | Complete |
| Run Phase Completion Checklist | Complete |

**Summary**: Implemented Phase 4.2 Async Implementation. Fixed fake async patterns, created true async fetcher with httpx.AsyncClient for future Celery integration. 563 tests passing.

**Files Created**:
- `scraping/__init__.py` - module exports
- `scraping/async_fetcher.py` - async HTTP fetcher with circuit breaker, rate limiting
- `tests/test_async_fetcher.py` - 11 tests (100% coverage)

**Files Modified**:
- `resilience/rate_limiter.py` - added `acquire_async()` method
- `websites/base_scraper.py` - `async def` → `def` for extract methods
- `websites/imot_bg/imot_scraper.py` - removed async from extract methods
- `websites/bazar_bg/bazar_scraper.py` - removed async from extract methods
- `main.py` - removed asyncio.run(), made scrape functions sync
- `config/settings.py` - added `ASYNC_FETCHER_MAX_CONCURRENT`
- `tests/scrapers/test_imot_bg.py` - removed await from tests
- `tests/scrapers/test_bazar_bg.py` - removed await from tests
- `tests/test_bazar.py` - removed async pattern

---

### 2025-12-27 (Session 34 - Phase 4.1 Scraping Configuration + Integration)

| Task | Status |
|------|--------|
| Research scraper settings (Scrapy/Colly/Crawlee) | Complete |
| Create spec 113 | Complete |
| Create `config/scraping_defaults.yaml` | Complete |
| Create `config/sites/*.yaml` per-site overrides | Complete |
| Create `config/scraping_config.py` loader | Complete |
| Write 7 unit tests (99% coverage) | Complete |
| Integrate into main.py | Complete |
| Remove old `DEFAULT_SCRAPE_DELAY` | Complete |
| Update `SCRAPER_GUIDE.md` | Complete |
| Archive spec 113 | Complete |

**Summary**: Implemented Phase 4.1 Scraping Configuration. Created 2-level config system (global defaults + per-site overrides) based on Scrapy/Colly/Crawlee best practices. Integrated into main.py, removed old settings. 37 tests passing.

---

### 2025-12-27 (Session 33 - Phase 3.5 Cross-Site Duplicate Detection)

| Task | Status |
|------|--------|
| Create spec 106B | Complete |
| Create `listing_sources` table | Complete |
| Build `PropertyFingerprinter` class | Complete |
| Build `PropertyMerger` class | Complete |
| Track price discrepancies across sites | Complete |
| Add cross-site comparison dashboard page | Complete |

**Summary**: Implemented Phase 3.5 Cross-Site Duplicate Detection. Created fingerprinting system to identify same property across imot.bg and bazar.bg. Added price discrepancy tracking and dashboard comparison view.

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
