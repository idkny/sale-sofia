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

### 2025-12-27 (Session 30 - Spec 112 Phase 2 + Cleanup + Consistency)

| Task | Status |
|------|--------|
| Implement circuit_breaker.py | ✅ Complete |
| Implement rate_limiter.py | ✅ Complete |
| Integrate circuit breaker into main.py | ✅ Complete |
| Integrate rate limiter into main.py | ✅ Complete |
| Update resilience/__init__.py exports | ✅ Complete |
| Write unit tests (42 tests) | ✅ Complete |
| Cleanup: Fix unused imports | ✅ Complete |
| Cleanup: Update docs (FILE_STRUCTURE, DESIGN_PATTERNS) | ✅ Complete |
| Cleanup: Update manifest.json | ✅ Complete |
| Consistency audit: Add 12 settings to config/settings.py | ✅ Complete |
| Consistency audit: Update error_classifier.py | ✅ Complete |
| Consistency audit: Update main.py preflight | ✅ Complete |

**Summary**: Implemented Spec 112 Phase 2 (Domain Protection). Created circuit breaker with fail-open design and token bucket rate limiter. Performed full cleanup: fixed unused imports, updated architecture docs, manifest. Consistency audit: added 12 new centralized settings (ERROR_RETRY_*, PREFLIGHT_*, etc.), updated all files to use them. All 87 tests passing.

**Files Created**:
- `resilience/circuit_breaker.py` - DomainCircuitBreaker with state transitions
- `resilience/rate_limiter.py` - DomainRateLimiter with token bucket
- `tests/test_resilience_phase2.py` (42 tests)

**Files Modified**:
- `main.py` - Circuit breaker, rate limiter, preflight settings
- `resilience/__init__.py` - Exports Phase 2 modules
- `resilience/error_classifier.py` - Uses ERROR_RETRY_* settings
- `resilience/exceptions.py` - Uses RATE_LIMIT_DEFAULT_RETRY_AFTER
- `resilience/retry.py` - Fixed unused import
- `config/settings.py` - Added 12 new settings
- `docs/architecture/FILE_STRUCTURE.md` - Added Phase 2 files
- `docs/architecture/DESIGN_PATTERNS.md` - Added patterns 12-13
- `admin/config/project_structure_manifest.json` - Added new files
- `docs/tasks/112_RESILIENCE_IMPLEMENTATION.md` - Updated consistency checks

---

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

*(Sessions 26 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
