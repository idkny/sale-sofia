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

### 2025-12-27 (Session 29 - Spec 112 Phase 1 Implementation)

| Task | Status |
|------|--------|
| Create resilience/ module structure | ✅ Complete |
| Implement exceptions.py | ✅ Complete |
| Implement error_classifier.py | ✅ Complete |
| Implement retry.py (backoff + jitter) | ✅ Complete |
| Add resilience settings to config/settings.py | ✅ Complete |
| Integrate retry decorator into main.py | ✅ Complete |
| Write unit tests (45 tests) | ✅ Complete |
| Consistency check + fixes | ✅ Complete |
| Update architecture docs | ✅ Complete |
| Update manifest.json | ✅ Complete |

**Summary**: Implemented Spec 112 Phase 1 (Foundation). Created `resilience/` module with exceptions, error_classifier, retry decorators. Integrated into main.py replacing manual retry loops. Fixed hardcoded timeouts in scrapling_base.py and proxy_validator.py. Updated architecture docs and manifest. Added CTO review tasks to remaining phases.

**Files Created**:
- `resilience/__init__.py`, `exceptions.py`, `error_classifier.py`, `retry.py`
- `tests/test_resilience_phase1.py` (45 tests)
- `docs/tasks/112_RESILIENCE_IMPLEMENTATION.md`

**Files Modified**:
- `main.py` - Uses retry decorators
- `config/settings.py` - Added RESILIENCE and PROXY_VALIDATION_TIMEOUT settings
- `websites/scrapling_base.py` - Uses centralized timeout settings
- `proxies/proxy_validator.py` - Uses PROXY_VALIDATION_TIMEOUT
- Architecture docs (ARCHITECTURE.md, FILE_STRUCTURE.md, DESIGN_PATTERNS.md)
- `admin/config/project_structure_manifest.json`

---

### 2025-12-27 (Session 28 - Scraper Resilience Research)

| Task | Status |
|------|--------|
| Analyze current scraper error handling | ✅ Complete |
| Research best practices (web search) | ✅ Complete |
| Explore AutoBiz codebase for patterns | ✅ Complete |
| Create research + spec documents | ✅ Complete |

**Summary**: Comprehensive research on scraper resilience. Found production-grade patterns in AutoBiz (circuit breaker, error system, rate limiter). Created spec 112 with 28 implementation tasks across 4 phases.

**Key AutoBiz References**:
- `core/_domain_circuit_breaker.py` - Circuit breaker pattern
- `core/_scraper_errors.py` - Error classification system
- `tools/scraping/_rate_limiter.py` - Rate limiting

---

### 2025-12-27 (Session 26 - TASKS.md Cleanup + Centralized Proxy Settings)

| Task | Status |
|------|--------|
| Clean up TASKS.md (remove duplicates, stale tasks) | ✅ Complete |
| Centralize proxy settings in config/settings.py | ✅ Complete |
| Fix inconsistent MIN_PROXIES values | ✅ Complete |

**Summary**: Cleaned up TASKS.md by removing duplicate JIT Proxy Validation (already in Solution F), homes.bg task, and P3 research tasks. Centralized proxy settings (`MUBENG_PROXY`, `MIN_PROXIES_TO_START`, `MIN_PROXIES_FOR_SCRAPING`, `MAX_PROXY_RETRIES`) in config/settings.py.

**Key Changes:**
- `config/settings.py` - Added proxy constants
- `main.py`, `websites/scrapling_base.py`, `proxies/proxies_main.py` - Import from config.settings

---

*(Sessions 13 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
