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

### 2025-12-28 (Session 45 - Phase 4.4.2 Site-Specific Config Overrides)

| Task | Status |
|------|--------|
| 4.4.2 Test site-specific config overrides | ✅ Complete |

**Summary**: Completed Phase 4.4.2 - tested site-specific configuration overrides. Created 14 tests covering config loading (5), chunk sizing (2), rate limits (2), integration (3), and gap documentation (2). **Key Finding**: `delay_seconds` from YAML config is not wired into Celery path - rate limiter uses `DOMAIN_RATE_LIMITS` from settings.py instead. This gap is documented in tests.

**Files Created**:
- `tests/test_site_config_overrides.py` - 14 tests

**Test Results**: 810 passed, 8 skipped

---

### 2025-12-28 (Session 44 - Phase 4.3.3 Scraping Celery Tasks)

| Task | Status |
|------|--------|
| 4.3.3.1 Create `scraping/redis_keys.py` | ✅ Complete |
| 4.3.3.2 Create `scraping/tasks.py` | ✅ Complete |
| 4.3.3.4 Write unit tests for Celery tasks | ✅ Complete |

**Summary**: Implemented Phase 4.3.3 Scraping Celery Tasks (3 of 4 tasks). Created `scraping/redis_keys.py` with ScrapingKeys class (8 key patterns, 22 tests). Created `scraping/tasks.py` with dispatcher/worker/callback pattern for parallel site scraping (25 tests). Task 4.3.3.3 (celery_app.py update) remains.

**Files Created**:
- `scraping/redis_keys.py` - ScrapingKeys class with Redis key patterns
- `scraping/tasks.py` - dispatch_site_scraping, scrape_chunk, aggregate_results, scrape_all_sites
- `tests/test_redis_keys.py` - 22 tests
- `tests/test_scraping_tasks.py` - 25 tests

**Test Results**: 769 passed, 8 skipped

*(Sessions 44 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
