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

**Files Created**:
- `config/scraping_defaults.yaml` - global defaults (timing, concurrency, retry, etc.)
- `config/sites/imot_bg.yaml` - faster settings (less anti-bot)
- `config/sites/bazar_bg.yaml` - conservative settings (anti-bot protection)
- `config/scraping_config.py` - loader with 8 dataclasses, deep merge
- `tests/test_scraping_config.py` - 7 tests

**Files Modified**:
- `main.py` - uses `load_scraping_config()` for delay/timeout
- `config/loader.py` - simplified SiteConfig (limit only)
- `config/settings.py` - removed `DEFAULT_SCRAPE_DELAY`
- `config/__init__.py` - removed dead `SCRAPER_CONFIG`
- `websites/SCRAPER_GUIDE.md` - added Step 8: Scraping Configuration

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

### 2025-12-27 (Session 31 - Phase 3 Change Detection)

| Task | Status |
|------|--------|
| Create `scrape_history` table | Complete |
| Create `listing_changes` table | Complete |
| Add 7 CRUD functions | Complete |
| Add `detect_all_changes()` | Complete |
| Write 30 tests | Complete |

**Summary**: Implemented Phase 3 Change Detection: added `scrape_history` and `listing_changes` tables, 7 CRUD functions, `detect_all_changes()` with SKIP_FIELDS, 30 tests.

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
