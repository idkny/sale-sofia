# Instance 1 Session

**You are Instance 1.** Work independently.

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
2. Claim task with `[Instance 1]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]}`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 1] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 1] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 1] Implement proxy rotation
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
3. **Claim in TASKS.md** - Add `[Instance 1]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_002.md** - Other instance file is off-limits

---

## Session History

### 2025-12-28 (Session 49 - Spec 116 Phase 1.1-1.2 Implementation)

| Task | Status |
|------|--------|
| 1.1 Create `websites/generic/__init__.py` | ✅ Complete |
| 1.2 Create `config_loader.py` (YAML loading + validation) | ✅ Complete |

**Summary**:
Started implementation of Spec 116 (Generic Scraper Template). Completed Phase 1 tasks 1.1 and 1.2.

**Files Created**:
- `websites/generic/__init__.py` - Module init with docstring, placeholder imports, `__all__` list
- `websites/generic/config_loader.py` - YAML config loading with validation

**config_loader.py contains**:
- 8 dataclasses: `SiteInfo`, `UrlPatterns`, `PaginationConfig`, `ListingPageConfig`, `DetailPageConfig`, `ExtractionConfig`, `TimingConfig`, `QuirksConfig`, `GenericScraperConfig`
- `load_config()` - Load YAML and return structured dataclass
- `validate_config()` - Validate raw config dict, returns error list
- `get_config_path()` - Convert site name to config path (olx.bg → config/sites/olx_bg.yaml)

**Patterns followed**:
- Dataclass structure from `config/scraping_config.py`
- YAML loading with `yaml.safe_load()`
- Loguru logging

**Next tasks** (Phase 1 remaining):
- 1.3 Create `selector_chain.py` (fallback extraction engine)
- 1.4 Create `config_scraper.py` (generic ConfigScraper class)
- 1.5 Write unit tests

---

### 2025-12-28 (Session 48 - Spec 116 Generic Scraper Template)

| Task | Status |
|------|--------|
| Review post-Phase 5 roadmap | ✅ Complete |
| Add Future Enhancements to TASKS.md | ✅ Complete |
| Research generic scraper patterns | ✅ Complete |
| Create Spec 116 | ✅ Complete |
| Add tasks to TASKS.md | ✅ Complete |

**Summary**:
All previous development tasks are COMPLETE (894 tests). This session focused on planning future enhancements:

1. **Added Future Enhancements to TASKS.md** (17 items in 5 categories):
   - Operations: Backup strategy, Systemd services
   - Notifications: Failure alerts, New listing alerts, Circuit breaker alerts, Daily digest
   - Additional Sites: olx.bg, homes.bg, Generic scraper template
   - Analytics: Price trends, Market heatmaps, Deal scoring, Time-on-market
   - Code Quality: Coverage 90%+, Type hints, Documentation, Dependency audit

2. **Researched Generic Scraper Template** via 2 parallel agents:
   - Agent 1: Real estate scraping patterns (Zillow, Rightmove, etc.)
   - Agent 2: E-commerce scraping patterns (Crawlee, Scrapy, Apify)

3. **Key Research Finding**: E-commerce and real estate scraping are structurally identical:
   ```
   Category Page (filtered) → Grid of Items → Detail Page
   ```
   User provides filtered starting URL, scraper takes over from there.

4. **Created Spec 116: Generic Scraper Template**:
   - Location: `docs/specs/116_GENERIC_SCRAPER_TEMPLATE.md`
   - Approach: YAML config per site, no code changes for new sites
   - 3-tier extraction: CSS selectors → XPath → LLM fallback (disabled by default)
   - LLM disabled due to local hardware constraints

5. **Added 24 tasks (6 phases) to TASKS.md**:
   - Phase 1: Core Framework (5 tasks) - config_loader, selector_chain, ConfigScraper
   - Phase 2: Field Parsers (3 tasks) - currency, numbers, Bulgarian patterns
   - Phase 3: Pagination (5 tasks) - numbered, next_link, load_more, infinite_scroll
   - Phase 4: OLX.bg Pilot (5 tasks) - first new site using template
   - Phase 5: Homes.bg (3 tasks) - second site, YAML only
   - Phase 6: Migration (3 tasks) - optional: migrate imot.bg/bazar.bg to YAML

**Files Created**:
- `docs/specs/116_GENERIC_SCRAPER_TEMPLATE.md` - Full spec with YAML schema, architecture, research sources

**Files Modified**:
- `docs/tasks/TASKS.md` - Added Future Enhancements + Generic Scraper Template tasks

**Research Sources Preserved in Spec**:
- Real Estate: fgrillo89/real-estate-scraper, SelectorLib, ScrapeGraphAI
- E-commerce: Crawlee, Crawlee One, llm-scraper, Firecrawl
- Architecture: Scrapy docs, Building Generic Scrapers (thewebscraping.club)

**Proposed YAML Config Structure** (key decision):
```yaml
site:
  name: olx.bg
  domain: www.olx.bg
urls:
  listing_pattern: "/ad/"
pagination:
  type: numbered
  param: page
detail_page:
  selectors:
    price:           # Fallback chain
      - "[data-testid='ad-price']"
      - "h3.price"
    title:
      - "h1[data-cy='ad_title']"
      - "h1"
timing:
  delay_seconds: 2.0
```

**Current State**:
- All development tasks COMPLETE (894 tests)
- Future work is in TASKS.md under "Future Enhancements (Backlog)"
- Next implementation: Phase 1 of Spec 116 (Core Framework)

**To Continue Next Session**:
1. Read `docs/specs/116_GENERIC_SCRAPER_TEMPLATE.md` for full context
2. Claim Phase 1.1 in TASKS.md
3. Start with `websites/generic/__init__.py`

---

### 2025-12-28 (Session 46 - Phase 4.4.5 + 5.2)

| Task | Status |
|------|--------|
| 4.4.5 Run Phase Completion Checklist | ✅ Complete |
| 5.2 Add Celery Flower | ✅ Complete |

**Summary**:
1. Reopened and fixed Phase 4.4.5 - wired `delay_seconds` from YAML to Celery rate limiting via `get_domain_rate_limits()`. YAML is now single source of truth.
2. Added Celery Flower for task monitoring (standalone, no Docker).

**4.4.5 Fix**:
- imot.bg: 1.5s delay → 40 req/min (was 10)
- bazar.bg: 3.0s delay → 20 req/min (was 10)
- default: 2.0s delay → 30 req/min (was 10)

**5.2 Flower Setup**:
- Added `flower>=2.0.0` to requirements.txt
- Created `scripts/start_flower.sh`
- Added FLOWER_PORT, FLOWER_BROKER_API to settings.py
- Verified: Flower detects all 12 Celery tasks

**Files Modified**:
- `config/scraping_config.py` - Added `get_domain_rate_limits()`
- `config/settings.py` - DOMAIN_RATE_LIMITS + FLOWER settings
- `tests/test_site_config_overrides.py` - Updated tests
- `requirements.txt` - Added flower
- `scripts/start_flower.sh` - New start script

**Test Results**: 894 passed, 8 skipped

---

*(Sessions 46 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
