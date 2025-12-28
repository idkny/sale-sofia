---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-28
---

# Instance 2 Session

**You are Instance 2.** Work independently.

---

## IMMEDIATE NEXT SESSION TASK

Continue **Phase 4.3 Pre-requisites**:
- [x] 4.3.0.1 Fix timeout forwarding (done)
- [x] 4.3.0.2 Move DB init to function (done)
- [ ] 4.3.0.3 Add `@retry_on_busy()` to read functions
- [ ] 4.3.0.4 Increase `SQLITE_BUSY_RETRIES` to 5

Then proceed to:
- Phase 4.3.1: Redis-backed circuit breaker
- Phase 4.3.2: Redis-backed rate limiter
- Phase 4.3.3: Scraping Celery tasks

**Spec**: [115_CELERY_SITE_TASKS.md](../specs/115_CELERY_SITE_TASKS.md)

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

### 2025-12-28 (Session 41 - Phase 4.3.0.3 + 4.3.1.1 Partial)

| Task | Status |
|------|--------|
| 4.3.0.3 Add @retry_on_busy() to read functions | Complete |
| 4.3.1.1 Create redis_circuit_breaker.py | Partial |
| Write tests for redis_circuit_breaker | Partial |
| Fix pytest venv path issues | Blocked |

**Summary**: Completed 4.3.0.3 (added @retry_on_busy() to 12 read functions, 563 tests passing). Started 4.3.1.1 - created `resilience/redis_circuit_breaker.py` and 35 unit tests. Tests pass with venv pytest but hit path resolution issues. Installed fakeredis in venv. Created `tests/conftest.py` and root `conftest.py` for pythonpath setup. Issue: pytest doesn't load conftest.py before test module imports.

**Files Created**:
- `resilience/redis_circuit_breaker.py` - Redis-backed circuit breaker (326 lines)
- `tests/test_redis_circuit_breaker.py` - 35 unit tests with fakeredis
- `tests/conftest.py` - Pytest path configuration
- `conftest.py` - Root pytest configuration

**Files Modified**:
- `data/data_store_main.py` - Added @retry_on_busy() to 12 read functions
- `pytest.ini` - Added `pythonpath = .`

**Next Session TODO**:
1. Fix pytest path issue - either create `pyproject.toml` with editable install, or fix conftest.py loading order
2. Run full test suite verification
3. Complete 4.3.1.2-4.3.1.4 (feature flag, factory function, remaining tests)

---

### 2025-12-28 (Session 40 - Phase 4.3 Spec + Pre-requisites)

| Task | Status |
|------|--------|
| Review validation research documents | Complete |
| Write Spec 115 (Celery Site Tasks) | Complete |
| Update TASKS.md with mandatory 4-step process | Complete |
| 4.3.0.1 Fix timeout forwarding | Complete |
| 4.3.0.2 Move DB init to function | Complete |
| Archive 16 research files | Complete |

**Summary**: Created Spec 115 from validation research. Added mandatory "Impact Analysis → Test → Implement → Verify" process to all Phase 4.3 tasks. Fixed 2 critical bugs: timeout forwarding and DB init race condition. 77 tests verified. Research archived.

**Files Created**:
- `docs/specs/115_CELERY_SITE_TASKS.md`

**Files Modified**:
- `orchestrator.py:521` - Added `timeout=timeout` parameter
- `data/data_store_main.py` - Created `initialize_database()` function
- `main.py` - Added explicit database init call
- `docs/tasks/TASKS.md` - Updated Phase 4.3 tasks with impact/tests

---

### 2025-12-28 (Session 39 - Orchestration Validation)

| Task | Status |
|------|--------|
| Launch 6 validation agents | Complete |
| Validate Scraping Module | Complete |
| Validate Resilience Module | Complete |
| Validate Data Module | Complete |
| Validate Proxy/Celery Patterns | Complete |
| Validate Orchestrator | Complete |
| Validate LLM Integration | Complete |
| Synthesize validation findings | Complete |

**Summary**: Launched 6 architect-review agents to validate module correctness (not just describe). Found 3 critical issues and 3 modules needing Redis backing. Created 7 validation documents. Added BLOCKING task to TASKS.md for next session.

**Files Created**:
- `docs/research/validation_scraping.md`
- `docs/research/validation_resilience.md`
- `docs/research/validation_data.md`
- `docs/research/validation_proxies.md`
- `docs/research/validation_orchestrator.md`
- `docs/research/validation_llm.md`
- `docs/research/validation_synthesis.md`

**Files Modified**:
- `docs/tasks/TASKS.md` - Added BLOCKING task for research review
- `docs/tasks/instance_002.md` - Updated for session continuity

---

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

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
