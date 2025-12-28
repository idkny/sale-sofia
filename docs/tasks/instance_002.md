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

Continue **Phase 4.3.3: Scraping Celery Tasks**:
- [ ] 4.3.3.1 Create `scraping/redis_keys.py` (key patterns)
- [ ] 4.3.3.2 Create `scraping/tasks.py` with dispatcher/worker/callback
- [ ] 4.3.3.3 Update `celery_app.py` to include `scraping.tasks`
- [ ] 4.3.3.4 Write unit tests for Celery tasks

Then proceed to:
- Phase 4.3.4: Integration

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

### 2025-12-28 (Session 43 - Phase 4.3.2 Redis Rate Limiter COMPLETE)

| Task | Status |
|------|--------|
| 4.3.2.1 Create redis_rate_limiter.py | Complete |
| 4.3.2.2 Add REDIS_RATE_LIMITER_ENABLED flag | Complete |
| 4.3.2.3 Update factory function | Complete |
| 4.3.2.4 Write unit tests | Complete |

**Summary**: Completed Phase 4.3.2: Created `resilience/redis_rate_limiter.py` with Lua script for atomic token acquisition (prevents race conditions across distributed workers). Added feature flag, updated factory function in `rate_limiter.py` to return either in-memory or Redis-backed rate limiter based on config. 29 new tests, 675 total passing.

**Files Created**:
- `resilience/redis_rate_limiter.py` - Redis-backed rate limiter with Lua script
- `tests/test_redis_rate_limiter.py` - 29 unit tests with fakeredis

**Files Modified**:
- `config/settings.py` - Added `REDIS_RATE_LIMITER_ENABLED = False`
- `resilience/rate_limiter.py` - Updated `get_rate_limiter()` factory function

---

### 2025-12-28 (Session 42 - Phase 4.3.1 Redis Circuit Breaker COMPLETE)

| Task | Status |
|------|--------|
| Fix pytest path issues | Complete |
| 4.3.1.1 Create redis_circuit_breaker.py | Complete |
| 4.3.1.2 Add REDIS_CIRCUIT_BREAKER_ENABLED flag | Complete |
| 4.3.1.3 Update factory function | Complete |
| 4.3.1.4 Verify tests pass | Complete |

**Summary**: Fixed pytest path issue - root cause was `tests/resilience/` directory shadowing the real `resilience/` module. Removed empty `tests/resilience/` directory. Completed Phase 4.3.1: added feature flag to settings, updated factory function in `circuit_breaker.py` to return either in-memory or Redis-backed circuit breaker based on config. All 35 Redis circuit breaker tests pass. Full suite: 646 tests passing.

**Files Modified**:
- `config/settings.py` - Added `REDIS_CIRCUIT_BREAKER_ENABLED = False`
- `resilience/circuit_breaker.py` - Updated `get_circuit_breaker()` factory function
- `tests/test_redis_circuit_breaker.py` - Cleaned up debug statements

**Files Deleted**:
- `tests/resilience/` - Removed shadowing directory

---

### 2025-12-28 (Session 41 - Phase 4.3.0.3 + 4.3.1.1 Partial)

| Task | Status |
|------|--------|
| 4.3.0.3 Add @retry_on_busy() to read functions | Complete |
| 4.3.1.1 Create redis_circuit_breaker.py | Complete |
| Write tests for redis_circuit_breaker | Complete |
| Fix pytest venv path issues | Blocked (fixed Session 42) |

**Summary**: Completed 4.3.0.3 (added @retry_on_busy() to 12 read functions, 563 tests passing). Created `resilience/redis_circuit_breaker.py` and 35 unit tests. Tests blocked by pytest path resolution issues.

**Files Created**:
- `resilience/redis_circuit_breaker.py` - Redis-backed circuit breaker (326 lines)
- `tests/test_redis_circuit_breaker.py` - 35 unit tests with fakeredis
- `tests/conftest.py` - Pytest path configuration
- `conftest.py` - Root pytest configuration

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
